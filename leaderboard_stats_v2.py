#!/usr/bin/env python3
"""ARC-AGI-2 leaderboard measurement audit v2.

The legacy paper treated an ARC-AGI-2 score as 120 independent Bernoulli trials
because the public evaluation set contains 120 tasks. Competition scoring is
actually computed over test outputs, and the public evaluation corpus contains
more test outputs than tasks. Test outputs are also nested within tasks.

This script counts both units directly from a pinned ARC-AGI-2 checkout and
reports what can and cannot be inferred from an aggregate percentage.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats


def wilson(successes: int, trials: int, z: float = 1.959963984540054) -> list[float]:
    p = successes / trials
    denominator = 1 + z * z / trials
    center = p + z * z / (2 * trials)
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials))
    return [(center - half) / denominator, (center + half) / denominator]


def nearest_count(score: float, trials: int) -> int:
    return int(round(score * trials))


def unpaired_two_proportion(a: int, b: int, trials: int) -> dict[str, float]:
    p1 = a / trials
    p2 = b / trials
    pooled = (a + b) / (2 * trials)
    se = math.sqrt(2 * pooled * (1 - pooled) / trials) if 0 < pooled < 1 else 0.0
    z = (p1 - p2) / se if se else 0.0
    return {"z": float(z), "two_sided_p": float(2 * stats.norm.sf(abs(z)))}


def sample_size_for_gap(p1: float, p2: float, alpha: float = 0.05, power: float = 0.8) -> int:
    za = stats.norm.ppf(1 - alpha / 2)
    zb = stats.norm.ppf(power)
    pooled = (p1 + p2) / 2
    numerator = (
        za * math.sqrt(2 * pooled * (1 - pooled))
        + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    return int(math.ceil(numerator / ((p1 - p2) ** 2)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="external/ARC-AGI-2/data")
    parser.add_argument("--split", default="evaluation")
    parser.add_argument("--score-a", type=float, default=0.54)
    parser.add_argument("--score-b", type=float, default=0.45)
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()

    split_dir = Path(args.data_root) / args.split
    files = sorted(split_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No ARC task files under {split_dir}")

    outputs_per_task: list[int] = []
    for path in files:
        task = json.loads(path.read_text(encoding="utf-8"))
        outputs_per_task.append(len(task.get("test", [])))

    n_tasks = len(files)
    n_outputs = int(sum(outputs_per_task))
    distribution = {str(k): int(v) for k, v in sorted(Counter(outputs_per_task).items())}

    count_a = nearest_count(args.score_a, n_outputs)
    count_b = nearest_count(args.score_b, n_outputs)
    approximate_a = count_a / n_outputs
    approximate_b = count_b / n_outputs
    ci_a = wilson(count_a, n_outputs)
    ci_b = wilson(count_b, n_outputs)
    unpaired = unpaired_two_proportion(count_a, count_b, n_outputs)

    # Average cluster size gives a transparent design-effect sensitivity, but it
    # is not a substitute for actual per-task outcomes. Equal cluster-size ICC
    # formula is shown only as a rough range.
    mean_cluster = n_outputs / n_tasks
    icc_sensitivity: list[dict[str, Any]] = []
    for rho in (0.0, 0.25, 0.5, 0.75, 1.0):
        design_effect = 1 + (mean_cluster - 1) * rho
        effective_n = n_outputs / design_effect
        icc_sensitivity.append(
            {
                "assumed_within_task_icc": rho,
                "design_effect_approx": design_effect,
                "effective_output_count_approx": effective_n,
            }
        )

    output: dict[str, Any] = {
        "split": args.split,
        "task_count": n_tasks,
        "test_output_count": n_outputs,
        "outputs_per_task_distribution": distribution,
        "mean_test_outputs_per_task": mean_cluster,
        "legacy_n_equals_120_assumption_valid": False,
        "reason": (
            "The official public evaluation set contains 120 tasks but 167 test outputs. "
            "Competition scores are computed over test outputs; outputs within a task are dependent."
        ),
        "aggregate_score_example": {
            "requested_score_a": args.score_a,
            "requested_score_b": args.score_b,
            "nearest_representable_score_a": approximate_a,
            "nearest_representable_score_b": approximate_b,
            "successes_a": count_a,
            "successes_b": count_b,
            "output_level_wilson_ci95_a": ci_a,
            "output_level_wilson_ci95_b": ci_b,
            "unpaired_output_level_test": unpaired,
            "warning": (
                "This is an output-level approximation. A system comparison needs paired per-output "
                "outcomes, and uncertainty should cluster by task when tasks contain multiple outputs."
            ),
        },
        "outputs_needed_for_five_point_gap_near_half_80pct_power_unpaired": sample_size_for_gap(0.50, 0.45),
        "icc_sensitivity": icc_sensitivity,
        "reporting_standard": [
            "State whether the denominator is tasks or test outputs.",
            "Release per-output outcomes for paired tests.",
            "Cluster uncertainty by task when tasks contain multiple test outputs.",
            "Do not infer significance by eyeballing overlapping or non-overlapping marginal intervals.",
        ],
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "leaderboard_measurement_v2.json"
    json_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# ARC-AGI-2 leaderboard measurement audit v2",
        "",
        f"Directly counted from the pinned public `{args.split}` corpus: **{n_tasks} tasks** and **{n_outputs} test outputs**.",
        "",
        "The legacy `N=120` binomial analysis used the number of tasks as the score denominator. That is not the competition scoring unit. Scores are computed over test outputs, and outputs are nested within tasks.",
        "",
        "## Consequences",
        "",
        f"- Output distribution per task: `{distribution}`; mean {mean_cluster:.3f} outputs/task.",
        f"- A nominal {100*args.score_a:.1f}% score corresponds most closely to {count_a}/{n_outputs} = {100*approximate_a:.2f}% on this public corpus.",
        f"- Its output-level Wilson interval is [{100*ci_a[0]:.1f}, {100*ci_a[1]:.1f}]%.",
        f"- A nominal {100*args.score_b:.1f}% score corresponds most closely to {count_b}/{n_outputs} = {100*approximate_b:.2f}%, interval [{100*ci_b[0]:.1f}, {100*ci_b[1]:.1f}]%.",
        f"- The unpaired output-level approximation gives p={unpaired['two_sided_p']:.3f}; this is not a substitute for paired, task-clustered analysis.",
        f"- Roughly {output['outputs_needed_for_five_point_gap_near_half_80pct_power_unpaired']:,} independent outputs are needed to resolve a five-point gap near 50% at 80% power under the same unpaired approximation.",
        "",
        "## Correct reporting standard",
        "",
        "1. Identify the score denominator: tasks or test outputs.",
        "2. Release per-output outcomes so systems can be compared with paired tests.",
        "3. Cluster uncertainty by ARC task when a task has multiple test outputs.",
        "4. Treat a single aggregate percentage without its outcome table as insufficient for a precise ranking claim.",
    ]
    md_path = output_dir / "leaderboard_measurement_v2.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
