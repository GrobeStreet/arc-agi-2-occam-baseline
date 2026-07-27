#!/usr/bin/env python3
"""Kaggle submission entrypoint for the frozen representation-expansion v3.

V3 was promoted only directionally on the registered training holdout: 5/201
outputs versus 4/201 for the released v2 grammar, with no v2-only losses. The
private Kaggle test set remains the fresh contest endpoint. This script does not
read solution labels and writes exactly two distinct attempts per test input.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from benchmark_representation_v3 import rank_v3


def find_test_file(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if path.exists():
            return path
        raise FileNotFoundError(path)
    roots = [Path("/kaggle/input"), Path.cwd(), Path(__file__).resolve().parent]
    patterns = [
        "arc-agi_test_challenges.json",
        "*test_challenges*.json",
        "*test*challenges*.json",
    ]
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            matches = sorted(root.rglob(pattern))
            if matches:
                return matches[0]
    raise FileNotFoundError(
        "Could not locate the ARC test challenge JSON. Pass --test-challenges explicitly."
    )


def validate(
    challenges: dict[str, Any], submission: dict[str, Any]
) -> None:
    if set(challenges) != set(submission):
        raise ValueError("Submission task IDs do not match challenge task IDs")
    for task_id, task in challenges.items():
        outputs = submission[task_id]
        if len(outputs) != len(task.get("test", [])):
            raise ValueError(f"{task_id}: wrong number of test outputs")
        for index, attempts in enumerate(outputs):
            if set(attempts) != {"attempt_1", "attempt_2"}:
                raise ValueError(f"{task_id}[{index}]: exactly two attempts required")
            first = np.asarray(attempts["attempt_1"])
            second = np.asarray(attempts["attempt_2"])
            for name, grid in (("attempt_1", first), ("attempt_2", second)):
                if grid.ndim != 2 or grid.size == 0:
                    raise ValueError(f"{task_id}[{index}].{name}: invalid grid")
                if grid.shape[0] > 30 or grid.shape[1] > 30:
                    raise ValueError(f"{task_id}[{index}].{name}: grid exceeds 30x30")
                if np.any(grid < 0) or np.any(grid > 9):
                    raise ValueError(f"{task_id}[{index}].{name}: cells must be 0..9")
            if first.shape == second.shape and np.array_equal(first, second):
                raise ValueError(f"{task_id}[{index}]: attempts must be distinct")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-challenges", default=os.environ.get("ARC_TEST_CHALLENGES"))
    parser.add_argument(
        "--output",
        default=os.environ.get("ARC_SUBMISSION", "/kaggle/working/submission.json"),
    )
    parser.add_argument(
        "--metadata",
        default=os.environ.get(
            "ARC_SUBMISSION_METADATA", "/kaggle/working/submission_v3_metadata.json"
        ),
    )
    args = parser.parse_args()

    test_path = find_test_file(args.test_challenges)
    challenges = json.loads(test_path.read_text(encoding="utf-8"))
    submission: dict[str, Any] = {}
    metadata: dict[str, Any] = {
        "version": "representation-v3.0-frozen",
        "registration": "HYPOTHESIS-representation-v3.md",
        "test_challenges": str(test_path),
        "tasks": {},
    }

    for task_id, task in challenges.items():
        train_pairs = [
            (
                np.asarray(pair["input"], dtype=np.int8),
                np.asarray(pair["output"], dtype=np.int8),
            )
            for pair in task["train"]
        ]
        task_outputs = []
        task_meta = []
        for test_pair in task["test"]:
            test_input = np.asarray(test_pair["input"], dtype=np.int8)
            attempts, info = rank_v3(train_pairs, test_input)
            task_outputs.append(
                {
                    "attempt_1": attempts[0].astype(int).tolist(),
                    "attempt_2": attempts[1].astype(int).tolist(),
                }
            )
            task_meta.append(
                {
                    "covered": info["covered"],
                    "passing_programs": info["passing_programs"],
                    "distinct_candidate_outputs": info["distinct_candidate_outputs"],
                    "top_votes": info["top_votes"],
                    "top_min_complexity": info["top_min_complexity"],
                }
            )
        submission[task_id] = task_outputs
        metadata["tasks"][task_id] = task_meta

    validate(challenges, submission)
    output_path = Path(args.output)
    metadata_path = Path(args.metadata)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(submission), encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    total_outputs = sum(len(outputs) for outputs in submission.values())
    covered = sum(
        record["covered"]
        for task_records in metadata["tasks"].values()
        for record in task_records
    )
    print(
        f"wrote {output_path}: {len(submission)} tasks, {total_outputs} test inputs, "
        f"{covered} inputs with at least one v3 candidate output"
    )
    print(f"metadata: {metadata_path}")


if __name__ == "__main__":
    main()
