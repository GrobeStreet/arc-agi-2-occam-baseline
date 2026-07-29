# ARC Elephant Hunt Takeover — 2026

**Owner:** Robert Morong / GrobeStreet  
**Status date:** 2026-07-29  
**Purpose:** Replace stale, contradictory contest claims with one auditable operating plan for the ARC-AGI-2 competition and Paper Prize.

## 1. Current verified state

### ARC-AGI-2 competition

- Corrected frozen-v3 Kaggle submission: `55057282`
- Kernel: `robertmorong/grobestreet-arc-frozen-v3-cycle-001`, version 10
- Public score: **0.00**
- Displayed public rank at terminal observation: **1291** in a field of approximately 1290 teams; tied zero-score ordering is not scientifically meaningful
- Cycle 001 verdict: **SCORED_NULL**
- Official schema validation: 240 tasks / 259 test outputs, exact sample and hidden-challenge task-ID match

The zero score is a valid model result. It is not a packaging error. Version 8 had a routing error; version 10 repaired only the routing and then scored zero.

### Paper Prize

- A canonical paper, generated PDF, code, and reproducibility record exist in this repository.
- A real Kaggle code submission now exists, satisfying the requirement that a paper describe a working entry.
- **Paper Track submission is not yet verified.** No submission confirmation is preserved in this repository or in the connected email search. Until a Kaggle writeup URL or confirmation is recorded, the official status is **READY, NOT VERIFIED SUBMITTED**.

### Important dates

- ARC competition submissions due: **2026-11-02**
- Paper submissions due: **2026-11-08**
- Results announced: **2026-12-04**

## 2. Strategic verdict

The symbolic DSL is closed as a standalone contest solver. Its best registered public-evaluation and hidden-test outcomes were both zero. More hand-authored primitives or selector tuning are not authorized as the primary path.

The project has two distinct assets:

1. **Research asset:** a strong self-correction and measurement paper showing how candidate weighting, moving targets, coverage, selection, and confidence can distort ARC conclusions.
2. **Engineering asset:** a reproducible Kaggle pipeline and measurement harness that can evaluate any new solver by coverage, oracle rate, selection regret, pass@1, pass@2, runtime, and uncertainty.

The highest expected-value strategy is therefore:

- **Paper Prize first:** maximize rubric quality and eligibility.
- **Solver Cycle 002 second:** replace the narrow DSL with a trained recursive/neural generator and retain the DSL only as a specialist second-attempt source.

## 3. Weighted ARC priorities

| Priority | Weight | Why it matters | Exit criterion |
|---|---:|---|---|
| Verify and submit Paper Track writeup | **10.0** | $450K paper pool; code score need not be high; current work fits theory/completeness/novelty better than leaderboard accuracy | Kaggle writeup URL and submission confirmation recorded in repo |
| Fix contest eligibility and licensing | **9.7** | ARC 2026 requires submitter-authored code under CC0 or MIT-0; current repo used standard MIT | MIT-0 or CC0 applied to original code; third-party notices audited |
| Rewrite paper around the terminal hidden result | **9.5** | Current paper predates the valid 0.00 score and contains stale contest claims | Abstract/results/conclusion include score 0.00 and clearly separate measurement contribution from solver performance |
| Establish Cycle 002 neural baseline | **8.8** | Zero score proves representation is the bottleneck | Reproduce a permissively licensed recursive baseline on fixed validation data |
| Add synthetic ARC-GEN training | **8.2** | Strong ARC systems depend on broad generated task distributions | Generator-family-separated validation and provenance report |
| Build two-attempt neural-symbolic router | **7.8** | ARC awards either of two outputs; diversity is valuable | Fixed router beats best component on pass@2 without private feedback |
| Make one registered Cycle 002 Kaggle submission | **6.8** | Fresh aggregate endpoint after architecture freeze | One immutable score and complete open-source writeup |
| Continue hand-written DSL expansion | **1.5** | Prior cycles show near-zero coverage and no hidden transfer | Only permitted as a small specialist component, never the primary path |

## 4. Paper Prize rubric audit

The Paper Prize scores six categories equally.

