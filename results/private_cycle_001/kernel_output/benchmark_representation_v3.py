#!/usr/bin/env python3
"""Frozen representation-v3 benchmark on a deterministic ARC training holdout.

The 120 public evaluation tasks are deliberately excluded because they were
already observed during v2. The private Kaggle test set remains the fresh contest
endpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import binomtest

import dsl as v2
import dsl_v3 as v3
from evidence_weighted_solver import legacy_solve_one


REGISTERED_SPLIT_MODULUS = 5
REGISTERED_SPLIT_REMAINDER = 0


def is_holdout(task_id: str) -> bool:
    value = int(hashlib.sha1(task_id.encode("utf-8")).hexdigest()[:8], 16)
    return value % REGISTERED_SPLIT_MODULUS == REGISTERED_SPLIT_REMAINDER


def grid_key(grid: np.ndarray) -> bytes:
    array = np.asarray(grid, dtype=np.int16)
    return np.asarray(array.shape, dtype=np.int16).tobytes() + array.tobytes()


def safe_predict(fn: Any, grid: np.ndarray) -> np.ndarray | None:
    try:
        output = fn(grid)
    except Exception:
        return None
    if not isinstance(output, np.ndarray) or output.ndim != 2 or output.size == 0:
        return None
    if output.shape[0] > 30 or output.shape[1] > 30:
        return None
    if np.any(output < 0) or np.any(output > 9):
        return None
    return output.astype(np.int8, copy=False)


def rank_v3(
    train_pairs: list[tuple[np.ndarray, np.ndarray]],
    test_input: np.ndarray,
) -> tuple[list[np.ndarray], dict[str, Any]]:
    passers = [
        (name, fn)
        for name, fn in v3.build_programs(train_pairs)
        if v3.passes_demos(fn, train_pairs)
    ]
    outputs: dict[bytes, dict[str, Any]] = {}
    for name, fn in passers:
        prediction = safe_predict(fn, test_input)
        if prediction is None:
            continue
        key = grid_key(prediction)
        bucket = outputs.setdefault(
            key,
            {
                "grid": prediction,
                "votes": 0,
                "min_complexity": 10_000,
                "names": [],
            },
        )
        bucket["votes"] += 1
        bucket["min_complexity"] = min(bucket["min_complexity"], v3.complexity(name))
        bucket["names"].append(name)

    ranked = sorted(
        outputs.values(),
        key=lambda item: (
            -item["votes"],
            item["min_complexity"],
            grid_key(item["grid"]),
        ),
    )
    fallbacks = [test_input, np.rot90(test_input, 2)]
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
        "passing_programs": len(passers),
        "distinct_candidate_outputs": len(ranked),
        "covered": int(bool(ranked)),
        "top_votes": int(ranked[0]["votes"]) if ranked else 0,
        "top_min_complexity": int(ranked[0]["min_complexity"]) if ranked else None,
        "all_candidate_grids": [item["grid"] for item in ranked],
    }
    return [first, second], metadata


def baseline_metadata(
    train_pairs: list[tuple[np.ndarray, np.ndarray]],
    test_input: np.ndarray,
) -> dict[str, Any]:
    passers = [
        (name, fn)
        for name, fn in v2.build_programs(train_pairs)
        if v2.passes_demos(fn, train_pairs)
    ]
    keys: set[bytes] = set()
    for _, fn in passers:
        prediction = safe_predict(fn, test_input)
        if prediction is not None:
            keys.add(grid_key(prediction))
    return {
        "passing_programs": len(passers),
        "distinct_candidate_outputs": len(keys),
        "covered": int(bool(keys)),
    }


def correct(prediction: list[list[int]] | np.ndarray, truth: np.ndarray) -> int:
    array = np.asarray(prediction, dtype=np.int8)
    return int(array.shape == truth.shape and np.array_equal(array, truth))


def wilson(successes: int, trials: int, z: float = 1.96) -> list[float]:
    if trials == 0:
        return [0.0, 0.0]
    p = successes / trials
    denominator = 1 + z * z / trials
    center = p + z * z / (2 * trials)
    half = z * np.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials))
    return [float((center - half) / denominator), float((center + half) / denominator)]


def paired(method_a: pd.Series, method_b: pd.Series) -> dict[str, Any]:
    a = method_a.astype(int).to_numpy()
    b = method_b.astype(int).to_numpy()
    a_only = int(np.sum((a == 1) & (b == 0)))
    b_only = int(np.sum((a == 0) & (b == 1)))
    discordant = a_only + b_only
    p_value = float(binomtest(a_only, discordant, 0.5).pvalue) if discordant else 1.0
    return {
        "a_only": a_only,
        "b_only": b_only,
        "discordant": discordant,
        "exact_two_sided_p": p_value,
    }


def summarize_binary(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    successes = int(frame[column].sum())
    trials = int(len(frame))
    return {
        "successes": successes,
        "trials": trials,
        "rate": float(successes / trials) if trials else 0.0,
        "wilson_ci95": wilson(successes, trials),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="external/ARC-AGI-2/data/training")
    parser.add_argument("--output-dir", default="results/representation_v3")
    parser.add_argument("--max-tasks", type=int, default=None)
    args = parser.parse_args()

    data_root = Path(args.data_root)
    files = [path for path in sorted(data_root.glob("*.json")) if is_holdout(path.stem)]
    if args.max_tasks is not None:
        files = files[: args.max_tasks]
    if not files:
        raise FileNotFoundError(f"No registered holdout tasks found under {data_root}")

    started = time.time()
    output_rows: list[dict[str, Any]] = []
    task_rows: list[dict[str, Any]] = []

    for task_number, path in enumerate(files, start=1):
        task_id = path.stem
        task = json.loads(path.read_text(encoding="utf-8"))
        train_pairs = [
            (np.asarray(pair["input"], dtype=np.int8), np.asarray(pair["output"], dtype=np.int8))
            for pair in task["train"]
        ]
        task_output_rows: list[dict[str, Any]] = []
        for test_index, test_pair in enumerate(task["test"]):
            test_input = np.asarray(test_pair["input"], dtype=np.int8)
            truth = np.asarray(test_pair["output"], dtype=np.int8)

            baseline_first, baseline_second = legacy_solve_one(train_pairs, test_input)
            base_meta = baseline_metadata(train_pairs, test_input)
            v3_attempts, v3_meta = rank_v3(train_pairs, test_input)

            baseline_pass1 = correct(baseline_first, truth)
            baseline_pass2 = int(
                baseline_pass1 or correct(baseline_second, truth)
            )
            v3_pass1 = correct(v3_attempts[0], truth)
            v3_pass2 = int(v3_pass1 or correct(v3_attempts[1], truth))
            v3_oracle = int(
                any(
                    candidate.shape == truth.shape and np.array_equal(candidate, truth)
                    for candidate in v3_meta["all_candidate_grids"]
                )
            )

            row = {
                "task": task_id,
                "test_index": test_index,
                "baseline_pass1": baseline_pass1,
                "baseline_pass2": baseline_pass2,
                "baseline_covered": base_meta["covered"],
                "baseline_passing_programs": base_meta["passing_programs"],
                "baseline_distinct_outputs": base_meta["distinct_candidate_outputs"],
                "v3_pass1": v3_pass1,
                "v3_pass2": v3_pass2,
                "v3_oracle": v3_oracle,
                "v3_covered": v3_meta["covered"],
                "v3_passing_programs": v3_meta["passing_programs"],
                "v3_distinct_outputs": v3_meta["distinct_candidate_outputs"],
                "v3_top_votes": v3_meta["top_votes"],
                "v3_top_min_complexity": v3_meta["top_min_complexity"],
            }
            output_rows.append(row)
            task_output_rows.append(row)

        task_rows.append(
            {
                "task": task_id,
                "n_test_outputs": len(task_output_rows),
                "baseline_task_pass2": int(all(row["baseline_pass2"] for row in task_output_rows)),
                "v3_task_pass2": int(all(row["v3_pass2"] for row in task_output_rows)),
                "v3_oracle_task": int(all(row["v3_oracle"] for row in task_output_rows)),
            }
        )
        if task_number % 25 == 0 or task_number == len(files):
            print(
                f"processed {task_number}/{len(files)} registered holdout tasks; "
                f"elapsed={time.time()-started:.1f}s",
                flush=True,
            )

    outputs = pd.DataFrame(output_rows)
    tasks = pd.DataFrame(task_rows)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs.to_csv(output_dir / "representation_v3_output_results.csv", index=False)
    tasks.to_csv(output_dir / "representation_v3_task_results.csv", index=False)

    result = {
        "registration": "HYPOTHESIS-representation-v3.md",
        "split": {
            "definition": "int(SHA1(task_id)[0:8],16) mod 5 == 0",
            "modulus": REGISTERED_SPLIT_MODULUS,
            "remainder": REGISTERED_SPLIT_REMAINDER,
            "task_count": int(len(tasks)),
            "output_count": int(len(outputs)),
        },
        "runtime_seconds": float(time.time() - started),
        "output_level": {
            "baseline_coverage": summarize_binary(outputs, "baseline_covered"),
            "v3_coverage": summarize_binary(outputs, "v3_covered"),
            "baseline_pass1": summarize_binary(outputs, "baseline_pass1"),
            "baseline_pass2": summarize_binary(outputs, "baseline_pass2"),
            "v3_pass1": summarize_binary(outputs, "v3_pass1"),
            "v3_pass2": summarize_binary(outputs, "v3_pass2"),
            "v3_candidate_oracle": summarize_binary(outputs, "v3_oracle"),
            "paired_v3_vs_baseline_pass2": paired(outputs["v3_pass2"], outputs["baseline_pass2"]),
        },
        "task_level": {
            "baseline_task_pass2": summarize_binary(tasks, "baseline_task_pass2"),
            "v3_task_pass2": summarize_binary(tasks, "v3_task_pass2"),
            "v3_candidate_oracle_task": summarize_binary(tasks, "v3_oracle_task"),
            "paired_v3_vs_baseline_task_pass2": paired(
                tasks["v3_task_pass2"], tasks["baseline_task_pass2"]
            ),
        },
        "candidate_counts": {
            "baseline_mean_passing_programs": float(outputs["baseline_passing_programs"].mean()),
            "v3_mean_passing_programs": float(outputs["v3_passing_programs"].mean()),
            "baseline_mean_distinct_outputs": float(outputs["baseline_distinct_outputs"].mean()),
            "v3_mean_distinct_outputs": float(outputs["v3_distinct_outputs"].mean()),
        },
    }

    json_path = output_dir / "representation_v3_benchmark.json"
    json_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    def rate(section: dict[str, Any]) -> str:
        return f"{section['successes']}/{section['trials']} ({100*section['rate']:.2f}%)"

    paired_output = result["output_level"]["paired_v3_vs_baseline_pass2"]
    paired_task = result["task_level"]["paired_v3_vs_baseline_task_pass2"]
    direction = (
        "CLEAR PROMOTION"
        if paired_output["a_only"] > paired_output["b_only"]
        and paired_output["exact_two_sided_p"] < 0.05
        else "DIRECTIONAL IMPROVEMENT"
        if paired_output["a_only"] > paired_output["b_only"]
        else "NULL"
        if paired_output["a_only"] == paired_output["b_only"]
        else "FAILURE"
    )

    lines = [
        "# ARC Representation Expansion v3 — Frozen Holdout Result",
        "",
        f"**Registered verdict: {direction}.**",
        "",
        f"Holdout: {len(tasks)} tasks / {len(outputs)} test outputs; deterministic SHA1 split; public evaluation excluded.",
        "",
        "| Endpoint | v2 baseline | v3 expanded grammar | v3 candidate oracle |",
        "|---|---:|---:|---:|",
        f"| Output pass@1 | {rate(result['output_level']['baseline_pass1'])} | {rate(result['output_level']['v3_pass1'])} | — |",
        f"| Output pass@2 | {rate(result['output_level']['baseline_pass2'])} | {rate(result['output_level']['v3_pass2'])} | {rate(result['output_level']['v3_candidate_oracle'])} |",
        f"| Whole-task pass@2 | {rate(result['task_level']['baseline_task_pass2'])} | {rate(result['task_level']['v3_task_pass2'])} | {rate(result['task_level']['v3_candidate_oracle_task'])} |",
        f"| Valid-candidate coverage | {rate(result['output_level']['baseline_coverage'])} | {rate(result['output_level']['v3_coverage'])} | — |",
        "",
        "## Paired output comparison",
        "",
        f"- v3-only wins: **{paired_output['a_only']}**",
        f"- v2-only wins: **{paired_output['b_only']}**",
        f"- exact two-sided p: **{paired_output['exact_two_sided_p']:.6f}**",
        "",
        "## Paired whole-task comparison",
        "",
        f"- v3-only wins: **{paired_task['a_only']}**",
        f"- v2-only wins: **{paired_task['b_only']}**",
        f"- exact two-sided p: **{paired_task['exact_two_sided_p']:.6f}**",
        "",
        "## Interpretation rule",
        "",
        "The v3 grammar is promoted to the private-test submission artifact only if its frozen holdout pass@2 is directionally better than v2. A larger candidate set is not itself progress; paired solved outputs control the verdict.",
    ]
    md_path = output_dir / "representation_v3_benchmark.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    main()
