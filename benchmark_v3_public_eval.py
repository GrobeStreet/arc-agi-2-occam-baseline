#!/usr/bin/env python3
"""Run the registered one-shot public-evaluation benchmark for representation v3.

The solver receives demonstration pairs and test inputs only. All predictions are
built and validated before public labels are read for scoring.
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

from kaggle_submission_v3 import build_submission, validate_submission


def exact_grid_equal(a: Any, b: Any) -> bool:
    try:
        return np.array_equal(np.asarray(a, dtype=np.int16), np.asarray(b, dtype=np.int16))
    except Exception:
        return False


def exact_paired_p(a_only: int, b_only: int) -> float:
    discordant = a_only + b_only
    if discordant == 0:
        return 1.0
    return float(stats.binomtest(a_only, discordant, 0.5).pvalue)


def summarize_binary(values: pd.Series) -> dict[str, Any]:
    successes = int(values.sum())
    trials = int(len(values))
    rate = successes / trials if trials else 0.0
    if trials:
        interval = stats.binomtest(successes, trials).proportion_ci(
            confidence_level=0.95, method="exact"
        )
        ci = [float(interval.low), float(interval.high)]
    else:
        ci = [None, None]
    return {"successes": successes, "trials": trials, "rate": rate, "exact_ci95": ci}


def verdict(v3_pass2: int, malformed: bool = False) -> str:
    if malformed:
        return "FAILURE"
    if v3_pass2 == 0:
        return "NULL"
    p_value = exact_paired_p(v3_pass2, 0)
    if v3_pass2 >= 6 and p_value < 0.05:
        return "CLEAR PROMOTION"
    return "DIRECTIONAL IMPROVEMENT"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root", default="external/ARC-AGI-2/data/evaluation"
    )
    parser.add_argument("--output-dir", default="results/representation_v3_public")
    parser.add_argument(
        "--baseline-json", default="results/solver/solver_v2_benchmark.json"
    )
    args = parser.parse_args()

    started = time.time()
    data_root = Path(args.data_root)
    files = sorted(data_root.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No public evaluation tasks found under {data_root}")

    # Build separate challenge and truth objects. The solver is invoked before
    # the truth object is used for any scoring.
    challenges: dict[str, Any] = {}
    truth: dict[str, list[Any]] = {}
    for path in files:
        task = json.loads(path.read_text(encoding="utf-8"))
        task_id = path.stem
        challenges[task_id] = {
            "train": task["train"],
            "test": [{"input": pair["input"]} for pair in task["test"]],
        }
        truth[task_id] = [pair["output"] for pair in task["test"]]

    # Freeze every prediction before inspecting correctness.
    submission, metadata = build_submission(challenges)
    validate_submission(challenges, submission)

    output_rows: list[dict[str, Any]] = []
    task_rows: list[dict[str, Any]] = []
    for task_id in sorted(challenges):
        task_output_rows: list[dict[str, Any]] = []
        for test_index, predicted in enumerate(submission[task_id]):
            expected = truth[task_id][test_index]
            pass1 = int(exact_grid_equal(predicted["attempt_1"], expected))
            pass2 = int(pass1 or exact_grid_equal(predicted["attempt_2"], expected))
            info = metadata[task_id][test_index]
            row = {
                "task": task_id,
                "test_index": test_index,
                "pass1": pass1,
                "pass2": pass2,
                "covered": int(info.get("passing_programs", 0) > 0),
                "passing_programs": int(info.get("passing_programs", 0)),
                "distinct_candidate_outputs": int(
                    info.get("distinct_candidate_outputs", 0)
                ),
                "top_votes": int(info.get("top_votes", 0)),
                "top_min_complexity": info.get("top_min_complexity"),
            }
            output_rows.append(row)
            task_output_rows.append(row)
        task_rows.append(
            {
                "task": task_id,
                "n_test_outputs": len(task_output_rows),
                "task_pass1": int(all(row["pass1"] for row in task_output_rows)),
                "task_pass2": int(all(row["pass2"] for row in task_output_rows)),
                "task_covered": int(any(row["covered"] for row in task_output_rows)),
            }
        )

    outputs = pd.DataFrame(output_rows)
    tasks = pd.DataFrame(task_rows)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs.to_csv(output_dir / "representation_v3_public_output_results.csv", index=False)
    tasks.to_csv(output_dir / "representation_v3_public_task_results.csv", index=False)
    (output_dir / "submission_v3_public_evaluation.json").write_text(
        json.dumps(submission), encoding="utf-8"
    )
    (output_dir / "submission_v3_public_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    baseline_pass2 = 0
    baseline_trials = int(len(outputs))
    baseline_path = Path(args.baseline_json)
    baseline_source = "registered v2 baseline: 0/167"
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        method = baseline.get("methods", {}).get("baseline_vote_then_mdl", {})
        baseline_pass2 = int(method.get("pass2", {}).get("correct", 0))
        baseline_trials = int(method.get("pass2", {}).get("trials", len(outputs)))
        baseline_source = str(baseline_path)
    if baseline_trials != len(outputs):
        raise ValueError(
            f"Baseline trials {baseline_trials} do not match v3 trials {len(outputs)}"
        )

    v3_pass2 = int(outputs["pass2"].sum())
    a_only = v3_pass2 - min(v3_pass2, baseline_pass2)
    b_only = baseline_pass2 - min(v3_pass2, baseline_pass2)
    paired_p = exact_paired_p(a_only, b_only)
    final_verdict = verdict(v3_pass2)

    result: dict[str, Any] = {
        "registration": "HYPOTHESIS-v3-public-eval.md",
        "solver": "representation-v3.0-frozen",
        "data_root": str(data_root),
        "task_count": int(len(tasks)),
        "output_count": int(len(outputs)),
        "runtime_seconds": float(time.time() - started),
        "output_level": {
            "coverage": summarize_binary(outputs["covered"]),
            "pass1": summarize_binary(outputs["pass1"]),
            "pass2": summarize_binary(outputs["pass2"]),
        },
        "task_level": {
            "any_output_covered": summarize_binary(tasks["task_covered"]),
            "whole_task_pass1": summarize_binary(tasks["task_pass1"]),
            "whole_task_pass2": summarize_binary(tasks["task_pass2"]),
        },
        "paired_vs_v2_baseline": {
            "baseline_source": baseline_source,
            "baseline_pass2_successes": baseline_pass2,
            "v3_pass2_successes": v3_pass2,
            "v3_only_wins": a_only,
            "v2_only_wins": b_only,
            "exact_two_sided_p": paired_p,
        },
        "registered_verdict": final_verdict,
        "submission": "submission_v3_public_evaluation.json",
        "claim_boundary": (
            "One-shot public-evaluation result; not a private Kaggle or verified score."
        ),
    }
    json_path = output_dir / "representation_v3_public_benchmark.json"
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    def rate(section: dict[str, Any]) -> str:
        return f"{section['successes']}/{section['trials']} ({100*section['rate']:.2f}%)"

    lines = [
        "# Frozen Representation v3 — One-Shot Public Evaluation",
        "",
        f"**Registered verdict: {final_verdict}.**",
        "",
        f"Public evaluation: {len(tasks)} tasks / {len(outputs)} test outputs. Predictions were generated and validated before labels were scored.",
        "",
        "| Endpoint | Frozen v3 result |",
        "|---|---:|",
        f"| Output coverage | {rate(result['output_level']['coverage'])} |",
        f"| Output pass@1 | {rate(result['output_level']['pass1'])} |",
        f"| Output pass@2 | {rate(result['output_level']['pass2'])} |",
        f"| Whole-task pass@1 | {rate(result['task_level']['whole_task_pass1'])} |",
        f"| Whole-task pass@2 | {rate(result['task_level']['whole_task_pass2'])} |",
        "",
        "## Paired comparison against the recorded v2 baseline",
        "",
        f"- v3-only pass@2 wins: **{a_only}**",
        f"- v2-only pass@2 wins: **{b_only}**",
        f"- exact two-sided p: **{paired_p:.6f}**",
        "",
        "## Interpretation",
        "",
        "The result is governed by `HYPOTHESIS-v3-public-eval.md`. It is a one-shot public holdout result, not a private competition score. No further public-evaluation tuning may be presented as confirmatory evidence.",
    ]
    md_path = output_dir / "representation_v3_public_benchmark.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    main()
