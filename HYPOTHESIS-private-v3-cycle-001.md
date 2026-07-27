# Registered Private Cycle 001 — Frozen Representation v3

**Registered:** 2026-07-27, before any Kaggle ARC Prize 2026 private-test submission from this automation.

## Purpose

Run the already-frozen representation-v3 artifact on the untouched ARC Prize 2026 Kaggle competition test. This cycle is evaluation only. It does not authorize changes to the grammar, ranking rule, fallback policy, output contract, or candidate-selection logic.

## Frozen artifacts

The submission must use the versions present in the source commit recorded by the submission workflow:

- `dsl.py`
- `dsl_v3.py`
- `benchmark_representation_v3.py`
- `kaggle_submission_v3.py`

The workflow records the source commit and SHA-256 digest of each file before uploading the Kaggle notebook.

## Competition endpoint

- Competition: `arc-prize-2026-arc-agi-2`
- Submission type: Kaggle code-competition notebook
- Internet during evaluation: disabled
- Output: exactly two distinct grids for every private test input
- Intended first submission count under this cycle: one

Kaggle exposes a public leaderboard score during the competition and determines the final private ranking from the held-back portion after the competition. Cycle 001 records the currently visible score and rank while preserving the exact notebook version for final evaluation.

## Precommitted interpretation

- **NONZERO TEST SUCCESS:** visible score above zero.
- **NULL:** visible score equals zero.
- **FORMAT OR EXECUTION FAILURE:** notebook or submission fails validation or scoring.

No outcome authorizes post-hoc changes under Cycle 001.

## Expansion firewall

After Cycle 001 is scored, representation may be expanded only under a new registration named `HYPOTHESIS-representation-cycle-002.md` or later, committed before the corresponding source change and defining:

1. a fresh holdout or untouched private-test endpoint;
2. the exact allowed representation changes;
3. fixed promotion and failure criteria;
4. a publish-regardless commitment;
5. a prohibition on using the Cycle 001 score as a task-level tuning signal.

Existing later experimental branches and packages are historical artifacts. They may not be described as Cycle 001 private-test results and may not replace the frozen v3 kernel in this submission.

## Reproducibility record

The workflow must record:

- kernel identifier and version;
- source commit and file hashes;
- notebook output metadata;
- Kaggle submission status;
- visible public score;
- visible public rank when available;
- timestamp and competition slug.

## Publish-regardless commitment

The score, rank, error, or blocked state will be recorded without changing the frozen v3 solver.