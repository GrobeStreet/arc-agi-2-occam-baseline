#!/usr/bin/env python3
"""Submit repaired frozen ARC Cycle 001 kernel version 10.

This is a mechanical replacement for scoring-error submission 55037417. It does
not push a new kernel or modify any prediction. Before submission it downloads
kernel version 10's output, downloads the official competition bundle, and proves
that submission.json has exactly the same 240 task IDs and 259 output slots as
both sample_submission.json and arc-agi_test_challenges.json.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
RESULT_DIR = REPO / "results" / "private_cycle_001" / "scoring_repair_v10"
LOG_DIR = RESULT_DIR / "logs"
VERIFY_DIR = RESULT_DIR / "verify"
COMPETITION = "arc-prize-2026-arc-agi-2"
KERNEL_REF = "robertmorong/grobestreet-arc-frozen-v3-cycle-001"
KERNEL_VERSION = 10
FROZEN_COMMIT = "70672f3aa62d089bfffd072461a5713caae1e099"
SUPERSEDES_SUBMISSION = "55037417"
MESSAGE = (
    "Frozen v3 Cycle 001 scoring repair — official 240/259 schema — "
    + FROZEN_COMMIT[:12]
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str], *, timeout: int = 1800) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "seconds": round(time.time() - started, 3),
            "output": completed.stdout or "",
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "command": command,
            "returncode": 124,
            "seconds": round(time.time() - started, 3),
            "output": stdout + stderr,
        }


def log(name: str, result: dict[str, Any], record: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / name).write_text(result.get("output", ""), encoding="utf-8")
    safe = dict(result)
    safe["output"] = str(safe.get("output", ""))[-20000:]
    record.setdefault("commands", []).append(safe)


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "".join(ch.lower() for ch in key if ch.isalnum()): value
        for key, value in row.items()
        if key
    }


def parse_csv(text: str) -> list[dict[str, str]]:
    try:
        return [normalize_row(row) for row in csv.DictReader(text.splitlines())]
    except Exception:
        return []


def first(row: dict[str, str] | None, *keys: str) -> str | None:
    if not row:
        return None
    for key in keys:
        value = row.get("".join(ch.lower() for ch in key if ch.isalnum()))
        if value is not None and str(value).strip() not in {"", "None", "null", "nan"}:
            return str(value).strip()
    return None


def number(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def find_file(root: Path, name: str) -> Path:
    matches = sorted(root.rglob(name))
    if not matches:
        raise FileNotFoundError(f"Could not find {name} under {root}")
    return matches[0]


def validate_grid(grid: Any, label: str) -> None:
    if not isinstance(grid, list) or not grid:
        raise ValueError(f"{label}: grid is not a non-empty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError(f"{label}: contains a non-list or empty row")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError(f"{label}: ragged rows")
    if len(grid) > 30 or width > 30:
        raise ValueError(f"{label}: grid exceeds 30x30")
    for row in grid:
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                raise ValueError(f"{label}: invalid cell {cell!r}")


def validate_official_schema(
    sample: dict[str, Any],
    challenges: dict[str, Any],
    submission: dict[str, Any],
) -> dict[str, Any]:
    if set(sample) != set(challenges) or set(sample) != set(submission):
        raise ValueError(
            "Task IDs differ among sample, official test challenges, and repaired submission"
        )
    output_count = 0
    for task_id in sorted(sample):
        sample_outputs = sample[task_id]
        challenge_outputs = challenges[task_id].get("test", [])
        submitted_outputs = submission[task_id]
        if not isinstance(sample_outputs, list) or not isinstance(submitted_outputs, list):
            raise ValueError(f"{task_id}: sample or submission entry is not a list")
        if not (
            len(sample_outputs) == len(challenge_outputs) == len(submitted_outputs)
        ):
            raise ValueError(
                f"{task_id}: output multiplicity differs: sample={len(sample_outputs)}, "
                f"challenge={len(challenge_outputs)}, submission={len(submitted_outputs)}"
            )
        output_count += len(submitted_outputs)
        for index, entry in enumerate(submitted_outputs):
            if not isinstance(entry, dict) or set(entry) != {"attempt_1", "attempt_2"}:
                raise ValueError(f"{task_id}[{index}]: invalid attempt keys")
            validate_grid(entry["attempt_1"], f"{task_id}[{index}].attempt_1")
            validate_grid(entry["attempt_2"], f"{task_id}[{index}].attempt_2")
    if len(submission) != 240 or output_count != 259:
        raise ValueError(
            f"Expected 240 tasks / 259 outputs, got {len(submission)} / {output_count}"
        )
    return {
        "valid": True,
        "task_count": len(submission),
        "output_count": output_count,
        "task_ids_match": True,
        "output_multiplicities_match": True,
    }


def write_record(record: dict[str, Any]) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    record["updated_at"] = now()
    (RESULT_DIR / "result.json").write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    score = record.get("public_score")
    rank = record.get("public_rank")
    lines = [
        "# ARC Cycle 001 — Version 10 Scoring Repair",
        "",
        f"**State:** `{record.get('state')}`  ",
        f"**Kernel:** `{KERNEL_REF}` version `{KERNEL_VERSION}`  ",
        f"**Frozen solver commit:** `{FROZEN_COMMIT}`  ",
        f"**Supersedes scoring-error submission:** `{SUPERSEDES_SUBMISSION}`  ",
        f"**Recorded:** {record['updated_at']}",
        "",
        "## Official schema proof",
        "",
        f"- 240 tasks / 259 outputs validated: **{record.get('schema_validation', {}).get('valid', False)}**",
        f"- Submission SHA-256: `{record.get('submission_sha256') or 'not available'}`",
        "",
        "## Competition record",
        "",
        f"- Submission ref: `{record.get('submission_ref') or 'not available'}`",
        f"- Submission status: `{record.get('submission_status') or 'not available'}`",
        f"- Public score: **{score if score is not None else 'not available'}**",
        f"- Public rank: **{rank if rank not in (None, 0) else 'not available'}**",
        f"- Teams: **{record.get('team_count') or 'not available'}**",
        "",
        "## Interpretation",
        "",
        record.get("interpretation", "No interpretation recorded."),
    ]
    if record.get("error"):
        lines += ["", "## Error", "", "```text", str(record["error"]), "```"]
    (RESULT_DIR / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def matching_repair_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in rows:
        description = first(row, "description", "message") or ""
        if "official 240/259 schema" in description or "scoring repair" in description.lower():
            return row
    return None


def refresh(record: dict[str, Any], *, wait_seconds: int = 2700) -> None:
    deadline = time.time() + wait_seconds
    submissions_text = ""
    entered_text = ""
    latest: dict[str, str] | None = None
    while True:
        submissions = run(
            ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"],
            timeout=180,
        )
        entered = run(
            ["kaggle", "competitions", "list", "--group", "entered", "-v"],
            timeout=180,
        )
        submissions_text = submissions["output"]
        entered_text = entered["output"]
        rows = parse_csv(submissions_text)
        latest = matching_repair_row(rows) or (rows[0] if rows else None)
        status = (first(latest, "status") or "").lower()
        score = first(latest, "publicScore", "public score", "score")
        if score is not None or any(token in status for token in ("error", "invalid", "failed")):
            break
        if time.time() >= deadline:
            break
        time.sleep(30)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "submissions.csv").write_text(submissions_text, encoding="utf-8")
    (LOG_DIR / "entered_competitions.csv").write_text(entered_text, encoding="utf-8")
    latest = matching_repair_row(parse_csv(submissions_text)) or latest
    record["submission_ref"] = first(latest, "ref", "id") or record.get("submission_ref")
    record["submission_status"] = first(latest, "status") or record.get("submission_status")
    record["public_score"] = number(first(latest, "publicScore", "public score", "score"))
    record["private_score"] = number(first(latest, "privateScore", "private score"))
    for row in parse_csv(entered_text):
        ref = first(row, "ref", "competition", "id") or ""
        if ref == COMPETITION or ref.endswith("/" + COMPETITION):
            rank_value = number(first(row, "userRank", "user rank", "rank"))
            team_value = number(first(row, "teamCount", "team count", "teams"))
            record["public_rank"] = int(rank_value) if rank_value is not None else None
            record["team_count"] = int(team_value) if team_value is not None else None
            break


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "cycle": "private-v3-cycle-001",
        "mechanical_repair": "PRIVATE_CYCLE_001_SCORING_REPAIR.md",
        "competition": COMPETITION,
        "state": "VERIFYING_REPAIRED_KERNEL_VERSION_10",
        "created_at": now(),
        "frozen_source_commit": FROZEN_COMMIT,
        "kernel_ref": KERNEL_REF,
        "kernel_version": KERNEL_VERSION,
        "supersedes_submission_ref": SUPERSEDES_SUBMISSION,
        "submission_ref": None,
        "submission_status": None,
        "public_score": None,
        "private_score": None,
        "public_rank": None,
        "team_count": None,
        "schema_validation": {},
        "commands": [],
    }

    if not (
        os.environ.get("KAGGLE_API_TOKEN", "").strip()
        or os.environ.get("KAGGLE_KEY", "").strip()
    ):
        record.update(
            state="BLOCKED_AUTH",
            error="Kaggle token unavailable.",
            interpretation="The repaired kernel was not submitted.",
        )
        write_record(record)
        return 0

    existing = run(
        ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"],
        timeout=180,
    )
    log("00_existing_submissions.txt", existing, record)
    existing_rows = parse_csv(existing["output"])
    if matching_repair_row(existing_rows):
        refresh(record, wait_seconds=1200)
        record["state"] = "REPAIR_SUBMISSION_ALREADY_EXISTS"
        record["interpretation"] = (
            "A schema-repaired competition submission already exists; no duplicate was created."
        )
        write_record(record)
        return 0

    status = run(["kaggle", "kernels", "status", KERNEL_REF], timeout=180)
    log("01_kernel_status.txt", status, record)
    if status["returncode"] != 0 or "complete" not in status["output"].lower():
        record.update(
            state="REPAIRED_KERNEL_NOT_COMPLETE",
            error=status["output"][-20000:],
            interpretation="Version 10 was not submitted because the kernel is not complete.",
        )
        write_record(record)
        return 0

    if VERIFY_DIR.exists():
        shutil.rmtree(VERIFY_DIR)
    kernel_dir = VERIFY_DIR / "kernel_output"
    competition_dir = VERIFY_DIR / "competition"
    kernel_dir.mkdir(parents=True, exist_ok=True)
    competition_dir.mkdir(parents=True, exist_ok=True)

    kernel_output = run(
        ["kaggle", "kernels", "output", KERNEL_REF, "-p", str(kernel_dir), "-o", "-q"],
        timeout=1200,
    )
    log("02_kernel_output.txt", kernel_output, record)
    if kernel_output["returncode"] != 0:
        raise RuntimeError(kernel_output["output"])

    competition_download = run(
        ["kaggle", "competitions", "download", COMPETITION, "-p", str(competition_dir), "-q"],
        timeout=1800,
    )
    log("03_competition_download.txt", competition_download, record)
    if competition_download["returncode"] != 0:
        raise RuntimeError(competition_download["output"])
    for archive in competition_dir.rglob("*.zip"):
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(competition_dir / archive.stem)

    submission_path = find_file(kernel_dir, "submission.json")
    schema_path = find_file(kernel_dir, "private_v3_cycle_001_schema_validation.json")
    sample_path = find_file(competition_dir, "sample_submission.json")
    challenge_path = find_file(competition_dir, "arc-agi_test_challenges.json")
    kernel_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if not (
        kernel_schema.get("task_count") == 240
        and kernel_schema.get("output_count") == 259
        and kernel_schema.get("sample_task_ids_match") is True
        and kernel_schema.get("challenge_task_ids_match") is True
    ):
        raise ValueError(f"Kernel schema certificate is invalid: {kernel_schema}")
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    challenges = json.loads(challenge_path.read_text(encoding="utf-8"))
    submission = json.loads(submission_path.read_text(encoding="utf-8"))
    validation = validate_official_schema(sample, challenges, submission)
    record["schema_validation"] = validation
    import hashlib

    record["submission_sha256"] = hashlib.sha256(submission_path.read_bytes()).hexdigest()
    record["schema_certificate"] = kernel_schema
    (RESULT_DIR / "official_schema_validation.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )

    submit = run(
        [
            "kaggle",
            "competitions",
            "submit",
            COMPETITION,
            "-f",
            "submission.json",
            "-k",
            KERNEL_REF,
            "-v",
            str(KERNEL_VERSION),
            "-m",
            MESSAGE,
        ],
        timeout=600,
    )
    log("04_submit.txt", submit, record)
    if submit["returncode"] != 0:
        record.update(
            state="REPAIR_SUBMISSION_FAILED",
            error=submit["output"][-20000:],
            interpretation="Kaggle rejected the schema-validated version-10 submission call.",
        )
        write_record(record)
        return 0

    record["state"] = "REPAIR_SUBMITTED_SCORE_PENDING"
    record["interpretation"] = (
        "Kaggle accepted frozen kernel version 10 after independent proof of the official "
        "240-task / 259-output schema. The prior version-8 scoring error is superseded."
    )
    refresh(record, wait_seconds=2700)
    score = record.get("public_score")
    status_text = str(record.get("submission_status") or "").lower()
    if score is not None and score > 0:
        record["state"] = "SCORED_NONZERO"
        record["interpretation"] = (
            "The schema-repaired frozen v3 artifact achieved a nonzero visible Kaggle score."
        )
    elif score == 0:
        record["state"] = "SCORED_NULL"
        record["interpretation"] = (
            "The schema-repaired frozen v3 artifact received a visible score of zero."
        )
    elif any(token in status_text for token in ("error", "invalid", "failed")):
        record["state"] = "REPAIR_SUBMISSION_SCORING_ERROR"
        record["error"] = record.get("submission_status")
        record["interpretation"] = (
            "Kaggle reported a scoring error despite exact official sample/challenge validation."
        )
    write_record(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
