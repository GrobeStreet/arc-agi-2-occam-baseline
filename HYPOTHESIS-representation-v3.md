# Registered Hypothesis — Representation Expansion v3

**Registered 2026-07-27 before the first complete v3 holdout run.**

## Motivation

ARC Measurement Audit v2 found that selection is not the active bottleneck on the public evaluation split: the released vote baseline, pure MDL, and an evidence-weighted selector all scored 0/167 outputs because the diagnostic DSL almost never generated a viable candidate. V3 therefore changes the hypothesis class rather than tuning another selector.

## Data firewall

The 120 public evaluation tasks have already been observed under v2 and are not used to develop or tune v3.

V3 is evaluated once on a deterministic holdout carved from the 1,000 public training tasks:

```text
holdout(task_id) := int(SHA1(task_id)[0:8], 16) mod 5 == 0
```

All other training tasks are available for future training-only priors, but the first v3 benchmark below is a frozen hand-written grammar comparison and does not fit weights on the holdout.

The private Kaggle test set remains the fresh contest endpoint.

## Frozen representation expansion

V3 extends the released diagnostic grammar with generic, domain-level transformations chosen before the holdout result is observed:

1. gravity in all four directions;
2. removal of internal background-only rows and columns;
3. 4- and 8-connected component selection by size, uniqueness, and density;
4. color isolation, removal, and cropping;
5. hole filling, bounding-box filling, and bounding-box outlines;
6. separator-panel extraction and logical/color-preserving overlays;
7. border removal and symmetry completion;
8. row/column line connection and extension;
9. object-count encodings;
10. component packing and block-mode reduction;
11. a limited set of geometry compositions around the new parameter-free operations.

No task-specific rule may be added after viewing the holdout benchmark under version v3.0.

## Comparators

Every test output in the frozen holdout is scored with exactly two attempts:

1. **v2 released baseline:** consensus vote over the original DSL, complexity tie-break.
2. **v3 expanded grammar:** semantic output vote over the expanded DSL, complexity tie-break, two distinct outputs.
3. **v3 candidate oracle:** succeeds when either of the two ranked v3 outputs is correct; full candidate-set oracle is reported separately as a representation ceiling.

## Primary endpoint

Primary endpoint: output-level pass@2 on the deterministic training holdout.

Paired comparison uses the exact two-sided binomial/McNemar test on discordant outputs.

- **Clear promotion:** v3-only wins exceed v2-only wins and exact `p < 0.05`.
- **Directional improvement:** v3-only wins exceed v2-only wins but `p >= 0.05`.
- **Null:** discordant wins are equal or both solve the same outputs.
- **Failure:** v3-only wins are fewer than v2-only wins.

Secondary endpoints:

- whole-task all-output pass@2;
- valid-candidate coverage;
- full candidate-set oracle coverage;
- runtime per task;
- candidate count and distinct-output count.

## Promotion rule for the contest artifact

A private-test `kaggle_submission_v3.py` artifact may be created if v3 is directionally better on the frozen training holdout. The private submission must preserve the frozen grammar and ranking rule. Public evaluation may not be used to tune v3.

## Publish-regardless commitment

The complete holdout table and negative result, if any, will remain in the repository. A larger grammar that merely manufactures more wrong hypotheses will not be promoted.
