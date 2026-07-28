#!/usr/bin/env python3
"""Wait for the schema-correct ARC repair submission to reach a terminal state.

This script is observational only. It never creates a kernel, changes predictions,
or submits another entry. It polls the exact accepted submission reference and
records its visible score, status, and current account rank.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "private_cycle_001"
LOG = OUT / "submission_55057282_poll.log"
COMPETITION = "arc-prize-2026-arc-agi-2"
SUBMISSION_REF = "55057282"
KERNEL_REF = "robertmorong/grobestreet-arc-frozen-v3-cycle-001"
KERNEL_VERSION = 10


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str], timeout: int = 180) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return completed.returncode, completed.stdout or ""


def normalize(row: dict[str, str]) -> dict[str, str]:
    return {
        "".join(character.lower() for character in key if character.isalnum()): value
        for key, value in row.items()
        if key
    }


def rows(text: str) -> list[dict[str, str]]:
    try:
        return [normalize(row) for row in csv.DictReader(text.splitlines())]
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


def as_float(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def find_submission(text: str) -> dict[str, str] | None:
    for row in rows(text):
        if first(row, "ref", "submissionRef", "id") == SUBMISSION_REF:
            return row
    return None


def rank_and_teams(text: str) -> tuple[int | None, int | None]:
    for row in rows(text):
        ref = first(row, "ref", "competition", "id") or ""
        if ref == COMPETITION or ref.endswith("/" + COMPETITION):
            rank_value = as_float(first(row, "userRank", "user rank", "rank"))
            team_value = as_float(first(row, "teamCount", "team count", "teams"))
            return (
                int(rank_value) if rank_value is not None else None,
                int(team_value) if team_value is not None else None,
            )
    return None, None


def write(record: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    record["observed_at_utc"] = now()
    (OUT / "submission_55057282_status.json").write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# ARC Cycle 001 — Repaired Submission 55057282",
        "",
        f"**State:** `{record.get('state')}`  ",
        f"**Observed:** {record['observed_at_utc']}  ",
        f"**Kernel:** `{KERNEL_REF}` version `{KERNEL_VERSION}`  ",
        f"**Submission ref:** `{SUBMISSION_REF}`",
        "",
        "## Official schema proof",
        "",
        "- 240 tasks: **validated**",
        "- 259 outputs: **validated**",
        "- Sample task IDs match: **true**",
        "- Hidden challenge task IDs match: **true**",
        "- Submission SHA-256: `457a36b6ed4b360a3e7d95a79c4de144b1c27051ce3559473901b33d6fc60a6d`",
        "",
        "## Kaggle record",
        "",
        f"- Status: `{record.get('submission_status') or 'not available'}`",
        f"- Public score: **{record.get('public_score') if record.get('public_score') is not None else 'not available'}**",
        f"- Public rank: **{record.get('public_rank') if record.get('public_rank') not in (None, 0) else 'not available'}**",
        f"- Teams: **{record.get('team_count') or 'not available'}**",
        "",
        "## Interpretation",
        "",
        record.get("interpretation", "No interpretation recorded."),
    ]
    if record.get("error"):
        lines.extend(["", "## Error", "", "```text", str(record["error"]), "```"])
    markdown = "\n".join(lines) + "\n"
    (OUT / "SUBMISSION_55057282_STATUS.md").write_text(markdown, encoding="utf-8")
    (OUT / "RESULT.md").write_text(markdown, encoding="utf-8")
    (REPO / "PRIVATE_CYCLE_001_STATUS.md").write_text(markdown, encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("KAGGLE_API_TOKEN", "").strip() or os.environ.get("KAGGLE_KEY", "").strip()
    record: dict[str, Any] = {
        "cycle": "private-v3-cycle-001",
        "state": "POLLING_REPAIRED_SUBMISSION",
        "competition": COMPETITION,
        "kernel_ref": KERNEL_REF,
        "kernel_version": KERNEL_VERSION,
        "frozen_solver_commit": "70672f3aa62d089bfffd072461a5713caae1e099",
        "mechanical_repair": "PRIVATE_CYCLE_001_SCORING_REPAIR.md",
        "supersedes_scoring_error_submission": "55037417",
        "submission_ref": SUBMISSION_REF,
        "submission_status": None,
        "public_score": None,
        "public_rank": None,
        "team_count": None,
        "accepted_at_utc": "2026-07-28T14:17:46.087000Z",
        "schema_validation": {
            "task_count": 240,
            "output_count": 259,
            "sample_task_ids_match": True,
            "challenge_task_ids_match": True,
            "submission_sha256": "457a36b6ed4b360a3e7d95a79c4de144b1c27051ce3559473901b33d6fc60a6d",
        },
    }
    if not token:
        record.update(
            state="BLOCKED_AUTH",
            error="Kaggle token unavailable to status watcher.",
            interpretation="The accepted submission exists, but its status could not be refreshed.",
        )
        write(record)
        return 0

    deadline = time.time() + 5400
    observations: list[str] = []
    latest_row: dict[str, str] | None = None
    entered_text = ""
    while True:
        rc, submission_text = run(
            ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"]
        )
        rc_entered, entered_text = run(
            ["kaggle", "competitions", "list", "--group", "entered", "-v"]
        )
        latest_row = find_submission(submission_text)
        status = first(latest_row, "status") or "MISSING"
        score_text = first(latest_row, "publicScore", "public score", "score")
        observations.append(f"{now()} rc={rc}/{rc_entered} status={status} score={score_text}")
        lowered = status.lower()
        if score_text is not None or any(token in lowered for token in ("error", "invalid", "failed")):
            break
        if "pending" not in lowered and "queued" not in lowered and "running" not in lowered:
            # COMPLETE with a blank score is still terminal enough to report accurately.
            break
        if time.time() >= deadline:
            break
        time.sleep(30)

    LOG.write_text("\n".join(observations) + "\n", encoding="utf-8")
    record["submission_status"] = first(latest_row, "status")
    record["public_score"] = as_float(first(latest_row, "publicScore", "public score", "score"))
    record["private_score"] = as_float(first(latest_row, "privateScore", "private score"))
    record["public_rank"], record["team_count"] = rank_and_teams(entered_text)
    status = str(record.get("submission_status") or "").lower()
    score = record.get("public_score")
    if any(token in status for token in ("error", "invalid", "failed")):
        record.update(
            state="REPAIRED_SUBMISSION_ERROR",
            error=record.get("submission_status"),
            interpretation="Kaggle could not score the schema-correct repaired submission. The exact status is preserved.",
        )
    elif score is not None and score > 0:
        record.update(
            state="SCORED_NONZERO",
            error=None,
            interpretation="The schema-correct repaired frozen v3 submission achieved a nonzero visible public score. Cycle 001 is terminal.",
        )
    elif score == 0:
        record.update(
            state="SCORED_NULL",
            error=None,
            interpretation="The schema-correct repaired frozen v3 submission received a visible score of zero. This valid null is the terminal Cycle 001 result.",
        )
    elif "complete" in status:
        record.update(
            state="COMPLETE_SCORE_NOT_EXPOSED",
            error=None,
            interpretation="Kaggle completed the repaired submission but did not expose a numeric public score through the authenticated API at observation time.",
        )
    else:
        record.update(
            state="REPAIRED_SUBMISSION_SCORE_PENDING",
            error=None,
            interpretation="Kaggle accepted the schema-correct repaired submission and it remained in the scoring queue when the watcher timed out.",
        )
    write(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
