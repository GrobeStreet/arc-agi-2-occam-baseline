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
    array = np.asarray(list(values), dtype=float)
    return array[np.isfinite(array)]


def interval(values: np.ndarray) -> list[float] | None:
    array = finite(values)
    if not array.size:
        return None
    return [float(np.quantile(array, 0.025)), float(np.quantile(array, 0.975))]


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
    output = np.empty(n_boot, dtype=float)
    chunk = 1_000
    for start in range(0, n_boot, chunk):
        stop = min(start + chunk, n_boot)
        train_counts = rng.multinomial(
            train.size,
            np.full(train.size, 1.0 / train.size),
            size=stop - start,
        )
        test_counts = rng.multinomial(
            test.size,
            np.full(test.size, 1.0 / test.size),
            size=stop - start,
        )
        output[start:stop] = (
            test_counts @ test / test.size
            - train_counts @ train / train.size
        )
    return output


def find_contrast(payload: dict[str, Any], name: str) -> dict[str, Any] | None:
    for item in payload.get("same_holdout_adjacent_k_contrasts", []):
        if item.get("contrast") == name:
            return item
    return None


def pct(value: float | None) -> str:
    return "NA" if value is None or not np.isfinite(value) else f"{100*value:.1f}%"


def pp(value: float | None) -> str:
    return "NA" if value is None or not np.isfinite(value) else f"{100*value:+.1f} pp"


def ci_pp(value: list[float] | None) -> str:
    if not value or len(value) != 2:
        return "NA"
    return f"[{100*value[0]:+.1f}, {100*value[1]:+.1f}] pp"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-task-summary", default="results/crossfold/training_audit/crossfold_task_summary.csv")
    parser.add_argument("--evaluation-task-summary", default="results/crossfold/evaluation_audit/crossfold_task_summary.csv")
    parser.add_argument("--training-json", default="results/crossfold/training_audit/crossfold_calibration.json")
    parser.add_argument("--evaluation-json", default="results/crossfold/evaluation_audit/crossfold_calibration.json")
    parser.add_argument("--output-dir", default="results/crossfold")
    parser.add_argument("--bootstrap", type=int, default=20_000)
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
        training_k = training[training["k"] == k]
        evaluation_k = evaluation[evaluation["k"] == k]
        row: dict[str, Any] = {
            "k": int(k),
            "n_training_tasks": int(training_k["task"].nunique()),
            "n_evaluation_tasks": int(evaluation_k["task"].nunique()),
            "metrics": {},
        }
        for metric in PRIMARY:
            training_values = finite(training_k[metric])
            evaluation_values = finite(evaluation_k[metric])
            bootstrap = independent_bootstrap_difference(
                training_values,
                evaluation_values,
                n_boot=args.bootstrap,
                rng=rng,
            )
            row["metrics"][metric] = {
                "training_task_weighted_mean": float(training_values.mean()) if training_values.size else None,
                "evaluation_task_weighted_mean": float(evaluation_values.mean()) if evaluation_values.size else None,
                "evaluation_minus_training": (
                    float(evaluation_values.mean() - training_values.mean())
                    if training_values.size and evaluation_values.size
                    else None
                ),
                "ci95": interval(bootstrap),
                "bootstrap_probability_evaluation_higher": (
                    float(np.mean(bootstrap > 0)) if bootstrap.size else None
                ),
            }
        by_k.append(row)

    primary_name = "k=2 minus k=1"
    training_contrast = find_contrast(train_json, primary_name)
    evaluation_contrast = find_contrast(eval_json, primary_name)
    primary_replication: dict[str, Any] = {
        "contrast": primary_name,
        "training": training_contrast,
        "evaluation": evaluation_contrast,
        "same_direction": {},
    }
    for metric in ["coverage", "random_yield", "mdl_vote_yield", "consensus_yield", "oracle_yield"]:
        training_delta = (
            training_contrast.get("metrics", {}).get(metric, {}).get("task_weighted_delta")
            if training_contrast
            else None
        )
        evaluation_delta = (
            evaluation_contrast.get("metrics", {}).get(metric, {}).get("task_weighted_delta")
            if evaluation_contrast
            else None
        )
        primary_replication["same_direction"][metric] = {
            "training_delta": training_delta,
            "evaluation_delta": evaluation_delta,
            "same_nonzero_direction": (
                bool(np.sign(training_delta) == np.sign(evaluation_delta))
                if training_delta is not None
                and evaluation_delta is not None
                and training_delta != 0
                and evaluation_delta != 0
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
            lines.append(
                f"| {row['k']} | {metric} | {pct(item['training_task_weighted_mean'])} | "
                f"{pct(item['evaluation_task_weighted_mean'])} | "
                f"{pp(item['evaluation_minus_training'])} | "
                f"{ci_pp(item['ci95'])} |"
            )

    lines += ["", "## Primary same-target effect replication", ""]
    for metric, item in primary_replication["same_direction"].items():
        if item["training_delta"] is None or item["evaluation_delta"] is None:
            continue
        lines.append(
            f"- **{metric}:** training {pp(item['training_delta'])}; "
            f"evaluation {pp(item['evaluation_delta'])}; "
            f"same direction = {item['same_nonzero_direction']}."
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "Replication concerns the direction and uncertainty of the pre-specified same-target effects. Differences in marginal levels are expected because the public evaluation set is deliberately harder and compositionally different. Sparse high-k cells are reported as NA rather than causing a formatting failure. No method or threshold is changed in response to this file.",
    ]
    md_path = output_dir / "crossfold_replication.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
