#!/usr/bin/env python3
"""Evidence-weighted ARC-AGI-2 solver and prior learner.

This is the algorithmic extension of the measurement audit. The original baseline
counts every demonstration-consistent program as one vote, so syntactic abundance
inside the hand-written DSL can masquerade as evidence. This solver instead:

1. learns out-of-task reliability priors for normalized program families using
   public ARC-AGI-2 *training* demonstrations only;
2. updates those priors with same-task leave-one-demonstration-out evidence;
3. deduplicates each family's support for a predicted output;
4. penalizes unnecessary description length;
5. uses near-consistent subset programs only as a clearly separated fallback when
   the full demonstration set has no executable hypothesis.

The frozen prior can then be applied to public evaluation challenges or a Kaggle
submission without reading evaluation labels.
"""

from __future__ import annotations

import argparse
import glob
import itertools
import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from dsl import build_programs, complexity, passes_demos


DEFAULT_PRIOR_STRENGTH = 8.0
DEFAULT_LOCAL_STRENGTH = 3.0


def valid_grid(value: Any) -> bool:
    return isinstance(value, np.ndarray) and value.size > 0 and value.ndim == 2


def grid_key(grid: np.ndarray) -> bytes:
    array = np.asarray(grid, dtype=np.int16)
    return np.asarray(array.shape, dtype=np.int16).tobytes() + array.tobytes()


def family_name(name: str) -> str:
    """Normalize nuisance parameters while preserving structural program type."""
    family = re.sub(r"(half(?:AND|OR|XOR|DIFF)):\d+", r"\1:*", name)
    family = re.sub(r"\b(tile|scale|reduce)\([^)]*\)", r"\1(*)", family)
    family = re.sub(r"\b(tile|scale|reduce)\[[^]]*\]", r"\1[*]", family)
    # Current DSL renders ratios as tile(2, 2), tile(2,2), or tile(2, 2).
    family = re.sub(r"\b(tile|scale|reduce)\s*\([^)]*\)", r"\1(*)", family)
    return family


def load_tasks(data_root: str | Path, split: str) -> dict[str, dict[str, Any]]:
    files = sorted(glob.glob(str(Path(data_root) / split / "*.json")))
    if not files:
        raise FileNotFoundError(f"No ARC JSON tasks under {Path(data_root) / split}")
    return {Path(filename).stem: json.loads(Path(filename).read_text()) for filename in files}


def pairs_from_task(task: dict[str, Any]) -> list[tuple[np.ndarray, np.ndarray]]:
    return [
        (
            np.asarray(pair["input"], dtype=np.int8),
            np.asarray(pair["output"], dtype=np.int8),
        )
        for pair in task["train"]
    ]


def safe_predict(fn: Any, grid: np.ndarray) -> np.ndarray | None:
    try:
        prediction = fn(grid)
    except Exception:
        return None
    return prediction if valid_grid(prediction) else None


def all_nonempty_subsets(indices: list[int]) -> Iterable[tuple[int, ...]]:
    for k in range(1, len(indices) + 1):
        yield from itertools.combinations(indices, k)


