# Registered Hypothesis — Evidence-Weighted ARC Solver v2

**Registered 2026-07-27 before the first public-evaluation scoring run.**

## Motivation

The released baseline counts each demonstration-consistent DSL program as one vote. This can confuse syntactic abundance with evidence: a transformation family that appears many times under superficial parameterizations can dominate a prediction even if it generalizes poorly.

The v2 solver converts the measurement audit into a working selection algorithm:

1. learn program-family reliability priors from public **training** demonstrations using same-holdout cross-validation;
2. update those priors with same-task leave-one-demonstration-out evidence;
3. deduplicate support so one normalized family contributes at most one vote to an output;
4. apply a description-length penalty;
5. prefer hypotheses consistent with every demonstration;
6. use near-consistent subset hypotheses only when no full-consistent output exists;
7. emit exactly two distinct outputs per test input.

## Frozen scoring rule

Before evaluation scoring, the following constants are frozen:

- global prior-strength pseudo-tasks: **8**;
- local prior strength: **3**;
- reliability exponent: **2**;
- demonstration-support exponent: **3**;
- complexity penalty: `1 + 0.30 × max(complexity − 1, 0)`;
- full-consistency bonus: **1.35**;
- output score: sum of one maximum weight per normalized family, divided by the square root of the number of supporting families.

No constant may be changed after observing public-evaluation outcomes under this version.

## Comparators

The frozen one-shot benchmark compares:

1. **Released baseline:** all-candidate consensus vote, tie-broken by minimum complexity.
2. **Pure MDL:** minimum output-supporting complexity, tie-broken by support within that complexity tier.
3. **Evidence-weighted v2:** the frozen rule above.

All family priors are learned exclusively from the 1,000 public training tasks. The 120 public evaluation tasks are scored once after freezing. This is not a Kaggle private-leaderboard claim.

## Primary endpoint

The primary endpoint is pass@2 per public-evaluation test output, matching the competition’s two-output rule. Paired differences use an exact McNemar/binomial test on identical test outputs.

- **Clear promotion:** evidence-weighted v2 has more evidence-only wins than comparator-only wins and exact two-sided `p < 0.05` against the released baseline.
- **Directional improvement:** more evidence-only wins but `p ≥ 0.05`; retain as promising, not established.
- **Null:** equal discordant wins or no change.
- **Failure:** fewer evidence-only wins than comparator-only wins; do not promote the selector.

Pass@1 and whole-task all-output success are secondary endpoints. Runtime and coverage are reported.

## Guardrails

- Evaluation outputs are not used for tuning, feature selection, or reranking.
- If the evaluation run fails because of code or format errors, only a mechanical repair that cannot depend on answer correctness is permitted under v2; otherwise the version is closed and a new preregistration is required.
- The measurement paper survives an algorithmic null result. A failed solver extension must be reported rather than hidden.
- Kaggle private and semi-private results remain distinct from this public, reproducible benchmark.

## Publish-regardless commitment

The benchmark artifacts, family priors, paired outcome table, and negative result—if any—will be committed to the repository unchanged in interpretation.
