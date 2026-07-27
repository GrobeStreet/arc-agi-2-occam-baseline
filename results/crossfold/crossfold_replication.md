# ARC cross-fold calibration: one-shot evaluation replication

The analysis was frozen before reading public-evaluation results. This compares public training and evaluation demonstration-pair calibration with ARC tasks as the sampling units.

| k | metric | training | evaluation | evaluation − training | 95% CI |
|---:|---|---:|---:|---:|---:|
| 1 | coverage | 7.1% | 1.0% | -6.1 pp | [-7.8, -4.3] pp |
| 1 | consensus_yield | 3.3% | 0.1% | -3.2 pp | [-4.3, -2.1] pp |
| 1 | mdl_vote_yield | 3.4% | 0.1% | -3.3 pp | [-4.4, -2.2] pp |
| 1 | candidate_reliability | 32.8% | 12.5% | -20.3 pp | [-38.3, +5.4] pp |
| 2 | coverage | 3.8% | 0.2% | -3.6 pp | [-4.9, -2.4] pp |
| 2 | consensus_yield | 3.0% | 0.0% | -3.0 pp | [-4.2, -1.9] pp |
| 2 | mdl_vote_yield | 3.0% | 0.0% | -3.0 pp | [-4.2, -1.9] pp |
| 2 | candidate_reliability | 50.8% | 0.0% | -50.8 pp | [-63.7, -37.9] pp |
| 3 | coverage | 4.4% | 0.0% | -4.4 pp | [-6.9, -2.2] pp |
| 3 | consensus_yield | 3.8% | 0.0% | -3.8 pp | [-6.4, -1.9] pp |
| 3 | mdl_vote_yield | 3.8% | 0.0% | -3.8 pp | [-6.3, -1.9] pp |
| 3 | candidate_reliability | 63.4% | NA | NA | NA |
| 4 | coverage | 2.6% | 0.0% | -2.6 pp | [-6.4, +0.0] pp |
| 4 | consensus_yield | 2.6% | 0.0% | -2.6 pp | [-6.4, +0.0] pp |
| 4 | mdl_vote_yield | 2.6% | 0.0% | -2.6 pp | [-6.4, +0.0] pp |
| 4 | candidate_reliability | 100.0% | NA | NA | NA |
| 5 | coverage | 0.0% | 0.0% | +0.0 pp | [+0.0, +0.0] pp |
| 5 | consensus_yield | 0.0% | 0.0% | +0.0 pp | [+0.0, +0.0] pp |
| 5 | mdl_vote_yield | 0.0% | 0.0% | +0.0 pp | [+0.0, +0.0] pp |
| 5 | candidate_reliability | NA | NA | NA | NA |

## Primary same-target effect replication

- **coverage:** training -3.7 pp; evaluation -1.2 pp; same direction = True.
- **random_yield:** training -0.2 pp; evaluation -0.2 pp; same direction = True.
- **mdl_vote_yield:** training -0.4 pp; evaluation -0.2 pp; same direction = True.
- **consensus_yield:** training -0.4 pp; evaluation -0.2 pp; same direction = True.
- **oracle_yield:** training -0.5 pp; evaluation -0.2 pp; same direction = True.

## Interpretation

Replication concerns the direction and uncertainty of the pre-specified same-target effects. Differences in marginal levels are expected because the public evaluation set is deliberately harder and compositionally different. Sparse high-k cells are reported as NA rather than causing a formatting failure. No method or threshold is changed in response to this file.
