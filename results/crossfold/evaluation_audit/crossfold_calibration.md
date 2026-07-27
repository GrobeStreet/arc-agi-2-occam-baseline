# Same-holdout cross-fold ARC calibration

This analysis holds the target demonstration fixed while varying how many of the remaining demonstrations are fitted. It resolves the main identification problem in the original prefix analysis.

Analyzed **120 tasks**, **800 task/holdout/k folds**, and **1,757 demonstration-subset cells**.

| k | tasks | coverage | random yield | legacy shortest | tie-aware MDL vote | consensus | oracle | candidate reliability |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 120 | 1.0% [0.2, 2.2] | 0.1% [0.0, 0.4] | 0.1% [0.0, 0.4] | 0.1% [0.0, 0.4] | 0.1% [0.0, 0.4] | 0.1% [0.0, 0.4] | 12.5% [0.0, 50.0] |
| 2 | 86 | 0.2% [0.0, 0.6] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] |
| 3 | 25 | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | NA |
| 4 | 7 | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | NA |
| 5 | 1 | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | NA |

## Same-target adjacent-k effects

### k=2 minus k=1 (86 tasks; 291 held-out folds)
- **coverage:** -1.2 pp; 95% CI [-2.6, -0.2] pp; P(delta>0)=0.0000.
- **random_yield:** -0.2 pp; 95% CI [-0.6, +0.0] pp; P(delta>0)=0.0000.
- **legacy_mdl_yield:** -0.2 pp; 95% CI [-0.6, +0.0] pp; P(delta>0)=0.0000.
- **mdl_random_yield:** -0.2 pp; 95% CI [-0.6, +0.0] pp; P(delta>0)=0.0000.
- **mdl_vote_yield:** -0.2 pp; 95% CI [-0.6, +0.0] pp; P(delta>0)=0.0000.
- **consensus_yield:** -0.2 pp; 95% CI [-0.6, +0.0] pp; P(delta>0)=0.0000.
- **oracle_yield:** -0.2 pp; 95% CI [-0.6, +0.0] pp; P(delta>0)=0.0000.

### k=3 minus k=2 (25 tasks; 108 held-out folds)
- **coverage:** -0.7 pp; 95% CI [-2.0, +0.0] pp; P(delta>0)=0.0000.
- **random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **legacy_mdl_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_vote_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **consensus_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **oracle_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.

### k=4 minus k=3 (7 tasks; 36 held-out folds)
- **coverage:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **legacy_mdl_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_vote_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **consensus_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **oracle_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.

### k=5 minus k=4 (1 tasks; 6 held-out folds)
- **coverage:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **legacy_mdl_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_random_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **mdl_vote_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **consensus_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.
- **oracle_yield:** +0.0 pp; 95% CI [+0.0, +0.0] pp; P(delta>0)=0.0000.

## Selection on ambiguous subset cells

**4 ambiguous cells across 1 tasks.**
- **random:** 0.0% [95% CI 0.0, 0.0]
- **legacy_first_shortest:** 0.0% [95% CI 0.0, 0.0]
- **mdl_random_tie:** 0.0% [95% CI 0.0, 0.0]
- **mdl_vote_tie:** 0.0% [95% CI 0.0, 0.0]
- **consensus:** 0.0% [95% CI 0.0, 0.0]
- **oracle:** 0.0% [95% CI 0.0, 0.0]

- **legacy_shortest_minus_random:** +0.0 pp [95% CI +0.0, +0.0]
- **mdl_random_minus_random:** +0.0 pp [95% CI +0.0, +0.0]
- **mdl_vote_minus_random:** +0.0 pp [95% CI +0.0, +0.0]
- **consensus_minus_random:** +0.0 pp [95% CI +0.0, +0.0]
- **mdl_vote_minus_legacy_shortest:** +0.0 pp [95% CI +0.0, +0.0]
- **oracle_minus_mdl_vote:** +0.0 pp [95% CI +0.0, +0.0]
- **oracle_minus_consensus:** +0.0 pp [95% CI +0.0, +0.0]

## Resolution rule

The same-target adjacent-k effects are the primary test of whether added demonstrations improve this DSL's reliable end-to-end behavior. The selection analysis distinguishes a legacy enumeration-order shortest program from tie-aware MDL and consensus, preventing arbitrary list order from masquerading as Occam's razor.

Task-cluster bootstrap: 20,000 replicates, seed 20260727.