def learn_family_priors(
    tasks: dict[str, dict[str, Any]],
    *,
    prior_strength: float = DEFAULT_PRIOR_STRENGTH,
    max_tasks: int | None = None,
) -> dict[str, Any]:
    """Estimate task-equal family reliability from same-holdout cross-validation."""
    family_task_rates: dict[str, list[float]] = defaultdict(list)
    task_ids = sorted(tasks)
    if max_tasks is not None:
        task_ids = task_ids[:max_tasks]

    for task_number, task_id in enumerate(task_ids, start=1):
        demos = pairs_from_task(tasks[task_id])
        per_task: dict[str, list[float]] = defaultdict(list)
        for heldout_index, (held_input, held_output) in enumerate(demos):
            available = [index for index in range(len(demos)) if index != heldout_index]
            # Average subset-level evidence inside each held-out fold so tasks with
            # more demonstrations do not receive combinatorial weight.
            fold_family: dict[str, list[float]] = defaultdict(list)
            for fit_indices in all_nonempty_subsets(available):
                fit_pairs = [demos[index] for index in fit_indices]
                candidates = [
                    (name, fn)
                    for name, fn in build_programs(fit_pairs)
                    if passes_demos(fn, fit_pairs)
                ]
                truth = grid_key(held_output)
                for name, fn in candidates:
                    prediction = safe_predict(fn, held_input)
                    if prediction is None:
                        continue
                    fold_family[family_name(name)].append(
                        float(grid_key(prediction) == truth)
                    )
            for family, values in fold_family.items():
                per_task[family].append(float(np.mean(values)))
        for family, heldout_rates in per_task.items():
            family_task_rates[family].append(float(np.mean(heldout_rates)))

        if task_number % 100 == 0 or task_number == len(task_ids):
            print(
                f"learned family evidence from {task_number}/{len(task_ids)} tasks; "
                f"{len(family_task_rates)} families",
                flush=True,
            )

    all_task_family_rates = [
        value for values in family_task_rates.values() for value in values
    ]
    global_mean = float(np.mean(all_task_family_rates)) if all_task_family_rates else 0.5
    families: dict[str, Any] = {}
    for family, values in sorted(family_task_rates.items()):
        array = np.asarray(values, dtype=float)
        raw_mean = float(array.mean())
        shrunk = float(
            (array.size * raw_mean + prior_strength * global_mean)
            / (array.size + prior_strength)
        )
        families[family] = {
            "n_tasks": int(array.size),
            "task_weighted_mean": raw_mean,
            "task_weighted_sd": float(array.std(ddof=1)) if array.size > 1 else 0.0,
            "shrunk_mean": shrunk,
        }

    return {
        "method": (
            "Same-holdout all-subsets cross-validation on public training demonstrations; "
            "subset evidence averaged within heldout fold, folds within task, tasks equally."
        ),
        "tasks_seen": len(task_ids),
        "global_task_family_mean": global_mean,
        "prior_strength_tasks": prior_strength,
        "families": families,
    }


def local_family_evidence(
    demos: list[tuple[np.ndarray, np.ndarray]],
) -> dict[str, dict[str, float]]:
    """Same-task cross-validation, collapsed to one observation per heldout fold."""
    family_fold_rates: dict[str, list[float]] = defaultdict(list)
    for heldout_index, (held_input, held_output) in enumerate(demos):
        available = [index for index in range(len(demos)) if index != heldout_index]
        fold: dict[str, list[float]] = defaultdict(list)
        truth = grid_key(held_output)
        for fit_indices in all_nonempty_subsets(available):
            fit_pairs = [demos[index] for index in fit_indices]
            for name, fn in build_programs(fit_pairs):
                if not passes_demos(fn, fit_pairs):
                    continue
                prediction = safe_predict(fn, held_input)
                if prediction is None:
                    continue
                fold[family_name(name)].append(float(grid_key(prediction) == truth))
        for family, values in fold.items():
            family_fold_rates[family].append(float(np.mean(values)))

    return {
        family: {"folds": float(len(values)), "sum_rate": float(np.sum(values))}
        for family, values in family_fold_rates.items()
    }


def family_reliability(
    family: str,
    priors: dict[str, Any],
    local: dict[str, dict[str, float]],
    *,
    local_strength: float = DEFAULT_LOCAL_STRENGTH,
) -> float:
    global_mean = float(priors.get("global_task_family_mean", 0.5))
    prior = float(
        priors.get("families", {}).get(family, {}).get("shrunk_mean", global_mean)
    )
    evidence = local.get(family)
    if not evidence:
        return prior
    folds = float(evidence["folds"])
    return float(
        (local_strength * prior + float(evidence["sum_rate"]))
        / (local_strength + folds)
    )


def candidate_weight(
    *, reliability: float, support: float, cx: int, full_consistent: bool
) -> float:
    reliability = min(0.995, max(0.005, reliability))
    complexity_penalty = 1.0 + 0.30 * max(0, cx - 1)
    full_bonus = 1.35 if full_consistent else 1.0
    return float(full_bonus * (reliability**2) * (support**3) / complexity_penalty)


