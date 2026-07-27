#!/usr/bin/env python3
"""Same-holdout cross-fold calibration for ARC-AGI-2.

The legacy ablation fits the first k demonstrations and tests the next one. As k
changes, the held-out target also changes, so the apparent k trend mixes evidence
quantity, task composition, and target difficulty.

This experiment fixes that identification problem. For every task, held-out
training demonstration h, and k in 1..D-1, it enumerates every size-k subset of
the remaining demonstrations, builds the DSL from that subset, and evaluates the
surviving candidates on the same held-out demonstration h. All uncertainty is
handled downstream with the ARC task as the sampling unit.

The experiment uses demonstration pairs only. It never reads hidden test labels.
"""

from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dsl import build_programs, complexity, passes_demos


def prediction_key(grid: np.ndarray) -> bytes:
    return grid.tobytes() + bytes(grid.shape)


def valid_grid(value: Any) -> bool:
    return isinstance(value, np.ndarray) and value.size > 0


def evaluate_candidate_set(
    candidates: list[tuple[str, Any]],
    held_input: np.ndarray,
    held_output: np.ndarray,
) -> dict[str, Any] | None:
    truth = prediction_key(held_output)
    records: list[dict[str, Any]] = []
    vote: dict[bytes, int] = {}
    grids: dict[bytes, np.ndarray] = {}

    for name, fn in candidates:
        try:
            pred = fn(held_input)
        except Exception:
            pred = None
        if not valid_grid(pred):
            continue
        key = prediction_key(pred)
        correct = int(key == truth)
        cx = int(complexity(name))
        records.append({"name": name, "key": key, "correct": correct, "cx": cx})
        vote[key] = vote.get(key, 0) + 1
        grids[key] = pred

    if not records:
        return None

    n_consistent = len(records)
    distinct = len(vote)
    random_rate = float(np.mean([record["correct"] for record in records]))

    # Legacy selector: first minimum-complexity program in DSL enumeration order.
    legacy_shortest = min(records, key=lambda record: record["cx"])

    # Tie-aware MDL selectors. A complexity tie can contain conflicting outputs,
    # so "the shortest program" is not fully defined without a tie rule.
    min_cx = min(record["cx"] for record in records)
    min_records = [record for record in records if record["cx"] == min_cx]
    mdl_random_rate = float(np.mean([record["correct"] for record in min_records]))
    mdl_vote: dict[bytes, int] = {}
    for record in min_records:
        mdl_vote[record["key"]] = mdl_vote.get(record["key"], 0) + 1
    mdl_modal_count = max(mdl_vote.values())
    mdl_modal_keys = sorted(key for key, count in mdl_vote.items() if count == mdl_modal_count)
    mdl_modal_key = mdl_modal_keys[0]

    # Consensus across all candidates. Ties are broken by the minimum complexity
    # supporting a prediction, then deterministically by key.
    prediction_min_cx = {
        key: min(record["cx"] for record in records if record["key"] == key)
        for key in vote
    }
    ranked_keys = sorted(vote, key=lambda key: (-vote[key], prediction_min_cx[key], key))
    modal_key = ranked_keys[0]

    return {
        "n_consistent": n_consistent,
        "candidate_correct": float(random_rate * n_consistent),
        "distinct": distinct,
        "ambiguous": int(distinct > 1),
        "modal_frac": float(vote[modal_key] / n_consistent),
        "modal_correct": int(modal_key == truth),
        "random_rate": random_rate,
        "legacy_shortest_correct": int(legacy_shortest["correct"]),
        "min_complexity": min_cx,
        "n_min_complexity": len(min_records),
        "min_complexity_distinct_predictions": len(mdl_vote),
        "mdl_random_rate": mdl_random_rate,
        "mdl_vote_correct": int(mdl_modal_key == truth),
        "consensus_correct": int(modal_key == truth),
        "any_correct": int(any(record["correct"] for record in records)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("split", choices=["training", "evaluation"])
    parser.add_argument(
        "--data-root",
        default=os.environ.get("ARC_DATA_ROOT", "/home/claude/ARC-AGI-2/data"),
        help="Directory containing training/ and evaluation/ task folders.",
    )
    parser.add_argument("--output-dir", default="results/crossfold")
    parser.add_argument("--max-tasks", type=int, default=None)
    args = parser.parse_args()

    task_dir = Path(args.data_root) / args.split
    files = sorted(glob.glob(str(task_dir / "*.json")))
    if args.max_tasks is not None:
        files = files[: args.max_tasks]
    if not files:
        raise FileNotFoundError(f"No ARC task JSON files found under {task_dir}")

    rows: list[dict[str, Any]] = []
    for task_index, filename in enumerate(files, start=1):
        task_id = Path(filename).stem
        task = json.loads(Path(filename).read_text(encoding="utf-8"))
        demos = [
            (np.asarray(pair["input"]), np.asarray(pair["output"]))
            for pair in task["train"]
        ]
        n_demos = len(demos)

        # Cache each fitted subset because it is evaluated against every held-out
        # demonstration not contained in that subset.
        for k in range(1, n_demos):
            for fit_indices in itertools.combinations(range(n_demos), k):
                fit_pairs = [demos[index] for index in fit_indices]
                candidates = [
                    (name, fn)
                    for name, fn in build_programs(fit_pairs)
                    if passes_demos(fn, fit_pairs)
                ]
                if not candidates:
                    continue
                fit_set = set(fit_indices)
                for heldout_index in range(n_demos):
                    if heldout_index in fit_set:
                        continue
                    held_input, held_output = demos[heldout_index]
                    result = evaluate_candidate_set(candidates, held_input, held_output)
                    if result is None:
                        continue
                    rows.append(
                        {
                            "split": args.split,
                            "task": task_id,
                            "n_demos": n_demos,
                            "k": k,
                            "fit_indices": ",".join(map(str, fit_indices)),
                            "heldout_index": heldout_index,
                            **result,
                        }
                    )

        if task_index % 100 == 0 or task_index == len(files):
            print(
                f"[{args.split}] processed {task_index}/{len(files)} tasks; "
                f"retained {len(rows)} cross-fold cells",
                flush=True,
            )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    parquet_path = output_dir / f"crossfold_{args.split}.parquet"
    csv_path = output_dir / f"crossfold_{args.split}.csv.gz"
    summary_path = output_dir / f"crossfold_{args.split}_run.json"
    frame.to_parquet(parquet_path, index=False)
    frame.to_csv(csv_path, index=False, compression="gzip")

    summary = {
        "split": args.split,
        "task_files_seen": len(files),
        "tasks_engaged": int(frame["task"].nunique()) if len(frame) else 0,
        "crossfold_cells": int(len(frame)),
        "k_values": sorted(int(k) for k in frame["k"].unique()) if len(frame) else [],
        "parquet": str(parquet_path),
        "csv_gz": str(csv_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
