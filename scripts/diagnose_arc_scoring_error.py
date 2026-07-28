#!/usr/bin/env python3
"""Forensically diagnose the frozen ARC Cycle 001 scoring error.

This script is observational. It never creates a kernel or submits a prediction.
It downloads the official competition bundle and the completed kernel output,
compares submission.json against sample_submission.json and the hidden challenge
schema, and inspects the Kaggle Python client for any error details not exposed by
`kaggle competitions submissions`.
"""
from __future__ import annotations

import inspect
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "private_cycle_001" / "scoring_diagnosis"
WORK = OUT / "work"
COMPETITION = "arc-prize-2026-arc-agi-2"
KERNEL = "robertmorong/grobestreet-arc-frozen-v3-cycle-001"
SUBMISSION_REF = "55037417"


def run(command: list[str], *, cwd: Path | None = None, timeout: int = 1800) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd or REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "output": completed.stdout or "",
    }


def jsonable(value: Any, depth: int = 0) -> Any:
    if depth > 5:
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): jsonable(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v, depth + 1) for v in value]
    if hasattr(value, "to_dict"):
        try:
            return jsonable(value.to_dict(), depth + 1)
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        try:
            return {
                str(k): jsonable(v, depth + 1)
                for k, v in vars(value).items()
                if not str(k).startswith("_")
            }
        except Exception:
            pass
    return repr(value)


def find_one(root: Path, names: list[str]) -> Path | None:
    for name in names:
        matches = sorted(root.rglob(name))
        if matches:
            return matches[0]
    return None


def rectangular_grid(value: Any) -> tuple[bool, str, tuple[int, int] | None]:
    if not isinstance(value, list) or not value:
        return False, "not a non-empty list", None
    if not all(isinstance(row, list) and row for row in value):
        return False, "contains a non-list or empty row", None
    width = len(value[0])
    if any(len(row) != width for row in value):
        return False, "ragged rows", None
    for row in value:
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                return False, f"invalid cell {cell!r} ({type(cell).__name__})", None
    return True, "ok", (len(value), width)


def validate_submission(
    sample: dict[str, Any],
    challenges: dict[str, Any],
    submission: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    sample_keys = set(sample)
    challenge_keys = set(challenges)
    submission_keys = set(submission)

    if submission_keys != sample_keys:
        errors.append(
            "submission task IDs differ from sample_submission: "
            f"missing={sorted(sample_keys - submission_keys)[:20]} "
            f"extra={sorted(submission_keys - sample_keys)[:20]}"
        )
    if submission_keys != challenge_keys:
        errors.append(
            "submission task IDs differ from test challenges: "
            f"missing={sorted(challenge_keys - submission_keys)[:20]} "
            f"extra={sorted(submission_keys - challenge_keys)[:20]}"
        )

    duplicate_attempts = 0
    shapes: list[tuple[int, int]] = []
    output_count = 0
    sample_output_count = 0
    challenge_output_count = 0

    for task_id in sorted(sample_keys | challenge_keys | submission_keys):
        sample_entries = sample.get(task_id)
        challenge = challenges.get(task_id)
        entries = submission.get(task_id)
        expected_from_challenge = len(challenge.get("test", [])) if isinstance(challenge, dict) else None
        expected_from_sample = len(sample_entries) if isinstance(sample_entries, list) else None
        if expected_from_sample is not None:
            sample_output_count += expected_from_sample
        if expected_from_challenge is not None:
            challenge_output_count += expected_from_challenge

        if not isinstance(entries, list):
            errors.append(f"{task_id}: submission value is not a list")
            continue
        output_count += len(entries)
        if expected_from_sample is not None and len(entries) != expected_from_sample:
            errors.append(
                f"{task_id}: {len(entries)} outputs but sample expects {expected_from_sample}"
            )
        if expected_from_challenge is not None and len(entries) != expected_from_challenge:
            errors.append(
                f"{task_id}: {len(entries)} outputs but challenges contain {expected_from_challenge}"
            )

        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"{task_id}[{index}]: entry is not an object")
                continue
            if set(entry) != {"attempt_1", "attempt_2"}:
                errors.append(
                    f"{task_id}[{index}]: keys={sorted(entry)} instead of attempt_1/attempt_2"
                )
            checked: dict[str, Any] = {}
            for attempt in ("attempt_1", "attempt_2"):
                ok, reason, shape = rectangular_grid(entry.get(attempt))
                if not ok:
                    errors.append(f"{task_id}[{index}].{attempt}: {reason}")
                else:
                    checked[attempt] = entry[attempt]
                    assert shape is not None
                    shapes.append(shape)
                    if shape[0] > 30 or shape[1] > 30:
                        errors.append(
                            f"{task_id}[{index}].{attempt}: shape {shape} exceeds 30x30"
                        )
            if (
                "attempt_1" in checked
                and "attempt_2" in checked
                and checked["attempt_1"] == checked["attempt_2"]
            ):
                duplicate_attempts += 1

    if duplicate_attempts:
        warnings.append(
            f"{duplicate_attempts} test outputs contain identical attempt_1 and attempt_2"
        )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "task_counts": {
            "sample": len(sample_keys),
            "challenges": len(challenge_keys),
            "submission": len(submission_keys),
        },
        "output_counts": {
            "sample": sample_output_count,
            "challenges": challenge_output_count,
            "submission": output_count,
        },
        "shape_summary": {
            "min_rows": min((s[0] for s in shapes), default=None),
            "max_rows": max((s[0] for s in shapes), default=None),
            "min_cols": min((s[1] for s in shapes), default=None),
            "max_cols": max((s[1] for s in shapes), default=None),
        },
        "identical_attempt_pairs": duplicate_attempts,
    }


