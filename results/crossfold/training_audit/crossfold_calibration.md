# Same-holdout cross-fold ARC calibration

This analysis holds the target demonstration fixed while varying how many of the remaining demonstrations are fitted. It resolves the main identification problem in the original prefix analysis.

Analyzed **1000 tasks**, **8,092 task/holdout/k folds**, and **28,476 demonstration-subset cells**.

| k | tasks | coverage | random yield | legacy shortest | tie-aware MDL vote | consensus | oracle | candidate reliability |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1000 | 7.1% [5.7, 8.6] | 3.1% [2.2, 4.2] | 3.4% [2.4, 4.5] | 3.4% [2.4, 4.5] | 3.3% [2.3, 4.4] | 3.4% [2.4, 4.6] | 32.8% [25.1, 40.4] |
| 2 | 842 | 3.8% [2.7, 5.1] | 3.0% [1.9, 4.1] | 3.0% [1.9, 4.2] | 3.0% [1.9, 4.2] | 3.0% [1.9, 4.2] | 3.0% [1.9, 4.2] | 50.8% [37.8, 64.0] |
| 3 | 267 | 4.4% [2.1, 6.9] | 3.8% [1.7, 6.2] | 3.8% [1.7, 6.3] | 3.8% [1.7, 6.3] | 3.8% [1.7, 6.3] | 3.8% [1.7, 6.3] | 63.4% [39.5, 86.0] |
| 4 | 78 | 2.6% [0.0, 6.4] | 2.6% [0.0, 6.4] | 2.6% [0.0, 6.4] | 2.6% [0.0, 6.4] | 2.6% [0.0, 6.4] | 2.6% [0.0, 6.4] | 100.0% [100.0, 100.0] |
| 5 | 29 | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | NA |
| 6 | 11 | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | NA |
| 7 | 3 | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | NA |
| 8 | 1 | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | NA |
| 9 | 1 | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | NA |

## Same-target adjacent-k effects

### k=2 minus k=1 (842 tasks; 2916 held-out folds)
- **coverage:** -3.7 pp; 95% CI [-4.6, -2.7] pp; P(delta>0)=0.0000.
- **random_yield:** -0.2 pp; 95% CI [-0.5, -0.0] pp; P(delta>0)=0.0234.
- **legacy_mdl_yield:** -0.4 pp; 95% CI [-0.7, -0.2] pp; P(delta>0)=0.0001.
- **mdl_random_yield:** -0.4 pp; 95% CI [-0.7, -0.2] pp; P(delta>0)=0.0001.
- **mdl_vote_yield:** -0.4 pp; 95% CI [-0.7, -0.2] pp; P(delta>0)=0.0001.
- **consensus_yield:** -0.4 pp; 95% CI [-0.6, -0.2] pp; P(delta>0)=0.0001.
- **oracle_yield:** -0.5 pp; 95% CI [-0.7, -0.2] pp; P(delta>0)=0.0000.

### k=3 minus k=2 (267 tasks; 1191 held-out folds)
- **coverage:** -1.2 pp; 95% CI [-1.8, -0.7] pp; P(delta>0)=0.0000.
- **random_yield:** -0.0 pp; 95% CI [-0.2, +0.2] pp; P(delta>0)=0.4571.
- **legacy_mdl_yield:** -0.1 pp; 95% CI [-0.3, +0.1] pp; P(delta>0)=0.1681.
- **mdl_random_yield:** -0.1 pp; 95% CI [-0.3, +0.1] pp; P(delta>0)=0.1681.
- **mdl_vote_yield:** -0.1 pp; 95% CI [-0.3, +0.1] pp; P(delta>0)=0.1681.
- **consensus_yield:** -0.1 pp; 95% CI [-0.3, +0.1] pp; P(delta>0)=0.1681.
- **oracle_yield:** -0.1 pp; 95% CI [-0.3, +0.1] pp; P(delta>0)=0.1681.

### k=4 minus k=3 (78 tasks; 435 held-out folds)
- **coverage:** -0.2 pp; 95% CI [-0.6, +0.0] pp; P(delta>0)=0.0000.
- **random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **legacy_mdl_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_vote_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **consensus_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **oracle_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.

### k=5 minus k=4 (29 tasks; 190 held-out folds)
- **coverage:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **legacy_mdl_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_vote_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **consensus_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **oracle_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.

### k=6 minus k=5 (11 tasks; 82 held-out folds)
- **coverage:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **legacy_mdl_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_vote_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **consensus_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **oracle_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.

### k=7 minus k=6 (3 tasks; 26 held-out folds)
- **coverage:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **legacy_mdl_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_vote_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **consensus_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **oracle_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.

### k=8 minus k=7 (1 tasks; 10 held-out folds)
- **coverage:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **legacy_mdl_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_vote_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **consensus_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **oracle_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.

### k=9 minus k=8 (1 tasks; 10 held-out folds)
- **coverage:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **legacy_mdl_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_vote_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **consensus_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **oracle_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.

## Selection on ambiguous subset cells

**224 ambiguous cells across 41 tasks.**
- **random:** 18.9% [95% CI 10.8, 27.8]
- **legacy_first_shortest:** 31.2% [95% CI 18.5, 44.8]
- **mdl_random_tie:** 30.4% [95% CI 18.3, 43.5]
- **mdl_vote_tie:** 30.0% [95% CI 17.7, 43.1]
- **consensus:** 27.4% [95% CI 15.6, 40.0]
- **oracle:** 33.7% [95% CI 20.5, 47.6]

- **legacy_shortest_minus_random:** +12.3 pp [95% CI +5.6, +19.4]
- **mdl_random_minus_random:** +11.5 pp [95% CI +5.9, +17.9]
- **mdl_vote_minus_random:** +11.1 pp [95% CI +4.6, +17.9]
- **consensus_minus_random:** +8.5 pp [95% CI +2.6, +14.8]
- **mdl_vote_minus_legacy_shortest:** -1.2 pp [95% CI -7.7, +4.3]
- **oracle_minus_mdl_vote:** +3.7 pp [95% CI +0.1, +9.5]
- **oracle_minus_consensus:** +6.3 pp [95% CI +1.7, +12.6]

## Resolution rule

The same-target adjacent-k effects are the primary test of whether added demonstrations improve this DSL's reliable end-to-end behavior. The selection analysis distinguishes a legacy enumeration-order shortest program from tie-aware MDL and consensus, preventing arbitrary list order from masquerading as Occam's razor.

Task-cluster bootstrap: 20,000 replicates, seed 20260727.
