# When a Calibration Curve Is a Selection Curve
## Task- and Target-Controlled Measurement of Demonstration Value in ARC-AGI-2

**Robert Morong** · Independent research · ARC Prize 2026 Paper Track candidate  
AI-assisted implementation; all numerical claims reproducible from released code and public data

---

## Abstract

ARC solvers commonly retain candidate transformations that reproduce the available demonstrations and then select among the survivors. Our earlier draft appeared to show that a demonstration-consistent program generalizes to the next example 50.0% of the time after one demonstration, 86.8% after two, and 94.9% after three. We show that this progression was not a learning curve. It pooled correlated programs, overweighted candidate-rich tasks, changed the held-out target as the number of fitted demonstrations changed, and selected progressively easier task subsets. Equal task weighting lowers the sequential estimates to 45.6%, 79.8%, and 90.9%, but the corrected paired sequential contrast from one to two demonstrations is −4.6 percentage points with an interval spanning zero.

We then run a pre-specified same-target experiment over all 1,000 public ARC-AGI-2 training tasks. For every task and held-out demonstration, every feasible subset of the remaining demonstrations is fitted and evaluated against that fixed target. The analysis contains 28,476 subset cells and uses the ARC task as the sampling unit. With one fitted demonstration, the DSL produces at least one executable consistent candidate in 7.1% of subset opportunities; conditional candidate reliability is 32.8%, and end-to-end consensus yield is 3.3%. With two demonstrations, conditional reliability rises to 50.8%, but coverage falls to 3.8%. The primary same-target contrast is therefore negative: consensus yield changes by −0.4 percentage points (95% task-cluster interval −0.6 to −0.2), while coverage changes by −3.7 points (−4.6 to −2.7). More demonstrations improve the precision of surviving hypotheses but make this brittle DSL less likely to generate any hypothesis at all.

On 224 genuinely ambiguous subset cells across 41 tasks, tie-aware minimum-description-length selection reaches 30.0% task-weighted accuracy versus 18.9% for random candidate selection, an improvement of 11.1 points (95% interval 4.6 to 17.9). However, the candidate oracle reaches 33.7%; the oracle–MDL gap is 3.7 points (0.1 to 9.5), killing the earlier claim that MDL matches the oracle ceiling. A frozen one-shot replication on the 120 public evaluation tasks reproduces the negative direction and reveals a severe external-validity wall: one-demonstration coverage is only 1.0%, consensus yield is 0.1%, and the second demonstration again reduces end-to-end yield. A separately frozen evidence-weighted selector scores 0/167 public-evaluation test outputs under both pass@1 and pass@2, identical to the released baseline. Selection improvements cannot rescue a hypothesis library that does not contain the required transformations.

Finally, we correct the leaderboard audit. ARC-AGI-2 public evaluation contains 120 tasks but 167 test outputs, and competition scores are calculated over test outputs. The earlier N=120 binomial analysis used the wrong denominator and ignored output nesting within tasks. Proper ranking claims require per-output paired outcomes and task-clustered uncertainty.

The contribution is not a new state-of-the-art solver. It is a resolved measurement account: demonstration consistency is a precision–coverage tradeoff, MDL is useful but not oracle-equivalent, public-evaluation generalization is far weaker than training-task diagnostics suggest, and aggregate ARC scores are less interpretable than a single percentage implies.

---

## 1. Introduction

ARC-AGI asks whether a system can infer a novel transformation from a few input–output examples and reproduce it exactly on unseen grids. ARC-AGI-2 contains 1,000 public training tasks and 120 public evaluation tasks, with additional hidden evaluation sets for verified and competition testing. The 2026 ARC-AGI-2 competition evaluates exactly two proposed outputs per test input and targets 85% accuracy under compute constraints.

Most ARC systems perform two conceptually separate operations:

1. **Hypothesis generation:** produce transformations that fit the demonstrations.
2. **Hypothesis selection:** decide which surviving transformation or output to trust.

The field often treats “fits all demonstrations” as a high-confidence acceptance signal. But a few demonstrations can underdetermine the transformation. Multiple candidates may fit perfectly while disagreeing on the unseen output, and the way those candidates are counted can change the apparent confidence.

Our original paper attempted to quantify this problem with a small deterministic DSL. It reported a dramatic reliability increase from one to three demonstrations and a large advantage for the shortest consistent program. Adversarial review identified two levels of dependence that the original analysis did not resolve:

- candidates are nested within tasks and are not independent observations;
- increasing the demonstration count also changed the held-out target and represented task population.

