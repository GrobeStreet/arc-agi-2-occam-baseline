#!/usr/bin/env python3
"""Generate publication figures for ARC Measurement Audit v2.

Each output is a separate figure. The script reads only committed machine-readable
results, so figures cannot drift from the paper's evidence record.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "results" / "task_weighted_calibration.json"
TRAINING = ROOT / "results" / "crossfold" / "training_audit" / "crossfold_calibration.json"


def load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required result file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save(name: str) -> None:
    plt.tight_layout()
    plt.savefig(ROOT / name, dpi=220, bbox_inches="tight")
    plt.close()
    print(f"wrote {name}")


def legacy_task_weighting(legacy: dict) -> None:
    rows = legacy["results_by_k"]
    ks = np.asarray([row["k"] for row in rows], dtype=float)
    program = np.asarray([row["program_weighted_rate"] for row in rows]) * 100
    task = np.asarray([row["task_weighted_rate"] for row in rows]) * 100
    lower = np.asarray([
        row["task_weighted_rate"] - row["task_cluster_bootstrap_ci95"][0]
        for row in rows
    ]) * 100
    upper = np.asarray([
        row["task_cluster_bootstrap_ci95"][1] - row["task_weighted_rate"]
        for row in rows
    ]) * 100

    plt.figure(figsize=(7.4, 4.5))
    plt.plot(ks, program, marker="o", label="Candidate-program weighted")
    plt.errorbar(
        ks,
        task,
        yerr=np.vstack([lower, upper]),
        marker="o",
        capsize=4,
        label="Equal-task weighted (95% task bootstrap CI)",
    )
    plt.xticks(ks, [f"k={int(k)}" for k in ks])
    plt.ylim(0, 105)
    plt.ylabel("Held-out generalization rate (%)")
    plt.xlabel("Demonstrations fitted")
    plt.title("The legacy marginal curve after equal-task reweighting")
    plt.legend(frameon=False)
    plt.grid(axis="y", alpha=0.25)
    save("fig_v2_task_weighting.png")


def same_target_levels(training: dict) -> None:
    rows = {int(row["k"]): row for row in training["results_by_k"]}
    ks = [1, 2]
    labels = ["Coverage", "Candidate reliability", "Consensus yield"]
    keys = ["coverage", "candidate_reliability", "consensus_yield"]
    x = np.arange(len(labels))
    width = 0.34

    plt.figure(figsize=(8.0, 4.8))
    for offset, k in [(-width / 2, 1), (width / 2, 2)]:
        values = []
        lowers = []
        uppers = []
        for key in keys:
            item = rows[k]["metrics"][key]
            value = item["task_weighted_mean"]
            interval = item["ci95"]
            values.append(value * 100)
            if interval is None:
                lowers.append(0)
                uppers.append(0)
            else:
                lowers.append((value - interval[0]) * 100)
                uppers.append((interval[1] - value) * 100)
        plt.bar(
            x + offset,
            values,
            width,
            yerr=np.vstack([lowers, uppers]),
            capsize=3,
            label=f"k={k}",
        )
    plt.xticks(x, labels)
    plt.ylabel("Task-weighted rate (%)")
    plt.title("More evidence improves purity but reduces representational coverage")
    plt.legend(frameon=False)
    plt.grid(axis="y", alpha=0.25)
    save("fig_v2_coverage_reliability.png")


def same_target_delta(training: dict) -> None:
    contrast = next(
        item
        for item in training["same_holdout_adjacent_k_contrasts"]
        if item["contrast"] == "k=2 minus k=1"
    )
    entries = [
        ("Coverage", "coverage"),
        ("Random-selection yield", "random_yield"),
        ("Tie-aware MDL yield", "mdl_vote_yield"),
        ("Consensus yield", "consensus_yield"),
        ("Candidate-oracle yield", "oracle_yield"),
    ]
    labels = [label for label, _ in entries]
    values = np.asarray([
        contrast["metrics"][key]["task_weighted_delta"] * 100
        for _, key in entries
    ])
    lower = np.asarray([
        (
            contrast["metrics"][key]["task_weighted_delta"]
            - contrast["metrics"][key]["ci95"][0]
        ) * 100
        for _, key in entries
    ])
    upper = np.asarray([
        (
            contrast["metrics"][key]["ci95"][1]
            - contrast["metrics"][key]["task_weighted_delta"]
        ) * 100
        for _, key in entries
    ])
    y = np.arange(len(entries))

    plt.figure(figsize=(8.2, 4.8))
    plt.errorbar(values, y, xerr=np.vstack([lower, upper]), fmt="o", capsize=4)
    plt.axvline(0, linewidth=1)
    plt.yticks(y, labels)
    plt.xlabel("Same-target change: k=2 minus k=1 (percentage points)")
    plt.title("Added demonstrations reduce end-to-end yield in the diagnostic DSL")
    plt.grid(axis="x", alpha=0.25)
    plt.gca().invert_yaxis()
    save("fig_v2_same_target_delta.png")


def selection(training: dict) -> None:
    result = training["ambiguous_subset_selection"]
    entries = [
        ("Random", "random"),
        ("First shortest", "legacy_first_shortest"),
        ("MDL random tie", "mdl_random_tie"),
        ("MDL vote", "mdl_vote_tie"),
        ("Consensus", "consensus"),
        ("Oracle", "oracle"),
    ]
    labels = [label for label, _ in entries]
    values = np.asarray([
        result["overall"][key]["task_weighted_rate"] * 100
        for _, key in entries
    ])
    lower = np.asarray([
        (
            result["overall"][key]["task_weighted_rate"]
            - result["overall"][key]["ci95"][0]
        ) * 100
        for _, key in entries
    ])
    upper = np.asarray([
        (
            result["overall"][key]["ci95"][1]
            - result["overall"][key]["task_weighted_rate"]
        ) * 100
        for _, key in entries
    ])
    x = np.arange(len(entries))

    plt.figure(figsize=(8.2, 4.8))
    plt.bar(x, values, yerr=np.vstack([lower, upper]), capsize=4)
    plt.xticks(x, labels, rotation=18, ha="right")
    plt.ylabel("Accuracy on ambiguous candidate sets (%)")
    plt.title("Description length helps, but does not reach the candidate oracle")
    plt.grid(axis="y", alpha=0.25)
    save("fig_v2_selection.png")


def calibration(training: dict) -> None:
    result = training["modal_vote_calibration"]
    bins = result["bins"]
    confidence = np.asarray([item["task_weighted_confidence"] for item in bins])
    accuracy = np.asarray([item["task_weighted_accuracy"] for item in bins])
    lower = np.asarray([
        item["task_weighted_accuracy"] - item["accuracy_ci95"][0]
        for item in bins
    ])
    upper = np.asarray([
        item["accuracy_ci95"][1] - item["task_weighted_accuracy"]
        for item in bins
    ])

    plt.figure(figsize=(5.8, 5.2))
    plt.plot([0, 1], [0, 1], linestyle="--", label="Perfect calibration")
    plt.errorbar(
        confidence,
        accuracy,
        yerr=np.vstack([lower, upper]),
        marker="o",
        capsize=4,
        label="Observed task-weighted accuracy",
    )
    plt.xlim(0, 1.03)
    plt.ylim(0, 1.03)
    plt.xlabel("Modal candidate-vote fraction")
    plt.ylabel("Held-out accuracy")
    plt.title("Candidate agreement is severely overconfident")
    plt.legend(frameon=False)
    plt.grid(alpha=0.25)
    save("fig_v2_consensus_calibration.png")


def main() -> None:
    legacy = load(LEGACY)
    training = load(TRAINING)
    legacy_task_weighting(legacy)
    same_target_levels(training)
    same_target_delta(training)
    selection(training)
    calibration(training)


if __name__ == "__main__":
    main()
