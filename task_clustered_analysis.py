#!/usr/bin/env python3
"""Task-weighted ARC demonstration-consistency calibration.

The original analysis pooled candidate programs. That estimand weights a task in
proportion to the number of demonstration-consistent programs the DSL happens to
generate for it. This analysis instead gives each ARC task equal weight.

For each (task, k) cell, ``random_rate`` in ``ablate_cell_training.parquet`` is
the fraction of that task's k-consistent candidate programs that generalize to
the held-out next demonstration. We average those cell rates across tasks and
obtain uncertainty by resampling whole task clusters with replacement.

Outputs:
  results/task_weighted_calibration.json
  results/task_weighted_calibration.md
  results/task_weighted_task_cells.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def percentile_interval(values: np.ndarray, alpha: float = 0.05) -> list[float]:
    lo, hi = np.quantile(values, [alpha / 2, 1 - alpha / 2])
    return [float(lo), float(hi)]


def bootstrap_task_matrix(
    matrix: np.ndarray,
    *,
    n_boot: int,
    seed: int,
    chunk_size: int = 5_000,
) -> np.ndarray:
    """Resample complete task clusters and return bootstrap means by k.

    Rows are tasks, columns are k values, and missing task/k cells are NaN.
    Sampling a row carries every k cell belonging to that task, preserving the
    within-task dependence across demonstration counts.
    """

    rng = np.random.default_rng(seed)
    n_tasks, n_k = matrix.shape
    out = np.empty((n_boot, n_k), dtype=float)

    for start in range(0, n_boot, chunk_size):
        stop = min(start + chunk_size, n_boot)
        draw = rng.integers(0, n_tasks, size=(stop - start, n_tasks))
        sampled = matrix[draw]
        with np.errstate(invalid="ignore"):
            out[start:stop] = np.nanmean(sampled, axis=1)
    return out


def as_pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="ablate_cell_training.parquet")
    parser.add_argument("--bootstrap", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260727)
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    input_path = Path(args.input)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(input_path)
    required = {"task", "k", "n_consistent", "random_rate"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # The experiment should create one record per (task, k). Collapse defensively
    # while retaining the exact candidate-weighted success count.
    cell = (
        df.assign(
            candidate_correct=lambda x: x["random_rate"] * x["n_consistent"]
        )
        .groupby(["task", "k"], as_index=False)
        .agg(
            n_consistent=("n_consistent", "sum"),
            candidate_correct=("candidate_correct", "sum"),
        )
    )
    cell["task_rate"] = cell["candidate_correct"] / cell["n_consistent"]

    tasks = sorted(cell["task"].astype(str).unique())
    ks = sorted(int(k) for k in cell["k"].unique())
    task_to_row = {task: i for i, task in enumerate(tasks)}
    k_to_col = {k: j for j, k in enumerate(ks)}
    matrix = np.full((len(tasks), len(ks)), np.nan, dtype=float)
    for row in cell.itertuples(index=False):
        matrix[task_to_row[str(row.task)], k_to_col[int(row.k)]] = float(row.task_rate)

    boot = bootstrap_task_matrix(
        matrix,
        n_boot=args.bootstrap,
        seed=args.seed,
    )

    rows: list[dict[str, Any]] = []
    for col, k in enumerate(ks):
        s = cell[cell["k"] == k]
        task_weighted = float(s["task_rate"].mean())
        program_weighted = float(s["candidate_correct"].sum() / s["n_consistent"].sum())
        b = boot[:, col]
        rows.append(
            {
                "k": k,
                "n_tasks": int(s["task"].nunique()),
                "n_programs": int(s["n_consistent"].sum()),
                "program_weighted_rate": program_weighted,
                "task_weighted_rate": task_weighted,
                "task_minus_program_weighted": task_weighted - program_weighted,
                "task_cluster_bootstrap_se": float(np.std(b, ddof=1)),
                "task_cluster_bootstrap_ci95": percentile_interval(b),
            }
        )

    contrasts: list[dict[str, Any]] = []
    for left_col, right_col in zip(range(len(ks) - 1), range(1, len(ks))):
        delta = boot[:, right_col] - boot[:, left_col]
        observed = float(np.nanmean(matrix[:, right_col]) - np.nanmean(matrix[:, left_col]))
        contrasts.append(
            {
                "contrast": f"k={ks[right_col]} minus k={ks[left_col]}",
                "observed_delta": observed,
                "bootstrap_ci95": percentile_interval(delta),
                "bootstrap_probability_positive": float(np.mean(delta > 0)),
            }
        )

    output = {
        "estimand": (
            "For each k, average the within-task fraction of demonstration-consistent "
            "programs that generalize, giving every represented task equal weight."
        ),
        "uncertainty": (
            "Nonparametric percentile bootstrap resampling complete task clusters; "
            "all k cells from a sampled task travel together."
        ),
        "input": str(input_path),
        "n_unique_tasks_any_k": len(tasks),
        "bootstrap_replicates": args.bootstrap,
        "bootstrap_seed": args.seed,
        "results_by_k": rows,
        "adjacent_k_contrasts": contrasts,
    }

    json_path = results_dir / "task_weighted_calibration.json"
    json_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    cell_path = results_dir / "task_weighted_task_cells.csv"
    cell.sort_values(["k", "task"]).to_csv(cell_path, index=False)

    lines = [
        "# Task-weighted ARC calibration with task-cluster uncertainty",
        "",
        "The original calibration pooled candidate programs, so tasks that generated more candidates received more weight. This reanalysis first computes a generalization rate within each `(task, k)` cell, then averages those rates across tasks. The 95% intervals resample whole tasks with replacement, preserving within-task dependence across demonstration counts.",
        "",
        "| demonstrations fit (k) | tasks | candidate programs | program-weighted | task-weighted | 95% task-cluster bootstrap CI | task minus program |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lo, hi = row["task_cluster_bootstrap_ci95"]
        lines.append(
            f"| {row['k']} | {row['n_tasks']} | {row['n_programs']} | "
            f"{as_pct(row['program_weighted_rate'])} | {as_pct(row['task_weighted_rate'])} | "
            f"[{as_pct(lo)}, {as_pct(hi)}] | {100 * row['task_minus_program_weighted']:+.1f} pp |"
        )

    lines.extend(["", "## Adjacent-k contrasts", ""])
    for c in contrasts:
        lo, hi = c["bootstrap_ci95"]
        lines.append(
            f"- **{c['contrast']}:** {100 * c['observed_delta']:+.1f} percentage points; "
            f"95% task-cluster CI [{100 * lo:+.1f}, {100 * hi:+.1f}] pp; "
            f"bootstrap P(delta > 0) = {c['bootstrap_probability_positive']:.4f}."
        )

    lines.extend(
        [
            "",
            "## Interpretation rule",
            "",
            "The task-weighted estimate is the primary benchmark-level estimand. The program-weighted estimate remains useful as a description of this DSL's candidate population, but it should not be described as the reliability experienced by an average ARC task.",
            "",
            f"Bootstrap: {args.bootstrap:,} task-cluster replicates, seed {args.seed}.",
        ]
    )
    md_path = results_dir / "task_weighted_calibration.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(md_path.read_text(encoding="utf-8"))
    print(f"Wrote {json_path}, {md_path}, and {cell_path}")


if __name__ == "__main__":
    main()