The present paper replaces the original interpretation rather than defending it.

### Contributions

1. **Equal-task correction.** Candidate programs no longer determine the sampling weights.
2. **Same-target identification.** Each held-out target is fixed while the evidence subset changes.
3. **Full public-training census.** The corrected experiment runs across all 1,000 training tasks, including no-candidate failures.
4. **Precision–coverage decomposition.** Conditional candidate reliability is separated from end-to-end yield.
5. **Explicit selector audit.** Enumeration-order shortest, tie-aware MDL, consensus, and oracle are compared on ambiguous cells.
6. **One-shot public-evaluation replication.** The analysis is frozen before running on evaluation demonstration pairs.
7. **Frozen solver test.** A training-only evidence-weighted selector is evaluated once on all 167 public-evaluation test outputs.
8. **Leaderboard denominator correction.** Task count, output count, and dependence are distinguished.
9. **Publish-regardless record.** Negative results supersede the original paper wherever they conflict.

---

## 2. Why the original curve was not causal

### 2.1 Candidate-program weighting

The original result pooled all generated consistent programs. If one task generates one candidate and another generates one hundred, the second task receives one hundred times the weight. This estimates the reliability of the DSL’s candidate population, not the reliability experienced by an average ARC task.

Equal task weighting changes the sequential estimates:

| demonstrations fitted | program weighted | equal-task weighted | represented tasks | task-cluster 95% interval |
|---:|---:|---:|---:|---:|
| 1 | 50.0% | 45.6% | 67 | 34.2–57.1% |
| 2 | 86.8% | 79.8% | 31 | 64.5–92.7% |
| 3 | 94.9% | 90.9% | 11 | 72.7–100.0% |
| 4 | 100.0% | 100.0% | 2 | uninformative small sample |

The direction remains cross-sectionally visible, but it still does not identify the effect of another demonstration.

### 2.2 Changing task composition

A task can contribute at larger `k` only if it contains enough demonstrations and the DSL still generates a consistent candidate. The higher-`k` population is therefore selected for both task structure and solver compatibility.

### 2.3 Moving targets

The original experiment fitted `d0...d(k−1)` and tested `dk`. The target at `k=1` was not the target at `k=2`. Any change could reflect target difficulty, demonstration ordering, or redundancy rather than additional evidence.

### 2.4 Correlated hypotheses

Programs produced from one task share the same examples, primitives, and search process. Treating them as independent understates uncertainty. All primary intervals in this paper resample complete ARC tasks.

### 2.5 What the paired legacy data already implied

Among the 31 tasks represented at both `k=1` and `k=2`, the task-weighted sequential change is −4.6 points, with a 95% task-bootstrap interval of −17.6 to +6.6. The dramatic cross-sectional rise does not survive a same-task comparison even before target control is imposed.

---

## 3. Same-target full-corpus experiment

### 3.1 Pre-specified design

The design was recorded in `HYPOTHESIS-crossfold-v2.md` before the first complete training/evaluation run.

For every task with demonstrations `d0...d(D−1)`:

1. select a held-out demonstration `h`;
2. hold `h` fixed;
3. for each feasible `k`, enumerate every size-`k` subset of the remaining demonstrations;
4. construct the DSL candidate set from that subset;
5. retain candidates reproducing the fitted demonstrations exactly;
6. apply each candidate to the fixed held-out input;
7. record success, ambiguity, and selector outcomes;
8. repeat for every held-out demonstration.

Subset cells are averaged inside held-out targets, targets inside tasks, and tasks equally in the population estimate.

### 3.2 Empty candidate sets are failures

No-candidate cells remain in the denominator. Otherwise a stricter acceptance rule can look more reliable merely by abstaining on hard cases.

We distinguish:

- **coverage:** probability that at least one executable consistent candidate is generated;
- **conditional candidate reliability:** correctness among generated candidates;
- **selector accuracy conditional on coverage;**
- **end-to-end yield:** correct output probability including no-candidate failures;
- **oracle yield:** probability that any generated candidate is correct.

### 3.3 Selection rules

We evaluate:

- random consistent candidate;
- legacy first-enumerated shortest candidate;
- random candidate among equal minimum-complexity ties;
- tie-aware MDL vote;
- all-candidate consensus;
- candidate oracle.

The oracle is diagnostic, not deployable. Oracle minus selector is selection regret.

### 3.4 Data and computation

The training run covers:

- 1,000 ARC-AGI-2 public training tasks;
- 8,092 task/held-out/`k` folds;
- 28,476 demonstration-subset cells;
- 1,166 covered subset cells;
- 20,000 task-cluster bootstrap replicates for the full cross-fold analysis.

The official ARC-AGI-2 source commit is pinned in the results directory.

---

## 4. Full-corpus results

### 4.1 Marginal levels

| fitted demos | represented tasks | coverage | random yield | MDL-vote yield | consensus yield | oracle yield | candidate reliability given generation |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,000 | 7.1% [5.7, 8.6] | 3.1% [2.2, 4.2] | 3.4% [2.4, 4.5] | 3.3% [2.3, 4.4] | 3.4% [2.4, 4.6] | 32.8% [25.1, 40.4] |
| 2 | 842 | 3.8% [2.7, 5.1] | 3.0% [1.9, 4.1] | 3.0% [1.9, 4.2] | 3.0% [1.9, 4.2] | 3.0% [1.9, 4.2] | 50.8% [37.8, 64.0] |
| 3 | 267 | 4.4% [2.1, 6.9] | 3.8% [1.7, 6.2] | 3.8% [1.7, 6.3] | 3.8% [1.7, 6.3] | 3.8% [1.7, 6.3] | 63.4% [39.5, 86.0] |

These marginal rows mix different task populations and are descriptive. The causal comparison is the same-target contrast below.

### 4.2 Primary same-target result: another demonstration reduces end-to-end yield

The registered primary contrast is `k=2 − k=1` on identical held-out targets.

| metric | task-weighted change | 95% task-cluster interval | registered verdict |
|---|---:|---:|---|
| coverage | −3.7 pp | −4.6 to −2.7 | negative |
| random-candidate yield | −0.2 pp | −0.5 to −0.0 | negative/slight |
| legacy shortest yield | −0.4 pp | −0.7 to −0.2 | negative |
| tie-aware MDL-vote yield | −0.4 pp | −0.7 to −0.2 | negative |
| consensus yield | **−0.4 pp** | **−0.6 to −0.2** | **negative primary result** |
| oracle yield | −0.5 pp | −0.7 to −0.2 | negative |

The extra demonstration filters out many wrong candidates, raising conditional reliability among survivors. But the current DSL often cannot express a transformation that satisfies both fitted demonstrations. The coverage loss dominates the precision gain.

This is a **precision–coverage tradeoff**, not a monotone learning curve.

### 4.3 The third demonstration does not restore end-to-end performance

On the 267 tasks that can contribute to the `k=3 − k=2` contrast:

- coverage changes by −1.2 points (−1.8 to −0.7);
- random yield is effectively unchanged (−0.2 to +0.2);
- MDL and consensus yield change by approximately −0.1 points with intervals spanning zero.

The DSL becomes more selective, but additional evidence does not produce a meaningful end-to-end gain.

### 4.4 MDL is useful

Across 224 ambiguous subset cells from 41 tasks:

| selector | task-weighted accuracy | 95% task-cluster interval |
|---|---:|---:|
| random candidate | 18.9% | 10.8–27.8% |
| legacy first-shortest | 31.2% | 18.5–44.8% |
| random minimum-complexity tie | 30.4% | 18.3–43.5% |
| tie-aware MDL vote | 30.0% | 17.7–43.1% |
| all-candidate consensus | 27.4% | 15.6–40.0% |
| candidate oracle | 33.7% | 20.5–47.6% |

Tie-aware MDL beats random selection by **11.1 points** with a 95% interval of **4.6 to 17.9**, satisfying the registered support criterion.

### 4.5 MDL does not match the oracle

Oracle minus tie-aware MDL is **3.7 points**, with a 95% interval of **0.1 to 9.5**. The registered kill condition is met: reproducible candidate sets exist in which the oracle can succeed and MDL fails.

The corrected conclusion is:

> MDL is a useful prior over underdetermined candidates, but it is not an oracle and its apparent exact match in 17 legacy cells was a small-sample accident.

### 4.6 Consensus support is not calibrated probability

Candidate agreement increases as the candidate set narrows, but aliases and shared DSL omissions can produce unanimous wrong answers. Modal vote fraction is therefore a routing feature, not a calibrated probability of correctness. Semantic deduplication and external calibration remain necessary.

---

## 5. One-shot public-evaluation demonstration replication

The scripts and interpretation thresholds were frozen before running once on public evaluation demonstration pairs. Hidden/private data were not used.

The replication contains:

- 120 public evaluation tasks;
- 800 task/held-out/`k` folds;
- 1,757 demonstration-subset cells;
- only 18 covered cells overall.