def inspect_kaggle_api() -> dict[str, Any]:
    report: dict[str, Any] = {}
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()
        methods = sorted(
            name
            for name in dir(api)
            if "submission" in name.lower() or "log" in name.lower()
        )
        report["candidate_methods"] = methods
        signatures: dict[str, str] = {}
        for name in methods:
            try:
                signatures[name] = str(inspect.signature(getattr(api, name)))
            except Exception:
                signatures[name] = "signature unavailable"
        report["method_signatures"] = signatures

        submissions = api.competition_submissions(COMPETITION)
        serialized = [jsonable(item) for item in submissions]
        report["submission_objects"] = serialized
        matches = []
        for raw, item in zip(serialized, submissions):
            text = json.dumps(raw, sort_keys=True, default=str)
            if SUBMISSION_REF in text or SUBMISSION_REF in repr(item):
                matches.append(raw)
        report["matched_submission_objects"] = matches

        # Try likely log/error methods without assuming a particular CLI release.
        attempts: list[dict[str, Any]] = []
        for name in methods:
            lowered = name.lower()
            if "log" not in lowered and "submission" not in lowered:
                continue
            method = getattr(api, name)
            try:
                sig = inspect.signature(method)
            except Exception:
                continue
            params = list(sig.parameters)
            candidate_args: list[tuple[Any, ...]] = []
            if len(params) == 1:
                candidate_args = [(SUBMISSION_REF,), (int(SUBMISSION_REF),), (COMPETITION,)]
            elif len(params) == 2:
                candidate_args = [
                    (COMPETITION, SUBMISSION_REF),
                    (COMPETITION, int(SUBMISSION_REF)),
                ]
            for args in candidate_args:
                try:
                    result = method(*args)
                    attempts.append(
                        {"method": name, "args": list(args), "ok": True, "result": jsonable(result)}
                    )
                except Exception as exc:
                    attempts.append(
                        {"method": name, "args": list(args), "ok": False, "error": repr(exc)}
                    )
        report["method_attempts"] = attempts
    except Exception as exc:
        report["fatal_error"] = repr(exc)
    return report


