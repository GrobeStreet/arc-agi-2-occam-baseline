#!/usr/bin/env python3
"""Submit the verified completed kernel version for frozen ARC Cycle 001.

This runner never pushes a kernel and never changes predictions. It verifies that
Kaggle kernel version 8 contains the frozen source commit and the registered
mechanical notebook repairs, then submits that version's `submission.json` by
its kernel-output filename, waits for scoring, and records score and rank.
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
RESULT_DIR = REPO / "results" / "private_cycle_001"
LOG_DIR = RESULT_DIR / "logs_version8_submit"
VERIFY_DIR = RESULT_DIR / "verify_kernel_version_8"
COMPETITION = "arc-prize-2026-arc-agi-2"
KERNEL_REF = "robertmorong/grobestreet-arc-frozen-v3-cycle-001"
KERNEL_VERSION = 8
FROZEN_COMMIT = "70672f3aa62d089bfffd072461a5713caae1e099"
MESSAGE = f"Frozen representation v3 — Private Cycle 001 — {FROZEN_COMMIT[:12]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(command: list[str], timeout: int = 900) -> dict[str, Any]:
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
    safe["output"] = str(safe.get("output", ""))[-16000:]
    record.setdefault("commands", []).append(safe)


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "".join(char.lower() for char in key if char.isalnum()): value
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
        value = row.get("".join(char.lower() for char in key if char.isalnum()))
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
    (RESULT_DIR / "result.json").write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Frozen V3 Private Cycle 001 — Kaggle Result",
        "",
        f"**State:** `{record.get('state')}`  ",
        f"**Competition:** `{COMPETITION}`  ",
        f"**Frozen source:** `{FROZEN_COMMIT}`  ",
        f"**Kernel:** `{KERNEL_REF}` version `{KERNEL_VERSION}`  ",
        f"**Recorded:** {record['updated_at']}",
        "",
        "## Official competition record",
        "",
        f"- Submission ref: `{record.get('submission_ref') or 'not available'}`",
        f"- Submission status: `{record.get('submission_status') or 'not available'}`",
        f"- Visible public score: **{record.get('public_score') if record.get('public_score') is not None else 'not available'}**",
        f"- Visible public rank: **{record.get('public_rank') if record.get('public_rank') not in (None, 0) else 'not available'}**",
        f"- Teams in snapshot: **{record.get('team_count') or 'not available'}**",
        "",
        "## Interpretation",
        "",
        record.get("interpretation", "No interpretation recorded."),
        "",
        "## Representation firewall",
        "",
        "Cycle 001 is terminal after a visible score. Any representation expansion requires a new precommitted Cycle 002 registration.",
    ]
    if record.get("error"):
        lines += ["", "## Error", "", "```text", str(record["error"]), "```"]
    (RESULT_DIR / "RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def refresh(record: dict[str, Any], wait_seconds: int = 1800) -> None:
    deadline = time.time() + wait_seconds
    submissions_text = ""
    entered_text = ""
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
        latest = rows[0] if rows else None
        score = first(latest, "publicScore", "public score", "score")
        rank = None
        for row in parse_csv(entered_text):
            ref = first(row, "ref", "competition", "id") or ""
            if ref == COMPETITION or ref.endswith("/" + COMPETITION):
                rank = first(row, "userRank", "user rank", "rank")
                break
        if score is not None and rank not in (None, "0"):
            break
        if time.time() >= deadline:
            break
        time.sleep(30)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "submissions.csv").write_text(submissions_text, encoding="utf-8")
    (LOG_DIR / "entered_competitions.csv").write_text(entered_text, encoding="utf-8")
    rows = parse_csv(submissions_text)
    latest = rows[0] if rows else None
    record["submission_status"] = first(latest, "status") or record.get("submission_status")
    record["public_score"] = number(first(latest, "publicScore", "public score", "score"))
    record["private_score"] = number(first(latest, "privateScore", "private score"))
    for row in parse_csv(entered_text):
        ref = first(row, "ref", "competition", "id") or ""
        if ref == COMPETITION or ref.endswith("/" + COMPETITION):
            rank = number(first(row, "userRank", "user rank", "rank"))
            teams = number(first(row, "teamCount", "team count", "teams"))
            record["public_rank"] = int(rank) if rank is not None else None
            record["team_count"] = int(teams) if teams is not None else None
            break


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "cycle": "private-v3-cycle-001",
        "competition": COMPETITION,
        "state": "VERIFYING_IMMUTABLE_KERNEL",
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
    }

    if not (os.environ.get("KAGGLE_API_TOKEN", "").strip() or os.environ.get("KAGGLE_KEY", "").strip()):
        record.update(
            state="BLOCKED_AUTH",
            error="Kaggle token is not available to the immutable-version submit workflow.",
            interpretation="No submission was attempted.",
        )
        write_record(record)
        return 0

    # Refuse a duplicate if the competition already lists any submission.
    existing = run(
        ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"], timeout=180
    )
    log("00_existing_submissions.txt", existing, record)
    existing_rows = parse_csv(existing["output"])
    if existing_rows:
        record["state"] = "EXISTING_SUBMISSION_DETECTED"
        record["interpretation"] = "A competition submission already exists; no duplicate was created. Score and rank were refreshed."
        refresh(record, wait_seconds=1200)
        score = record.get("public_score")
        if score is not None and score > 0:
            record["state"] = "SCORED_NONZERO"
        elif score == 0:
            record["state"] = "SCORED_NULL"
        elif record.get("submission_status"):
            record["state"] = "SUBMITTED_SCORE_PENDING"
        write_record(record)
        return 0

    # Pull exact immutable version and verify registered source/repair markers.
    shutil.rmtree(VERIFY_DIR, ignore_errors=True)
    VERIFY_DIR.mkdir(parents=True, exist_ok=True)
    pull = run(
        [
            "kaggle", "kernels", "pull", f"{KERNEL_REF}/{KERNEL_VERSION}",
            "-p", str(VERIFY_DIR), "-m",
        ],
        timeout=600,
    )
    log("01_pull_version8.txt", pull, record)
    notebooks = list(VERIFY_DIR.glob("*.ipynb"))
    if pull["returncode"] != 0 or not notebooks:
        record.update(
            state="IMMUTABLE_KERNEL_VERIFY_FAILED",
            error=pull["output"][-16000:] or "Version 8 notebook was not pulled.",
            interpretation="No competition submission was attempted.",
        )
        write_record(record)
        return 0
    notebook_text = notebooks[0].read_text(encoding="utf-8")
    required_markers = [
        FROZEN_COMMIT,
        "arc-agi_evaluation_challenges.json",
        'sys.argv = ["kaggle_submission_v3.py"]',
    ]
    missing = [marker for marker in required_markers if marker not in notebook_text]
    if missing:
        record.update(
            state="IMMUTABLE_KERNEL_VERIFY_FAILED",
            error="Version 8 is missing registered marker(s): " + repr(missing),
            interpretation="No competition submission was attempted.",
        )
        write_record(record)
        return 0
    record["verified_notebook"] = notebooks[0].name
    record["verification_markers"] = required_markers

    files = run(
        ["kaggle", "kernels", "files", f"{KERNEL_REF}/{KERNEL_VERSION}", "-v", "--page-size", "200"],
        timeout=180,
    )
    log("02_version8_files.txt", files, record)
    if "submission.json" not in files["output"]:
        # Some CLI versions do not accept /version on the files endpoint. Verify
        # the latest completed output as secondary evidence, but still submit v8.
        latest_files = run(
            ["kaggle", "kernels", "files", KERNEL_REF, "-v", "--page-size", "200"],
            timeout=180,
        )
        log("02b_latest_files.txt", latest_files, record)
        if "submission.json" not in latest_files["output"]:
            record.update(
                state="IMMUTABLE_KERNEL_OUTPUT_NOT_FOUND",
                error="Kaggle did not list submission.json among kernel outputs.",
                interpretation="No competition submission was attempted.",
            )
            write_record(record)
            return 0

    submit = run(
        [
            "kaggle", "competitions", "submit", COMPETITION,
            "-f", "submission.json",
            "-k", KERNEL_REF,
            "-v", str(KERNEL_VERSION),
            "-m", MESSAGE,
            "--wait", "10800",
            "--poll-interval", "30",
        ],
        timeout=10900,
    )
    log("03_competition_submit.txt", submit, record)
    ref_match = re.search(r"(?i)submission\s+ref:\s*(\d+)", submit["output"])
    if ref_match:
        record["submission_ref"] = ref_match.group(1)

    refresh(record, wait_seconds=1800)
    score = record.get("public_score")
    if score is not None and score > 0:
        record.update(
            state="SCORED_NONZERO",
            error=None,
            interpretation="Frozen ARC v3 Cycle 001 achieved a nonzero visible Kaggle score. The cycle is terminal.",
        )
    elif score == 0:
        record.update(
            state="SCORED_NULL",
            error=None,
            interpretation="Frozen ARC v3 Cycle 001 received a visible score of zero. The cycle is terminal.",
        )
    elif submit["returncode"] == 0 or record.get("submission_ref"):
        record.update(
            state="SUBMITTED_SCORE_PENDING",
            error=None,
            interpretation="Kaggle accepted immutable kernel version 8; score or rank was still pending when recorded.",
        )
    else:
        record.update(
            state="SUBMISSION_FAILED_OR_TIMED_OUT",
            error=submit["output"][-16000:],
            interpretation="Kaggle did not accept or complete the immutable version-8 code submission.",
        )
    write_record(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
