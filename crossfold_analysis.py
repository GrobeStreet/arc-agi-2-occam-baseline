#!/usr/bin/env python3
"""Analyze the same-holdout ARC cross-fold calibration experiment.

Primary statistical unit: ARC task.

The raw cross-fold experiment records every combination of:
  task x held-out demonstration x k fitted demonstrations x fitted subset.

This script first averages subset choices within each fixed task/holdout/k fold,
then averages held-out folds within each task, and finally averages tasks equally.
Task-cluster bootstrap intervals preserve every dependency below the task level.

Outputs
-------
results/crossfold/crossfold_calibration.json
results/crossfold/crossfold_calibration.md
results/crossfold/crossfold_fold_summary.csv
results/crossfold/crossfold_task_summary.csv
results/crossfold/crossfold_selection_by_k.csv
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
    arr = np.asarray(list(values), dtype=float)
    return arr[np.isfinite(arr)]


def safe_mean(values: Iterable[float]) -> float | None:
    arr = finite(values)
    return float(arr.mean()) if arr.size else None


def ci95(values: np.ndarray) -> list[float] | None:
    arr = finite(values)
    if not arr.size:
        return None
    return [float(np.quantile(arr, 0.025)), float(np.quantile(arr, 0.975))]


def bootstrap_task_matrix(
    task_table: pd.DataFrame,
    metric: str,
    ks: list[int],
    *,
    n_boot: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Resample complete task rows while retaining all k values for each task."""
    pivot = task_table.pivot(index="task", columns="k", values=metric).reindex(columns=ks)
    matrix = pivot.to_numpy(float)
    n_tasks = len(matrix)
    out = np.full((n_boot, len(ks)), np.nan, dtype=float)
    if n_tasks == 0:
        return out
    chunk = 2_000
    for start in range(0, n_boot, chunk):
        stop = min(start + chunk, n_boot)
        draw = rng.integers(0, n_tasks, size=(stop - start, n_tasks))
        sampled = matrix[draw]
        counts = np.sum(np.isfinite(sampled), axis=1)
        sums = np.nansum(sampled, axis=1)
        np.divide(sums, counts, out=out[start:stop], where=counts > 0)
    return out


def bootstrap_task_mean(
    values: np.ndarray,
    *,
    n_boot: int,
    rng: np.random.Generator,
) -> np.ndarray:
    vals = finite(values)
    if vals.size == 0:
        return np.array([], dtype=float)
    if vals.size == 1:
        return np.repeat(vals[0], n_boot)
    out = np.empty(n_boot, dtype=float)
    chunk = 5_000
    for start in range(0, n_boot, chunk):
        stop = min(start + chunk, n_boot)
        idx = rng.integers(0, vals.size, size=(stop - start, vals.size))
        out[start:stop] = vals[idx].mean(axis=1)
    return out


