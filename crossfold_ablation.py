#!/usr/bin/env python3
"""Same-holdout cross-fold calibration for ARC-AGI-2.

The legacy ablation fits the first k demonstrations and tests the next one. As k
changes, the held-out target also changes, so the apparent k trend mixes evidence
quantity, task composition, and target difficulty.

This experiment fixes that identification problem. For every task, held-out
training demonstration h, and k in 1..D-1, it enumerates every size-k subset of
the remaining demonstrations, builds the DSL from that subset, and evaluates the
surviving candidates on the same held-out demonstration h.

Every possible subset/holdout cell is written, including cells where the DSL finds
no demonstration-consistent candidate. This permits separate estimation of
candidate reliability, solver coverage, and end-to-end yield.

The experiment uses demonstration pairs only. It never reads hidden test labels.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import itertools
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dsl import build_programs, complexity, passes_demos


def prediction_key(grid: np.ndarray) -> bytes:
    """Canonical key including shape and integer cell values."""
    arr = np.asarray(grid, dtype=np.int16)
    return np.asarray(arr.shape, dtype=np.int16).tobytes() + arr.tobytes()


def prediction_hash(key: bytes) -> str:
    return hashlib.sha1(key).hexdigest()[:16]


def valid_grid(value: Any) -> bool:
    return isinstance(value, np.ndarray) and value.size > 0


def empty_result() -> dict[str, Any]:
    return {
        "covered": 0,
        "n_consistent": 0,
        "candidate_correct": 0.0,
        "distinct": 0,
        "ambiguous": 0,
        "modal_frac": np.nan,
        "modal_correct": 0,
        "random_rate": np.nan,
        "legacy_shortest_correct": 0,
        "legacy_prediction": "",
        "min_complexity": np.nan,
        "n_min_complexity": 0,
        "min_complexity_distinct_predictions": 0,
        "mdl_random_rate": np.nan,
        "mdl_vote_correct": 0,
        "mdl_prediction": "",
        "consensus_correct": 0,
        "consensus_prediction": "",
        "any_correct": 0,
    }


def evaluate_candidate_set(
    candidates: list[tuple[str, Any]],
    held_input: np.ndarray,
    held_output: np.ndarray,
) -> dict[str, Any]:
    truth = prediction_key(held_output)
    records: list[dict[str, Any]] = []
    vote: dict[bytes, int] = {}

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

    if not records:
        return empty_result()

    n_consistent = len(records)
    distinct = len(vote)
    random_rate = float(np.mean([record["correct"] for record in records]))

    # Legacy selector: first minimum-complexity program in DSL enumeration order.
    legacy_shortest = min(records, key=lambda record: record["cx"])

    # Tie-aware MDL. Complexity ties may predict different grids, so the phrase
    # "the shortest program" is incomplete without a tie rule. We report both
    # random choice among minimum-complexity programs and a vote within that tier.
    min_cx = min(record["cx"] for record in records)
    min_records = [record for record in records if record["cx"] == min_cx]
    mdl_random_rate = float(np.mean([record["correct"] for record in min_records]))
    mdl_vote: dict[bytes, int] = {}
    for record in min_records:
        mdl_vote[record["key"]] = mdl_vote.get(record["key"], 0) + 1
    mdl_modal_count = max(mdl_vote.values())
    mdl_modal_keys = sorted(key for key, count in mdl_vote.items() if count == mdl_modal_count)
    mdl_modal_key = mdl_modal_keys[0]

    # Consensus across all candidates. Ties are broken by minimum supporting
    # complexity and then by prediction bytes for deterministic reproduction.
    prediction_min_cx = {
        key: min(record["cx"] for record in records if record["key"] == key)
        for key in vote
    }
    ranked_keys = sorted(vote, key=lambda key: (-vote[key], prediction_min_cx[key], key))
    modal_key = ranked_keys[0]

    return {
        "covered": 1,
        "n_consistent": n_consistent,
        "candidate_correct": float(random_rate * n_consistent),
        "distinct": distinct,
        "ambiguous": int(distinct > 1),
        "modal_frac": float(vote[modal_key] / n_consistent),
        "modal_correct": int(modal_key == truth),
        "random_rate": random_rate,
        "legacy_shortest_correct": int(legacy_shortest["correct"]),
        "legacy_prediction": prediction_hash(legacy_shortest["key"]),
        "min_complexity": min_cx,
        "n_min_complexity": len(min_records),
        "min_complexity_distinct_predictions": len(mdl_vote),
        "mdl_random_rate": mdl_random_rate,
        "mdl_vote_correct": int(mdl_modal_key == truth),
        "mdl_prediction": prediction_hash(mdl_modal_key),
        "consensus_correct": int(modal_key == truth),
        "consensus_prediction": prediction_hash(modal_key),
        "any_correct": int(any(record["correct"] for record in records)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("split", choices=["training", "evaluation"])
    parser.add_argument(
        "--data-root",
        default=os.environ.get("ARC_DATA_ROOT", "external/ARC-AGI-2/data"),
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
    possible_cells = 0
    for task_index, filename in enumerate(files, start=1):
        task_id = Path(filename).stem
        task = json.loads(Path(filename).read_text(encoding="utf-8"))
        demos = [
            (np.asarray(pair["input"], dtype=np.int8), np.asarray(pair["output"], dtype=np.int8))
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
                fit_set = set(fit_indices)
                for heldout_index in range(n_demos):
                    if heldout_index in fit_set:
                        continue
                    possible_cells += 1
                    held_input, held_output = demos[heldout_index]
                    result = evaluate_candidate_set(candidates, held_input, held_output)
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
                f"wrote {len(rows):,}/{possible_cells:,} possible cross-fold cells",
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
        "tasks_written": int(frame["task"].nunique()) if len(frame) else 0,
        "possible_crossfold_cells": int(possible_cells),
        "written_crossfold_cells": int(len(frame)),
        "covered_cells": int(frame["covered"].sum()) if len(frame) else 0,
        "coverage": float(frame["covered"].mean()) if len(frame) else 0.0,
        "k_values": sorted(int(k) for k in frame["k"].unique()) if len(frame) else [],
        "parquet": str(parquet_path),
        "csv_gz": str(csv_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