def generate_hypotheses(
    demos: list[tuple[np.ndarray, np.ndarray]],
) -> list[dict[str, Any]]:
    """Generate full-consistent hypotheses plus a marked near-consistent fallback."""
    n_demos = len(demos)
    hypotheses: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[int, ...]]] = set()

    index_sets = [tuple(range(n_demos))]
    index_sets.extend(
        subset
        for k in range(n_demos - 1, 0, -1)
        for subset in itertools.combinations(range(n_demos), k)
    )

    for fit_indices in index_sets:
        fit_pairs = [demos[index] for index in fit_indices]
        for name, fn in build_programs(fit_pairs):
            if not passes_demos(fn, fit_pairs):
                continue
            signature = (name, fit_indices)
            if signature in seen:
                continue
            seen.add(signature)
            hits = 0
            executable = 0
            for demo_input, demo_output in demos:
                prediction = safe_predict(fn, demo_input)
                if prediction is None:
                    continue
                executable += 1
                hits += int(grid_key(prediction) == grid_key(demo_output))
            if executable == 0:
                continue
            full_consistent = hits == n_demos
            # Near-consistent fallback is admitted only when no more than one
            # demonstration is missed. For D=2 this includes one-demo hypotheses,
            # but evidence weighting and pass@2 limit the damage.
            if hits < max(1, n_demos - 1):
                continue
            hypotheses.append(
                {
                    "name": name,
                    "family": family_name(name),
                    "fn": fn,
                    "complexity": int(complexity(name)),
                    "hits": hits,
                    "support": float(hits / n_demos),
                    "full_consistent": full_consistent,
                    "fit_indices": fit_indices,
                }
            )
    return hypotheses


def rank_predictions(
    demos: list[tuple[np.ndarray, np.ndarray]],
    test_input: np.ndarray,
    priors: dict[str, Any],
) -> list[dict[str, Any]]:
    local = local_family_evidence(demos)
    hypotheses = generate_hypotheses(demos)
    full_exists = any(hypothesis["full_consistent"] for hypothesis in hypotheses)
    if full_exists:
        hypotheses = [h for h in hypotheses if h["full_consistent"]]

    predictions: dict[bytes, dict[str, Any]] = {}
    for hypothesis in hypotheses:
        prediction = safe_predict(hypothesis["fn"], test_input)
        if prediction is None:
            continue
        key = grid_key(prediction)
        reliability = family_reliability(hypothesis["family"], priors, local)
        weight = candidate_weight(
            reliability=reliability,
            support=hypothesis["support"],
            cx=hypothesis["complexity"],
            full_consistent=hypothesis["full_consistent"],
        )
        bucket = predictions.setdefault(
            key,
            {
                "grid": prediction,
                "family_weights": {},
                "best_reliability": 0.0,
                "min_complexity": 10_000,
                "n_hypotheses": 0,
                "full_consistent": False,
            },
        )
        # One DSL family gets at most one vote for a given output. This blocks
        # syntactic duplication from manufacturing confidence.
        previous = bucket["family_weights"].get(hypothesis["family"], 0.0)
        bucket["family_weights"][hypothesis["family"]] = max(previous, weight)
        bucket["best_reliability"] = max(bucket["best_reliability"], reliability)
        bucket["min_complexity"] = min(
            bucket["min_complexity"], hypothesis["complexity"]
        )
        bucket["n_hypotheses"] += 1
        bucket["full_consistent"] = bool(
            bucket["full_consistent"] or hypothesis["full_consistent"]
        )

    ranked: list[dict[str, Any]] = []
    for key, bucket in predictions.items():
        weights = list(bucket["family_weights"].values())
        total = float(sum(weights))
        # Diminishing returns for many closely related families.
        score = float(total / math.sqrt(max(1, len(weights))))
        ranked.append(
            {
                **bucket,
                "key": key,
                "score": score,
                "n_families": len(weights),
            }
        )
    ranked.sort(
        key=lambda item: (
            -int(item["full_consistent"]),
            -item["score"],
            -item["best_reliability"],
            item["min_complexity"],
            -item["n_families"],
            item["key"],
        )
    )
    return ranked


