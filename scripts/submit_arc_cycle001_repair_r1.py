#!/usr/bin/env python3
"""Submit the validated mechanical repair for ARC Private Cycle 001.

The representation-v3 solver, ranking, candidate generation, fallbacks, and two-
attempt policy remain identical to frozen commit 70672f3. Kernel version 10 changes
only input routing in the notebook wrapper and has already produced a submission
validated against the official 240-task / 259-output sample schema.
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "private_cycle_001" / "repair_r1"
LOGS = OUT / "logs"
COMPETITION = "arc-prize-2026-arc-agi-2"
KERNEL_REF = "robertmorong/grobestreet-arc-frozen-v3-cycle-001"
KERNEL_VERSION = 10
ORIGINAL_SUBMISSION_REF = "55037417"
BASE_SOLVER_COMMIT = "70672f3aa62d089bfffd072461a5713caae1e099"
MESSAGE = "Frozen v3 Cycle 001 — mechanical test-routing repair R1 — 240 tasks / 259 outputs"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str], timeout: int = 900) -> dict[str, Any]:
    started = time.time()
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


def log(name: str, result: dict[str, Any], record: dict[str, Any]) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / name).write_text(str(result.get("output", "")), encoding="utf-8")
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


def value(row: dict[str, str] | None, *keys: str) -> str | None:
    if not row:
        return None
    for key in keys:
        normalized = "".join(ch.lower() for ch in key if ch.isalnum())
        item = row.get(normalized)
        if item is not None and str(item).strip() not in {"", "None", "null", "nan"}:
            return str(item).strip()
    return None


def as_number(item: str | None) -> float | None:
    if item is None:
        return None
    try:
        return float(item)
    except (TypeError, ValueError):
        return None


def write_record(record: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    record["updated_at"] = now()
    (OUT / "result.json").write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    score = record.get("public_score")
    rank = record.get("public_rank")
    lines = [
        "# ARC Private Cycle 001 — Mechanical Repair R1",
        "",
        f"**State:** `{record.get('state')}`  ",
        f"**Kernel:** `{KERNEL_REF}` version `{KERNEL_VERSION}`  ",
        f"**Base solver:** `{BASE_SOLVER_COMMIT}`  ",
        f"**Original scoring-error submission:** `{ORIGINAL_SUBMISSION_REF}`  ",
        f"**Repaired submission ref:** `{record.get('submission_ref') or 'not available'}`  ",
        f"**Submission status:** `{record.get('submission_status') or 'not available'}`  ",
        f"**Public score:** **{score if score is not None else 'not available'}**  ",
        f"**Public rank:** **{rank if rank not in (None, 0) else 'not available'}**  ",
        f"**Recorded:** {record['updated_at']}",
        "",
        "## Schema gate",
        "",
        f"- Official task IDs matched: `{record.get('schema_validation', {}).get('sample_task_ids_match')}`",
        f"- Official challenge IDs matched: `{record.get('schema_validation', {}).get('challenge_task_ids_match')}`",
        f"- Task count: `{record.get('schema_validation', {}).get('task_count')}`",
        f"- Output count: `{record.get('schema_validation', {}).get('output_count')}`",
        "",
        "## Interpretation",
        "",
        record.get("interpretation", "No interpretation recorded."),
    ]
    if record.get("error"):
        lines += ["", "## Error", "", "```text", str(record["error"]), "```"]
    (OUT / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def choose_repair_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in rows:
        description = (value(row, "description") or "").lower()
        if "mechanical test-routing repair r1" in description:
            return row
    return None


def refresh(record: dict[str, Any], wait_seconds: int = 2400) -> None:
    deadline = time.time() + wait_seconds
    latest_submissions = ""
    latest_entered = ""
    while True:
        submissions = run(
            ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"],
            timeout=180,
        )
        entered = run(
            ["kaggle", "competitions", "list", "--group", "entered", "-v"],
            timeout=180,
        )
        latest_submissions = submissions["output"]
        latest_entered = entered["output"]
        row = choose_repair_row(parse_csv(latest_submissions))
        if row:
            record["submission_ref"] = value(row, "ref") or record.get("submission_ref")
            record["submission_status"] = value(row, "status")
            record["public_score"] = as_number(value(row, "publicScore", "score"))
            record["private_score"] = as_number(value(row, "privateScore"))
            status = (record.get("submission_status") or "").lower()
            if record["public_score"] is not None or any(
                token in status for token in ("error", "invalid", "failed")
            ):
                break
        if time.time() >= deadline:
            break
        time.sleep(30)

    (LOGS / "submissions.csv").write_text(latest_submissions, encoding="utf-8")
    (LOGS / "entered_competitions.csv").write_text(latest_entered, encoding="utf-8")
    for row in parse_csv(latest_entered):
        ref = value(row, "ref", "competition", "id") or ""
        if COMPETITION in ref:
            rank = as_number(value(row, "userRank", "rank"))
            teams = as_number(value(row, "teamCount", "teams"))
            record["public_rank"] = int(rank) if rank is not None else None
            record["team_count"] = int(teams) if teams is not None else None
            break


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "cycle": "private-v3-cycle-001-repair-r1",
        "competition": COMPETITION,
        "state": "INITIALIZING",
        "created_at": now(),
        "base_solver_commit": BASE_SOLVER_COMMIT,
        "kernel_ref": KERNEL_REF,
        "kernel_version": KERNEL_VERSION,
        "original_submission_ref": ORIGINAL_SUBMISSION_REF,
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
            interpretation="No repaired submission was attempted.",
        )
        write_record(record)
        return 0

    # Avoid duplicate repaired submissions if this workflow is re-run.
    existing = run(
        ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"],
        timeout=180,
    )
    log("00_existing_submissions.txt", existing, record)
    existing_row = choose_repair_row(parse_csv(existing["output"]))
    if existing_row:
        record["submission_ref"] = value(existing_row, "ref")
        record["submission_status"] = value(existing_row, "status")
        record["public_score"] = as_number(value(existing_row, "publicScore", "score"))
        record.update(
            state="REPAIR_ALREADY_SUBMITTED",
            interpretation="The repaired Cycle 001 submission already exists; no duplicate was created.",
        )
        refresh(record, wait_seconds=1200)
    else:
        status = run(["kaggle", "kernels", "status", KERNEL_REF], timeout=180)
        log("01_kernel_status.txt", status, record)
        if status["returncode"] != 0 or "complete" not in status["output"].lower():
            record.update(
                state="REPAIRED_KERNEL_NOT_COMPLETE",
                error=status["output"][-16000:],
                interpretation="No submission was attempted because repaired kernel version 10 is not complete.",
            )
            write_record(record)
            return 0

        kernel_dir = OUT / "kernel_output"
        if kernel_dir.exists():
            shutil.rmtree(kernel_dir)
        kernel_dir.mkdir(parents=True, exist_ok=True)
        pulled = run(
            ["kaggle", "kernels", "output", KERNEL_REF, "-p", str(kernel_dir), "-o", "-q"],
            timeout=900,
        )
        log("02_kernel_output.txt", pulled, record)
        validation_path = kernel_dir / "private_v3_cycle_001_schema_validation.json"
        submission_path = kernel_dir / "submission.json"
        if pulled["returncode"] != 0 or not validation_path.is_file() or not submission_path.is_file():
            record.update(
                state="REPAIRED_OUTPUT_MISSING",
                error=pulled["output"][-16000:] or "Validation or submission artifact missing.",
                interpretation="No repaired submission was attempted.",
            )
            write_record(record)
            return 0

        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        record["schema_validation"] = validation
        if not (
            validation.get("task_count") == 240
            and validation.get("output_count") == 259
            and validation.get("sample_task_ids_match") is True
            and validation.get("challenge_task_ids_match") is True
        ):
            record.update(
                state="SCHEMA_GATE_FAILED",
                error=json.dumps(validation, indent=2),
                interpretation="No repaired submission was attempted because official schema validation failed.",
            )
            write_record(record)
            return 0

        submitted = run(
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
            timeout=300,
        )
        log("03_competition_submit.txt", submitted, record)
        match = re.search(r"(?i)submission\s+ref:\s*(\d+)", submitted["output"])
        if match:
            record["submission_ref"] = match.group(1)
        if submitted["returncode"] != 0 and not record.get("submission_ref"):
            record.update(
                state="REPAIRED_SUBMISSION_FAILED",
                error=submitted["output"][-16000:],
                interpretation="Kaggle did not accept repaired kernel version 10.",
            )
            write_record(record)
            return 0
        record.update(
            state="REPAIRED_SUBMITTED_SCORE_PENDING",
            error=None,
            interpretation="Kaggle accepted the mechanically repaired frozen v3 submission; polling for score and rank.",
        )
        write_record(record)
        refresh(record, wait_seconds=2400)

    score = record.get("public_score")
    status_text = str(record.get("submission_status") or "").lower()
    if score is not None and score > 0:
        record.update(
            state="REPAIRED_SCORED_NONZERO",
            error=None,
            interpretation="The frozen v3 solver received a nonzero score after the registered mechanical input-routing repair.",
        )
    elif score == 0:
        record.update(
            state="REPAIRED_SCORED_NULL",
            error=None,
            interpretation="The frozen v3 solver received a visible zero after the registered mechanical input-routing repair.",
        )
    elif any(token in status_text for token in ("error", "invalid", "failed")):
        record.update(
            state="REPAIRED_SUBMISSION_ERROR",
            error=record.get("submission_status"),
            interpretation="Kaggle reported an error for the repaired submission; diagnostics are preserved.",
        )
    else:
        record.update(
            state="REPAIRED_SUBMITTED_SCORE_PENDING",
            error=None,
            interpretation="The repaired submission exists, but Kaggle has not yet exposed a public score.",
        )
    write_record(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
