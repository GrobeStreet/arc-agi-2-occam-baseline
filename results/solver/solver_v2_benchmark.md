# Evidence-weighted ARC solver: frozen public-evaluation benchmark

Program-family priors were learned only from public training demonstrations. The public evaluation split was then scored once as a holdout. This is not a private Kaggle leaderboard claim.

| method | pass@1 | 95% CI | pass@2 | 95% CI | tasks with any pass@2 | tasks all outputs pass@2 |
|---|---:|---:|---:|---:|---:|---:|
| Released vote + MDL baseline | 0.00% (0/167) | [0.00, 2.25] | 0.00% (0/167) | [0.00, 2.25] | 0 | 0 |
| Pure minimum description length | 0.00% (0/167) | [0.00, 2.25] | 0.00% (0/167) | [0.00, 2.25] | 0 | 0 |
| Evidence-weighted family selector | 0.00% (0/167) | [0.00, 2.25] | 0.00% (0/167) | [0.00, 2.25] | 0 | 0 |

## Paired differences

- **evidence_vs_legacy_pass1:** evidence-only wins 0; comparator-only wins 0; exact McNemar/binomial p=1.0000.
- **evidence_vs_legacy_pass2:** evidence-only wins 0; comparator-only wins 0; exact McNemar/binomial p=1.0000.
- **evidence_vs_mdl_pass1:** evidence-only wins 0; comparator-only wins 0; exact McNemar/binomial p=1.0000.
- **evidence_vs_mdl_pass2:** evidence-only wins 0; comparator-only wins 0; exact McNemar/binomial p=1.0000.

## Decision rule

The selector is promoted only if it improves frozen paired evaluation outcomes. A tie or loss is retained as a negative result; the measurement paper does not depend on a solver gain.

Runtime: 42.5 seconds after prior learning.
