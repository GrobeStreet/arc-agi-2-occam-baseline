#!/usr/bin/env python3
"""Kaggle-compatible ARC-AGI-2 submission entrypoint for representation v3.

Promotion basis
---------------
The frozen representation-v3 grammar was registered before a deterministic
training-holdout benchmark and produced one v3-only pass@2 win, zero v2-only
wins (5/201 versus 4/201 outputs). Under the registered rule this is a
DIRECTIONAL IMPROVEMENT, not a statistically clear promotion. The grammar and
ranking below are therefore frozen before any private Kaggle evaluation.

The script auto-discovers the ARC challenge JSON under /kaggle/input and writes
exactly two semantically distinct output grids per test input.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

import dsl_v3 as v3


def find_first(patterns: list[str], roots: list[Path]) -> Path | None:
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            matches = sorted(root.rglob(pattern))
            if matches:
                return matches[0]
    return None


def grid_key(grid: np.ndarray) -> bytes:
    array = np.asarray(grid, dtype=np.int16)
    return np.asarray(array.shape, dtype=np.int16).tobytes() + array.tobytes()


def safe_predict(fn: Any, grid: np.ndarray) -> np.ndarray | None:
    try:
        output = fn(grid)
    except Exception:
        return None
    if not isinstance(output, np.ndarray) or output.ndim != 2 or output.size == 0:
        return None
    if output.shape[0] > 30 or output.shape[1] > 30:
        return None
    if np.any(output < 0) or np.any(output > 9):
        return None
    return output.astype(np.int8, copy=False)


def rank_outputs(
    train_pairs: list[tuple[np.ndarray, np.ndarray]],
    test_input: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    passers = [
        (name, fn)
        for name, fn in v3.build_programs(train_pairs)
        if v3.passes_demos(fn, train_pairs)
    ]
    outputs: dict[bytes, dict[str, Any]] = {}
    for name, fn in passers:
        prediction = safe_predict(fn, test_input)
        if prediction is None:
            continue
        key = grid_key(prediction)
        bucket = outputs.setdefault(
            key,
            {
                "grid": prediction,
                "votes": 0,
                "min_complexity": 10_000,
                "program_names": [],
            },
        )
        bucket["votes"] += 1
        bucket["min_complexity"] = min(
            bucket["min_complexity"], int(v3.complexity(name))
        )
        bucket["program_names"].append(name)

    ranked = sorted(
        outputs.values(),
        key=lambda item: (
            -item["votes"],
            item["min_complexity"],
            grid_key(item["grid"]),
        ),
    )

    # The two fallback outputs preserve valid dimensions and ensure that pass@2
    # always contains two grids even when the frozen grammar has no candidate.
    fallbacks = [test_input.copy(), np.rot90(test_input, 2).copy()]
    grids = [item["grid"] for item in ranked] + fallbacks
    first = grids[0]
    second = next(
        (
            grid
            for grid in grids[1:]
            if grid.shape != first.shape or not np.array_equal(grid, first)
        ),
        fallbacks[0],
    )
    metadata = {
        "passing_programs": len(passers),
        "distinct_candidate_outputs": len(ranked),
        "top_votes": int(ranked[0]["votes"]) if ranked else 0,
        "top_min_complexity": int(ranked[0]["min_complexity"]) if ranked else None,
    }
    return first, second, metadata


def build_submission(challenges: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    submission: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    for task_id, task in challenges.items():
        train_pairs = [
            (
                np.asarray(pair["input"], dtype=np.int8),
                np.asarray(pair["output"], dtype=np.int8),
            )
            for pair in task["train"]
        ]
        task_outputs: list[dict[str, Any]] = []
        task_meta: list[dict[str, Any]] = []
        for test in task["test"]:
            test_input = np.asarray(test["input"], dtype=np.int8)
            first, second, info = rank_outputs(train_pairs, test_input)
            task_outputs.append(
                {
                    "attempt_1": first.tolist(),
                    "attempt_2": second.tolist(),
                }
            )
            task_meta.append(info)
        submission[task_id] = task_outputs
        metadata[task_id] = task_meta
    return submission, metadata


def validate_submission(
    challenges: dict[str, Any], submission: dict[str, Any]
) -> None:
    if set(challenges) != set(submission):
        raise ValueError("Submission task IDs do not match challenge task IDs")
    for task_id, task in challenges.items():
        outputs = submission[task_id]
        if len(outputs) != len(task.get("test", [])):
            raise ValueError(f"{task_id}: wrong number of test outputs")
        for index, entry in enumerate(outputs):
            if set(entry) != {"attempt_1", "attempt_2"}:
                raise ValueError(f"{task_id}[{index}]: exactly two attempts required")
            for attempt in ("attempt_1", "attempt_2"):
                grid = entry[attempt]
                if not isinstance(grid, list) or not grid:
                    raise ValueError(f"{task_id}[{index}].{attempt}: invalid grid")
                width = len(grid[0])
                if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
                    raise ValueError(f"{task_id}[{index}].{attempt}: ragged grid")
                if len(grid) > 30 or width > 30:
                    raise ValueError(f"{task_id}[{index}].{attempt}: grid exceeds 30x30")
                if any(
                    not isinstance(cell, int) or cell < 0 or cell > 9
                    for row in grid
                    for cell in row
                ):
                    raise ValueError(f"{task_id}[{index}].{attempt}: cells must be 0..9")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test-challenges",
        default=os.environ.get("ARC_TEST_CHALLENGES"),
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("ARC_SUBMISSION", "/kaggle/working/submission.json"),
    )
    parser.add_argument(
        "--metadata",
        default=os.environ.get(
            "ARC_SUBMISSION_METADATA",
            "/kaggle/working/submission_v3_metadata.json",
        ),
    )
    args = parser.parse_args()

    roots = [Path("/kaggle/input"), Path.cwd(), Path(__file__).resolve().parent]
    challenge_path = (
        Path(args.test_challenges)
        if args.test_challenges
        else find_first(
            [
                "arc-agi_test_challenges.json",
                "*test_challenges*.json",
                "*test*challenges*.json",
            ],
            roots,
        )
    )
    if challenge_path is None or not challenge_path.exists():
        raise FileNotFoundError(
            "Could not locate the ARC test challenge JSON; pass --test-challenges explicitly."
        )

    challenges = json.loads(challenge_path.read_text(encoding="utf-8"))
    submission, metadata = build_submission(challenges)
    validate_submission(challenges, submission)

    output_path = Path(args.output)
    metadata_path = Path(args.metadata)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(submission), encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "solver": "representation-v3.0-frozen",
                "registration": "HYPOTHESIS-representation-v3.md",
                "promotion_basis": {
                    "holdout_v2_pass2": "4/201",
                    "holdout_v3_pass2": "5/201",
                    "v3_only_wins": 1,
                    "v2_only_wins": 0,
                    "exact_two_sided_p": 1.0,
                    "registered_verdict": "DIRECTIONAL IMPROVEMENT",
                },
                "challenge_file": str(challenge_path),
                "task_count": len(submission),
                "output_count": sum(len(value) for value in submission.values()),
                "task_metadata": metadata,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote frozen v3 submission for {len(submission)} tasks / "
        f"{sum(len(value) for value in submission.values())} test inputs to {output_path}"
    )
    print(f"metadata: {metadata_path}")


if __name__ == "__main__":
    main()
