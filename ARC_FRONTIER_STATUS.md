# ARC Frontier Status

The measurement program is complete enough to support one frozen contest evaluation. The active contest action is now **Private Cycle 001: frozen representation v3**.

## Completed methodological corrections

1. Program-pooled calibration was separated from equal-task calibration.
2. Task-cluster bootstrap uncertainty was added.
3. Same-target all-subsets testing separated evidence purification from coverage collapse.
4. MDL was expanded from 17 ambiguous cells to a larger task-clustered comparison and no longer claimed to match the oracle.
5. Candidate agreement was tested as a confidence signal and found overconfident.
6. Frozen selectors were benchmarked before representation expansion.
7. Representation v3 was registered, evaluated on a deterministic training holdout, and then tested once on public evaluation without further tuning.

## Active contest cycle

- Registration: `HYPOTHESIS-private-v3-cycle-001.md`
- Frozen solver: `kaggle_submission_v3.py`
- Frozen representation: `dsl_v3.py`
- Competition: `arc-prize-2026-arc-agi-2`
- Submission type: Kaggle code-competition notebook
- Internet during evaluation: disabled
- Output contract: exactly two distinct grids for every private test input
- Automation: `.github/workflows/kaggle-private-v3-cycle-001.yml`
- Status record: `results/private_cycle_001/`

Cycle 001 is evaluation-only. It may not alter the representation grammar, ranking rule, fallback policy, or output contract.

## Expansion firewall

Any further representation work must begin with a new registration named `HYPOTHESIS-representation-cycle-002.md` or later. The registration must be committed before the corresponding source changes and must define a fresh holdout or untouched private-test endpoint, fixed promotion criteria, fixed failure criteria, and a publish-regardless rule.

The later v4/v4.1 files and packages already present in the history are retained as exploratory or historical artifacts. They are **not authorized substitutes for frozen v3 in Private Cycle 001**, and they cannot be described as its private-test result.

## Ranking boundary

A repository holdout, public evaluation run, or generated submission file does not create a Kaggle rank. The workflow records the actual visible Kaggle score and public rank only after Kaggle accepts and scores the code-competition submission. Final private ranking is determined by Kaggle at competition close.

All results—including blocked credentials, execution failure, zero score, and nonzero score—publish without changing frozen v3.