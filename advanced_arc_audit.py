#!/usr/bin/env python3
"""Task-clustered audit of the same-holdout ARC cross-fold experiment.

This script treats ARC tasks—not candidate programs and not cross-fold cells—as
the sampling units. It estimates calibration, the within-task effect of adding a
demonstration while holding the target fixed, selector accuracy under ambiguity,
MDL tie sensitivity, and replication from the public training split to the harder
public evaluation split.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy import stats


def finite(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def bootstrap_mean(
    values: Iterable[float], *, n_boot: int, seed: int, chunk: int = 5_000
) -> np.ndarray:
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return np.array([], dtype=float)
    rng = np.random.default_rng(seed)
    output = np.empty(n_boot, dtype=float)
    for start in range(0, n_boot, chunk):
        stop = min(start + chunk, n_boot)
        indices = rng.integers(0, array.size, size=(stop - start, array.size))
        output[start:stop] = array[indices].mean(axis=1)
    return output


def bootstrap_independent_difference(
    left: Iterable[float],
    right: Iterable[float],
    *,
    n_boot: int,
    seed: int,
    chunk: int = 5_000,
) -> np.ndarray:
    a = np.asarray(list(left), dtype=float)
    b = np.asarray(list(right), dtype=float)
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if a.size == 0 or b.size == 0:
        return np.array([], dtype=float)
    rng = np.random.default_rng(seed)
    output = np.empty(n_boot, dtype=float)
    for start in range(0, n_boot, chunk):
        stop = min(start + chunk, n_boot)
        draw_a = rng.integers(0, a.size, size=(stop - start, a.size))
        draw_b = rng.integers(0, b.size, size=(stop - start, b.size))
        output[start:stop] = b[draw_b].mean(axis=1) - a[draw_a].mean(axis=1)
    return output


def interval(values: np.ndarray) -> list[float | None]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return [None, None]
    return [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]


def one_sided_failure_upper(failures: int, trials: int, confidence: float = 0.95) -> float | None:
    if trials <= 0:
        return None
    if failures >= trials:
        return 1.0
    return float(stats.beta.ppf(confidence, failures + 1, trials - failures))


def task_level_calibration(
    frame: pd.DataFrame,
    *,
    n_boot: int,
    seed: int,
) -> tuple[list[dict[str, Any]], pd.DataFrame]:
    # Each fit subset / held-out pair is a cell. Equalize cells within task, then
    # equalize tasks. Program weighting is retained only as a secondary estimand.
    task_k = (
        frame.groupby(["task", "k"], as_index=False)
        .agg(
            task_rate=("random_rate", "mean"),
            mean_candidates=("n_consistent", "mean"),
            n_cells=("random_rate", "size"),
            candidate_correct=("candidate_correct", "sum"),
            candidate_trials=("n_consistent", "sum"),
        )
    )
    rows: list[dict[str, Any]] = []
    for k, group in task_k.groupby("k", sort=True):
        rates = group["task_rate"].to_numpy(float)
        boot = bootstrap_mean(rates, n_boot=n_boot, seed=seed + int(k) * 101)
        rho = p_value = None
        if len(group) >= 3 and group["mean_candidates"].nunique() > 1 and np.std(rates) > 0:
            result = stats.spearmanr(group["mean_candidates"], rates)
            rho, p_value = finite(result.statistic), finite(result.pvalue)
        rows.append(
            {
                "k": int(k),
                "n_tasks": int(group["task"].nunique()),
                "n_cells": int(group["n_cells"].sum()),
                "candidate_evaluations": int(group["candidate_trials"].sum()),
                "program_weighted_rate": finite(
                    group["candidate_correct"].sum() / group["candidate_trials"].sum()
                ),
                "cell_weighted_rate": finite(
                    frame.loc[frame["k"] == k, "random_rate"].mean()
                ),
                "task_weighted_rate": finite(rates.mean()),
                "task_cluster_bootstrap_ci95": interval(boot),
                "task_cluster_bootstrap_se": finite(np.std(boot, ddof=1)),
                "median_task_rate": finite(np.median(rates)),
                "candidate_count_spearman_rho": rho,
                "candidate_count_spearman_p": p_value,
                "small_sample_warning": bool(len(group) < 20),
            }
        )
    return rows, task_k


def same_holdout_increments(
    frame: pd.DataFrame,
    *,
    n_boot: int,
    seed: int,
) -> list[dict[str, Any]]:
    target_k = (
        frame.groupby(["task", "heldout_index", "k"], as_index=False)["random_rate"]
        .mean()
        .rename(columns={"random_rate": "rate"})
    )
    wide = target_k.pivot(index=["task", "heldout_index"], columns="k", values="rate")
    ks = sorted(int(k) for k in target_k["k"].unique())
    rows: list[dict[str, Any]] = []
    for left_k, right_k in zip(ks[:-1], ks[1:]):
        paired = wide[[left_k, right_k]].dropna().reset_index()
        paired["delta"] = paired[right_k] - paired[left_k]
        # Multiple held-out targets within one task are dependent. Average those
        # deltas first, then resample tasks.
        task_delta = paired.groupby("task")["delta"].mean()
        boot = bootstrap_mean(
            task_delta.to_numpy(float),
            n_boot=n_boot,
            seed=seed + 10_000 + right_k,
        )
        nonzero = task_delta[task_delta != 0]
        sign_p = None
        if len(nonzero):
            sign_p = float(
                stats.binomtest(int((nonzero > 0).sum()), len(nonzero), 0.5).pvalue
            )
        wilcoxon_p = None
        if len(nonzero) >= 5:
            wilcoxon_p = finite(stats.wilcoxon(nonzero).pvalue)
        rows.append(
            {
                "contrast": f"k={right_k} minus k={left_k}",
                "n_tasks": int(task_delta.size),
                "n_task_heldout_pairs": int(len(paired)),
                "mean_within_task_delta": finite(task_delta.mean()),
                "median_within_task_delta": finite(task_delta.median()),
                "task_cluster_bootstrap_ci95": interval(boot),
                "bootstrap_probability_positive_mean": finite(np.mean(boot > 0)),
                "n_positive_tasks": int((task_delta > 0).sum()),
                "n_negative_tasks": int((task_delta < 0).sum()),
                "n_zero_tasks": int((task_delta == 0).sum()),
                "exact_sign_test_p": sign_p,
                "wilcoxon_signed_rank_p": wilcoxon_p,
            }
        )
    return rows


def selector_audit(
    frame: pd.DataFrame,
    *,
    n_boot: int,
    seed: int,
) -> dict[str, Any]:
    ambiguous = frame[frame["ambiguous"] == 1].copy()
    rule_columns = [
        "random_rate",
        "legacy_shortest_correct",
        "mdl_random_rate",
        "mdl_vote_correct",
        "consensus_correct",
        "any_correct",
    ]
    if ambiguous.empty:
        return {
            "n_ambiguous_cells": 0,
            "n_ambiguous_tasks": 0,
            "rules": {},
        }

    task_rules = ambiguous.groupby("task")[rule_columns].mean()
    rules: dict[str, Any] = {}
    for index, column in enumerate(rule_columns):
        values = task_rules[column].to_numpy(float)
        boot = bootstrap_mean(
            values,
            n_boot=n_boot,
            seed=seed + 20_000 + index,
        )
        rules[column] = {
            "task_weighted_rate": finite(values.mean()),
            "task_cluster_bootstrap_ci95": interval(boot),
        }

    def contrast(left: str, right: str, offset: int) -> dict[str, Any]:
        delta = task_rules[left] - task_rules[right]
        boot = bootstrap_mean(
            delta.to_numpy(float),
            n_boot=n_boot,
            seed=seed + 30_000 + offset,
        )
        return {
            "contrast": f"{left} minus {right}",
            "mean_delta": finite(delta.mean()),
            "task_cluster_bootstrap_ci95": interval(boot),
            "bootstrap_probability_positive_mean": finite(np.mean(boot > 0)),
        }

    oracle = ambiguous[ambiguous["any_correct"] == 1]
    mdl_vote_misses = int((oracle["mdl_vote_correct"] == 0).sum())
    legacy_misses = int((oracle["legacy_shortest_correct"] == 0).sum())
    trials = int(len(oracle))

    ambiguity_per_task = frame.groupby("task")["ambiguous"].mean()
    ambiguity_boot = bootstrap_mean(
        ambiguity_per_task.to_numpy(float),
        n_boot=n_boot,
        seed=seed + 40_000,
    )

    # How often is "shortest" itself ambiguous because equal-complexity programs
    # disagree? This measures sensitivity to an unstated tie rule.
    mdl_tie = ambiguous[ambiguous["n_min_complexity"] > 1]
    conflicting_mdl_tie = ambiguous[
        ambiguous["min_complexity_distinct_predictions"] > 1
    ]

    return {
        "n_ambiguous_cells": int(len(ambiguous)),
        "n_ambiguous_tasks": int(ambiguous["task"].nunique()),
        "task_weighted_ambiguity_prevalence": finite(ambiguity_per_task.mean()),
        "task_cluster_bootstrap_ambiguity_ci95": interval(ambiguity_boot),
        "rules": rules,
        "contrasts": [
            contrast("mdl_vote_correct", "random_rate", 1),
            contrast("mdl_vote_correct", "consensus_correct", 2),
            contrast("any_correct", "mdl_vote_correct", 3),
            contrast("mdl_vote_correct", "legacy_shortest_correct", 4),
        ],
        "equal_minimum_complexity_tie_cells": int(len(mdl_tie)),
        "conflicting_minimum_complexity_prediction_cells": int(len(conflicting_mdl_tie)),
        "oracle_success_opportunities": trials,
        "legacy_mdl_misses_when_oracle_can_succeed": legacy_misses,
        "tie_aware_mdl_misses_when_oracle_can_succeed": mdl_vote_misses,
        "legacy_one_sided_95pct_miss_upper": one_sided_failure_upper(
            legacy_misses, trials
        ),
        "tie_aware_one_sided_95pct_miss_upper": one_sided_failure_upper(
            mdl_vote_misses, trials
        ),
    }


def split_replication(
    train_task_k: pd.DataFrame,
    eval_task_k: pd.DataFrame,
    *,
    n_boot: int,
    seed: int,
) -> list[dict[str, Any]]:
    common_k = sorted(set(train_task_k["k"]) & set(eval_task_k["k"]))
    rows: list[dict[str, Any]] = []
    for k in common_k:
        train = train_task_k.loc[train_task_k["k"] == k, "task_rate"].to_numpy(float)
        evaluation = eval_task_k.loc[eval_task_k["k"] == k, "task_rate"].to_numpy(float)
        boot = bootstrap_independent_difference(
            train,
            evaluation,
            n_boot=n_boot,
            seed=seed + 50_000 + int(k),
        )
        rows.append(
            {
                "k": int(k),
                "n_training_tasks": int(len(train)),
                "n_evaluation_tasks": int(len(evaluation)),
                "training_task_weighted_rate": finite(train.mean()),
                "evaluation_task_weighted_rate": finite(evaluation.mean()),
                "evaluation_minus_training": finite(evaluation.mean() - train.mean()),
                "independent_task_bootstrap_ci95": interval(boot),
                "bootstrap_probability_evaluation_higher": finite(np.mean(boot > 0)),
            }
        )
    return rows


def p(value: float | None) -> str:
    return "NA" if value is None else f"{100 * value:.1f}%"


def pp(value: float | None) -> str:
    return "NA" if value is None else f"{100 * value:+.1f} pp"


def summarize_split(
    name: str,
    frame: pd.DataFrame,
    *,
    total_tasks: int,
    n_boot: int,
    seed: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    calibration, task_k = task_level_calibration(frame, n_boot=n_boot, seed=seed)
    return (
        {
            "split": name,
            "total_tasks_in_split": total_tasks,
            "tasks_engaged": int(frame["task"].nunique()),
            "engagement_rate": finite(frame["task"].nunique() / total_tasks),
            "crossfold_cells": int(len(frame)),
            "calibration_by_k": calibration,
            "same_holdout_demonstration_increments": same_holdout_increments(
                frame, n_boot=n_boot, seed=seed
            ),
            "selector_audit": selector_audit(frame, n_boot=n_boot, seed=seed),
        },
        task_k,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--training", default="results/crossfold/crossfold_training.parquet"
    )
    parser.add_argument(
        "--evaluation", default="results/crossfold/crossfold_evaluation.parquet"
    )
    parser.add_argument("--output-dir", default="results/crossfold")
    parser.add_argument("--bootstrap", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260727)
    args = parser.parse_args()

    train = pd.read_parquet(args.training)
    evaluation = pd.read_parquet(args.evaluation)
    required = {
        "task",
        "k",
        "heldout_index",
        "n_consistent",
        "candidate_correct",
        "random_rate",
        "ambiguous",
        "legacy_shortest_correct",
        "mdl_random_rate",
        "mdl_vote_correct",
        "consensus_correct",
        "any_correct",
        "n_min_complexity",
        "min_complexity_distinct_predictions",
    }
    for name, frame in (("training", train), ("evaluation", evaluation)):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"{name} crossfold data missing columns: {missing}")

    train_summary, train_task_k = summarize_split(
        "training",
        train,
        total_tasks=1000,
        n_boot=args.bootstrap,
        seed=args.seed,
    )
    eval_summary, eval_task_k = summarize_split(
        "evaluation",
        evaluation,
        total_tasks=120,
        n_boot=args.bootstrap,
        seed=args.seed + 1_000_000,
    )

    output = {
        "design": (
            "All demonstration subsets are evaluated against held-out demonstrations. "
            "When k changes, the held-out target is held fixed. Tasks are the sampling units."
        ),
        "bootstrap_replicates": args.bootstrap,
        "bootstrap_seed": args.seed,
        "training": train_summary,
        "evaluation": eval_summary,
        "evaluation_replication": split_replication(
            train_task_k,
            eval_task_k,
            n_boot=args.bootstrap,
            seed=args.seed,
        ),
        "scope": (
            "Calibration is conditional on the current DSL generating at least one "
            "consistent candidate. Evaluation-split ablation uses only public demonstration "
            "pairs and does not access hidden Kaggle labels."
        ),
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "arc_crossfold_audit.json"
    json_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# ARC same-holdout cross-fold audit",
        "",
        "This is the resolved calibration design: every held-out demonstration is kept fixed while the number of fitted demonstrations changes. All subsets are used, and ARC tasks—not programs or folds—are the sampling units.",
        "",
    ]
    for summary in (train_summary, eval_summary):
        lines.extend(
            [
                f"## {summary['split'].title()} split",
                "",
                f"Engaged {summary['tasks_engaged']} of {summary['total_tasks_in_split']} tasks ({p(summary['engagement_rate'])}); {summary['crossfold_cells']} cross-fold cells.",
                "",
                "| k | tasks | cells | candidate evals | program-weighted | cell-weighted | task-weighted | 95% task CI |",
                "|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in summary["calibration_by_k"]:
            lo, hi = row["task_cluster_bootstrap_ci95"]
            lines.append(
                f"| {row['k']} | {row['n_tasks']} | {row['n_cells']} | {row['candidate_evaluations']} | "
                f"{p(row['program_weighted_rate'])} | {p(row['cell_weighted_rate'])} | "
                f"{p(row['task_weighted_rate'])} | [{p(lo)}, {p(hi)}] |"
            )
        lines.extend(["", "### Same-heldout effect of one more demonstration", ""])
        for row in summary["same_holdout_demonstration_increments"]:
            lo, hi = row["task_cluster_bootstrap_ci95"]
            lines.append(
                f"- **{row['contrast']}**, {row['n_tasks']} tasks: mean {pp(row['mean_within_task_delta'])}; "
                f"95% CI [{pp(lo)}, {pp(hi)}]; +/−/0 tasks "
                f"{row['n_positive_tasks']}/{row['n_negative_tasks']}/{row['n_zero_tasks']}."
            )
        selector = summary["selector_audit"]
        lines.extend(
            [
                "",
                "### Selection under genuine prediction disagreement",
                "",
                f"{selector['n_ambiguous_cells']} ambiguous cells across {selector['n_ambiguous_tasks']} tasks; "
                f"task-weighted ambiguity prevalence {p(selector['task_weighted_ambiguity_prevalence'])}.",
                "",
                "| selector | task-weighted accuracy | 95% task CI |",
                "|---|---:|---:|",
            ]
        )
        labels = {
            "random_rate": "Random consistent candidate (expected)",
            "legacy_shortest_correct": "Legacy first-shortest",
            "mdl_random_rate": "Random among minimum-complexity ties",
            "mdl_vote_correct": "Tie-aware MDL vote",
            "consensus_correct": "All-candidate consensus",
            "any_correct": "Oracle candidate ceiling",
        }
        for key, label in labels.items():
            rule = selector["rules"].get(key, {})
            lo, hi = rule.get("task_cluster_bootstrap_ci95", [None, None])
            lines.append(
                f"| {label} | {p(rule.get('task_weighted_rate'))} | [{p(lo)}, {p(hi)}] |"
            )
        lines.extend(
            [
                "",
                f"Minimum-complexity ties occurred in {selector.get('equal_minimum_complexity_tie_cells', 0)} ambiguous cells; "
                f"they produced conflicting predictions in {selector.get('conflicting_minimum_complexity_prediction_cells', 0)} cells.",
                f"Tie-aware MDL missed {selector.get('tie_aware_mdl_misses_when_oracle_can_succeed', 0)} of "
                f"{selector.get('oracle_success_opportunities', 0)} oracle-success opportunities; the one-sided 95% upper "
                f"bound on its miss rate is {p(selector.get('tie_aware_one_sided_95pct_miss_upper'))}.",
                "",
            ]
        )

    lines.extend(["## Training-to-evaluation replication", ""])
    for row in output["evaluation_replication"]:
        lo, hi = row["independent_task_bootstrap_ci95"]
        lines.append(
            f"- **k={row['k']}**: training {p(row['training_task_weighted_rate'])}, evaluation "
            f"{p(row['evaluation_task_weighted_rate'])}, difference {pp(row['evaluation_minus_training'])}; "
            f"95% CI [{pp(lo)}, {pp(hi)}]."
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "1. The same-holdout contrasts identify the effect of additional demonstrations within the represented tasks; the legacy prefix trend did not.",
            "2. Program-weighted percentages describe the DSL's candidate population, not an average ARC task. Task-weighted estimates are primary.",
            "3. Tie-aware MDL is a real algorithmic choice. 'Shortest' is not uniquely defined when equally short programs disagree.",
            "4. Evaluation-split reproduction tests whether the calibration texture survives on harder, larger public tasks without using hidden test outputs.",
            "5. Engagement remains selective. These results characterize tasks the DSL can engage, not the entire benchmark.",
            "",
            f"Bootstrap: {args.bootstrap:,} task replicates; seed {args.seed}.",
        ]
    )
    md_path = output_dir / "arc_crossfold_audit.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))
    print(f"Wrote {json_path} and {md_path}")


if __name__ == "__main__":
    main()
