# How Do We Know an ARC Solution Is Right?

[![Results: corrected v2](https://img.shields.io/badge/results-corrected_v2-78e6c4.svg)](#headline-result)
[![Design: pre-specified](https://img.shields.io/badge/design-pre--specified-78e6c4.svg)](HYPOTHESIS-crossfold-v2.md)
[![Evidence: frozen results](https://img.shields.io/badge/evidence-frozen_results-2a3b55.svg)](results/)
[![License: MIT-0](https://img.shields.io/badge/license-MIT--0-2a3b55.svg)](LICENSE)

**Question:** if a synthesized program matches the demonstrations, how much evidence is that it will actually solve a held-out ARC task — and how much can better selection recover from an over-generated candidate set?

## Headline result

A stricter same-holdout analysis overturned the project's earlier optimistic calibration story.

- Demonstration-consistent programs reproduce a held-out demonstration only **32.8% / 50.8% / 63.4%** of the time at k=1/2/3.
- On ambiguous cases, minimum-description-length selection beats random by **+11.1 points** [95% CI +4.6, +17.9].
- The candidate oracle is only **+3.7 points** [ +0.1, +9.5 ] above MDL.
- The linked frozen solver remains **0/167 pass@2** on the verified set.

The contribution is the measurement and corrected selection analysis — **not** a competitive ARC solver.

## Proof / receipts

- **Paper:** [`ARC_Paper_Draft.pdf`](ARC_Paper_Draft.pdf)
- **Paper source:** [`PAPER.md`](PAPER.md)
- **Before-run specification:** [`HYPOTHESIS-crossfold-v2.md`](HYPOTHESIS-crossfold-v2.md)
- **Frozen machine-readable outputs:** [`results/`](results/)
- **Rebuild scripts:** `crossfold_analysis.py`, `crossfold_replication.py`, `leaderboard_stats.py`, `fig_v2.py`, `build_paper.py`
- **License:** [MIT-0](LICENSE), with third-party notices separated in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)

**Verification status:** corrected v2 code, frozen results, figures, and paper are public. The repository records that the same-holdout design was frozen before the first complete run; it does **not** claim an independently timestamped public preregistration unless separate evidence is produced. Scientific CI/tests are the next engineering-hardening step.

## Why the self-correction matters

The earlier prefix analysis suggested a much stronger calibration curve (~50%→87%→95%) and a large selection lever (~+24 points). The stricter same-holdout design was fixed before the first complete training/evaluation cross-fold run with a publish-regardless commitment, and it overturned both conclusions.

The corrected numbers are therefore the public result.

## Leaderboard uncertainty

The N=120 ARC-AGI-2 leaderboard is noisy at the scale of small frontier gaps: roughly ±9-point confidence intervals, a top-two gap with p=0.16 in this analysis, and an estimated ~1,566 tasks required to resolve a 5-point gap at 80% power under the modeled assumptions.

## Reproduce

CPU-only; intended to run in minutes once the public ARC-AGI-2 corpus is available locally.

```bash
pip install numpy pandas scipy matplotlib markdown playwright
git clone https://github.com/arcprize/ARC-AGI-2

python crossfold_analysis.py
python crossfold_replication.py
python leaderboard_stats.py
python fig_v2.py
python build_paper.py
```

Point the analysis scripts at your ARC-AGI-2 checkout as documented in the source.

## Repository map

```text
dsl.py                     over-generating CPU program-synthesis solver
crossfold_analysis.py      primary same-holdout calibration + selection analysis
crossfold_replication.py   one-shot public-evaluation replication
leaderboard_stats.py       confidence intervals, significance, and power analysis
fig_v2.py                  paper figures from committed results
build_paper.py             PAPER.md + figures -> ARC_Paper_Draft.pdf
HYPOTHESIS-crossfold-v2.md before-run specification for corrected analysis
PAPER.md                   paper source
results/                   frozen machine-readable outputs
```

## What this does not claim

- The linked solver is not competitive; it scores **0/167 pass@2** on the verified set.
- Demonstration consistency is not shown to be a reliable correctness certificate.
- MDL improves selection within this candidate generator; it does not solve candidate-generation failure.
- The public record supports a **pre-specified/frozen-before-run** corrected design, not an independently timestamped public preregistration claim.
- The N=120 leaderboard calculations are an uncertainty/power analysis under stated assumptions, not a claim that all ARC leaderboard comparisons are meaningless.

Data source: ARC-AGI-2 public corpus (1000 train / 120 evaluation), maintained by ARC Prize.

— Robert “Bobby” Morong, independent researcher
