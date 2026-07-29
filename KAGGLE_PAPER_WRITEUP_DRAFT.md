# When a Calibration Curve Is a Selection Curve
## Task- and Target-Controlled Measurement of Demonstration Value in ARC-AGI-2

**Author:** Robert Morong  
**Repository:** `GrobeStreet/arc-agi-2-occam-baseline`  
**Linked ARC-AGI-2 code submission:** `55057282`  
**Submission public score:** `0.00`

## Summary

ARC solvers often generate several hypotheses that reproduce the available demonstrations and then choose among the survivors. It is tempting to treat demonstration consistency, candidate agreement, or minimum description length as confidence that a hypothesis will generalize. This project tests those assumptions directly and documents a full correction cycle when the original interpretation did not survive stronger controls.

Our first analysis appeared to show that a demonstration-consistent program generalized 50.0% of the time after fitting one demonstration, 86.8% after two, and 94.9% after three. The pattern was numerically reproducible, but it was not a learning curve. It pooled correlated programs, overweighted tasks that generated many candidates, changed the held-out target as the number of fitted demonstrations increased, selected progressively easier task subsets, and omitted cases where the DSL produced no candidate.

We replace that design with a task-weighted, same-target, all-subsets experiment over the complete 1,000-task public training corpus. The result is a precision–coverage tradeoff rather than monotone learning: additional demonstrations make surviving hypotheses more reliable, but the limited hypothesis library stops producing candidates often enough that end-to-end performance declines.

## Method

For every ARC task and every demonstration selected as a held-out target:

1. hold the target fixed;
2. enumerate every feasible subset of the remaining demonstrations;
3. generate deterministic DSL programs from the fitted subset;
4. retain programs reproducing every fitted demonstration exactly;
5. apply all survivors to the fixed held-out input;
6. record candidate correctness, semantic output diversity, ambiguity, selector outcomes, and no-candidate failures;
7. average subsets within targets and targets within tasks;
8. resample complete ARC tasks for uncertainty.

The analysis separates:

- **coverage:** whether any executable consistent hypothesis is generated;
- **conditional candidate reliability:** correctness among generated hypotheses;
- **end-to-end yield:** correctness including no-candidate failures;
- **candidate oracle:** whether any generated candidate is correct;
- **selection regret:** candidate oracle minus the deployed selector;
- **semantic output diversity:** distinct outputs rather than syntactic program count.

We compare random candidate selection, enumeration-order shortest, random selection among minimum-complexity ties, tie-aware MDL voting, all-candidate consensus, and the candidate oracle.

## Main results

The full training analysis includes 28,476 demonstration-subset cells and uses the ARC task as the independent sampling unit.

| Quantity | One fitted demonstration | Two fitted demonstrations |
|---|---:|---:|
| Candidate coverage | 7.10% | 3.83% |
| Conditional candidate reliability | 32.8% | 50.8% |
| Consensus end-to-end yield | 3.31% | 3.03% |
| Candidate-oracle yield | 3.44% | 3.03% |

On identical tasks and held-out targets, the second demonstration changes:

- coverage by **−3.66 percentage points** (95% task-cluster interval −4.63 to −2.74);
- consensus yield by **−0.37 points** (−0.60 to −0.17);
- candidate-oracle yield by **−0.46 points** (−0.70 to −0.25).

The extra evidence removes many incorrect candidates, raising conditional precision, but the representation cannot express a surviving hypothesis for many tasks. The coverage loss dominates the precision gain.

## Selection and confidence

Across 224 genuinely ambiguous subset cells from 41 tasks:

| Selector | Task-weighted accuracy |
|---|---:|
| Random candidate | 18.9% |
| Enumeration-order shortest | 31.2% |
| Random minimum-complexity tie | 30.4% |
| Tie-aware MDL vote | 30.0% |
| Consensus | 27.4% |
| Candidate oracle | 33.7% |

Tie-aware MDL improves over random selection by **11.1 percentage points** with a task-cluster interval of 4.6 to 17.9. However, the candidate oracle exceeds MDL by **3.65 points** with an interval of 0.13 to 9.47. The earlier claim that shortest selection matched the oracle is therefore rejected.

