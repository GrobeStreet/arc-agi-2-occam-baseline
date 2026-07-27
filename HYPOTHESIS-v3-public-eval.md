# Registered Hypothesis — Frozen Representation v3 on ARC-AGI-2 Public Evaluation

**Registered before the first representation-v3 run on the 120 public evaluation tasks.**  
**Date:** 2026-07-27  
**Status at registration:** v3 was developed and selected only on the deterministic SHA1 training holdout. The public evaluation outputs have not been used to alter `dsl_v3.py` or `kaggle_submission_v3.py`.

## Question

Does the frozen representation-v3 grammar produce any genuine public-evaluation improvement over the already-recorded v2 baseline of 0/167 pass@1 and 0/167 pass@2?

## Frozen artifacts

- `dsl_v3.py`
- `kaggle_submission_v3.py`
- `HYPOTHESIS-representation-v3.md`
- training-holdout result: v2 4/201 pass@2, v3 5/201 pass@2, one v3-only win and zero v2-only wins

No change to the grammar, selector, or fallback policy is allowed after this registration and before the one-shot run.

## Test

1. Load all 120 official public evaluation tasks from a pinned `arcprize/ARC-AGI-2` commit.
2. Remove test outputs from the challenge object used by the solver.
3. Generate exactly two semantically distinct attempts per test input with `kaggle_submission_v3.py` logic.
4. Score pass@1 and pass@2 against the public labels only after all predictions are frozen.
5. Report output-level and whole-task success, candidate coverage, and a paired comparison against the recorded v2 baseline.
6. Save the exact submission JSON and per-output predictions.

## Pre-committed verdicts

- **CLEAR PROMOTION:** at least six v3-only pass@2 output wins, zero or fewer v2-only wins, and exact two-sided paired p < 0.05.
- **DIRECTIONAL IMPROVEMENT:** one to five v3-only pass@2 output wins and no v2-only wins.
- **NULL:** zero v3 pass@2 wins.
- **FAILURE:** v3 produces fewer pass@2 wins than the v2 baseline, generates malformed outputs, or violates the two-attempt contract.

Because the v2 public-evaluation baseline is 0/167, any v3 success is necessarily v3-only. Statistical clarity still requires the registered paired threshold.

## Interpretation boundary

This public evaluation set is observable and is not the private Kaggle test. The result is a one-shot public holdout check, not a verified competition score. After this run, no further tuning may be described as public-evaluation-confirmed; new development must return to a fresh training holdout or private test.