### 5.1 Evaluation levels

| fitted demos | coverage | consensus yield | MDL-vote yield | conditional candidate reliability |
|---:|---:|---:|---:|---:|
| 1 | 1.0% [0.2, 2.2] | 0.1% [0.0, 0.4] | 0.1% [0.0, 0.4] | 12.5% [0.0, 50.0] |
| 2 | 0.2% [0.0, 0.6] | 0.0% | 0.0% | 0.0% |
| 3+ | 0.0% | 0.0% | 0.0% | not estimable |

### 5.2 Primary effect replicates in direction

For `k=2 − k=1`:

- coverage: −1.2 points (−2.6 to −0.2);
- consensus yield: −0.2 points (−0.6 to 0.0);
- MDL-vote yield: −0.2 points (−0.6 to 0.0);
- oracle yield: −0.2 points (−0.6 to 0.0).

The direction matches training for every registered end-to-end quantity. The much lower marginal levels expose the extent to which training-task engagement overstates external capability.

---

## 6. Frozen contest-facing selector experiment

The measurement findings suggested a contest-facing hypothesis: candidate outputs should be weighted by demonstrated predictive reliability, not by the number of syntactic programs that emit them.

We therefore learned equal-task reliability priors for 136 DSL program families using only public training demonstration folds. Those priors were frozen and combined with task-local leave-one-demonstration-out evidence. The selector was then evaluated once on all 167 public-evaluation test outputs.

| method | pass@1 | pass@2 | tasks with any pass@2 |
|---|---:|---:|---:|
| released vote + MDL baseline | 0/167 | 0/167 | 0 |
| pure MDL | 0/167 | 0/167 | 0 |
| evidence-weighted family selector | 0/167 | 0/167 | 0 |

The exact paired comparisons contain no discordant outcomes. The registered promotion criterion is not met.

This is not evidence that selection research is useless. It is evidence that **selection cannot recover an absent hypothesis**. The primary contest bottleneck for this system is representation and hypothesis generation.

### Contest implications

A more competitive hybrid should:

1. use the symbolic module as a cheap exact verifier and source of interpretable hypotheses;
2. route uncovered tasks to a richer code-generating or neural solver;
3. preserve two semantically distinct attempts;
4. score generated programs by held-out predictive evidence;
5. treat candidate-set coverage and selection regret as separate engineering metrics.

The released evidence-weighted selector remains a reproducible negative result, not a promoted leaderboard method.

---

## 7. Correcting the leaderboard audit

The original paper treated an ARC-AGI-2 score as 120 Bernoulli trials because the public evaluation set contains 120 tasks. Direct inspection of the official corpus shows:

- 120 public evaluation tasks;
- **167 public evaluation test outputs**;
- multiple outputs nested within some tasks.

The 2026 competition scoring description averages success over task test outputs. Therefore:

1. `N=120` is not the score denominator for public evaluation percentages;
2. an output-level binomial approximation uses `N=167` on this corpus;
3. outputs within a task are dependent, so task-clustered uncertainty is preferable;
4. system comparisons require paired per-output outcomes, not independent two-proportion tests on headline percentages;
5. private and semi-private sets require their own exact denominators and outcome tables.

At 50% and `N=167`, the output-level Wilson 95% interval is approximately 42.5–57.5%, still broad enough that small leaderboard differences are not precisely resolved. Roughly 1,565 independent outcomes are needed to detect a five-point gap near 50% at 80% power under the unpaired approximation. Task clustering can reduce the effective sample further.

The original high-level warning survives, but the original `N=120` calculation is superseded.

---

## 8. What is established, refuted, and open

### Established

- Program-pooled and task-weighted reliability are different estimands.
- The original 50→87→95 progression was dominated by selection and target changes.
- For this DSL, more fitted demonstrations improve conditional reliability but reduce coverage.
- The registered primary end-to-end effect is negative on training and replicates in direction on public evaluation demonstrations.
- MDL materially improves selection over random candidates on ambiguous sets.
- Public evaluation is much harder for this DSL than public training.
- The evidence-weighted selector does not improve actual public-evaluation pass@1 or pass@2.
- Public evaluation contains 167 test outputs, not 120 independent score trials.

### Refuted

- “A consistent program is exactly a coin flip after one example” as a universal ARC statement.
- “Reliability rises from 50% to 95% because the solver learned from more demonstrations.”
- “MDL matches the oracle ceiling.”
- “Candidate selection is the main bottleneck for this solver.”
- “The ARC-AGI-2 leaderboard is literally N=120 Bernoulli trials.”

