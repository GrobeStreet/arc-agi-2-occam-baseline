#!/usr/bin/env python3
"""Submit the repaired, already-complete ARC Cycle 001 kernel version 10.

This is a mechanical repair submission. It does not push a new kernel or alter the
frozen v3 solver. Before using one competition submission, it independently checks
that the latest completed kernel output matches the official ARC Prize 2026 sample
submission and hidden challenge schema: 240 tasks and 259 test outputs.
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
RESULT_DIR = REPO / "results" / "private_cycle_001"
LOG_DIR = RESULT_DIR / "logs_version10_repair_submit"
VERIFY_DIR = RESULT_DIR / "verify_kernel_version_10"
COMPETITION_DIR = VERIFY_DIR / "competition"
KERNEL_OUTPUT_DIR = VERIFY_DIR / "kernel_output"
COMPETITION = "arc-prize-2026-arc-agi-2"
KERNEL_REF = "robertmorong/grobestreet-arc-frozen-v3-cycle-001"
KERNEL_VERSION = 10
FROZEN_COMMIT = "70672f3aa62d089bfffd072461a5713caae1e099"
MESSAGE = f"Frozen v3 Cycle 001 mechanical repair v10 official schema — {FROZEN_COMMIT[:12]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str], *, timeout: int = 900) -> dict[str, Any]:
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
            "timeout": timeout,
        }


def log(name: str, result: dict[str, Any], record: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / name).write_text(result.get("output", ""), encoding="utf-8")
    safe = dict(result)
    safe["output"] = str(safe.get("output", ""))[-20000:]
    record.setdefault("commands", []).append(safe)


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "".join(character.lower() for character in key if character.isalnum()): value
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
        normalized = "".join(character.lower() for character in key if character.isalnum())
        value = row.get(normalized)
        if value is not None and str(value).strip() not in {"", "None", "null", "nan"}:
            return str(value).strip()
    return None


def number(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def write_record(record: dict[str, Any]) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    record["updated_at"] = utc_now()
    payload = json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n"
    (RESULT_DIR / "result.json").write_text(payload, encoding="utf-8")
    (RESULT_DIR / "result_version10_repair.json").write_text(payload, encoding="utf-8")

    score = record.get("public_score")
    rank = record.get("public_rank")
    lines = [
        "# Frozen V3 Private Cycle 001 — Repaired Kaggle Result",
        "",
        f"**State:** `{record.get('state')}`  ",
        f"**Competition:** `{COMPETITION}`  ",
        f"**Frozen solver source:** `{FROZEN_COMMIT}`  ",
        f"**Kernel:** `{KERNEL_REF}` version `{KERNEL_VERSION}`  ",
        f"**Recorded:** {record['updated_at']}",
        "",
        "## Mechanical repair",
        "",
        "The solver, ranking, and two-output policy are unchanged. Version 10 fixes only the input-routing error that caused version 8 to run on the 120-task public evaluation file instead of the 240-task official competition test file.",
        "",
        "## Independent pre-submission validation",
        "",
        f"- Official task count: **{record.get('validated_task_count', 'not available')}**",
        f"- Official output count: **{record.get('validated_output_count', 'not available')}**",
        f"- Sample task IDs match: **{record.get('sample_task_ids_match', False)}**",
        f"- Challenge task IDs match: **{record.get('challenge_task_ids_match', False)}**",
        f"- Submission SHA-256: `{record.get('submission_sha256') or 'not available'}`",
        "",
        "## Official competition record",
        "",
        f"- Submission ref: `{record.get('submission_ref') or 'not available'}`",
        f"- Submission status: `{record.get('submission_status') or 'not available'}`",
        f"- Visible public score: **{score if score is not None else 'not available'}**",
        f"- Visible public rank: **{rank if rank not in (None, 0) else 'not available'}**",
        f"- Teams in snapshot: **{record.get('team_count') or 'not available'}**",
        "",
        "## Interpretation",
        "",
        record.get("interpretation", "No interpretation recorded."),
        "",
        "## Representation firewall",
        "",
        "Cycle 001 changes no model behavior. Any representation expansion requires a separately precommitted Cycle 002 registration.",
    ]
    if record.get("error"):
        lines.extend(["", "## Error", "", "```text", str(record["error"]), "```"])
    markdown = "\n".join(lines) + "\n"
    (RESULT_DIR / "RESULT.md").write_text(markdown, encoding="utf-8")
    (RESULT_DIR / "RESULT_VERSION10_REPAIR.md").write_text(markdown, encoding="utf-8")


def rectangular_grid(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    if not all(isinstance(row, list) and row for row in value):
        return False
    width = len(value[0])
    if any(len(row) != width for row in value):
        return False
    if len(value) > 30 or width > 30:
        return False
    return all(type(cell) is int and 0 <= cell <= 9 for row in value for cell in row)


def validate_submission(sample: dict[str, Any], challenges: dict[str, Any], submission: dict[str, Any]) -> tuple[int, int]:
    if set(sample) != set(challenges):
        raise ValueError("Official sample and official challenge task IDs differ")
    if set(submission) != set(sample):
        missing = sorted(set(sample) - set(submission))[:30]
        extra = sorted(set(submission) - set(sample))[:30]
        raise ValueError(f"Submission task IDs differ from official sample: missing={missing}, extra={extra}")

    outputs = 0
    for task_id in sorted(sample):
        sample_entries = sample[task_id]
        challenge_entries = challenges[task_id].get("test", [])
        predicted_entries = submission[task_id]
        if not isinstance(sample_entries, list) or not isinstance(predicted_entries, list):
            raise ValueError(f"{task_id}: expected list-valued output entries")
        if len(sample_entries) != len(challenge_entries) or len(predicted_entries) != len(sample_entries):
            raise ValueError(
                f"{task_id}: output counts differ: sample={len(sample_entries)}, "
                f"challenges={len(challenge_entries)}, submission={len(predicted_entries)}"
            )
        outputs += len(predicted_entries)
        for index, entry in enumerate(predicted_entries):
            if not isinstance(entry, dict) or set(entry) != {"attempt_1", "attempt_2"}:
                raise ValueError(f"{task_id}[{index}]: expected exactly attempt_1 and attempt_2")
            for attempt in ("attempt_1", "attempt_2"):
                if not rectangular_grid(entry[attempt]):
                    raise ValueError(f"{task_id}[{index}].{attempt}: invalid ARC grid")

    if len(submission) != 240 or outputs != 259:
        raise ValueError(f"Expected 240 tasks / 259 outputs, got {len(submission)} / {outputs}")
    return len(submission), outputs


def find_file(root: Path, name: str) -> Path:
    matches = sorted(root.rglob(name))
    if not matches:
        raise FileNotFoundError(f"Could not locate {name} under {root}")
    return matches[0]


def prepare_and_validate(record: dict[str, Any]) -> Path:
    shutil.rmtree(VERIFY_DIR, ignore_errors=True)
    COMPETITION_DIR.mkdir(parents=True, exist_ok=True)
    KERNEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    repository_push_log = RESULT_DIR / "logs" / "02_kernel_push.txt"
    if not repository_push_log.is_file() or f"Kernel version {KERNEL_VERSION} successfully pushed" not in repository_push_log.read_text(encoding="utf-8"):
        raise RuntimeError("Repository evidence does not identify completed repaired kernel version 10")

    status = run(["kaggle", "kernels", "status", KERNEL_REF], timeout=180)
    log("00_kernel_status.txt", status, record)
    if status["returncode"] != 0 or "complete" not in status["output"].lower():
        raise RuntimeError("Repaired kernel is not COMPLETE: " + status["output"][-5000:])

    output = run(
        ["kaggle", "kernels", "output", KERNEL_REF, "-p", str(KERNEL_OUTPUT_DIR), "-o", "-q"],
        timeout=1200,
    )
    log("01_kernel_output.txt", output, record)
    if output["returncode"] != 0:
        raise RuntimeError("Could not download repaired kernel output: " + output["output"][-5000:])

    validation_path = KERNEL_OUTPUT_DIR / "private_v3_cycle_001_schema_validation.json"
    submission_path = KERNEL_OUTPUT_DIR / "submission.json"
    if not validation_path.is_file() or not submission_path.is_file():
        raise RuntimeError("Repaired kernel output is missing schema validation or submission.json")
    kernel_validation = json.loads(validation_path.read_text(encoding="utf-8"))
    expected_validation = {
        "task_count": 240,
        "output_count": 259,
        "sample_task_ids_match": True,
        "challenge_task_ids_match": True,
    }
    for key, expected in expected_validation.items():
        if kernel_validation.get(key) != expected:
            raise RuntimeError(f"Kernel schema validation failed for {key}: {kernel_validation.get(key)!r} != {expected!r}")

    download = run(
        ["kaggle", "competitions", "download", COMPETITION, "-p", str(COMPETITION_DIR), "-q"],
        timeout=1800,
    )
    log("02_competition_download.txt", download, record)
    if download["returncode"] != 0:
        raise RuntimeError("Could not download official competition files: " + download["output"][-5000:])
    for archive in COMPETITION_DIR.rglob("*.zip"):
        with zipfile.ZipFile(archive) as handle:
            handle.extractall(COMPETITION_DIR / archive.stem)

    sample_path = find_file(COMPETITION_DIR, "sample_submission.json")
    challenge_path = find_file(COMPETITION_DIR, "arc-agi_test_challenges.json")
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    challenges = json.loads(challenge_path.read_text(encoding="utf-8"))
    submission = json.loads(submission_path.read_text(encoding="utf-8"))
    tasks, outputs = validate_submission(sample, challenges, submission)

    import hashlib
    digest = hashlib.sha256(submission_path.read_bytes()).hexdigest()
    record.update(
        validated_task_count=tasks,
        validated_output_count=outputs,
        sample_task_ids_match=True,
        challenge_task_ids_match=True,
        submission_sha256=digest,
        kernel_schema_validation=kernel_validation,
    )
    return submission_path


def target_submission(rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in rows:
        description = first(row, "description", "message") or ""
        if MESSAGE in description or "mechanical repair v10 official schema" in description:
            return row
    return None


def refresh(record: dict[str, Any], *, wait_seconds: int = 2400) -> None:
    deadline = time.time() + wait_seconds
    submissions_text = ""
    entered_text = ""
    matched: dict[str, str] | None = None
    while True:
        submissions = run(["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"], timeout=180)
        entered = run(["kaggle", "competitions", "list", "--group", "entered", "-v"], timeout=180)
        submissions_text = submissions["output"]
        entered_text = entered["output"]
        matched = target_submission(parse_csv(submissions_text))
        score = first(matched, "publicScore", "public score", "score")
        status = (first(matched, "status") or "").lower()
        if score is not None or any(token in status for token in ("error", "invalid", "failed")):
            break
        if time.time() >= deadline:
            break
        time.sleep(30)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "05_submissions.csv").write_text(submissions_text, encoding="utf-8")
    (LOG_DIR / "06_entered_competitions.csv").write_text(entered_text, encoding="utf-8")
    matched = target_submission(parse_csv(submissions_text))
    record["submission_ref"] = first(matched, "ref", "submissionRef", "id") or record.get("submission_ref")
    record["submission_status"] = first(matched, "status") or record.get("submission_status")
    record["public_score"] = number(first(matched, "publicScore", "public score", "score"))
    record["private_score"] = number(first(matched, "privateScore", "private score"))
    for row in parse_csv(entered_text):
        ref = first(row, "ref", "competition", "id") or ""
        if ref == COMPETITION or ref.endswith("/" + COMPETITION):
            rank = number(first(row, "userRank", "user rank", "rank"))
            teams = number(first(row, "teamCount", "team count", "teams"))
            record["public_rank"] = int(rank) if rank is not None else None
            record["team_count"] = int(teams) if teams is not None else None
            break


def terminalize(record: dict[str, Any], submit_returncode: int | None = None) -> None:
    score = record.get("public_score")
    status = str(record.get("submission_status") or "").lower()
    if any(token in status for token in ("error", "invalid", "failed")):
        record.update(
            state="SUBMISSION_ERROR",
            error=record.get("submission_status"),
            interpretation="Kaggle rejected or could not score the mechanically repaired version-10 submission.",
        )
    elif score is not None and score > 0:
        record.update(
            state="SCORED_NONZERO",
            error=None,
            interpretation="The repaired frozen v3 artifact achieved a nonzero visible Kaggle score. Cycle 001 is terminal.",
        )
    elif score == 0:
        record.update(
            state="SCORED_NULL",
            error=None,
            interpretation="The repaired frozen v3 artifact received a visible score of zero. The valid null result is preserved and Cycle 001 is terminal.",
        )
    elif record.get("submission_ref") or submit_returncode == 0:
        record.update(
            state="SUBMITTED_SCORE_PENDING",
            error=None,
            interpretation="Kaggle accepted repaired immutable kernel version 10; scoring or rank remained pending when recorded.",
        )
    else:
        record.update(
            state="SUBMISSION_FAILED",
            interpretation="Kaggle did not accept the mechanically repaired version-10 code submission.",
        )


def main() -> int:
    record: dict[str, Any] = {
        "cycle": "private-v3-cycle-001",
        "repair": "PRIVATE_CYCLE_001_SCORING_REPAIR.md",
        "competition": COMPETITION,
        "state": "VERIFYING_REPAIRED_KERNEL_VERSION_10",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "frozen_source_commit": FROZEN_COMMIT,
        "kernel_ref": KERNEL_REF,
        "kernel_version": KERNEL_VERSION,
        "submission_ref": None,
        "submission_status": None,
        "public_score": None,
        "private_score": None,
        "public_rank": None,
        "team_count": None,
        "commands": [],
        "provenance": {
            "version8_scoring_error_submission": "55037417",
            "diagnosis_commit": "100c6a1352cb38cf8c8ee019acfb82af9775f759",
            "repair_registration_commit": "5bcf58ae2029c3fc921da482592537bae6f164a6",
            "repaired_kernel_output_commit": "428ecd9df60d8deb6b7a05a3922f6ba6ddfbe41f",
        },
    }

    if not (os.environ.get("KAGGLE_API_TOKEN", "").strip() or os.environ.get("KAGGLE_KEY", "").strip()):
        record.update(
            state="BLOCKED_AUTH",
            error="Kaggle token unavailable to repaired direct-submission workflow.",
            interpretation="No repaired submission was attempted.",
        )
        write_record(record)
        return 0

    existing = run(["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"], timeout=180)
    log("03_existing_submissions.txt", existing, record)
    already = target_submission(parse_csv(existing["output"]))
    if already:
        record["submission_ref"] = first(already, "ref", "submissionRef", "id")
        record["interpretation"] = "The repaired version-10 submission already exists; no duplicate was created."
        refresh(record, wait_seconds=1800)
        terminalize(record, 0)
        write_record(record)
        return 0

    try:
        prepare_and_validate(record)
    except Exception as exc:
        record.update(
            state="REPAIRED_KERNEL_VALIDATION_FAILED",
            error=str(exc),
            interpretation="The repaired output did not pass independent official-schema validation; no competition submission was attempted.",
        )
        write_record(record)
        return 0

    limits = run(["kaggle", "competitions", "submission-limits", COMPETITION, "-v"], timeout=180)
    log("03b_submission_limits.txt", limits, record)

    submit = run(
        [
            "kaggle", "competitions", "submit", COMPETITION,
            "-f", "submission.json",
            "-k", KERNEL_REF,
            "-v", str(KERNEL_VERSION),
            "-m", MESSAGE,
        ],
        timeout=300,
    )
    log("04_competition_submit.txt", submit, record)
    ref_match = re.search(r"(?i)submission\s+ref:\s*(\d+)", submit["output"])
    if ref_match:
        record["submission_ref"] = ref_match.group(1)

    if submit["returncode"] != 0 and not record.get("submission_ref"):
        record["error"] = submit["output"][-20000:]
        terminalize(record, submit["returncode"])
        write_record(record)
        return 0

    record.update(
        state="SUBMITTED_SCORE_PENDING",
        error=None,
        interpretation="Kaggle accepted repaired immutable kernel version 10; polling for score and rank.",
    )
    write_record(record)
    refresh(record, wait_seconds=2400)
    terminalize(record, submit["returncode"])
    write_record(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
