# ARC Frontier Status

The project has moved from measurement diagnosis to a frozen representation experiment.

## Completed methodological corrections

1. Program-pooled calibration was separated from equal-task calibration.
2. Task-cluster bootstrap uncertainty was added.
3. Same-target all-subsets testing separated evidence purification from coverage collapse.
4. MDL was expanded from 17 ambiguous cells to a larger task-clustered comparison and no longer claimed to match the oracle.
5. Candidate agreement was tested as a confidence signal and found overconfident.
6. Frozen selectors were benchmarked before representation expansion.

## Active resolving experiment

- Registration: `HYPOTHESIS-representation-frontier-v4.md`
- Core: `representation_frontier_v4.py`
- Scoring correction: `HYPOTHESIS-representation-v4.1-scoring.md` and `representation_frontier_v4_1.py`
- Deterministic untouched holdout: SHA-256 bucket 0 of ARC-AGI-2 training tasks
- Public evaluation excluded from development and confirmation
- Inference: paired task wins/losses, exact paired test, and task bootstrap interval
- Output: `results/representation_v4_1/`
- Live JSON: `site/representation-v4.json`
- Live dashboard: `site/representation-frontier-live.html`
- Frozen contest package: `submission/`

## Interpretation boundary

The public holdout determines whether the expanded grammar creates genuine exact-solve gains. It does not establish private-leaderboard capability. After the holdout is frozen, the generated pass@2 JSON can be submitted once to the contest endpoint without further grammar editing.

All verdicts publish regardless of direction.
