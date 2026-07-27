#!/usr/bin/env python3
"""Score-corrected ARC representation v4.1.

All representation, ranking, split, and inference code comes from v4. Only the
multi-test-item pass@2/oracle semantics are corrected to the standard ARC rule.
"""
from __future__ import annotations

import sys
import numpy as np

import representation_frontier_v4 as core


def task_outcomes_standard(task: dict, expanded: bool, priors: dict[str, dict], strength: float) -> dict:
    demos = [(np.asarray(p["input"], dtype=int), np.asarray(p["output"], dtype=int)) for p in task["train"]]
    test_pairs = [(np.asarray(p["input"], dtype=int), np.asarray(p["output"], dtype=int)) for p in task.get("test", []) if "output" in p]
    test_inputs = [x for x, _ in test_pairs]
    cands = core.consistent_candidates(demos, expanded)
    ranked = core.rank_and_dedup(cands, test_inputs, priors, strength)

    correctness: list[list[bool]] = []
    for cand in ranked:
        correctness.append([core.exact(core.safe_apply(cand.fn, x), y) for x, y in test_pairs])

    pass1 = bool(test_pairs) and bool(ranked) and all(correctness[0])
    pass2 = bool(test_pairs) and all(
        any(correctness[j][i] for j in range(min(2, len(correctness))))
        for i in range(len(test_pairs))
    )
    oracle = bool(test_pairs) and all(
        any(row[i] for row in correctness)
        for i in range(len(test_pairs))
    )
    oracle_family = None
    if oracle:
        for cand, row in zip(ranked, correctness):
            if any(row):
                oracle_family = cand.family
                break

    return {
        "coverage": bool(ranked),
        "n_consistent": len(cands),
        "n_semantic": len(ranked),
        "pass1": pass1,
        "pass2": pass2,
        "oracle": oracle,
        "attempt1": ranked[0].name if ranked else None,
        "attempt2": ranked[1].name if len(ranked) > 1 else None,
        "oracle_family": oracle_family,
    }


if __name__ == "__main__":
    core.task_outcomes = task_outcomes_standard
    # Keep all frozen defaults but write to a distinct immutable result directory.
    if "--output-dir" not in sys.argv:
        sys.argv.extend(["--output-dir", "results/representation_v4_1"])
    core.main()
