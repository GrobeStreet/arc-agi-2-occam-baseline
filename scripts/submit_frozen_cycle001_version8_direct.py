#!/usr/bin/env python3
"""Submit frozen ARC Cycle 001 kernel version 8 without pushing a new kernel.

Version 8 was built from the registered frozen source and its latest Kaggle run is
COMPLETE with `submission.json` present. This script performs no model work. It
checks for an existing submission, verifies the live kernel/output state, submits
the immutable kernel output filename, waits for scoring, and records score/rank.
"""
from __future__ import annotations

import os
import re

from submit_frozen_cycle001_version8 import (
    COMPETITION,
    FROZEN_COMMIT,
    KERNEL_REF,
    KERNEL_VERSION,
    MESSAGE,
    first,
    log,
    number,
    parse_csv,
    refresh,
    run,
    utc_now,
    write_record,
)


def terminalize(record, submit_returncode: int | None = None) -> None:
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
    elif record.get("submission_ref") or submit_returncode == 0:
        record.update(
            state="SUBMITTED_SCORE_PENDING",
            error=None,
            interpretation="Kaggle accepted immutable kernel version 8; score or rank remained pending when recorded.",
        )
    else:
        record.update(
            state="SUBMISSION_FAILED_OR_TIMED_OUT",
            interpretation="Kaggle did not accept or complete the immutable version-8 code submission.",
        )


def main() -> int:
    record = {
        "cycle": "private-v3-cycle-001",
        "competition": COMPETITION,
        "state": "CHECKING_COMPLETED_KERNEL_VERSION_8",
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
            "kernel_push_record_commit": "24457fc3480474d5a424966d082c7285a4db6160",
            "completed_output_probe_commit": "73a612e836f35c286ba2428280ed7e27e11243c3",
            "output_filename": "submission.json",
        },
    }

    if not (os.environ.get("KAGGLE_API_TOKEN", "").strip() or os.environ.get("KAGGLE_KEY", "").strip()):
        record.update(
            state="BLOCKED_AUTH",
            error="Kaggle token unavailable to direct immutable-version workflow.",
            interpretation="No submission was attempted.",
        )
        write_record(record)
        return 0

    existing = run(
        ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"],
        timeout=180,
    )
    log("direct_00_existing_submissions.txt", existing, record)
    rows = parse_csv(existing["output"])
    if rows:
        record["interpretation"] = "A competition submission already exists; no duplicate was created."
        refresh(record, wait_seconds=1800)
        terminalize(record, 0)
        write_record(record)
        return 0

    status = run(["kaggle", "kernels", "status", KERNEL_REF], timeout=180)
    log("direct_01_kernel_status.txt", status, record)
    if status["returncode"] != 0 or "complete" not in status["output"].lower():
        record.update(
            state="COMPLETED_KERNEL_NOT_AVAILABLE",
            error=status["output"][-16000:],
            interpretation="No submission was attempted because the frozen kernel was not COMPLETE.",
        )
        write_record(record)
        return 0

    files = run(
        ["kaggle", "kernels", "files", KERNEL_REF, "-v", "--page-size", "200"],
        timeout=180,
    )
    log("direct_02_kernel_files.txt", files, record)
    if files["returncode"] != 0 or "submission.json" not in files["output"]:
        record.update(
            state="COMPLETED_KERNEL_OUTPUT_NOT_AVAILABLE",
            error=files["output"][-16000:] or "submission.json was not listed.",
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
    log("direct_03_competition_submit.txt", submit, record)
    ref_match = re.search(r"(?i)submission\s+ref:\s*(\d+)", submit["output"])
    if ref_match:
        record["submission_ref"] = ref_match.group(1)
    if submit["returncode"] != 0:
        record["error"] = submit["output"][-16000:]

    refresh(record, wait_seconds=1800)
    terminalize(record, submit["returncode"])
    write_record(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
