#!/usr/bin/env python3
"""Build the self-contained Kaggle notebook for Private Cycle 001.

The notebook embeds the exact frozen v3 source files from a supplied directory.
It writes those modules into /kaggle/working, records their SHA-256 hashes, finds
the official attached ARC challenge JSON without modifying solver logic, and
executes kaggle_submission_v3.py with internet disabled by kernel metadata. Only
Python's standard library is needed to build the notebook.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


FROZEN_FILES = (
    "dsl.py",
    "dsl_v3.py",
    "benchmark_representation_v3.py",
    "kaggle_submission_v3.py",
)


def git_head(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def make_notebook(
    root: Path,
    output: Path,
    manifest_path: Path,
    source_commit_override: str | None = None,
) -> None:
    payload: dict[str, str] = {}
    hashes: dict[str, str] = {}
    sizes: dict[str, int] = {}

    for relative in FROZEN_FILES:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"Missing frozen source file: {path}")
        raw = path.read_bytes()
        payload[relative] = base64.b64encode(raw).decode("ascii")
        hashes[relative] = hashlib.sha256(raw).hexdigest()
        sizes[relative] = len(raw)

    source_commit = source_commit_override or git_head(root)
    created_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "cycle": "private-v3-cycle-001",
        "competition": "arc-prize-2026-arc-agi-2",
        "source_commit": source_commit,
        "created_at_utc": created_at,
        "frozen_files": {
            name: {"sha256": hashes[name], "bytes": sizes[name]}
            for name in FROZEN_FILES
        },
        "registration": "HYPOTHESIS-private-v3-cycle-001.md",
        "packaging_note": "PRIVATE_CYCLE_001_PACKAGING_NOTE.md",
        "output_contract": "/kaggle/working/submission.json",
    }

    bootstrap = f'''\
import base64
import hashlib
import json
import os
import pathlib
import sys

WORK = pathlib.Path("/kaggle/working")
WORK.mkdir(parents=True, exist_ok=True)
os.chdir(WORK)
sys.path.insert(0, str(WORK))

payload = {json.dumps(payload, sort_keys=True)}
expected = {json.dumps(hashes, sort_keys=True)}
for name, encoded in payload.items():
    raw = base64.b64decode(encoded)
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected[name]:
        raise RuntimeError(f"Embedded source digest mismatch for {{name}}: {{actual}} != {{expected[name]}}")
    pathlib.Path(name).write_bytes(raw)

manifest = {json.dumps(manifest, sort_keys=True)}
pathlib.Path("private_v3_cycle_001_source_manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\\n", encoding="utf-8"
)
print("Frozen source restored at", WORK)
print(json.dumps(manifest, indent=2))
'''

    run_cell = '''\
import json
import os
import pathlib
import runpy


def is_arc_challenge_file(path):
    name = path.name.lower()
    if "solution" in name or "submission" in name:
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(payload, dict) or not payload:
        return False
    first = next(iter(payload.values()))
    return (
        isinstance(first, dict)
        and isinstance(first.get("train"), list)
        and isinstance(first.get("test"), list)
    )


input_root = pathlib.Path("/kaggle/input")
patterns = (
    "arc-agi_evaluation_challenges.json",
    "*evaluation_challenges*.json",
    "arc-agi_test_challenges.json",
    "*test_challenges*.json",
    "*challenges*.json",
)
ordered = []
seen = set()
for pattern in patterns:
    for candidate in sorted(input_root.rglob(pattern)):
        resolved = str(candidate.resolve())
        if resolved not in seen:
            seen.add(resolved)
            ordered.append(candidate)
challenge_path = next((path for path in ordered if is_arc_challenge_file(path)), None)
if challenge_path is None:
    available = [str(path) for path in sorted(input_root.rglob("*.json"))[:100]]
    raise FileNotFoundError(
        "No valid ARC challenge JSON was found under /kaggle/input. "
        f"Observed JSON files: {available}"
    )
os.environ["ARC_TEST_CHALLENGES"] = str(challenge_path)
print("Using ARC challenge file:", challenge_path)

runpy.run_path("/kaggle/working/kaggle_submission_v3.py", run_name="__main__")
submission = pathlib.Path("/kaggle/working/submission.json")
if not submission.is_file() or submission.stat().st_size == 0:
    raise RuntimeError("Frozen v3 solver did not produce /kaggle/working/submission.json")
print(f"Submission ready: {submission} ({submission.stat().st_size:,} bytes)")
'''

    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# GrobeStreet ARC Frozen V3 — Private Cycle 001\n",
                    "\n",
                    "This code-competition notebook is generated from the frozen source commit and file hashes recorded below. It uses the preregistered representation-v3 grammar without post-hoc modification. Internet is disabled by `kernel-metadata.json`.\n",
                    "\n",
                    f"- Frozen source commit: `{source_commit}`\n",
                    "- Registration: `HYPOTHESIS-private-v3-cycle-001.md`\n",
                    "- Mechanical packaging note: `PRIVATE_CYCLE_001_PACKAGING_NOTE.md`\n",
                    "- Required output: `/kaggle/working/submission.json`\n",
                ],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": bootstrap.splitlines(keepends=True),
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": run_cell.splitlines(keepends=True),
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
            "private_cycle": manifest,
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Wrote {manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--output",
        default="contest/kaggle_kernel_v3/frozen_v3_cycle_001.ipynb",
    )
    parser.add_argument(
        "--manifest",
        default="contest/kaggle_kernel_v3/source_manifest.json",
    )
    parser.add_argument(
        "--source-commit",
        default=None,
        help="Commit label to record when --root contains materialized frozen files.",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    make_notebook(
        root,
        Path(args.output),
        Path(args.manifest),
        source_commit_override=args.source_commit,
    )


if __name__ == "__main__":
    main()
