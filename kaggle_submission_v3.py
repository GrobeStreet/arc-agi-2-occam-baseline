#!/usr/bin/env python3
"""Kaggle-compatible ARC-AGI-2 submission entrypoint for representation v3.

This file preserves the frozen representation-v3 grammar and ranking policy. The
only post-Cycle-001 change is a mechanical input-selection repair: the competition
mount can contain several ARC challenge JSON files, so the correct hidden test
file is selected only when its task IDs and output multiplicities exactly match an
official ``sample_submission.json`` file.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

import dsl_v3 as v3


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) and value else None


def is_challenge_payload(value: dict[str, Any]) -> bool:
    first = next(iter(value.values()), None)
    return (
        isinstance(first, dict)
        and isinstance(first.get("train"), list)
        and isinstance(first.get("test"), list)
    )


def is_sample_payload(value: dict[str, Any]) -> bool:
    first = next(iter(value.values()), None)
    if not isinstance(first, list) or not first:
        return False
    item = first[0]
    return isinstance(item, dict) and {"attempt_1", "attempt_2"}.issubset(item)


def pair_matches(sample: dict[str, Any], challenges: dict[str, Any]) -> bool:
    if set(sample) != set(challenges):
        return False
    return all(
        isinstance(sample[task_id], list)
        and isinstance(challenges[task_id], dict)
        and len(sample[task_id]) == len(challenges[task_id].get("test", []))
        for task_id in sample
    )


def discover_official_pair(
    roots: list[Path],
    explicit_challenges: str | None,
    explicit_sample: str | None,
) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    if explicit_challenges:
        challenge_paths = [Path(explicit_challenges)]
    else:
        challenge_paths = []
        patterns = (
            "arc-agi_test_challenges.json",
            "*test_challenges*.json",
            "*test*challenges*.json",
        )
        seen: set[Path] = set()
        for root in roots:
            if not root.exists():
                continue
            for pattern in patterns:
                for path in sorted(root.rglob(pattern)):
                    resolved = path.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        challenge_paths.append(path)

    if explicit_sample:
        sample_paths = [Path(explicit_sample)]
    else:
        sample_paths = []
        seen_samples: set[Path] = set()
        for root in roots:
            if not root.exists():
                continue
            for path in sorted(root.rglob("sample_submission.json")):
                resolved = path.resolve()
                if resolved not in seen_samples:
                    seen_samples.add(resolved)
                    sample_paths.append(path)

    challenge_records: list[tuple[Path, dict[str, Any]]] = []
    for path in challenge_paths:
        payload = load_json(path)
        if payload is not None and is_challenge_payload(payload):
            challenge_records.append((path, payload))

    sample_records: list[tuple[Path, dict[str, Any]]] = []
    for path in sample_paths:
        payload = load_json(path)
        if payload is not None and is_sample_payload(payload):
            sample_records.append((path, payload))

    candidates: list[
        tuple[tuple[int, int, int, int], Path, Path, dict[str, Any], dict[str, Any]]
    ] = []
    for sample_path, sample in sample_records:
        for challenge_path, challenges in challenge_records:
            if not pair_matches(sample, challenges):
                continue
            score = (
                int(sample_path.parent.resolve() == challenge_path.parent.resolve()),
                int("arc-prize-2026-arc-agi-2" in str(challenge_path).lower()),
                int(challenge_path.name == "arc-agi_test_challenges.json"),
                len(challenges),
            )
            candidates.append((score, sample_path, challenge_path, sample, challenges))

    if not candidates:
        inventory = {
            "challenge_candidates": [str(path) for path, _ in challenge_records],
            "sample_candidates": [str(path) for path, _ in sample_records],
            "challenge_task_counts": {
                str(path): len(payload) for path, payload in challenge_records
            },
            "sample_task_counts": {str(path): len(payload) for path, payload in sample_records},
        }
        raise FileNotFoundError(
            "No challenge JSON exactly matched an official sample_submission.json. "
            + json.dumps(inventory, indent=2)
        )

    _, sample_path, challenge_path, sample, challenges = max(
        candidates, key=lambda item: item[0]
    )
    return sample_path, challenge_path, sample, challenges


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
    challenges: dict[str, Any],
    sample: dict[str, Any],
    submission: dict[str, Any],
) -> None:
    if set(challenges) != set(sample) or set(submission) != set(sample):
        raise ValueError("Submission, challenge, and sample task IDs do not match")
    for task_id, expected in sample.items():
        outputs = submission[task_id]
        if len(outputs) != len(expected) or len(outputs) != len(
            challenges[task_id].get("test", [])
        ):
            raise ValueError(f"{task_id}: wrong number of test outputs")
        for index, entry in enumerate(outputs):
            if set(entry) != {"attempt_1", "attempt_2"}:
                raise ValueError(f"{task_id}[{index}]: exactly two attempts required")
            for attempt in ("attempt_1", "attempt_2"):
                grid = entry[attempt]
                if not isinstance(grid, list) or not grid:
                    raise ValueError(f"{task_id}[{index}].{attempt}: invalid grid")
                width = len(grid[0])
                if width == 0 or any(
                    not isinstance(row, list) or len(row) != width for row in grid
                ):
                    raise ValueError(f"{task_id}[{index}].{attempt}: ragged grid")
                if len(grid) > 30 or width > 30:
                    raise ValueError(f"{task_id}[{index}].{attempt}: grid exceeds 30x30")
                if any(
                    type(cell) is not int or cell < 0 or cell > 9
                    for row in grid
                    for cell in row
                ):
                    raise ValueError(f"{task_id}[{index}].{attempt}: cells must be 0..9")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test-challenges", default=os.environ.get("ARC_TEST_CHALLENGES")
    )
    parser.add_argument(
        "--sample-submission", default=os.environ.get("ARC_SAMPLE_SUBMISSION")
    )
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

    roots = [Path("/kaggle/input"), Path.cwd(), Path(__file__).resolve().parent]
    sample_path, challenge_path, sample, challenges = discover_official_pair(
        roots,
        args.test_challenges,
        args.sample_submission,
    )
    print("Using ARC sample submission:", sample_path)
    print("Using ARC challenge file:", challenge_path)
    print("Matched task/output counts:", len(sample), sum(len(v) for v in sample.values()))

    submission, metadata = build_submission(challenges)
    validate_submission(challenges, sample, submission)

    output_path = Path(args.output)
    metadata_path = Path(args.metadata)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(submission), encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "solver": "representation-v3.0-frozen-mechanical-repair-r1",
                "registration": "HYPOTHESIS-private-v3-cycle-001-repair-r1.md",
                "base_solver_commit": "70672f3aa62d089bfffd072461a5713caae1e099",
                "repair_scope": "match hidden challenge IDs and output multiplicities to official sample_submission.json",
                "sample_submission_file": str(sample_path),
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
        f"wrote repaired frozen v3 submission for {len(submission)} tasks / "
        f"{sum(len(value) for value in submission.values())} test inputs to {output_path}"
    )
    print(f"metadata: {metadata_path}")


if __name__ == "__main__":
    main()