Candidate agreement is also badly overconfident. The task-weighted Brier score is 0.542, the mean absolute confidence-error gap is 59.5 percentage points, and unanimous candidate sets are correct only 37.8% of the time. Agreement inside a shared, misspecified hypothesis class is not calibrated confidence.

## External validity and contest result

A one-shot public-evaluation replication shows a sharp transfer failure:

- one-demonstration coverage: 1.03%;
- one-demonstration consensus yield: 0.139%;
- released baseline, pure MDL, evidence-weighted selection, and representation v3: all 0/167 pass@2.

The first Kaggle code-kernel version had a mechanical input-routing failure and is not treated as model evidence. The repaired kernel kept the solver frozen, validated exact agreement with the official 240-task / 259-output hidden schema, and was submitted as `55057282`. It received a public score of **0.00**.

The hidden null closes the symbolic v3 cycle. The paper does not claim a competitive solver. It claims a resolved measurement framework and demonstrates why training-task candidate diagnostics can dramatically overstate hidden capability.

## What is new

1. **Task-weighted correction of candidate-population reliability.**
2. **Same-target all-subsets identification of demonstration-count effects.**
3. **No-candidate failures retained in the denominator.**
4. **Explicit decomposition into coverage, conditional reliability, end-to-end yield, oracle coverage, and selection regret.**
5. **Semantic output counting rather than syntactic program counting.**
6. **Task-clustered uncertainty for nested candidate systems.**
7. **A publish-regardless correction record extending through a valid hidden score of zero.**

## Implications

For ARC systems that generate multiple programs, samples, or candidate grids:

- report the task as the independent unit;
- hold comparison targets fixed;
- report candidate coverage and no-candidate rate;
- separate conditional candidate accuracy from end-to-end pass@1/pass@2;
- report distinct outputs, not only sample count;
- report the candidate oracle and selection regret;
- calibrate confidence against held-out targets;
- use paired per-output comparisons and task-clustered uncertainty;
- disclose public-evaluation tuning history and hidden-test status.

The engineering conclusion is direct: selection improvements cannot recover a transformation that the candidate generator never proposes. Future work must prioritize substantially broader learned representation and candidate generation.

## Reproducibility

The public repository contains:

- pre-specified hypotheses and kill conditions;
- complete public-training and public-evaluation result files;
- task-cluster bootstrap code;
- frozen Kaggle notebook construction and source hashes;
- the mechanical routing diagnosis and repaired submission record;
- the generated paper PDF;
- MIT-0 submitter-authored source code and third-party notices.

Key files:

- `PAPER_V2.md`
- `PAPER_CYCLE_001_ADDENDUM.md`
- `HYPOTHESIS-crossfold-v2.md`
- `HYPOTHESIS-evidence-weighted-solver.md`
- `HYPOTHESIS-private-v3-cycle-001.md`
- `results/crossfold/`
- `results/solver/`
- `results/private_cycle_001/`

## Limitations

The DSL is intentionally narrow, and its negative evidence-count effect is a property of this candidate library and search process—not a theorem that demonstrations generally reduce reasoning ability. Public evaluation is observable and can be overfit. The competition score is aggregate and supplies no task-level diagnostic information. The submitted solver scored 0.00 and is not competitive on ARC-AGI-2.

The value of the work is methodological: it demonstrates how an attractive ARC result can survive numerical reproduction while failing under the correct sampling unit, fixed targets, coverage-aware denominators, external replication, and hidden evaluation.

## Conclusion

The original analysis found a real numerical pattern and attached the wrong causal story. Stronger controls resolve it into a precision–coverage tradeoff. MDL is useful but not oracle-equivalent. Candidate unanimity can be confidently wrong. Public-training engagement does not guarantee evaluation coverage. A valid hidden score of 0.00 confirms that the symbolic hypothesis library is inadequate as a contest solver.

The lasting contribution is an auditable protocol for measuring candidate-generating ARC systems—and a public record of changing the conclusion when the better experiment demands it.