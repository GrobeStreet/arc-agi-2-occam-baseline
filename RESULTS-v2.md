# ARC Measurement Audit v2 — Results Ledger

**Canonical machine-readable sources:**

- `results/task_weighted_calibration.json`
- `results/crossfold/training_audit/crossfold_calibration.json`
- `results/crossfold/evaluation_audit/crossfold_calibration.json`
- `results/crossfold/crossfold_replication.json`
- `results/solver/solver_v2_benchmark.json`

This ledger summarizes those files. The JSON files control if any prose and data diverge.

---

## Test 1 — Equal-task correction of the legacy prefix experiment

| k fitted | Program-weighted | Task-weighted | 95% task-cluster CI | Tasks |
|---:|---:|---:|---:|---:|
| 1 | 50.0% | **45.5%** | [34.1, 57.0] | 67 |
| 2 | 86.8% | **79.8%** | [64.7, 92.6] | 31 |
| 3 | 94.9% | **90.9%** | [72.7, 100] | 11 |

**Verdict:** candidate-rich tasks inflated the marginal rates modestly. The much larger interpretation problem remains: k changes the task population and the held-out target. The marginal curve is descriptive, not an identified demonstration-count effect.

---

## Test 2 — Complete same-target training experiment

**Data:** 1,000 tasks · 28,476 subset cells · 8,092 task/holdout/k folds · 20,000 task-cluster bootstrap replicates.

| k | Coverage | Candidate reliability | Consensus yield | Oracle yield |
|---:|---:|---:|---:|---:|
| 1 | **7.10%** [5.71, 8.58] | **32.8%** [25.1, 40.4] | **3.31%** [2.31, 4.40] | **3.44%** [2.41, 4.55] |
| 2 | **3.83%** [2.66, 5.08] | **50.8%** [37.8, 64.0] | **3.03%** [1.94, 4.22] | **3.03%** [1.94, 4.22] |

**Same task and same held-out target, k=2 minus k=1:**

| Quantity | Difference | 95% task-cluster CI |
|---|---:|---:|
| Coverage | **−3.66 pp** | [−4.63, −2.74] |
| Random-selection yield | **−0.25 pp** | [−0.50, −0.00] |
| Legacy shortest yield | **−0.43 pp** | [−0.68, −0.21] |
| Tie-aware MDL yield | **−0.42 pp** | [−0.66, −0.20] |
| Consensus yield | **−0.37 pp** | [−0.60, −0.17] |
| Candidate-oracle yield | **−0.46 pp** | [−0.70, −0.25] |

**Registered verdict:** NEGATIVE. The pre-specified positive consensus-yield condition is not met; the interval lies below zero.

**Interpretation:** the second demonstration increases the purity of the rare candidates that survive but reduces the DSL's coverage enough to lower end-to-end yield. This is a representation failure, not evidence that demonstrations are generally harmful.

---

## Test 3 — One-shot public-evaluation replication

**Data:** 120 tasks · 1,757 subset cells · 800 folds · 18 covered cells.

| k | Coverage | Consensus yield | Candidate reliability |
|---:|---:|---:|---:|
| 1 | **1.03%** [0.17, 2.25] | **0.139%** [0, 0.417] | 12.5% [0, 50.0] |
| 2 | **0.194%** [0, 0.581] | **0%** | **0%** |

**Same-target k=2 minus k=1:**

- coverage: **−1.24 pp [−2.64, −0.23]**;
- consensus yield: **−0.194 pp [−0.581, 0]**;
- candidate-oracle yield: **−0.194 pp [−0.581, 0]**.

**Verdict:** the negative coverage/yield direction replicates. Evaluation is substantially harder for this grammar.

---

## Test 4 — Training-to-evaluation shift

At k=1:

- evaluation coverage is **−6.07 pp** below training [−7.84, −4.26];
- evaluation consensus yield is **−3.17 pp** below training [−4.28, −2.14].

At k=2:

- evaluation coverage is **−3.63 pp** below training [−4.93, −2.39];
- evaluation consensus yield is **−3.03 pp** below training [−4.22, −1.94].

**Verdict:** the public evaluation distribution presents a measurable representation and difficulty shift even before private leaderboard scoring.

---

## Test 5 — Selection on ambiguous candidate sets

**Data:** 224 ambiguous subset cells across 41 training tasks.

| Rule | Task-weighted accuracy | 95% task CI |
|---|---:|---:|
| Random candidate | **18.9%** | [10.8, 27.8] |
| Legacy first-shortest | **31.2%** | [18.5, 44.8] |
| Random minimum-complexity tie | **30.4%** | [18.3, 43.5] |
| Tie-aware MDL vote | **30.0%** | [17.7, 43.1] |
| All-candidate consensus | **27.4%** | [15.6, 40.0] |
| Candidate oracle | **33.7%** | [20.5, 47.6] |

Contrasts:

- MDL vote minus random: **+11.1 pp [4.6, 17.9]**;
- consensus minus random: **+8.5 pp [2.6, 14.8]**;
- oracle minus MDL vote: **+3.65 pp [0.13, 9.47]**.

**Verdict:** description length is a useful prior. The exact “shortest matches oracle” claim is REFUTED.

---

## Test 6 — Candidate agreement as confidence

**Data:** 1,166 covered cells across 107 tasks.

- task-weighted Brier score: **0.542 [0.465, 0.618]**;
- mean absolute confidence-error gap: **59.5 pp [52.1, 66.7]**;
- at modal vote fraction exactly 1.0, task-weighted accuracy: **37.8% [28.8, 47.0]**.

**Verdict:** candidate agreement is not calibrated confidence. The original calibration claim is REFUTED.

---

## Test 7 — Evidence-weighted selector

**Training:** family priors learned from 1,000 training tasks across 136 normalized program families.

**Frozen public-evaluation benchmark:** 120 tasks, 167 test outputs.

| Method | pass@1 | pass@2 |
|---|---:|---:|
| Released vote + MDL baseline | 0/167 | 0/167 |
| Pure MDL | 0/167 | 0/167 |
| Evidence-weighted family selector | 0/167 | 0/167 |

All paired discordant counts are zero; exact paired p-values are 1.

**Verdict:** NULL. Better selection cannot rescue a grammar that rarely generates a viable evaluation hypothesis. The contest frontier is candidate representation, not another tie-break rule over this DSL.

---

## Consolidated conclusion

The v2 investigation overturns the cleanest parts of the first draft while preserving its central methodological premise.

**Established:**

1. Few demonstrations underdetermine transformations inside this DSL.
2. Candidate-rich tasks must not receive extra inferential weight.
3. Added evidence can increase conditional purity while reducing system yield when the hypothesis class is misspecified.
4. MDL improves selection but does not attain the available candidate oracle.
5. Candidate unanimity can be confidently wrong.
6. ARC evaluation results require coverage, calibration, paired comparisons, and task-level uncertainty—not one aggregate score.

**Not established:**

- that demonstrations generally harm reasoning;
- that this diagnostic DSL is competitive;
- that public evaluation results equal private Kaggle performance;
- that the N=120 benchmark should be replaced rather than reported with uncertainty.

**Next research frontier:** richer object-centric, compositional, neural, or test-time-adapted candidate generation evaluated through this same measurement harness.
