#!/usr/bin/env python3
"""Inspect the scored ARC Cycle 001 entry without submitting anything."""
from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "private_cycle_001" / "leaderboard_snapshot"
COMPETITION = "arc-prize-2026-arc-agi-2"
SEARCH_NAMES = {"robertmorong", "grobestreet", "robert morong"}


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


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "competition": COMPETITION,
        "authenticated": bool(os.environ.get("KAGGLE_API_TOKEN") or os.environ.get("KAGGLE_KEY")),
        "commands": {},
        "matched_rows": [],
    }
    commands = {
        "submissions": ["kaggle", "competitions", "submissions", COMPETITION, "-v", "-q"],
        "team_submissions": ["kaggle", "competitions", "team-submissions", COMPETITION, "-v", "-q"],
        "entered": ["kaggle", "competitions", "list", "--group", "entered", "-v"],
        "leaderboard": ["kaggle", "competitions", "leaderboard", COMPETITION, "-d", "-p", str(OUT), "-q"],
    }
    for name, command in commands.items():
        try:
            result = run(command)
        except Exception as exc:
            result = {"command": command, "returncode": 999, "output": repr(exc)}
        record["commands"][name] = result
        (OUT / f"{name}.txt").write_text(result["output"], encoding="utf-8")

    csv_files = sorted(OUT.glob("*.csv"))
    record["leaderboard_files"] = [path.name for path in csv_files]
    for path in csv_files:
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.DictReader(handle))
        except Exception:
            continue
        record["leaderboard_row_count"] = len(rows)
        for index, row in enumerate(rows, start=1):
            haystack = " ".join(norm(value) for value in row.values())
            if any(name in haystack for name in SEARCH_NAMES):
                record["matched_rows"].append({"row_number": index, "file": path.name, "row": row})

    (OUT / "snapshot.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# ARC Cycle 001 — Leaderboard Snapshot",
        "",
        f"**Observed:** {record['observed_at']}  ",
        f"**Competition:** `{COMPETITION}`  ",
        f"**Downloaded leaderboard rows:** `{record.get('leaderboard_row_count', 'unavailable')}`",
        "",
        "## Matched GrobeStreet / robertmorong rows",
        "",
        "```json",
        json.dumps(record["matched_rows"], indent=2),
        "```",
        "",
    ]
    for name, result in record["commands"].items():
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
    (OUT / "SNAPSHOT.md").write_text("\n".join(lines), encoding="utf-8")
    print((OUT / "SNAPSHOT.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