def aggregate_fold(group: pd.DataFrame) -> pd.Series:
    covered = group[group["covered"] == 1]
    n_total = len(group)
    n_covered = len(covered)

    def covered_mean(column: str) -> float:
        return float(covered[column].mean()) if n_covered else np.nan

    candidate_total = float(covered["n_consistent"].sum()) if n_covered else 0.0
    candidate_correct = float(covered["candidate_correct"].sum()) if n_covered else 0.0

    def unstable(column: str) -> float:
        values = covered[column][covered[column].astype(str) != ""]
        return float(values.nunique() > 1) if len(values) > 1 else 0.0

    return pd.Series(
        {
            "n_subsets": n_total,
            "n_covered_subsets": n_covered,
            "coverage": n_covered / n_total if n_total else np.nan,
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
            "legacy_subset_instability": unstable("legacy_prediction"),
            "mdl_subset_instability": unstable("mdl_prediction"),
            "consensus_subset_instability": unstable("consensus_prediction"),
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
    rng = np.random.default_rng(seed)

    overall_task = ambiguous.groupby("task")[[*SELECTION_COLUMNS.values()]].mean()
    for label, column in SELECTION_COLUMNS.items():
        values = overall_task[column].to_numpy(float)
        boot = bootstrap_task_mean(values, n_boot=n_boot, rng=rng)
        result["overall"][label] = {
            "task_weighted_rate": float(values.mean()),
            "ci95": ci95(boot),
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
        values = (overall_task[left] - overall_task[right]).to_numpy(float)
        boot = bootstrap_task_mean(values, n_boot=n_boot, rng=rng)
        result["contrasts"][label] = {
            "task_weighted_difference": float(values.mean()),
            "ci95": ci95(boot),
            "bootstrap_probability_positive": float(np.mean(boot > 0)),
        }

    rows: list[dict[str, Any]] = []
    for k, group in ambiguous.groupby("k", sort=True):
        task = group.groupby("task")[[*SELECTION_COLUMNS.values()]].mean()
        row: dict[str, Any] = {
            "k": int(k),
            "n_cells": int(len(group)),
            "n_tasks": int(len(task)),
        }
        for label, column in SELECTION_COLUMNS.items():
            values = task[column].to_numpy(float)
            boot = bootstrap_task_mean(values, n_boot=n_boot, rng=rng)
            row[label] = float(values.mean())
            row[f"{label}_ci95"] = ci95(boot)
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

    rng = np.random.default_rng(seed)
    task_brier = covered.assign(
        brier=(covered["modal_frac"] - covered["modal_correct"]) ** 2,
        abs_gap=np.abs(covered["modal_frac"] - covered["modal_correct"]),
    ).groupby("task")[["brier", "abs_gap"]].mean()

    brier_boot = bootstrap_task_mean(task_brier["brier"].to_numpy(float), n_boot=n_boot, rng=rng)
    gap_boot = bootstrap_task_mean(task_brier["abs_gap"].to_numpy(float), n_boot=n_boot, rng=rng)

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
    for label, group in covered.groupby("confidence_bin", observed=True):
        task = group.groupby("task").agg(
            confidence=("modal_frac", "mean"),
            accuracy=("modal_correct", "mean"),
        )
        if task.empty:
            continue
        acc_boot = bootstrap_task_mean(task["accuracy"].to_numpy(float), n_boot=n_boot, rng=rng)
        calibration_gap = (task["confidence"] - task["accuracy"]).to_numpy(float)
        gap_bin_boot = bootstrap_task_mean(calibration_gap, n_boot=n_boot, rng=rng)
        bins.append(
            {
                "bin": str(label),
                "n_cells": int(len(group)),
                "n_tasks": int(len(task)),
                "task_weighted_confidence": float(task["confidence"].mean()),
                "task_weighted_accuracy": float(task["accuracy"].mean()),
                "accuracy_ci95": ci95(acc_boot),
                "confidence_minus_accuracy": float(calibration_gap.mean()),
                "gap_ci95": ci95(gap_bin_boot),
            }
        )

    return {
        "n_cells": int(len(covered)),
        "n_tasks": int(covered["task"].nunique()),
        "task_weighted_brier": float(task_brier["brier"].mean()),
        "brier_ci95": ci95(brier_boot),
        "task_weighted_mean_absolute_gap": float(task_brier["abs_gap"].mean()),
        "mean_absolute_gap_ci95": ci95(gap_boot),
        "bins": bins,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/crossfold/crossfold_training.parquet")
    parser.add_argument("--results-dir", default="results/crossfold")
    parser.add_argument("--bootstrap", type=int, default=50_000)
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
    rng = np.random.default_rng(args.seed)
    boot_by_metric = {
        metric: bootstrap_task_matrix(task, metric, ks, n_boot=args.bootstrap, rng=rng)
        for metric in PRIMARY_METRICS
    }

    results_by_k: list[dict[str, Any]] = []
    for col, k in enumerate(ks):
        observed = task[task["k"] == k]
        row: dict[str, Any] = {
            "k": k,
            "n_tasks": int(observed["task"].nunique()),
            "n_holdout_folds": int(len(fold[fold["k"] == k])),
            "n_subset_cells": int(len(cells[cells["k"] == k])),
            "metrics": {},
        }
        for metric in PRIMARY_METRICS:
            value = safe_mean(observed[metric])
            row["metrics"][metric] = {
                "task_weighted_mean": value,
                "ci95": ci95(boot_by_metric[metric][:, col]),
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
        contrast: dict[str, Any] = {
            "contrast": f"k={k2} minus k={k1}",
            "n_common_task_holdouts": int(len(common)),
            "n_common_tasks": int(len(set(index[0] for index in common))),
            "metrics": {},
        }
        contrast_rng = np.random.default_rng(args.seed + 1000 + k1)
        for metric in YIELD_METRICS:
            diff = (
                right.loc[common, metric].to_numpy(float)
                - left.loc[common, metric].to_numpy(float)
            )
            diff_table = pd.DataFrame(
                {
                    "task": [index[0] for index in common],
                    "difference": diff,
                }
            )
            task_diff = diff_table.groupby("task")["difference"].mean().to_numpy(float)
            boot = bootstrap_task_mean(task_diff, n_boot=args.bootstrap, rng=contrast_rng)
            contrast["metrics"][metric] = {
                "task_weighted_delta": float(task_diff.mean()),
                "ci95": ci95(boot),
                "bootstrap_probability_positive": float(np.mean(boot > 0)),
            }
        contrasts.append(contrast)

    selection, selection_table = summarize_selection(
        cells,
        n_boot=args.bootstrap,
        seed=args.seed + 2000,
    )
    modal = summarize_modal_calibration(
        cells,
        n_boot=args.bootstrap,
        seed=args.seed + 3000,
    )

    output: dict[str, Any] = {
        "design": (
            "For every training task and held-out demonstration, evaluate every subset of the "
            "remaining demonstrations. Same-target adjacent-k effects hold the target fixed."
        ),
        "data_policy": (
            "Public ARC-AGI-2 training demonstrations only; no evaluation labels or leaderboard "
            "feedback used for development."
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
            "contribute at larger k. Same-holdout contrasts are the primary demonstration-count test."
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
        interval = item["ci95"]
        if value is None or interval is None:
            return "NA"
        return f"{100*value:.1f}% [{100*interval[0]:.1f}, {100*interval[1]:.1f}]"

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
            interval = item["ci95"]
            lines.append(
                f"- **{metric}:** {100*item['task_weighted_delta']:+.1f} pp; "
                f"95% CI [{100*interval[0]:+.1f}, {100*interval[1]:+.1f}] pp; "
                f"P(delta>0)={item['bootstrap_probability_positive']:.4f}."
            )
        lines.append("")

    lines += ["## Selection on ambiguous subset cells", ""]
    if selection.get("n_cells", 0):
        lines.append(
            f"**{selection['n_cells']:,} ambiguous cells across {selection['n_tasks']} tasks.**"
        )
        for label, item in selection["overall"].items():
            interval = item["ci95"]
            lines.append(
                f"- **{label}:** {100*item['task_weighted_rate']:.1f}% "
                f"[95% CI {100*interval[0]:.1f}, {100*interval[1]:.1f}]"
            )
        lines.append("")
        for label, item in selection["contrasts"].items():
            interval = item["ci95"]
            lines.append(
                f"- **{label}:** {100*item['task_weighted_difference']:+.1f} pp "
                f"[95% CI {100*interval[0]:+.1f}, {100*interval[1]:+.1f}]"
            )

    lines += [
        "",
        "## Resolution rule",
        "",
        "The same-target adjacent-k effects are the primary test of whether added demonstrations improve this DSL's reliable end-to-end behavior. The selection analysis distinguishes a legacy enumeration-order shortest program from tie-aware MDL and consensus, preventing an arbitrary list order from masquerading as Occam's razor.",
    ]
    md_path = results_dir / "crossfold_calibration.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"), flush=True)
    print(f"Wrote {json_path}", flush=True)


if __name__ == "__main__":
    main()
