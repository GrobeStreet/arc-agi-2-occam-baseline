# ARC Representation Expansion v3 — Frozen Holdout Result

**Registered verdict: DIRECTIONAL IMPROVEMENT.**

Holdout: 183 tasks / 201 test outputs; deterministic SHA1 split; public evaluation excluded.

| Endpoint | v2 baseline | v3 expanded grammar | v3 candidate oracle |
|---|---:|---:|---:|
| Output pass@1 | 4/201 (1.99%) | 5/201 (2.49%) | — |
| Output pass@2 | 4/201 (1.99%) | 5/201 (2.49%) | 5/201 (2.49%) |
| Whole-task pass@2 | 4/183 (2.19%) | 5/183 (2.73%) | 5/183 (2.73%) |
| Valid-candidate coverage | 4/201 (1.99%) | 5/201 (2.49%) | — |

## Paired output comparison

- v3-only wins: **1**
- v2-only wins: **0**
- exact two-sided p: **1.000000**

## Paired whole-task comparison

- v3-only wins: **1**
- v2-only wins: **0**
- exact two-sided p: **1.000000**

## Interpretation rule

The v3 grammar is promoted to the private-test submission artifact only if its frozen holdout pass@2 is directionally better than v2. A larger candidate set is not itself progress; paired solved outputs control the verdict.