| Rubric category | Current position | Takeover action |
|---|---|---|
| Accuracy | **Weak** — valid Kaggle score 0.00 | State it prominently; do not disguise it. Link future Cycle 002 only if completed before deadline. |
| Universality | **Promising** — task-clustered measurement and coverage decomposition generalize beyond this DSL | Add examples showing how the framework applies to neural candidate sets and selective prediction. |
| Progress | **Moderate** — identifies failure modes but does not itself approach 85% | Convert measurement findings into concrete solver-design implications and evaluate at least one stronger baseline. |
| Theory | **Strong** — precision–coverage tradeoff, dependence, underdetermination, selector regret | Tighten formal definitions and distinguish estimands. |
| Completeness | **Strong but stale** — extensive evidence, yet contest status and licensing are outdated | Reconcile every README/paper/status contradiction and include terminal hidden result. |
| Novelty | **Promising** — same-target all-subsets audit and publish-regardless correction record | Compare explicitly with prior ARC calibration, MDL, and test-time-training literature. |

## 5. Cycle 002 architecture

Cycle 002 is not “v3 plus more rules.” It is a portfolio with three candidate sources:

1. **Recursive neural solver**
   - Start from a permissively licensed Tiny Recursive Model-style implementation.
   - Train with task-family-separated validation.
   - Measure augmentation stability and iterative refinement.

2. **Synthetic-data generator**
   - Use Apache-2.0 ARC-GEN and other license-compatible generators.
   - Hold out entire generator families and compositions.
   - Record every source, version, license, and generation seed.

3. **Frozen symbolic specialist**
   - Keep v3 unchanged as an interpretable exact-fit specialist.
   - It may provide one of two attempts only when it yields a validated, distinct candidate.

The final pass@2 router must be frozen before any new Kaggle score is observed.

## 6. Promotion gates before another private submission

A Cycle 002 Kaggle submission is allowed only after all gates pass:

1. Fixed task-family-separated validation split committed before model fitting.
2. Exact pass@1, pass@2, candidate-oracle coverage, selection regret, and runtime reported.
3. Repeated-seed or bootstrap uncertainty reported at the task level.
4. At least **5% pass@2** on a clean held-out development endpoint, or a clearly pre-specified alternative threshold justified before fitting.
5. Two-attempt portfolio beats every component alone on the same held-out tasks.
6. Kaggle notebook runs offline within the official resource limits.
7. Code, weights, data-generation scripts, licenses, and hashes are public.
8. One-shot private submission rule registered before upload.

## 7. Immediate operating sequence

### Phase A — eligibility and truth repair

- [ ] Change submitter-authored code license to MIT-0 or CC0.
- [ ] Create third-party license inventory.
- [ ] Update README and contest status to score 0.00 / SCORED_NULL.
- [ ] Verify whether a Paper Track writeup already exists.
- [ ] If absent, create and submit one early; tie-breaks favor earlier entry.

### Phase B — paper surgery

- [ ] Add the valid hidden score and Kaggle submission reference.
- [ ] Remove stale “unranked,” “blocked auth,” and “awaiting score” language.
- [ ] Do not present training-set accuracy as contest capability.
- [ ] Add a rubric-mapped executive summary.
- [ ] Add a limitations section explaining that the paper contributes measurement, not a competitive solver.

### Phase C — Cycle 002 build

- [ ] Complete and commit `HYPOTHESIS-representation-cycle-002.md`.
- [ ] Reproduce a recursive neural baseline.
- [ ] Add ARC-GEN synthetic data with held-out generator families.
- [ ] Train and evaluate the neural model.
- [ ] Build and freeze a diverse two-attempt router.
- [ ] Submit once only after promotion gates pass.

## 8. Claim boundaries

- The valid Cycle 001 score is **0.00**.
- Rank among tied zero-score entries is not a meaningful performance measure.
- The paper is a candidate, not verified submitted, until a writeup URL or confirmation is recorded.
- The measurement results apply directly to the evaluated hypothesis library and experimental design; they do not prove that demonstrations generally reduce reasoning ability.
- No future model may use hidden task-level feedback. Aggregate Cycle 001 score may be cited only as a terminal outcome.

## 9. Definition of winning

There are two independent wins:

1. **Paper win:** submit an eligible, concise, honest paper that scores highly on theory, completeness, novelty, universality, and progress despite weak accuracy.
2. **Solver win:** build a registered Cycle 002 system that achieves a nonzero and materially improved Kaggle score without private feedback tuning.

Paper eligibility and submission are the first operational objective. Cycle 002 is the first engineering objective.