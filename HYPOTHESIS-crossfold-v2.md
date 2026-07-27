# Registered Hypothesis — Same-Holdout ARC Calibration v2

**Registered 2026-07-27 before the first complete training/evaluation cross-fold run.**

## Why this test exists

The original experiment fitted demonstrations `d0..d{k-1}` and tested the next demonstration `dk`. As `k` increased, the held-out target changed, the represented task set shrank, and candidate-rich tasks received greater weight. Therefore the published 50% → 87% → 95% progression did not isolate the effect of adding demonstrations.

## Design

For every task and each held-out demonstration `h`:

1. hold `h` fixed;
2. enumerate every subset of size `k` from the remaining demonstrations;
3. generate the DSL candidate programs from that subset;
4. retain exact demonstration-consistent programs;
5. evaluate candidates on the same held-out target `h`;
6. repeat for every feasible `k`.

Every subset cell is recorded, including cases where no candidate survives. The ARC task is the independent sampling unit. Subsets and held-out demonstrations are averaged within task before task-cluster bootstrap resampling.

## Primary quantities

1. **Coverage:** probability that the DSL produces an executable demonstration-consistent candidate.
2. **Consensus yield:** end-to-end probability that consensus returns the held-out output, counting no-candidate cells as failures.
3. **Tie-aware MDL-vote yield:** end-to-end probability for minimum-description-length selection after explicitly resolving equal-complexity ties by vote.
4. **Candidate reliability:** correctness rate among generated demonstration-consistent programs, conditional on candidate generation.
5. **Oracle yield:** probability that at least one generated candidate is correct.

## Primary same-target contrast

The primary contrast is `k=2 minus k=1` on the same task and held-out target. Differences are averaged across held-out targets within task, then tasks are bootstrapped.

- **Positive evidence-count effect:** the 95% task-cluster interval for consensus yield is entirely above zero.
- **Inconclusive:** the interval includes zero.
- **Negative effect:** the interval is entirely below zero.

Coverage and candidate reliability are reported separately so an apparent reliability gain cannot hide loss of solver coverage.

## Selection hypothesis

On ambiguous candidate sets:

- MDL-vote is supported only if its task-weighted improvement over random candidate selection has a 95% interval entirely above zero.
- The exact claim that MDL “matches the oracle ceiling” is killed by any reproducible ambiguous cell in which the oracle can succeed and MDL-vote fails.
- Enumeration-order `legacy_shortest` is not considered a principled MDL rule when equal-complexity programs disagree; it is retained only as a diagnostic.

## Confidence hypothesis

Consensus vote fraction is treated as a proposed confidence measure, not assumed calibrated. Reliability bins, task-weighted Brier score, and confidence-minus-accuracy gaps are reported. A monotone pattern alone is not called calibration.

## One-shot replication policy

Development and debugging use only the 1,000 public training tasks. After the scripts and interpretation rules above are frozen, the same cross-fold program may run once on the 120 public evaluation tasks using their demonstration pairs only. No test-output score or evaluation result may be used to modify the analysis. Any subsequent change requires a new version and must label the evaluation result as previously observed.

## Publish-regardless commitment

All results are retained whether they strengthen, weaken, or reverse the original paper. The paper’s abstract and claims must be revised to the same-target, task-weighted results before submission.
