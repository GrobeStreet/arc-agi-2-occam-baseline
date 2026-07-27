# ARC Prize 2026 — Contest Status

**Updated:** 2026-07-27  
**Repository:** `GrobeStreet/arc-agi-2-occam-baseline`

## Executive status

The research, corrected measurement paper, frozen public-evaluation diagnostics, and a Kaggle-compatible solver entrypoint are pushed to `main`.

There is **not yet an official Kaggle score or leaderboard rank for this repository**. A rank is created only after an authenticated Kaggle notebook is run and submitted to the ARC Prize 2026 competition.

The ARC Prize rules require ARC-AGI-2 competition submissions to be made through a **Kaggle notebook**, with internet disabled during evaluation. A standalone JSON file in GitHub does not create a competition entry.

Official pages:

- Competition: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2
- ARC Prize requirements: https://arcprize.org/competitions/2026/arc-agi-2
- Paper Prize: https://arcprize.org/competitions/2026/paper

## What is pushed and reproducible

### Measurement program

- `PAPER_V2.md`
- `ARC_Measurement_Audit_v2.pdf`
- `RESULTS_V2.md`
- `results/task_weighted_calibration.json`
- `results/crossfold/`
- `results/solver/`
- `results/representation_v3/`
- `results/representation_v3_public/`

### Working contest entrypoint

- `kaggle_submission_v3.py`
- `dsl.py`
- `dsl_v3.py`
- `benchmark_representation_v3.py`
- `kaggle/arc_v3_entrypoint.py`

The frozen v3 public-evaluation check produced **0/167 pass@2**. That is a real negative result. It means the current symbolic grammar should not be represented as a high-scoring solver.

A valid low-scoring Kaggle notebook submission is still strategically useful because the ARC Prize Paper Track requires the paper to be linked to an ARC-AGI-2 or ARC-AGI-3 Kaggle code submission; the linked code submission does not need a high score.

## V4.1 boundary

The repository contains v4.1 registration and workflow scaffolding, but the expected frozen core branch is no longer available and no canonical `site/representation-v4.json`, `results/representation_v4_1/` result, or committed `submission/arc_v4_1_submission.json` was produced.

Therefore:

- do **not** claim a v4.1 score;
- do **not** label a v3 artifact as v4.1;
- do **not** claim a new competition rank from v4.1;
- restore and rerun the frozen v4 core before using that name.

## Exact next contest action

1. Open the ARC Prize 2026 Kaggle competition and join it.
2. Create a private competition notebook.
3. Turn internet **off**.
4. Attach the competition data and an uploaded dataset containing the repository files listed above.
5. Run `kaggle/arc_v3_entrypoint.py`.
6. Confirm `/kaggle/working/submission.json` exists and contains exactly two attempts per test input.
7. Save a version and click **Submit to Competition**.
8. Record the returned score, team name, entry timestamp, and leaderboard rank in this file.

Detailed instructions are in [`KAGGLE_SUBMIT_NOW.md`](KAGGLE_SUBMIT_NOW.md).

## Ranking rule

Until Kaggle returns a scored notebook submission, the official status is:

> **Unranked — submission not yet authenticated and scored by Kaggle.**

No local holdout, public demonstration audit, GitHub workflow, or generated JSON file is a substitute for the official competition rank.
