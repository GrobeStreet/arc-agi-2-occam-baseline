# Addendum: Terminal ARC-AGI-2 Competition Result

**Applies to:** `PAPER_V2.md` and `ARC_Measurement_Audit_v2.pdf`  
**Date:** 2026-07-29  
**Cycle:** Private Cycle 001

## Why this addendum exists

The canonical paper was written before the frozen representation-v3 system completed a valid ARC Prize 2026 Kaggle evaluation. This addendum records the terminal result and defines how it changes the interpretation of the paper.

## Submission history

### Version 8 — mechanical failure

The first code-kernel submission selected an already-public evaluation challenge file from the mounted inputs and produced predictions for the wrong task set. It emitted 120 task IDs / 172 test outputs, while the official competition schema required 240 task IDs / 259 outputs. Kaggle returned a scoring-format error.

This run is not a model-performance result.

### Version 10 — mechanically repaired, model frozen

The repair changed only the input-routing wrapper. The representation, candidate generation, ranking, fallbacks, and two-attempt policy remained frozen at source commit:

```text
70672f3aa62d089bfffd072461a5713caae1e099
```

Before submission, Version 10 verified:

- exactly 240 task IDs;
- exactly 259 test-output entries;
- exact task-ID equality with the official `sample_submission.json`;
- exact task-ID equality with the hidden challenge file;
- two valid grid attempts for every output.

The corrected submission was accepted as Kaggle submission:

```text
55057282
```

## Terminal outcome

| Field | Result |
|---|---:|
| Submission status | COMPLETE |
| Public score | **0.00** |
| Cycle verdict | **SCORED_NULL** |

The zero is a valid hidden-test outcome for the frozen solver. It is not attributable to the Version 8 routing defect.

## Consequences for the paper

The terminal result strengthens some of the paper's negative conclusions and narrows its positive claims.

### Strengthened

1. **Representation coverage is the dominant bottleneck.**
   The public-evaluation experiments already showed 0/167 pass@2 for the released baseline, pure MDL, the evidence-weighted selector, and representation v3. The valid hidden score of 0.00 confirms that selector refinements and the limited symbolic expansion did not create hidden-set transfer.

2. **Training-task diagnostics are not capability claims.**
   The earlier deterministic holdout result of 5/201 versus 4/201 was a small directional development result. It did not predict hidden competition performance.

3. **Publishing null results is scientifically necessary.**
   The project now contains a complete chain from an attractive original interpretation, through adversarial correction, public-evaluation failure, a mechanical submission error, a schema-correct repair, and a valid hidden null.

### Narrowed

1. The paper does not present a competitive ARC-AGI-2 solver.
2. The paper's contribution is measurement methodology: candidate dependence, same-target controls, coverage-aware denominators, selector regret, calibration, and uncertainty.
3. Any claim of progress toward the ARC accuracy target must come from a future registered solver cycle, not from the v3 symbolic system.

## Revised abstract sentence

The final paper should add the following sentence after the frozen public-evaluation result:

> A mechanically validated Kaggle submission of the same frozen solver, covering the official 240-task / 259-output hidden schema, received a public score of 0.00, confirming that the representation and selection gains observed on public training tasks did not transfer to the competition distribution.

## Revised conclusion sentence

The final paper should add:

> The valid hidden score of 0.00 closes the symbolic v3 cycle: the measurement framework remains useful, but the submitted hypothesis library is not a competitive ARC solver and future progress requires a substantially broader learned representation.

## Future-work boundary

Cycle 002 is separately registered in `HYPOTHESIS-representation-cycle-002.md`. It authorizes a trained recursive neural generator, license-compatible procedural synthetic data, the frozen symbolic solver as a specialist, and a fixed diverse two-attempt router. Private Cycle 001 feedback may not be converted into task-level tuning information.

## Citation and reproducibility record

- Submission: `55057282`
- Frozen source commit: `70672f3aa62d089bfffd072461a5713caae1e099`
- Terminal status: `PRIVATE_CYCLE_001_STATUS.md`
- Machine-readable records: `results/private_cycle_001/`
- Mechanical repair record: `PRIVATE_CYCLE_001_SCORING_REPAIR.md`

This addendum is controlling wherever an earlier paper or status document implies that the hidden score was pending, unavailable, or expected to be nonzero.