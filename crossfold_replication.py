#!/usr/bin/env python3
"""One-shot training-to-evaluation replication for ARC cross-fold calibration.

The analysis scripts are frozen before this program reads the public evaluation
split. It compares task-level summaries, never candidate-program rows, and does
not alter the solver or calibration rule from evaluation feedback.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


PRIMARY = [
    "coverage",
    "random_yield",
    "legacy_mdl_yield",
    "mdl_random_yield",
    "mdl_vote_yield",
    "consensus_yield",
    "oracle_yield",
    "candidate_reliability",
    "ambiguity_rate_covered",
]


def finite(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    return arr[np.isfinite(arr)]


def interval(values: np.ndarray) -> list[float] | None:
    arr = finite(values)
    if not arr.size:
        return None
    return [float(np.quantile(arr, 0.025)), float(np.quantile(arr, 0.975))]


def independent_bootstrap_difference(
    training: np.ndarray,
    evaluation: np.ndarray,
    *,
    n_boot: int,
    rng: np.random.Generator,
) -> np.ndarray:
    train = finite(training)
    test = finite(evaluation)
    if not train.size or not test.size:
        return np.array([], dtype=float)
    out = np.empty(n_boot, dtype=float)
    chunk = 2_000
    for start in range(0, n_boot, chunk):
        stop = min(start + chunk, n_boot)
        train_idx = rng.integers(0, train.size, size=(stop - start, train.size))
        test_idx = rng.integers(0, test.size, size=(stop - start, test.size))
        out[start:stop] = test[test_idx].mean(axis=1) - train[train_idx].mean(axis=1)
    return out


def find_contrast(payload: dict[str, Any], name: str) -> dict[str, Any] | None:
    for item in payload.get("same_holdout_adjacent_k_contrasts", []):
        if item.get("contrast") == name:
            return item
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-task-summary", default="results/crossfold/training_audit/crossfold_task_summary.csv")
    parser.add_argument("--evaluation-task-summary", default="results/crossfold/evaluation_audit/crossfold_task_summary.csv")
    parser.add_argument("--training-json", default="results/crossfold/training_audit/crossfold_calibration.json")
    parser.add_argument("--evaluation-json", default="results/crossfold/evaluation_audit/crossfold_calibration.json")
    parser.add_argument("--output-dir", default="results/crossfold")
    parser.add_argument("--bootstrap", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260727)
    args = parser.parse_args()

    training = pd.read_csv(args.training_task_summary)
    evaluation = pd.read_csv(args.evaluation_task_summary)
    train_json = json.loads(Path(args.training_json).read_text(encoding="utf-8"))
    eval_json = json.loads(Path(args.evaluation_json).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    common_k = sorted(set(training["k"].astype(int)) & set(evaluation["k"].astype(int)))
    by_k: list[dict[str, Any]] = []
    for k in common_k:
        train_k = training[training["k"] == k]
        eval_k = evaluation[evaluation["k"] == k]
        row: dict[str, Any] = {
            "k": int(k),
            "n_training_tasks": int(train_k["task"].nunique()),
            "n_evaluation_tasks": int(eval_k["task"].nunique()),
            "metrics": {},
        }
        for metric in PRIMARY:
            train_values = finite(train_k[metric])
            eval_values = finite(eval_k[metric])
            boot = independent_bootstrap_difference(
                train_values,
                eval_values,
                n_boot=args.bootstrap,
                rng=rng,
            )
            row["metrics"][metric] = {
                "training_task_weighted_mean": float(train_values.mean()) if train_values.size else None,
                "evaluation_task_weighted_mean": float(eval_values.mean()) if eval_values.size else None,
                "evaluation_minus_training": (
                    float(eval_values.mean() - train_values.mean())
                    if train_values.size and eval_values.size
                    else None
                ),
                "ci95": interval(boot),
                "bootstrap_probability_evaluation_higher": (
                    float(np.mean(boot > 0)) if boot.size else None
                ),
            }
        by_k.append(row)

    primary_name = "k=2 minus k=1"
    train_contrast = find_contrast(train_json, primary_name)
    eval_contrast = find_contrast(eval_json, primary_name)
    primary_replication: dict[str, Any] = {
        "contrast": primary_name,
        "training": train_contrast,
        "evaluation": eval_contrast,
        "same_direction": {},
    }
    for metric in ["coverage", "random_yield", "mdl_vote_yield", "consensus_yield", "oracle_yield"]:
        train_delta = (
            train_contrast.get("metrics", {}).get(metric, {}).get("task_weighted_delta")
            if train_contrast
            else None
        )
        eval_delta = (
            eval_contrast.get("metrics", {}).get(metric, {}).get("task_weighted_delta")
            if eval_contrast
            else None
        )
        primary_replication["same_direction"][metric] = {
            "training_delta": train_delta,
            "evaluation_delta": eval_delta,
            "same_nonzero_direction": (
                bool(np.sign(train_delta) == np.sign(eval_delta))
                if train_delta is not None and eval_delta is not None and train_delta != 0 and eval_delta != 0
                else None
            ),
        }

    output = {
        "registration": "HYPOTHESIS-crossfold-v2.md",
        "policy": (
            "One-shot confirmatory application to public evaluation demonstration pairs after "
            "analysis code and interpretation thresholds were frozen. No evaluation feedback tuning."
        ),
        "bootstrap_replicates": int(args.bootstrap),
        "bootstrap_seed": int(args.seed),
        "training_tasks": int(training["task"].nunique()),
        "evaluation_tasks": int(evaluation["task"].nunique()),
        "by_k": by_k,
        "primary_same_holdout_replication": primary_replication,
    }

    json_path = output_dir / "crossfold_replication.json"
    json_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# ARC cross-fold calibration: one-shot evaluation replication",
        "",
        "The analysis was frozen before reading public-evaluation results. This compares public training and evaluation demonstration-pair calibration with ARC tasks as the sampling units.",
        "",
        "| k | metric | training | evaluation | evaluation − training | 95% CI |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for row in by_k:
        for metric in ["coverage", "consensus_yield", "mdl_vote_yield", "candidate_reliability"]:
            item = row["metrics"][metric]
            ci = item["ci95"]
            lines.append(
                f"| {row['k']} | {metric} | {100*item['training_task_weighted_mean']:.1f}% | "
                f"{100*item['evaluation_task_weighted_mean']:.1f}% | "
                f"{100*item['evaluation_minus_training']:+.1f} pp | "
                f"[{100*ci[0]:+.1f}, {100*ci[1]:+.1f}] pp |"
            )

    lines += ["", "## Primary same-target effect replication", ""]
    for metric, item in primary_replication["same_direction"].items():
        if item["training_delta"] is None or item["evaluation_delta"] is None:
            continue
        lines.append(
            f"- **{metric}:** training {100*item['training_delta']:+.1f} pp; "
            f"evaluation {100*item['evaluation_delta']:+.1f} pp; "
            f"same direction = {item['same_nonzero_direction']}."
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "Replication concerns the direction and uncertainty of the pre-specified same-target effects. Differences in marginal levels are expected because the public evaluation set is deliberately harder and compositionally different. No method or threshold is changed in response to this file.",
    ]
    md_path = output_dir / "crossfold_replication.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