def evidence_solve_one(
    train_pairs: list[tuple[np.ndarray, np.ndarray]],
    test_input: list[list[int]] | np.ndarray,
    priors: dict[str, Any],
) -> tuple[list[list[int]], list[list[int]], dict[str, Any]]:
    x = np.asarray(test_input, dtype=np.int8)
    ranked = rank_predictions(train_pairs, x, priors)
    fallbacks = [x, np.rot90(x, 2)]
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
        "candidate_outputs": len(ranked),
        "top_score": float(ranked[0]["score"]) if ranked else 0.0,
        "top_families": int(ranked[0]["n_families"]) if ranked else 0,
        "full_consistent_output_available": bool(
            ranked and ranked[0]["full_consistent"]
        ),
    }
    return first.tolist(), second.tolist(), metadata


def legacy_solve_one(
    train_pairs: list[tuple[np.ndarray, np.ndarray]],
    test_input: list[list[int]] | np.ndarray,
) -> tuple[list[list[int]], list[list[int]]]:
    x = np.asarray(test_input, dtype=np.int8)
    candidates = [
        (name, fn)
        for name, fn in build_programs(train_pairs)
        if passes_demos(fn, train_pairs)
    ]
    predictions: dict[bytes, dict[str, Any]] = {}
    for name, fn in candidates:
        prediction = safe_predict(fn, x)
        if prediction is None:
            continue
        key = grid_key(prediction)
        bucket = predictions.setdefault(
            key, {"grid": prediction, "votes": 0, "min_cx": 10_000}
        )
        bucket["votes"] += 1
        bucket["min_cx"] = min(bucket["min_cx"], complexity(name))
    ranked = sorted(
        predictions.values(), key=lambda item: (-item["votes"], item["min_cx"])
    )
    fallbacks = [x, np.rot90(x, 2)]
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
    return first.tolist(), second.tolist()


def build_submission(
    challenges: dict[str, dict[str, Any]],
    priors: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    submission: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    for task_id, task in challenges.items():
        demos = pairs_from_task(task)
        outputs = []
        task_meta = []
        for test in task["test"]:
            attempt_1, attempt_2, meta = evidence_solve_one(
                demos, test["input"], priors
            )
            outputs.append({"attempt_1": attempt_1, "attempt_2": attempt_2})
            task_meta.append(meta)
        submission[task_id] = outputs
        metadata[task_id] = task_meta
    return submission, metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Challenge JSON file or split name training/evaluation")
    parser.add_argument("--data-root", default=os.environ.get("ARC_DATA_ROOT", "external/ARC-AGI-2/data"))
    parser.add_argument("--priors", default="results/solver/family_priors.json")
    parser.add_argument("--learn-priors", action="store_true")
    parser.add_argument("--prior-strength", type=float, default=DEFAULT_PRIOR_STRENGTH)
    parser.add_argument("--output", default="submission_v2.json")
    parser.add_argument("--metadata", default="submission_v2_metadata.json")
    args = parser.parse_args()

    prior_path = Path(args.priors)
    if args.learn_priors:
        training = load_tasks(args.data_root, "training")
        priors = learn_family_priors(
            training, prior_strength=args.prior_strength
        )
        prior_path.parent.mkdir(parents=True, exist_ok=True)
        prior_path.write_text(json.dumps(priors, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {prior_path}")
    else:
        priors = json.loads(prior_path.read_text(encoding="utf-8"))

    if args.input in {"training", "evaluation"}:
        tasks = load_tasks(args.data_root, args.input)
        challenges = tasks
    else:
        challenges = json.loads(Path(args.input).read_text(encoding="utf-8"))

    submission, metadata = build_submission(challenges, priors)
    Path(args.output).write_text(json.dumps(submission), encoding="utf-8")
    Path(args.metadata).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} for {len(submission)} tasks")


if __name__ == "__main__":
    main()