def main() -> int:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    record: dict[str, Any] = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "competition": COMPETITION,
        "kernel": KERNEL,
        "submission_ref": SUBMISSION_REF,
        "authenticated": bool(
            os.environ.get("KAGGLE_API_TOKEN", "").strip()
            or os.environ.get("KAGGLE_KEY", "").strip()
        ),
        "commands": {},
    }

    commands = {
        "kaggle_version": ["kaggle", "--version"],
        "submissions": ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"],
        "competition_logs_help": ["kaggle", "competitions", "logs", "--help"],
        "competition_logs_by_competition": ["kaggle", "competitions", "logs", COMPETITION],
        "competition_logs_by_submission": ["kaggle", "competitions", "logs", SUBMISSION_REF],
    }
    for name, command in commands.items():
        try:
            result = run(command, timeout=600)
        except Exception as exc:
            result = {"command": command, "returncode": 999, "output": repr(exc)}
        record["commands"][name] = result
        (OUT / f"{name}.txt").write_text(result["output"], encoding="utf-8")

    competition_dir = WORK / "competition"
    kernel_dir = WORK / "kernel_output"
    competition_dir.mkdir(parents=True, exist_ok=True)
    kernel_dir.mkdir(parents=True, exist_ok=True)

    download_comp = run(
        ["kaggle", "competitions", "download", COMPETITION, "-p", str(competition_dir), "-q"],
        timeout=1800,
    )
    record["commands"]["competition_download"] = download_comp
    (OUT / "competition_download.txt").write_text(download_comp["output"], encoding="utf-8")

    for archive in competition_dir.rglob("*.zip"):
        try:
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(competition_dir / archive.stem)
        except Exception as exc:
            record.setdefault("archive_errors", []).append({"path": str(archive), "error": repr(exc)})

    kernel_output = run(
        ["kaggle", "kernels", "output", KERNEL, "-p", str(kernel_dir), "-o", "-q"],
        timeout=1800,
    )
    record["commands"]["kernel_output_download"] = kernel_output
    (OUT / "kernel_output_download.txt").write_text(kernel_output["output"], encoding="utf-8")

    sample_path = find_one(competition_dir, ["sample_submission.json"])
    challenges_path = find_one(competition_dir, ["arc-agi_test_challenges.json"])
    submission_path = find_one(kernel_dir, ["submission.json"])
    metadata_path = find_one(kernel_dir, ["submission_v3_metadata.json"])
    record["located_files"] = {
        "sample_submission": str(sample_path) if sample_path else None,
        "test_challenges": str(challenges_path) if challenges_path else None,
        "kernel_submission": str(submission_path) if submission_path else None,
        "kernel_metadata": str(metadata_path) if metadata_path else None,
    }

    if sample_path and challenges_path and submission_path:
        try:
            sample = json.loads(sample_path.read_text(encoding="utf-8"))
            challenges = json.loads(challenges_path.read_text(encoding="utf-8"))
            submission = json.loads(submission_path.read_text(encoding="utf-8"))
            record["schema_validation"] = validate_submission(sample, challenges, submission)
            record["file_sizes"] = {
                "sample_submission": sample_path.stat().st_size,
                "test_challenges": challenges_path.stat().st_size,
                "kernel_submission": submission_path.stat().st_size,
            }
            if metadata_path:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                record["kernel_metadata_summary"] = {
                    "solver": metadata.get("solver"),
                    "challenge_file": metadata.get("challenge_file"),
                    "task_count": metadata.get("task_count"),
                    "output_count": metadata.get("output_count"),
                }
        except Exception as exc:
            record["validation_error"] = repr(exc)
    else:
        record["validation_error"] = "Could not locate sample, challenge, and generated submission files."

    record["kaggle_api_introspection"] = inspect_kaggle_api()

    diagnosis_path = OUT / "diagnosis.json"
    diagnosis_path.write_text(json.dumps(record, indent=2, default=str) + "\n", encoding="utf-8")

    schema = record.get("schema_validation", {})
    matched = record.get("kaggle_api_introspection", {}).get("matched_submission_objects", [])
    lines = [
        "# ARC Cycle 001 — Scoring Error Diagnosis",
        "",
        f"**Observed:** {record['observed_at']}  ",
        f"**Submission:** `{SUBMISSION_REF}`  ",
        f"**Kernel:** `{KERNEL}`",
        "",
        "## Schema comparison",
        "",
        f"- Valid against downloaded sample and challenges: **{schema.get('valid', 'unavailable')}**",
        f"- Task counts: `{schema.get('task_counts')}`",
        f"- Output counts: `{schema.get('output_counts')}`",
        f"- Shape summary: `{schema.get('shape_summary')}`",
        f"- Identical attempt pairs: `{schema.get('identical_attempt_pairs')}`",
        "",
    ]
    errors = schema.get("errors", [])
    warnings = schema.get("warnings", [])
    lines += ["## Validation errors", ""]
    lines += [f"- {item}" for item in errors] or ["- None detected by the local validator."]
    lines += ["", "## Warnings", ""]
    lines += [f"- {item}" for item in warnings] or ["- None."]
    lines += ["", "## Kaggle submission object", "", "```json"]
    lines.append(json.dumps(matched, indent=2, default=str)[:30000])
    lines += ["```", "", "## Located files", "", "```json"]
    lines.append(json.dumps(record.get("located_files", {}), indent=2))
    lines += ["```", ""]
    (OUT / "DIAGNOSIS.md").write_text("\n".join(lines), encoding="utf-8")
    print((OUT / "DIAGNOSIS.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
