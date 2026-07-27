#!/usr/bin/env python3
"""Kaggle-compatible entrypoint for the frozen ARC evidence-weighted baseline.

The script auto-discovers the official ARC Prize challenge files under
``/kaggle/input`` and writes exactly two output grids per test input to
``/kaggle/working/submission.json``. It uses the committed training-only family
priors when available. If those priors are not bundled, it may relearn them from
the public training challenge file; no evaluation or test labels are read.

This is a reproducible diagnostic baseline, not a claimed competitive solver. The
public evaluation audit found a severe representation/coverage bottleneck.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from evidence_weighted_solver import (
    DEFAULT_PRIOR_STRENGTH,
    build_submission,
    learn_family_priors,
)


def find_first(patterns: list[str], roots: list[Path]) -> Path | None:
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            matches = sorted(root.rglob(pattern))
            if matches:
                return matches[0]
    return None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_submission(
    challenges: dict[str, Any], submission: dict[str, Any]
) -> None:
    if set(challenges) != set(submission):
        missing = sorted(set(challenges) - set(submission))
        extra = sorted(set(submission) - set(challenges))
        raise ValueError(f"Task mismatch: missing={missing[:5]} extra={extra[:5]}")

    for task_id, task in challenges.items():
        attempts = submission[task_id]
        if len(attempts) != len(task.get("test", [])):
            raise ValueError(
                f"{task_id}: expected {len(task.get('test', []))} test outputs, "
                f"found {len(attempts)}"
            )
        for index, entry in enumerate(attempts):
            if set(entry) != {"attempt_1", "attempt_2"}:
                raise ValueError(f"{task_id}[{index}]: expected exactly two attempts")
            for name in ("attempt_1", "attempt_2"):
                grid = entry[name]
                if not isinstance(grid, list) or not grid or not all(
                    isinstance(row, list) and row for row in grid
                ):
                    raise ValueError(f"{task_id}[{index}].{name}: invalid grid")
                width = len(grid[0])
                if any(len(row) != width for row in grid):
                    raise ValueError(f"{task_id}[{index}].{name}: ragged grid")
                if any(
                    not isinstance(cell, int) or cell < 0 or cell > 9
                    for row in grid
                    for cell in row
                ):
                    raise ValueError(
                        f"{task_id}[{index}].{name}: cells must be integers 0..9"
                    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-challenges", default=os.environ.get("ARC_TEST_CHALLENGES"))
    parser.add_argument("--training-challenges", default=os.environ.get("ARC_TRAINING_CHALLENGES"))
    parser.add_argument(
        "--priors",
        default=os.environ.get(
            "ARC_PRIORS", str(Path(__file__).resolve().parent / "results/solver/family_priors.json")
        ),
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("ARC_SUBMISSION", "/kaggle/working/submission.json"),
    )
    parser.add_argument(
        "--metadata",
        default=os.environ.get(
            "ARC_SUBMISSION_METADATA", "/kaggle/working/submission_v2_metadata.json"
        ),
    )
    parser.add_argument("--prior-strength", type=float, default=DEFAULT_PRIOR_STRENGTH)
    args = parser.parse_args()

    roots = [Path("/kaggle/input"), Path.cwd(), Path(__file__).resolve().parent]
    test_path = Path(args.test_challenges) if args.test_challenges else find_first(
        [
            "arc-agi_test_challenges.json",
            "*test_challenges*.json",
            "*test*challenges*.json",
        ],
        roots,
    )
    if test_path is None or not test_path.exists():
        raise FileNotFoundError(
            "Could not locate the ARC test challenge JSON. Pass --test-challenges explicitly."
        )

    prior_path = Path(args.priors)
    if prior_path.exists():
        priors = load_json(prior_path)
        prior_source = str(prior_path)
    else:
        training_path = (
            Path(args.training_challenges)
            if args.training_challenges
            else find_first(
                [
                    "arc-agi_training_challenges.json",
                    "*training_challenges*.json",
                    "*train*challenges*.json",
                ],
                roots,
            )
        )
        if training_path is None or not training_path.exists():
            raise FileNotFoundError(
                "No committed family priors and no public training challenge JSON found."
            )
        training = load_json(training_path)
        priors = learn_family_priors(
            training,
            prior_strength=args.prior_strength,
        )
        prior_path.parent.mkdir(parents=True, exist_ok=True)
        prior_path.write_text(json.dumps(priors, indent=2) + "\n", encoding="utf-8")
        prior_source = f"learned from {training_path}"

    challenges = load_json(test_path)
    submission, metadata = build_submission(challenges, priors)
    validate_submission(challenges, submission)

    output_path = Path(args.output)
    metadata_path = Path(args.metadata)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(submission), encoding="utf-8")
    metadata_path.write_text(
        json.dumps(
            {
                "test_challenges": str(test_path),
                "prior_source": prior_source,
                "task_count": len(submission),
                "solver_metadata": metadata,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    total_outputs = sum(len(outputs) for outputs in submission.values())
    print(
        f"wrote {output_path} for {len(submission)} tasks / {total_outputs} test inputs; "
        f"two attempts validated for every output"
    )
    print(f"metadata: {metadata_path}")


if __name__ == "__main__":
    main()
