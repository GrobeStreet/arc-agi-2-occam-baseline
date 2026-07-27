#!/usr/bin/env python3
"""Inspect the live Kaggle state for frozen ARC Private Cycle 001.

This probe is observational only. It never pushes a kernel, submits a prediction,
or changes solver code. It records the latest Kaggle kernel status, attempts to
retrieve output/error artifacts, and captures the authenticated submission and
competition-rank views for debugging and progress reporting.
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "private_cycle_001" / "live_probe"
KERNEL = "robertmorong/grobestreet-arc-frozen-v3-cycle-001"
COMPETITION = "arc-prize-2026-arc-agi-2"


def run(command: list[str], timeout: int = 600) -> dict[str, Any]:
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
        "output": completed.stdout or "",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("KAGGLE_API_TOKEN", "").strip() or os.environ.get("KAGGLE_KEY", "").strip()
    record: dict[str, Any] = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "kernel_ref": KERNEL,
        "competition": COMPETITION,
        "authenticated": bool(token),
        "commands": {},
    }
    if not token:
        record["state"] = "BLOCKED_AUTH"
        record["error"] = "Kaggle API token unavailable to probe workflow."
    else:
        commands = {
            "kernel_status": ["kaggle", "kernels", "status", KERNEL],
            "kernel_output": [
                "kaggle", "kernels", "output", KERNEL,
                "-p", str(OUT / "kernel_output"), "-o", "-q",
            ],
            "kernel_pull": [
                "kaggle", "kernels", "pull", KERNEL,
                "-p", str(OUT / "kernel_pull"), "-m",
            ],
            "submissions": [
                "kaggle", "competitions", "submissions", COMPETITION, "-v", "-q",
            ],
            "entered_competitions": [
                "kaggle", "competitions", "list", "--group", "entered", "-v",
            ],
        }
        for name, command in commands.items():
            try:
                result = run(command)
            except Exception as exc:
                result = {"command": command, "returncode": 999, "output": repr(exc)}
            record["commands"][name] = result
            (OUT / f"{name}.txt").write_text(result["output"], encoding="utf-8")
        status_text = record["commands"]["kernel_status"]["output"].strip()
        record["state"] = status_text or "STATUS_UNAVAILABLE"

    (OUT / "probe.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Frozen ARC Cycle 001 — Live Kaggle Probe",
        "",
        f"**Observed:** {record['observed_at']}  ",
        f"**Kernel:** `{KERNEL}`  ",
        f"**State:** `{record.get('state')}`",
        "",
    ]
    if record.get("error"):
        lines += ["## Error", "", "```text", str(record["error"]), "```", ""]
    for name, result in record.get("commands", {}).items():
        lines += [
            f"## {name}",
            "",
            f"Return code: `{result['returncode']}`",
            "",
            "```text",
            result["output"][-12000:],
            "```",
            "",
        ]
    (OUT / "PROBE.md").write_text("\n".join(lines), encoding="utf-8")
    print((OUT / "PROBE.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
