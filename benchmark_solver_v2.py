#!/usr/bin/env python3
"""Benchmark the evidence-weighted solver against the released baseline.

Family reliability priors are learned only from the public training split. The
public evaluation split is then treated as a frozen temporal/difficulty holdout:
no evaluation result is used to tune the ranking rule or its constants.

This is not a Kaggle-private capability claim. It is an independently reproducible
public-split comparison and a required bridge from the paper's measurement result
to a working selection algorithm.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from dsl import build_programs, complexity, passes_demos
from evidence_weighted_solver import (
    evidence_solve_one,
    grid_key,
    learn_family_priors,
    legacy_solve_one,
    load_tasks,
    pairs_from_task,
    safe_predict,
)


def wilson(successes: int, trials: int, confidence: float = 0.95) -> list[float] | None:
    if trials <= 0:
        return None
    interval = stats.binomtest(successes, trials).proportion_ci(
        confidence_level=confidence, method="wilson"
    )
    return [float(interval.low), float(interval.high)]


def exact_mcnemar(a_correct: np.ndarray, b_correct: np.ndarray) -> dict[str, Any]:
    """Exact two-sided McNemar/binomial test for paired binary outcomes."""
    a = np.asarray(a_correct, dtype=bool)
    b = np.asarray(b_correct, dtype=bool)
    a_only = int(np.sum(a & ~b))
    b_only = int(np.sum(~a & b))
    discordant = a_only + b_only
    p_value = (
        float(stats.binomtest(min(a_only, b_only), discordant, 0.5).pvalue)
        if discordant
        else 1.0
    )
    return {
        "a_only": a_only,
        "b_only": b_only,
        "discordant": discordant,
        "exact_two_sided_p": p_value,
    }


def pure_mdl_solve_one(
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
            key,
            {
                "grid": prediction,
                "min_complexity": 10_000,
                "support_at_min": 0,
            },
        )
        cx = int(complexity(name))
        if cx < bucket["min_complexity"]:
            bucket["min_complexity"] = cx
            bucket["support_at_min"] = 1
        elif cx == bucket["min_complexity"]:
            bucket["support_at_min"] += 1
    ranked = sorted(
        predictions.values(),
        key=lambda item: (item["min_complexity"], -item["support_at_min"]),
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


def score_attempts(
    truth: np.ndarray,
    attempt_1: list[list[int]],
    attempt_2: list[list[int]],
) -> tuple[int, int]:
    a1 = np.asarray(attempt_1)
    a2 = np.asarray(attempt_2)
    first = int(a1.shape == truth.shape and np.array_equal(a1, truth))
    second = int(
        first
        or (a2.shape == truth.shape and np.array_equal(a2, truth))
    )
    return first, second


def summarize_method(frame: pd.DataFrame, method: str) -> dict[str, Any]:
    p1 = frame[f"{method}_pass1"].astype(int)
    p2 = frame[f"{method}_pass2"].astype(int)
    return {
        "pass1": {
            "correct": int(p1.sum()),
            "trials": int(len(p1)),
            "rate": float(p1.mean()),
            "wilson_ci95": wilson(int(p1.sum()), len(p1)),
        },
        "pass2": {
            "correct": int(p2.sum()),
            "trials": int(len(p2)),
            "rate": float(p2.mean()),
            "wilson_ci95": wilson(int(p2.sum()), len(p2)),
        },
        "tasks_with_any_pass2": int(
            frame.groupby("task")[f"{method}_pass2"].max().sum()
        ),
        "tasks_all_test_outputs_pass2": int(
            frame.groupby("task")[f"{method}_pass2"].min().sum()
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="external/ARC-AGI-2/data")
    parser.add_argument("--priors", default="results/solver/family_priors.json")
    parser.add_argument("--output-dir", default="results/solver")
    parser.add_argument("--prior-strength", type=float, default=8.0)
    parser.add_argument("--relearn", action="store_true")
    parser.add_argument("--max-training-tasks", type=int, default=None)
    parser.add_argument("--max-evaluation-tasks", type=int, default=None)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prior_path = Path(args.priors)

    training = load_tasks(args.data_root, "training")
    if args.max_training_tasks is not None:
        training = dict(list(sorted(training.items()))[: args.max_training_tasks])

    if args.relearn or not prior_path.exists():
        started = time.perf_counter()
        priors = learn_family_priors(
            training,
            prior_strength=args.prior_strength,
            max_tasks=None,
        )
        priors["learning_seconds"] = float(time.perf_counter() - started)
        prior_path.parent.mkdir(parents=True, exist_ok=True)
        prior_path.write_text(json.dumps(priors, indent=2) + "\n", encoding="utf-8")
    else:
        priors = json.loads(prior_path.read_text(encoding="utf-8"))

    evaluation = load_tasks(args.data_root, "evaluation")
    if args.max_evaluation_tasks is not None:
        evaluation = dict(
            list(sorted(evaluation.items()))[: args.max_evaluation_tasks]
        )

    rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    for task_number, (task_id, task) in enumerate(sorted(evaluation.items()), start=1):
        demos = pairs_from_task(task)
        for test_index, test in enumerate(task["test"]):
            if "output" not in test:
                continue
            truth = np.asarray(test["output"], dtype=np.int8)

            legacy_1, legacy_2 = legacy_solve_one(demos, test["input"])
            mdl_1, mdl_2 = pure_mdl_solve_one(demos, test["input"])
            evidence_1, evidence_2, metadata = evidence_solve_one(
                demos, test["input"], priors
            )

            legacy_pass1, legacy_pass2 = score_attempts(
                truth, legacy_1, legacy_2
            )
            mdl_pass1, mdl_pass2 = score_attempts(truth, mdl_1, mdl_2)
            evidence_pass1, evidence_pass2 = score_attempts(
                truth, evidence_1, evidence_2
            )
            rows.append(
                {
                    "task": task_id,
                    "test_index": test_index,
                    "n_demos": len(demos),
                    "legacy_pass1": legacy_pass1,
                    "legacy_pass2": legacy_pass2,
                    "mdl_pass1": mdl_pass1,
                    "mdl_pass2": mdl_pass2,
                    "evidence_pass1": evidence_pass1,
                    "evidence_pass2": evidence_pass2,
                    **metadata,
                }
            )

        if task_number % 20 == 0 or task_number == len(evaluation):
            print(
                f"benchmarked {task_number}/{len(evaluation)} evaluation tasks; "
                f"{len(rows)} test outputs",
                flush=True,
            )

    elapsed = float(time.perf_counter() - started)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError(
            "No public evaluation outputs were found. The official checkout may "
            "have changed format or removed labels."
        )

    methods = {
        method: summarize_method(frame, method)
        for method in ("legacy", "mdl", "evidence")
    }
    comparisons = {
        "evidence_vs_legacy_pass1": exact_mcnemar(
            frame["evidence_pass1"], frame["legacy_pass1"]
        ),
        "evidence_vs_legacy_pass2": exact_mcnemar(
            frame["evidence_pass2"], frame["legacy_pass2"]
        ),
        "evidence_vs_mdl_pass1": exact_mcnemar(
            frame["evidence_pass1"], frame["mdl_pass1"]
        ),
        "evidence_vs_mdl_pass2": exact_mcnemar(
            frame["evidence_pass2"], frame["mdl_pass2"]
        ),
    }

    output = {
        "design": (
            "Family priors learned only from public training demonstrations; fixed "
            "algorithm then evaluated once on public evaluation test outputs."
        ),
        "not_a_private_leaderboard_claim": True,
        "training_tasks_used_for_priors": len(training),
        "evaluation_tasks": int(frame["task"].nunique()),
        "evaluation_test_outputs": int(len(frame)),
        "prior_strength": args.prior_strength,
        "family_count": len(priors.get("families", {})),
        "benchmark_seconds": elapsed,
        "methods": methods,
        "paired_exact_tests": comparisons,
        "interpretation_rule": (
            "Promote the evidence-weighted selector only if it improves paired public-"
            "evaluation outcomes without using evaluation feedback for tuning. Otherwise "
            "retain the measurement audit and report the algorithmic null result."
        ),
    }

    frame.to_csv(output_dir / "solver_v2_evaluation_predictions.csv", index=False)
    (output_dir / "solver_v2_benchmark.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Evidence-weighted ARC solver: frozen public-evaluation benchmark",
        "",
        "Program-family priors were learned only from public training demonstrations. The public evaluation split was then scored once as a holdout. This is not a private Kaggle leaderboard claim.",
        "",
        "| method | pass@1 | 95% CI | pass@2 | 95% CI | tasks with any pass@2 | tasks all outputs pass@2 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    labels = {
        "legacy": "Released vote + MDL baseline",
        "mdl": "Pure minimum description length",
        "evidence": "Evidence-weighted family selector",
    }
    for method, label in labels.items():
        result = methods[method]
        p1 = result["pass1"]
        p2 = result["pass2"]
        lines.append(
            f"| {label} | {100*p1['rate']:.2f}% ({p1['correct']}/{p1['trials']}) | "
            f"[{100*p1['wilson_ci95'][0]:.2f}, {100*p1['wilson_ci95'][1]:.2f}] | "
            f"{100*p2['rate']:.2f}% ({p2['correct']}/{p2['trials']}) | "
            f"[{100*p2['wilson_ci95'][0]:.2f}, {100*p2['wilson_ci95'][1]:.2f}] | "
            f"{result['tasks_with_any_pass2']} | {result['tasks_all_test_outputs_pass2']} |"
        )
    lines.extend(["", "## Paired differences", ""])
    for name, comparison in comparisons.items():
        lines.append(
            f"- **{name}:** evidence-only wins {comparison['a_only']}; comparator-only wins "
            f"{comparison['b_only']}; exact McNemar/binomial p={comparison['exact_two_sided_p']:.4f}."
        )
    lines.extend(
        [
            "",
            "## Decision rule",
            "",
            "The selector is promoted only if it improves frozen paired evaluation outcomes. A tie or loss is retained as a negative result; the measurement paper does not depend on a solver gain.",
            "",
            f"Runtime: {elapsed:.1f} seconds after prior learning.",
        ]
    )
    (output_dir / "solver_v2_benchmark.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
