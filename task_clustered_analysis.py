#!/usr/bin/env python3
"""Task-weighted ARC demonstration-consistency calibration.

The original analysis pooled candidate programs. That estimand weights a task in
proportion to the number of demonstration-consistent programs the DSL happens to
generate for it. This analysis instead gives each represented ARC task equal
weight and obtains uncertainty by resampling complete task clusters.

Important: the legacy prefix experiment tests a different held-out demonstration
at each k (k=1 tests d1, k=2 tests d2, ...). Adjacent-k comparisons are therefore
reported as *prefix diagnostics*, not causal effects of adding demonstrations.
The cross-fold experiment in ``crossfold_ablation.py`` is the proper same-holdout
test of demonstration count.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def bootstrap_mean(values: np.ndarray, *, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """Nonparametric bootstrap of an equally weighted task-level mean."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return np.array([], dtype=float)
    if values.size == 1:
        return np.repeat(values[0], n_boot)
    out = np.empty(n_boot, dtype=float)
    chunk = 5_000
    for start in range(0, n_boot, chunk):
        stop = min(start + chunk, n_boot)
        idx = rng.integers(0, values.size, size=(stop - start, values.size))
        out[start:stop] = values[idx].mean(axis=1)
    return out


def summarize_boot(values: np.ndarray) -> tuple[float, list[float]]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), [float("nan"), float("nan")]
    return float(values.std(ddof=1)) if values.size > 1 else 0.0, [
        float(np.quantile(values, 0.025)),
        float(np.quantile(values, 0.975)),
    ]


def pct(x: float) -> str:
    return "NA" if not np.isfinite(x) else f"{100*x:.1f}%"


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
    rng = np.random.default_rng(args.seed)

    df = pd.read_parquet(input_path)
    required = {"task", "k", "n_consistent", "random_rate"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    cell = (
        df.assign(candidate_correct=lambda x: x["random_rate"] * x["n_consistent"])
        .groupby(["task", "k"], as_index=False)
        .agg(
            n_consistent=("n_consistent", "sum"),
            candidate_correct=("candidate_correct", "sum"),
        )
    )
    cell["task_rate"] = cell["candidate_correct"] / cell["n_consistent"]

    rows: list[dict[str, Any]] = []
    for k, s in cell.groupby("k", sort=True):
        task_values = s.groupby("task")["task_rate"].mean().to_numpy(float)
        boot = bootstrap_mean(task_values, n_boot=args.bootstrap, rng=rng)
        se, ci = summarize_boot(boot)
        program_weighted = float(s["candidate_correct"].sum() / s["n_consistent"].sum())
        task_weighted = float(task_values.mean())
        rows.append(
            {
                "k": int(k),
                "n_tasks": int(task_values.size),
                "n_programs": int(s["n_consistent"].sum()),
                "program_weighted_rate": program_weighted,
                "task_weighted_rate": task_weighted,
                "task_minus_program_weighted": task_weighted - program_weighted,
                "task_cluster_bootstrap_se": se,
                "task_cluster_bootstrap_ci95": ci,
            }
        )

    # Legacy prefix diagnostic: same task, but not the same held-out example.
    # Crossfold analysis is required for an identified demonstration-count effect.
    wide = cell.pivot(index="task", columns="k", values="task_rate")
    prefix_contrasts: list[dict[str, Any]] = []
    ks = sorted(int(k) for k in cell["k"].unique())
    for k1, k2 in zip(ks[:-1], ks[1:]):
        pair = wide[[k1, k2]].dropna()
        diffs = (pair[k2] - pair[k1]).to_numpy(float)
        boot = bootstrap_mean(diffs, n_boot=args.bootstrap, rng=rng)
        se, ci = summarize_boot(boot)
        prefix_contrasts.append(
            {
                "contrast": f"k={k2} minus k={k1}",
                "n_common_tasks": int(diffs.size),
                "observed_delta": float(diffs.mean()) if diffs.size else float("nan"),
                "bootstrap_se": se,
                "bootstrap_ci95": ci,
                "bootstrap_probability_positive": float(np.mean(boot > 0)) if boot.size else float("nan"),
                "warning": "Different held-out demonstration at each k; not a same-target causal contrast.",
            }
        )

    output = {
        "estimand": (
            "For each k, average the within-task fraction of demonstration-consistent "
            "programs that generalize, giving every represented task equal weight."
        ),
        "uncertainty": "Percentile bootstrap resampling equally weighted task-level rates.",
        "input": str(input_path),
        "n_unique_tasks_any_k": int(cell["task"].nunique()),
        "bootstrap_replicates": args.bootstrap,
        "bootstrap_seed": args.seed,
        "results_by_k": rows,
        "legacy_prefix_contrasts": prefix_contrasts,
        "identification_note": (
            "The original prefix experiment changes both k and the held-out target. "
            "Use crossfold_ablation.py for same-holdout comparisons."
        ),
    }

    json_path = results_dir / "task_weighted_calibration.json"
    json_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    cell_path = results_dir / "task_weighted_task_cells.csv"
    cell.sort_values(["k", "task"]).to_csv(cell_path, index=False)

    lines = [
        "# Task-weighted ARC calibration with task-cluster uncertainty",
        "",
        "The original calibration pooled candidate programs, so tasks that generated more candidates received more weight. This reanalysis computes a rate within each `(task, k)` cell and averages those rates equally across represented tasks.",
        "",
        "| k | tasks | programs | program-weighted | task-weighted | 95% task-bootstrap CI | task minus program |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lo, hi = row["task_cluster_bootstrap_ci95"]
        lines.append(
            f"| {row['k']} | {row['n_tasks']} | {row['n_programs']} | {pct(row['program_weighted_rate'])} | "
            f"{pct(row['task_weighted_rate'])} | [{pct(lo)}, {pct(hi)}] | "
            f"{100*row['task_minus_program_weighted']:+.1f} pp |"
        )

    lines += [
        "",
        "## Legacy prefix contrasts",
        "",
        "These compare common tasks but still change the held-out demonstration as k changes. They diagnose the original design; they do **not** identify the effect of adding demonstrations.",
        "",
    ]
    for c in prefix_contrasts:
        lo, hi = c["bootstrap_ci95"]
        lines.append(
            f"- **{c['contrast']}** on {c['n_common_tasks']} common tasks: "
            f"{100*c['observed_delta']:+.1f} pp, 95% CI [{100*lo:+.1f}, {100*hi:+.1f}] pp."
        )
    lines += [
        "",
        "## Resolution",
        "",
        "The task-weighted marginal rates remain lower than the program-weighted rates. More importantly, the apparent marginal rise with k is confounded by changing task composition and changing held-out targets. The cross-fold experiment is now the primary analysis because it holds the target demonstration fixed while varying how many of the remaining demonstrations are fitted.",
        "",
        f"Bootstrap: {args.bootstrap:,} task replicates, seed {args.seed}.",
    ]
    md_path = results_dir / "task_weighted_calibration.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))
    print(f"Wrote {json_path}, {md_path}, and {cell_path}")


if __name__ == "__main__":
    main()