### Open

- Whether the same precision–coverage pattern holds for richer program synthesizers and LLM-generated code.
- Whether semantic pass@2 remains near the candidate oracle when candidate diversity grows.
- How best to expand hypothesis coverage without introducing an overwhelming wrong-hypothesis burden.
- How well task-local held-out evidence transfers to private evaluation tasks for systems with meaningful coverage.
- How benchmark organizers should publish paired, clustered uncertainty without exposing protected evaluation data.

---

## 9. Reporting standard for ARC candidate systems

ARC papers that generate multiple hypotheses should report:

1. the independent sampling unit;
2. task coverage and no-candidate rate;
3. conditional candidate reliability;
4. end-to-end pass@1 and pass@2 yield;
5. distinct semantic output count, not only program count;
6. the exact selection and tie-breaking rule;
7. candidate oracle and selection regret;
8. task-clustered uncertainty;
9. whether comparison targets are held fixed;
10. whether scores are over tasks or test outputs;
11. paired outcome comparisons between systems;
12. public-evaluation tuning history and verification status.

---

## 10. Limitations

The DSL is deliberately small. The negative end-to-end evidence-count effect is a property of this hypothesis library and search procedure, not a theorem that demonstrations generally hurt ARC systems.

Cross-fold demonstrations are internal targets. They provide a controlled model-selection diagnostic but are not substitutes for hidden test performance. The severe public-evaluation drop is informative precisely because it shows how little training engagement transfers.

The public evaluation split is observable and can be overfit. Our evaluation experiments were pre-specified and run once; future methodological changes must be labeled as post-evaluation development and require a new hidden test for confirmation.

The leaderboard uncertainty section cannot produce a correct paired comparison from aggregate percentages alone. That is the finding: the outcome table is required.

Finally, the current system is not competitive on ARC-AGI-2. Its value is as a measurement instrument and negative-result baseline.

---

## 11. Conclusion

The original analysis found a real numerical pattern and attached the wrong causal story to it. After equal-task weighting, fixed targets, full-corpus execution, and one-shot replication, the pattern resolves into a precision–coverage tradeoff.

Another demonstration makes surviving candidates more trustworthy, but this DSL often stops producing candidates altogether. End-to-end performance therefore declines. MDL helps when multiple hypotheses survive, but it does not equal the oracle. Evidence weighting cannot improve a zero-coverage hypothesis library on the hard evaluation set. And a leaderboard percentage cannot be assigned uncertainty until its scoring unit and dependence structure are specified correctly.

The research frontier exposed by this audit is not better rhetoric around confidence. It is better hypothesis generation, measured with coverage-aware, task-clustered, target-controlled evaluation.

---

## Reproducibility

Principal files:

- `task_clustered_analysis.py` — equal-task correction of the legacy prefix experiment;
- `crossfold_ablation.py` — complete same-target subset experiment;
- `crossfold_analysis.py` — task-clustered coverage, yield, ambiguity, and selector analysis;
- `crossfold_replication.py` — frozen training-to-evaluation comparison;
- `leaderboard_stats_v2.py` — scoring-unit and denominator correction;
- `evidence_weighted_solver.py` — training-only family priors and frozen selector;
- `benchmark_solver_v2.py` — public-evaluation paired benchmark and submission artifact;
- `HYPOTHESIS-crossfold-v2.md` and `HYPOTHESIS-evidence-weighted-solver.md` — pre-specified interpretation rules;
- `results/` — machine-readable outputs and exact data commit.

All authored code is intended for permissive open-source release. ARC-AGI-2 data retain their original license.

## References

1. F. Chollet, “On the Measure of Intelligence,” arXiv:1911.01547, 2019.
2. F. Chollet, M. Knoop, G. Kamradt, B. Landers, H. Pinkard, “ARC-AGI-2: A New Challenge for Frontier AI Reasoning Systems,” arXiv:2505.11831, 2025.
3. ARC Prize Foundation, “ARC Prize 2026 — ARC-AGI-2 Competition,” 2026.
4. C. Guo, G. Pleiss, Y. Sun, K. Q. Weinberger, “On Calibration of Modern Neural Networks,” ICML, 2017.
5. E. B. Wilson, “Probable Inference, the Law of Succession, and Statistical Inference,” JASA, 1927.
6. Q. McNemar, “Note on the Sampling Error of the Difference Between Correlated Proportions or Percentages,” Psychometrika, 1947.
