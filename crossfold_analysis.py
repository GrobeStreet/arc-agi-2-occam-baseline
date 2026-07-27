#!/usr/bin/env python3
"""Analyze the same-holdout ARC cross-fold calibration experiment.

Primary statistical unit: ARC task.

The raw experiment records every combination of task, held-out demonstration,
k fitted demonstrations, and fitted subset. This script averages subset choices
within fixed task/holdout/k folds, averages held-out folds within task, then gives
each task equal weight. Bootstrap uncertainty resamples complete task clusters.

The bootstrap is vectorized with multinomial task weights. A single set of task
weights is shared across every metric for a given estimand, preserving covariance
while avoiding the enormous 3-D sampled arrays used by the first implementation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


PRIMARY_METRICS = [
    "coverage",
    "random_yield",
    "legacy_mdl_yield",
    "mdl_random_yield",
    "mdl_vote_yield",
    "consensus_yield",
    "oracle_yield",
    "candidate_reliability",
    "subset_random_rate_covered",
    "legacy_accuracy_covered",
    "mdl_random_accuracy_covered",
    "mdl_vote_accuracy_covered",
    "consensus_accuracy_covered",
    "oracle_accuracy_covered",
    "ambiguity_rate_covered",
    "minimum_complexity_output_tie_rate",
    "modal_fraction_covered",
    "mean_candidate_count_covered",
    "legacy_subset_instability",
    "mdl_subset_instability",
    "consensus_subset_instability",
    "random_rate_range",
]

YIELD_METRICS = [
    "coverage",
    "random_yield",
    "legacy_mdl_yield",
    "mdl_random_yield",
    "mdl_vote_yield",
    "consensus_yield",
    "oracle_yield",
]

SELECTION_COLUMNS = {
    "random": "random_rate",
    "legacy_first_shortest": "legacy_shortest_correct",
    "mdl_random_tie": "mdl_random_rate",
    "mdl_vote_tie": "mdl_vote_correct",
    "consensus": "consensus_correct",
    "oracle": "any_correct",
}


def finite(values: Iterable[float]) -> np.ndarray:
    array = np.asarray(list(values), dtype=float)
    return array[np.isfinite(array)]


def safe_mean(values: Iterable[float]) -> float | None:
    array = finite(values)
    return float(array.mean()) if array.size else None


def interval(values: np.ndarray) -> list[float] | None:
    array = finite(values)
    if not array.size:
        return None
    return [float(np.quantile(array, 0.025)), float(np.quantile(array, 0.975))]


def bootstrap_columns(
    frame: pd.DataFrame,
    columns: list[str],
    *,
    n_boot: int,
    seed: int,
    chunk_size: int = 1_000,
) -> dict[str, np.ndarray]:
    """Bootstrap equally weighted rows and all requested columns together.

    Multinomial counts are equivalent to sampling rows with replacement. Missing
    values are handled column-by-column by dividing weighted sums by weighted
    finite counts. Sharing count draws preserves cross-metric covariance.
    """
    if frame.empty:
        return {column: np.array([], dtype=float) for column in columns}

    values = frame[columns].to_numpy(dtype=float)
    valid = np.isfinite(values).astype(float)
    filled = np.nan_to_num(values, nan=0.0)
    n_rows = len(frame)
    probability = np.full(n_rows, 1.0 / n_rows)
    rng = np.random.default_rng(seed)
    output = np.full((n_boot, len(columns)), np.nan, dtype=float)

    for start in range(0, n_boot, chunk_size):
        stop = min(start + chunk_size, n_boot)
        counts = rng.multinomial(n_rows, probability, size=stop - start).astype(float)
        numerator = counts @ filled
        denominator = counts @ valid
        np.divide(
            numerator,
            denominator,
            out=output[start:stop],
            where=denominator > 0,
        )

    return {column: output[:, index] for index, column in enumerate(columns)}


def aggregate_fold(group: pd.DataFrame) -> pd.Series:
    covered = group[group["covered"] == 1]
    total = len(group)
    n_covered = len(covered)

    def covered_mean(column: str) -> float:
        return float(covered[column].mean()) if n_covered else np.nan

    candidate_total = float(covered["n_consistent"].sum()) if n_covered else 0.0
    candidate_correct = float(covered["candidate_correct"].sum()) if n_covered else 0.0

    def instability(column: str) -> float:
        values = covered[column].astype(str)
        values = values[values != ""]
        return float(values.nunique() > 1) if len(values) > 1 else 0.0

    return pd.Series(
        {
            "n_subsets": total,
            "n_covered_subsets": n_covered,
            "coverage": n_covered / total if total else np.nan,
            "random_yield": float(group["random_rate"].fillna(0).mean()),
            "legacy_mdl_yield": float(group["legacy_shortest_correct"].mean()),
            "mdl_random_yield": float(group["mdl_random_rate"].fillna(0).mean()),
            "mdl_vote_yield": float(group["mdl_vote_correct"].mean()),
            "consensus_yield": float(group["consensus_correct"].mean()),
            "oracle_yield": float(group["any_correct"].mean()),
            "candidate_reliability": candidate_correct / candidate_total if candidate_total else np.nan,
            "subset_random_rate_covered": covered_mean("random_rate"),
            "legacy_accuracy_covered": covered_mean("legacy_shortest_correct"),
            "mdl_random_accuracy_covered": covered_mean("mdl_random_rate"),
            "mdl_vote_accuracy_covered": covered_mean("mdl_vote_correct"),
            "consensus_accuracy_covered": covered_mean("consensus_correct"),
            "oracle_accuracy_covered": covered_mean("any_correct"),
            "ambiguity_rate_covered": covered_mean("ambiguous"),
            "minimum_complexity_output_tie_rate": (
                float((covered["min_complexity_distinct_predictions"] > 1).mean())
                if n_covered
                else np.nan
            ),
            "modal_fraction_covered": covered_mean("modal_frac"),
            "mean_candidate_count_covered": covered_mean("n_consistent"),
            "legacy_subset_instability": instability("legacy_prediction"),
            "mdl_subset_instability": instability("mdl_prediction"),
            "consensus_subset_instability": instability("consensus_prediction"),
            "random_rate_range": (
                float(covered["random_rate"].max() - covered["random_rate"].min())
                if n_covered > 1
                else 0.0
            ),
        }
    )


def summarize_selection(
    cells: pd.DataFrame,
    *,
    n_boot: int,
    seed: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    ambiguous = cells[(cells["covered"] == 1) & (cells["ambiguous"] == 1)].copy()
    if ambiguous.empty:
        return {"n_cells": 0, "n_tasks": 0}, pd.DataFrame()

    result: dict[str, Any] = {
        "n_cells": int(len(ambiguous)),
        "n_tasks": int(ambiguous["task"].nunique()),
        "overall": {},
        "by_k": [],
        "contrasts": {},
    }

    task_overall = ambiguous.groupby("task")[[*SELECTION_COLUMNS.values()]].mean()
    boot = bootstrap_columns(
        task_overall,
        list(SELECTION_COLUMNS.values()),
        n_boot=n_boot,
        seed=seed,
    )
    for label, column in SELECTION_COLUMNS.items():
        values = finite(task_overall[column])
        result["overall"][label] = {
            "task_weighted_rate": float(values.mean()),
            "ci95": interval(boot[column]),
        }

    contrast_pairs = [
        ("legacy_shortest_minus_random", "legacy_shortest_correct", "random_rate"),
        ("mdl_random_minus_random", "mdl_random_rate", "random_rate"),
        ("mdl_vote_minus_random", "mdl_vote_correct", "random_rate"),
        ("consensus_minus_random", "consensus_correct", "random_rate"),
        ("mdl_vote_minus_legacy_shortest", "mdl_vote_correct", "legacy_shortest_correct"),
        ("oracle_minus_mdl_vote", "any_correct", "mdl_vote_correct"),
        ("oracle_minus_consensus", "any_correct", "consensus_correct"),
    ]
    for label, left, right in contrast_pairs:
        task_difference = (task_overall[left] - task_overall[right]).to_frame("difference")
        difference_boot = bootstrap_columns(
            task_difference,
            ["difference"],
            n_boot=n_boot,
            seed=seed + 100 + len(result["contrasts"]),
        )["difference"]
        observed = finite(task_difference["difference"])
        result["contrasts"][label] = {
            "task_weighted_difference": float(observed.mean()),
            "ci95": interval(difference_boot),
            "bootstrap_probability_positive": float(np.mean(difference_boot > 0)),
        }

    rows: list[dict[str, Any]] = []
    for k, group in ambiguous.groupby("k", sort=True):
        task = group.groupby("task")[[*SELECTION_COLUMNS.values()]].mean()
        boot_k = bootstrap_columns(
            task,
            list(SELECTION_COLUMNS.values()),
            n_boot=n_boot,
            seed=seed + 1_000 + int(k),
        )
        row: dict[str, Any] = {
            "k": int(k),
            "n_cells": int(len(group)),
            "n_tasks": int(len(task)),
        }
        for label, column in SELECTION_COLUMNS.items():
            values = finite(task[column])
            row[label] = float(values.mean())
            row[f"{label}_ci95"] = interval(boot_k[column])
        result["by_k"].append(row)
        rows.append(row)

    return result, pd.DataFrame(rows)


def summarize_modal_calibration(
    cells: pd.DataFrame,
    *,
    n_boot: int,
    seed: int,
) -> dict[str, Any]:
    covered = cells[cells["covered"] == 1].copy()
    if covered.empty:
        return {"n_cells": 0, "n_tasks": 0}

    covered["brier"] = (covered["modal_frac"] - covered["modal_correct"]) ** 2
    covered["abs_gap"] = np.abs(covered["modal_frac"] - covered["modal_correct"])
    task_overall = covered.groupby("task")[["brier", "abs_gap"]].mean()
    boot_overall = bootstrap_columns(
        task_overall,
        ["brier", "abs_gap"],
        n_boot=n_boot,
        seed=seed,
    )

    edges = [0.0, 0.5, 0.7, 0.9, 0.999999, 1.000001]
    labels = ["[0,.5)", "[.5,.7)", "[.7,.9)", "[.9,1)", "1.0"]
    covered["confidence_bin"] = pd.cut(
        covered["modal_frac"],
        bins=edges,
        labels=labels,
        right=False,
        include_lowest=True,
    )
    bins: list[dict[str, Any]] = []
    for index, (label, group) in enumerate(covered.groupby("confidence_bin", observed=True)):
        task = group.groupby("task").agg(
            confidence=("modal_frac", "mean"),
            accuracy=("modal_correct", "mean"),
        )
        task["gap"] = task["confidence"] - task["accuracy"]
        boot = bootstrap_columns(
            task,
            ["accuracy", "gap"],
            n_boot=n_boot,
            seed=seed + 100 + index,
        )
        bins.append(
            {
                "bin": str(label),
                "n_cells": int(len(group)),
                "n_tasks": int(len(task)),
                "task_weighted_confidence": float(task["confidence"].mean()),
                "task_weighted_accuracy": float(task["accuracy"].mean()),
                "accuracy_ci95": interval(boot["accuracy"]),
                "confidence_minus_accuracy": float(task["gap"].mean()),
                "gap_ci95": interval(boot["gap"]),
            }
        )

    return {
        "n_cells": int(len(covered)),
        "n_tasks": int(covered["task"].nunique()),
        "task_weighted_brier": float(task_overall["brier"].mean()),
        "brier_ci95": interval(boot_overall["brier"]),
        "task_weighted_mean_absolute_gap": float(task_overall["abs_gap"].mean()),
        "mean_absolute_gap_ci95": interval(boot_overall["abs_gap"]),
        "bins": bins,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/crossfold/crossfold_training.parquet")
    parser.add_argument("--results-dir", default="results/crossfold")
    parser.add_argument("--bootstrap", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260727)
    args = parser.parse_args()

    input_path = Path(args.input)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    cells = pd.read_parquet(input_path)

    required = {
        "task",
        "heldout_index",
        "k",
        "covered",
        "n_consistent",
        "candidate_correct",
        "random_rate",
        "legacy_shortest_correct",
        "legacy_prediction",
        "mdl_random_rate",
        "mdl_vote_correct",
        "mdl_prediction",
        "consensus_correct",
        "consensus_prediction",
        "any_correct",
        "ambiguous",
        "modal_frac",
        "modal_correct",
        "min_complexity_distinct_predictions",
    }
    missing = sorted(required - set(cells.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    fold = (
        cells.groupby(["task", "n_demos", "heldout_index", "k"], sort=True, dropna=False)
        .apply(aggregate_fold, include_groups=False)
        .reset_index()
    )
    task = fold.groupby(["task", "n_demos", "k"], as_index=False)[PRIMARY_METRICS].mean()

    ks = sorted(int(k) for k in task["k"].unique())
    results_by_k: list[dict[str, Any]] = []
    for k in ks:
        observed = task[task["k"] == k].set_index("task")
        boot = bootstrap_columns(
            observed,
            PRIMARY_METRICS,
            n_boot=args.bootstrap,
            seed=args.seed + 10 * k,
        )
        row: dict[str, Any] = {
            "k": k,
            "n_tasks": int(len(observed)),
            "n_holdout_folds": int(len(fold[fold["k"] == k])),
            "n_subset_cells": int(len(cells[cells["k"] == k])),
            "metrics": {},
        }
        for metric in PRIMARY_METRICS:
            row["metrics"][metric] = {
                "task_weighted_mean": safe_mean(observed[metric]),
                "ci95": interval(boot[metric]),
            }
        results_by_k.append(row)

    # Same held-out target on both sides of every adjacent-k contrast.
    contrasts: list[dict[str, Any]] = []
    for k1, k2 in zip(ks[:-1], ks[1:]):
        left = fold[fold["k"] == k1].set_index(["task", "heldout_index"])
        right = fold[fold["k"] == k2].set_index(["task", "heldout_index"])
        common = left.index.intersection(right.index)
        if len(common) == 0:
            continue
        difference = pd.DataFrame(
            right.loc[common, YIELD_METRICS].to_numpy(float)
            - left.loc[common, YIELD_METRICS].to_numpy(float),
            columns=YIELD_METRICS,
        )
        difference["task"] = [index[0] for index in common]
        task_difference = difference.groupby("task")[YIELD_METRICS].mean()
        boot = bootstrap_columns(
            task_difference,
            YIELD_METRICS,
            n_boot=args.bootstrap,
            seed=args.seed + 10_000 + k1,
        )
        contrast: dict[str, Any] = {
            "contrast": f"k={k2} minus k={k1}",
            "n_common_task_holdouts": int(len(common)),
            "n_common_tasks": int(len(task_difference)),
            "metrics": {},
        }
        for metric in YIELD_METRICS:
            values = finite(task_difference[metric])
            contrast["metrics"][metric] = {
                "task_weighted_delta": float(values.mean()),
                "ci95": interval(boot[metric]),
                "bootstrap_probability_positive": float(np.mean(boot[metric] > 0)),
            }
        contrasts.append(contrast)

    selection, selection_table = summarize_selection(
        cells,
        n_boot=args.bootstrap,
        seed=args.seed + 20_000,
    )
    modal = summarize_modal_calibration(
        cells,
        n_boot=args.bootstrap,
        seed=args.seed + 30_000,
    )

    output: dict[str, Any] = {
        "design": (
            "For every task and held-out demonstration, evaluate every subset of the remaining "
            "demonstrations. Same-target adjacent-k effects hold the target fixed."
        ),
        "data_policy": (
            "Public ARC-AGI-2 demonstration pairs only; no hidden test labels or private "
            "leaderboard feedback used for development."
        ),
        "primary_unit": "ARC task",
        "input": str(input_path),
        "n_analyzed_tasks": int(task["task"].nunique()),
        "n_subset_cells": int(len(cells)),
        "n_covered_subset_cells": int(cells["covered"].sum()),
        "n_holdout_k_folds": int(len(fold)),
        "bootstrap_replicates": int(args.bootstrap),
        "bootstrap_seed": int(args.seed),
        "results_by_k": results_by_k,
        "same_holdout_adjacent_k_contrasts": contrasts,
        "ambiguous_subset_selection": selection,
        "modal_vote_calibration": modal,
        "interpretation": (
            "Marginal rates by k are descriptive because tasks with fewer demonstrations cannot "
            "contribute at larger k. Same-holdout contrasts are the primary evidence-count test."
        ),
    }

    json_path = results_dir / "crossfold_calibration.json"
    json_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    fold.to_csv(results_dir / "crossfold_fold_summary.csv", index=False)
    task.to_csv(results_dir / "crossfold_task_summary.csv", index=False)
    selection_table.to_csv(results_dir / "crossfold_selection_by_k.csv", index=False)

    lines = [
        "# Same-holdout cross-fold ARC calibration",
        "",
        "This analysis holds the target demonstration fixed while varying how many of the remaining demonstrations are fitted. It resolves the main identification problem in the original prefix analysis.",
        "",
        f"Analyzed **{output['n_analyzed_tasks']} tasks**, **{output['n_holdout_k_folds']:,} task/holdout/k folds**, and **{output['n_subset_cells']:,} demonstration-subset cells**.",
        "",
        "| k | tasks | coverage | random yield | legacy shortest | tie-aware MDL vote | consensus | oracle | candidate reliability |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def format_metric(row: dict[str, Any], metric: str) -> str:
        item = row["metrics"][metric]
        value = item["task_weighted_mean"]
        ci = item["ci95"]
        if value is None or ci is None:
            return "NA"
        return f"{100*value:.1f}% [{100*ci[0]:.1f}, {100*ci[1]:.1f}]"

    for row in results_by_k:
        lines.append(
            f"| {row['k']} | {row['n_tasks']} | {format_metric(row, 'coverage')} | "
            f"{format_metric(row, 'random_yield')} | {format_metric(row, 'legacy_mdl_yield')} | "
            f"{format_metric(row, 'mdl_vote_yield')} | {format_metric(row, 'consensus_yield')} | "
            f"{format_metric(row, 'oracle_yield')} | {format_metric(row, 'candidate_reliability')} |"
        )

    lines += ["", "## Same-target adjacent-k effects", ""]
    for contrast in contrasts:
        lines.append(
            f"### {contrast['contrast']} ({contrast['n_common_tasks']} tasks; "
            f"{contrast['n_common_task_holdouts']} held-out folds)"
        )
        for metric, item in contrast["metrics"].items():
            ci = item["ci95"]
            lines.append(
                f"- **{metric}:** {100*item['task_weighted_delta']:+.1f} pp; "
                f"95% CI [{100*ci[0]:+.1f}, {100*ci[1]:+.1f}] pp; "
                f"P(delta>0)={item['bootstrap_probability_positive']:.4f}."
            )
        lines.append("")

    lines += ["## Selection on ambiguous subset cells", ""]
    if selection.get("n_cells", 0):
        lines.append(f"**{selection['n_cells']:,} ambiguous cells across {selection['n_tasks']} tasks.**")
        for label, item in selection["overall"].items():
            ci = item["ci95"]
            lines.append(
                f"- **{label}:** {100*item['task_weighted_rate']:.1f}% "
                f"[95% CI {100*ci[0]:.1f}, {100*ci[1]:.1f}]"
            )
        lines.append("")
        for label, item in selection["contrasts"].items():
            ci = item["ci95"]
            lines.append(
                f"- **{label}:** {100*item['task_weighted_difference']:+.1f} pp "
                f"[95% CI {100*ci[0]:+.1f}, {100*ci[1]:+.1f}]"
            )

    lines += [
        "",
        "## Resolution rule",
        "",
        "The same-target adjacent-k effects are the primary test of whether added demonstrations improve this DSL's reliable end-to-end behavior. The selection analysis distinguishes a legacy enumeration-order shortest program from tie-aware MDL and consensus, preventing arbitrary list order from masquerading as Occam's razor.",
        "",
        f"Task-cluster bootstrap: {args.bootstrap:,} replicates, seed {args.seed}.",
    ]
    md_path = results_dir / "crossfold_calibration.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"), flush=True)
    print(f"Wrote {json_path}", flush=True)


if __name__ == "__main__":
    main()
