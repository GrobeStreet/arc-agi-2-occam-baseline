#!/usr/bin/env python3
"""Submit the exact validated output of frozen ARC Cycle 001.

This is a mechanical fallback for the code-competition plumbing. It does not push
or change a kernel, modify solver code, regenerate predictions, or alter the
submission bytes. It reads the kernel version recorded by the registered runner,
retrieves that version's output if needed, validates the two-attempt contract,
and passes the exact downloaded file path to the official Kaggle CLI.
"""
from __future__ import annotations

import re
from pathlib import Path

from kaggle_private_cycle_001_v2 import (
    COMPETITION,
    FROZEN_COMMIT,
    RESULT_DIR,
    TERMINAL_STATES,
    load_existing,
    refresh_score_and_rank,
    run,
    sha256,
    tail,
    validate_submission,
    write_records,
)


def main() -> int:
    record = load_existing()
    if not record:
        print("No Cycle 001 result record exists; exact-path fallback has nothing to submit.")
        return 0
    if record.get("state") in TERMINAL_STATES:
        print(f"Cycle 001 is already terminal: {record['state']}")
        return 0
    if record.get("submission_ref"):
        print(f"Submission already exists: {record['submission_ref']}; refreshing score and rank only.")
        refresh_score_and_rank(record, wait_seconds=1200)
        score = record.get("public_score")
        if score is None:
            record["state"] = "SUBMITTED_SCORE_PENDING"
        elif score > 0:
            record["state"] = "SCORED_NONZERO"
        else:
            record["state"] = "SCORED_NULL"
        record["error"] = None
        write_records(record)
        return 0

    kernel_ref = record.get("kernel_ref")
    version = record.get("kernel_version")
    if not kernel_ref or not version:
        print("No immutable completed kernel version is recorded; fallback will not submit.")
        return 0

    output_dir = RESULT_DIR / "kernel_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    submission_path = output_dir / "submission.json"
    if not submission_path.is_file():
        downloaded = run(
            [
                "kaggle", "kernels", "output", str(kernel_ref),
                "-p", str(output_dir), "-o", "-q",
            ],
            timeout=600,
        )
        (RESULT_DIR / "logs" / "04b_exact_path_kernel_output.txt").write_text(
            downloaded.get("output", ""), encoding="utf-8"
        )
        if downloaded["returncode"] != 0 or not submission_path.is_file():
            record.update(
                state="EXACT_PATH_OUTPUT_UNAVAILABLE",
                error=tail(downloaded.get("output", "")) or "submission.json was not retrieved",
                interpretation="The immutable kernel version exists, but its exact output could not be retrieved for submission.",
            )
            write_records(record)
            return 0

    task_count, output_count = validate_submission(submission_path)
    record["hidden_task_count"] = task_count
    record["hidden_output_count"] = output_count
    record["submission_sha256"] = sha256(submission_path)
    record["exact_submission_path"] = str(submission_path.relative_to(Path.cwd()))

    submit = run(
        [
            "kaggle", "competitions", "submit", COMPETITION,
            "-f", str(submission_path),
            "-k", str(kernel_ref),
            "-v", str(version),
            "-m", f"Frozen representation v3 — Private Cycle 001 — {FROZEN_COMMIT[:12]}",
            "--wait", "10800",
            "--poll-interval", "30",
        ],
        timeout=10900,
    )
    (RESULT_DIR / "logs" / "05b_exact_path_competition_submit.txt").write_text(
        submit.get("output", ""), encoding="utf-8"
    )
    ref_match = re.search(r"(?i)submission\s+ref:\s*(\d+)", submit.get("output", ""))
    if ref_match:
        record["submission_ref"] = ref_match.group(1)

    refresh_score_and_rank(record, wait_seconds=1200)
    score = record.get("public_score")
    if score is not None and score > 0:
        record.update(
            state="SCORED_NONZERO",
            error=None,
            interpretation="The exact frozen v3 kernel output achieved a nonzero visible Kaggle score. Cycle 001 is terminal.",
        )
    elif score == 0:
        record.update(
            state="SCORED_NULL",
            error=None,
            interpretation="The exact frozen v3 kernel output received a visible score of zero. Cycle 001 is terminal.",
        )
    elif submit["returncode"] == 0 or record.get("submission_ref"):
        record.update(
            state="SUBMITTED_SCORE_PENDING",
            error=None,
            interpretation="Kaggle accepted the exact immutable kernel output, but its visible score or rank was still pending.",
        )
    else:
        record.update(
            state="EXACT_PATH_SUBMISSION_FAILED",
            error=tail(submit.get("output", "")),
            interpretation="Kaggle rejected or timed out on the exact downloaded submission path; solver bytes remain unchanged.",
        )
    write_records(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
