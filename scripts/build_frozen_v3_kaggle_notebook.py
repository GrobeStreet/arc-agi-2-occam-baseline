#!/usr/bin/env python3
"""Build the self-contained Kaggle notebook for Private Cycle 001.

The notebook embeds the exact frozen v3 source files from a supplied directory.
It writes those modules into /kaggle/working, records their SHA-256 hashes, pairs
the official ARC test challenge file with the official sample submission by exact
task-ID equality, and executes kaggle_submission_v3.py with internet disabled by
kernel metadata.

The solver is unchanged. This wrapper includes the mechanical repair registered
in PRIVATE_CYCLE_001_SCORING_REPAIR.md after kernel version 8 accidentally routed
to the already-observed public evaluation challenge file.
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
        "mechanical_repair": "PRIVATE_CYCLE_001_SCORING_REPAIR.md",
        "output_contract": "/kaggle/working/submission.json",
        "required_schema": {
            "task_count": 240,
            "output_count": 259,
            "source_pairing": "sample_submission task IDs must exactly equal test challenge task IDs",
        },
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
import sys


def load_json_object(path):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) and payload else None


def is_arc_challenge_payload(payload):
    if not isinstance(payload, dict) or not payload:
        return False
    first = next(iter(payload.values()))
    return (
        isinstance(first, dict)
        and isinstance(first.get("train"), list)
        and isinstance(first.get("test"), list)
    )


def choose_official_pair(root):
    sample_paths = sorted(root.rglob("sample_submission.json"))
    exact_test_paths = sorted(root.rglob("arc-agi_test_challenges.json"))
    wildcard_test_paths = sorted(root.rglob("*test_challenges*.json"))
    all_test_paths = []
    seen = set()
    for path in exact_test_paths + wildcard_test_paths:
        if "evaluation" in path.name.lower():
            continue
        resolved = str(path.resolve())
        if resolved not in seen:
            seen.add(resolved)
            all_test_paths.append(path)

    pairs = []
    for sample_path in sample_paths:
        sample = load_json_object(sample_path)
        if sample is None:
            continue
        sample_keys = set(sample)
        candidates = []
        sibling = sample_path.parent / "arc-agi_test_challenges.json"
        if sibling.is_file():
            candidates.append(sibling)
        candidates.extend(all_test_paths)
        candidate_seen = set()
        for challenge_path in candidates:
            resolved = str(challenge_path.resolve())
            if resolved in candidate_seen:
                continue
            candidate_seen.add(resolved)
            challenge = load_json_object(challenge_path)
            if not is_arc_challenge_payload(challenge):
                continue
            if set(challenge) != sample_keys:
                continue
            path_text = str(challenge_path).lower()
            priority = (
                0 if challenge_path.parent == sample_path.parent else 1,
                0 if "arc-prize-2026-arc-agi-2" in path_text else 1,
                len(challenge_path.parts),
                path_text,
            )
            pairs.append((priority, sample_path, challenge_path, sample, challenge))

    if not pairs:
        observed_samples = [str(path) for path in sample_paths[:50]]
        observed_tests = [str(path) for path in all_test_paths[:50]]
        raise FileNotFoundError(
            "Could not pair an official sample_submission.json with an ARC test "
            "challenge file having exactly the same task IDs. "
            f"Samples={observed_samples}; tests={observed_tests}"
        )
    pairs.sort(key=lambda item: item[0])
    _, sample_path, challenge_path, sample, challenge = pairs[0]
    return sample_path, challenge_path, sample, challenge


def validate_grid(grid, label):
    if not isinstance(grid, list) or not grid:
        raise ValueError(f"{label}: grid is not a non-empty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError(f"{label}: contains a non-list or empty row")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError(f"{label}: ragged rows")
    if len(grid) > 30 or width > 30:
        raise ValueError(f"{label}: grid exceeds 30x30")
    for row in grid:
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                raise ValueError(f"{label}: invalid cell {cell!r}")


def validate_against_official(sample, challenges, submission):
    sample_keys = set(sample)
    challenge_keys = set(challenges)
    submission_keys = set(submission)
    if sample_keys != challenge_keys:
        raise ValueError("Official sample and challenge task IDs differ")
    if submission_keys != sample_keys:
        missing = sorted(sample_keys - submission_keys)[:30]
        extra = sorted(submission_keys - sample_keys)[:30]
        raise ValueError(
            f"Submission task IDs do not match official sample: missing={missing}, extra={extra}"
        )

    sample_outputs = 0
    challenge_outputs = 0
    submission_outputs = 0
    for task_id in sorted(sample_keys):
        sample_entries = sample[task_id]
        test_entries = challenges[task_id].get("test", [])
        entries = submission[task_id]
        if not isinstance(sample_entries, list):
            raise ValueError(f"{task_id}: official sample entry is not a list")
        if not isinstance(entries, list):
            raise ValueError(f"{task_id}: submission entry is not a list")
        if len(entries) != len(sample_entries) or len(entries) != len(test_entries):
            raise ValueError(
                f"{task_id}: output count submission={len(entries)}, "
                f"sample={len(sample_entries)}, challenges={len(test_entries)}"
            )
        sample_outputs += len(sample_entries)
        challenge_outputs += len(test_entries)
        submission_outputs += len(entries)
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or set(entry) != {"attempt_1", "attempt_2"}:
                raise ValueError(f"{task_id}[{index}]: expected attempt_1 and attempt_2")
            validate_grid(entry["attempt_1"], f"{task_id}[{index}].attempt_1")
            validate_grid(entry["attempt_2"], f"{task_id}[{index}].attempt_2")

    if len(submission) != 240 or submission_outputs != 259:
        raise ValueError(
            "Competition schema count mismatch: expected 240 tasks / 259 outputs, "
            f"got {len(submission)} tasks / {submission_outputs} outputs"
        )
    if not (sample_outputs == challenge_outputs == submission_outputs):
        raise ValueError(
            f"Output totals differ: sample={sample_outputs}, challenges={challenge_outputs}, "
            f"submission={submission_outputs}"
        )
    return {
        "task_count": len(submission),
        "output_count": submission_outputs,
        "sample_task_ids_match": True,
        "challenge_task_ids_match": True,
    }


input_root = pathlib.Path("/kaggle/input")
sample_path, challenge_path, sample_payload, challenge_payload = choose_official_pair(input_root)
os.environ["ARC_TEST_CHALLENGES"] = str(challenge_path)
print("Using official sample submission:", sample_path)
print("Using official ARC test challenge file:", challenge_path)
print("Official task/output counts:", len(sample_payload), sum(len(value) for value in sample_payload.values()))

# Jupyter launches kernels with its own '-f <connection-file>' arguments. The
# frozen script uses argparse, so expose only the script name and preserve all
# registered solver defaults.
sys.argv = ["kaggle_submission_v3.py"]
runpy.run_path("/kaggle/working/kaggle_submission_v3.py", run_name="__main__")
submission_path = pathlib.Path("/kaggle/working/submission.json")
if not submission_path.is_file() or submission_path.stat().st_size == 0:
    raise RuntimeError("Frozen v3 solver did not produce /kaggle/working/submission.json")
submission_payload = json.loads(submission_path.read_text(encoding="utf-8"))
validation = validate_against_official(
    sample_payload, challenge_payload, submission_payload
)
pathlib.Path("private_v3_cycle_001_schema_validation.json").write_text(
    json.dumps(
        {
            **validation,
            "sample_submission": str(sample_path),
            "test_challenges": str(challenge_path),
            "submission_bytes": submission_path.stat().st_size,
        },
        indent=2,
    )
    + "\\n",
    encoding="utf-8",
)
print("Official schema validation passed:", json.dumps(validation, sort_keys=True))
print(f"Submission ready: {submission_path} ({submission_path.stat().st_size:,} bytes)")
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
                    "- Mechanical repair: `PRIVATE_CYCLE_001_SCORING_REPAIR.md`\n",
                    "- Required output: `/kaggle/working/submission.json`\n",
                    "- Required official schema: `240 tasks / 259 test outputs`\n",
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
