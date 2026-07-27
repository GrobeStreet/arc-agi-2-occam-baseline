#!/usr/bin/env python3
"""Mechanical live wrapper for the registered frozen ARC v3 Cycle 001.

This file does not change the frozen solver, ranking rule, fallbacks, or output
contract. It only hardens Kaggle packaging and evidence classification:

* make the human-readable kernel title resolve exactly to the registered slug;
* distinguish an authenticated account that has not accepted competition rules
  from a kernel-version parsing failure;
* route the Kaggle submit command to the exact validated downloaded output path;
* preserve every underlying CLI command and log from the registered runner.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import kaggle_private_cycle_001_v2 as cycle


_original_write_records = cycle.write_records
_original_run = cycle.run


def _all_command_output(record: dict[str, Any]) -> str:
    return "\n".join(
        str(command.get("output", ""))
        for command in record.get("commands", [])
        if isinstance(command, dict)
    )


def write_records(record: dict[str, Any]) -> None:
    combined = "\n".join(
        [str(record.get("error") or ""), _all_command_output(record)]
    ).lower()
    if "must accept this competition's rules" in combined:
        record.update(
            state="BLOCKED_RULES_NOT_ACCEPTED",
            error=(
                "Kaggle authentication succeeded, but the robertmorong account has not "
                "accepted the ARC Prize 2026 - ARC-AGI-2 competition rules."
            ),
            interpretation=(
                "The exact frozen notebook was built and authenticated access to the "
                "competition data was confirmed. Kaggle refused to attach the competition "
                "as a notebook datasource until the account joins the competition and "
                "accepts its rules. No kernel version, submission, score, or rank exists yet."
            ),
        )
    _original_write_records(record)


def write_kernel_metadata(username: str) -> None:
    metadata = {
        "id": f"{username}/{cycle.KERNEL_SLUG}",
        "title": cycle.KERNEL_SLUG,
        "code_file": cycle.NOTEBOOK.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": False,
        "competition_sources": [cycle.COMPETITION],
        "dataset_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    path = cycle.KERNEL_DIR / "kernel-metadata.json"
    path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def run(command: list[str], *, timeout: int = 900) -> dict[str, Any]:
    """Apply only the pre-registered exact-path CLI repair."""
    rewritten = list(command)
    if rewritten[:3] == ["kaggle", "competitions", "submit"] and "-f" in rewritten:
        index = rewritten.index("-f") + 1
        if index < len(rewritten) and rewritten[index] == "submission.json":
            exact = cycle.RESULT_DIR / "kernel_output" / "submission.json"
            rewritten[index] = str(exact)
    return _original_run(rewritten, timeout=timeout)


cycle.write_records = write_records
cycle.write_kernel_metadata = write_kernel_metadata
cycle.run = run


if __name__ == "__main__":
    raise SystemExit(cycle.main())
