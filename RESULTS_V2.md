# ARC Measurement Audit v2 — Resolved Findings Ledger

**Status:** full public-training run complete; pre-specified public-evaluation demonstration replication complete; frozen public-evaluation solver benchmark complete.  
**Canonical paper:** [`PAPER_V2.md`](PAPER_V2.md)  
**Registration:** [`HYPOTHESIS-crossfold-v2.md`](HYPOTHESIS-crossfold-v2.md), [`HYPOTHESIS-evidence-weighted-solver.md`](HYPOTHESIS-evidence-weighted-solver.md)

## Executive answer

The original 50% → 87% → 95% demonstration-consistency curve was mostly a **selection curve**, not a causal learning curve. Candidate-rich tasks were overweighted, later `k` values represented easier task subsets, and the held-out target changed with `k`.

The corrected full-corpus experiment shows a **precision–coverage tradeoff**:

- More demonstrations make surviving candidates more reliable.
- More demonstrations also make the current DSL much less likely to generate any candidate.
- End-to-end accuracy therefore falls slightly rather than rising.

## Test ledger

| # | Test | Result | Verdict |
|---:|---|---|---|
| 1 | Reproduce legacy program-pooled curve | 50.0% / 86.8% / 94.9% | NUMERICALLY REPRODUCED |
| 2 | Equal task weighting | 45.6% / 79.8% / 90.9%; wide task intervals | PROGRAM WEIGHTING MATTERS |
| 3 | Paired legacy `k=2−k=1` | −4.6 pp; CI spans zero | CROSS-SECTIONAL RISE NOT PAIRED |
| 4 | Registered same-target design | 1,000 tasks; 28,476 subset cells | COMPLETE |
| 5 | One-demo full-corpus coverage | 7.1% [5.7, 8.6] | DSL COVERAGE LOW |
| 6 | One-demo candidate reliability given generation | 32.8% [25.1, 40.4] | CONDITIONAL SIGNAL MODEST |
| 7 | Two-demo candidate reliability given generation | 50.8% [37.8, 64.0] | PRECISION RISES |
| 8 | Primary same-target coverage effect | −3.7 pp [−4.6, −2.7] | COVERAGE COLLAPSES |
| 9 | Primary same-target consensus-yield effect | **−0.4 pp [−0.6, −0.2]** | **REGISTERED NEGATIVE EFFECT** |
| 10 | MDL-vote vs random on ambiguous cells | +11.1 pp [4.6, 17.9] | MDL SUPPORTED |
| 11 | Oracle vs MDL-vote | +3.7 pp [0.1, 9.5] | “MDL=ORACLE” REFUTED |
| 12 | Public-evaluation demonstration replication | k=1 coverage 1.0%; yield 0.1%; negative effect direction repeats | HARDNESS WALL CONFIRMED |
| 13 | Frozen evidence-weighted selector | 0/167 pass@1 and 0/167 pass@2, same as baseline | NO SOLVER GAIN |
| 14 | Public-evaluation score denominator | 120 tasks, **167 test outputs** | LEGACY N=120 AUDIT WRONG |
| 15 | Leaderboard comparison requirement | paired per-output outcomes + task clustering required | AGGREGATE SCORE INSUFFICIENT |

## Full-corpus training results

| fitted demonstrations | coverage | consensus yield | oracle yield | conditional candidate reliability |
|---:|---:|---:|---:|---:|
| 1 | 7.1% [5.7, 8.6] | 3.3% [2.3, 4.4] | 3.4% [2.4, 4.6] | 32.8% [25.1, 40.4] |
| 2 | 3.8% [2.7, 5.1] | 3.0% [1.9, 4.2] | 3.0% [1.9, 4.2] | 50.8% [37.8, 64.0] |
| 3 | 4.4% [2.1, 6.9] | 3.8% [1.7, 6.3] | 3.8% [1.7, 6.3] | 63.4% [39.5, 86.0] |

The marginal rows use different task populations. The registered same-target `k=2−k=1` comparison is primary.

## Selection on genuine ambiguity

Across 224 ambiguous subset cells from 41 tasks:

| rule | task-weighted accuracy |
|---|---:|
| Random consistent candidate | 18.9% [10.8, 27.8] |
| Legacy first-shortest | 31.2% [18.5, 44.8] |
| Tie-aware MDL vote | 30.0% [17.7, 43.1] |
| Consensus | 27.4% [15.6, 40.0] |
| Candidate oracle | 33.7% [20.5, 47.6] |

MDL is useful, but the oracle gap is non-zero and statistically resolved under the task-cluster bootstrap.

## Public-evaluation replication

The same analysis was frozen and run once on public evaluation demonstration pairs:

- 120 tasks;
- 1,757 subset cells;
- only 18 covered cells;
- k=1 coverage 1.0% [0.2, 2.2];
- k=1 consensus yield 0.1% [0.0, 0.4];
- k=2 coverage 0.2% [0.0, 0.6];
- k=2 consensus yield 0.0%;
- registered end-to-end effects all repeat in the negative direction.

## Frozen contest-facing result

Program-family reliability priors were learned from the 1,000 public training tasks and frozen. On 167 public-evaluation test outputs:

| method | pass@1 | pass@2 |
|---|---:|---:|
| Released vote + MDL baseline | 0/167 | 0/167 |
| Pure MDL | 0/167 | 0/167 |
| Evidence-weighted selector | 0/167 | 0/167 |

This is a negative algorithmic result. The current bottleneck is hypothesis coverage, not tie-breaking among generated hypotheses.

## Claims withdrawn

- “A demonstration-consistent program is exactly a coin flip after one example.”
- “Reliability rises to 95% because additional demonstrations teach the solver the rule.”
- “MDL matches the oracle ceiling.”
- “The 120-task leaderboard is 120 Bernoulli trials.”
- “Selection is the main obstacle for this DSL.”

## Claims retained in corrected form

- Demonstration consistency is an imperfect generalization signal.
- Candidate programs within a task are dependent and must not be treated as independent benchmark observations.
- MDL is a useful selection prior under ambiguity.
- ARC score differences require uncertainty and paired outcomes.
- The decisive engineering frontier for this solver is richer hypothesis generation plus coverage-aware routing.

## Machine-readable record

- `results/task_weighted_calibration.json`
- `results/crossfold/training_audit/crossfold_calibration.json`
- `results/crossfold/evaluation_audit/crossfold_calibration.json`
- `results/crossfold/crossfold_replication.json`
- `results/solver/solver_v2_benchmark.json`
- `results/leaderboard_measurement_v2.json` (generated by the updated workflow)
