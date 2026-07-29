# How Do We Know an ARC Solution Is Right? — code & data release

Reproduces every number and figure in the paper (`ARC_Paper_Draft.pdf`). CPU-only, minutes.
Our own code is released under **MIT-0** (see `LICENSE`); third-party deps under their own
permissive licenses (see `THIRD_PARTY_NOTICES.md`).

## What the paper shows
1. **A free, model-agnostic selection lever.** Among a solver's demonstration-consistent
   candidates, minimum-description-length (Occam) selection recovers ~all of the oracle
   ceiling (59.4% vs 62.5%, +23.6 pts over random) on ambiguous cases.
2. **The acceptance signal is miscalibrated:** a program consistent with 1 demonstration
   generalizes only 45.6% of the time (coin flip), 87.6% at two, 97.9% at three.
3. **The N=120 leaderboard is mostly noise:** ±~9-pt CIs, top-two gap p=0.16 (n.s.), and
   ~1,566 tasks needed to resolve a 5-pt frontier gap at 80% power.

## Setup
    pip install numpy pandas scipy matplotlib markdown playwright
    git clone https://github.com/arcprize/ARC-AGI-2   # edit the /home/claude path in scripts to your checkout

## Reproduce
    python ablate.py training        # calibration curve + selection -> ablate_*_training.parquet
    python make_calib_figs.py        # fig1_calibration.png, fig_selection.png
    python leaderboard_stats.py      # §4.3 CIs + significance + power -> fig_leaderboard_ci.png
    python build_paper.py            # rebuild ARC_Paper_Draft.pdf from PAPER.md + figures

## Files
    dsl.py                 over-generating CPU program-synthesis solver (excludes degenerate hypotheses)
    ablate.py              demonstration-ablation calibration + selection experiment
    leaderboard_stats.py   §4.3 leaderboard statistics + figure
    make_calib_figs.py     calibration + selection figures
    build_paper.py         PAPER.md (+figures) -> PDF
    PAPER.md               paper source ; ARC_Paper_Draft.pdf built output
    ablate_*_training_v2.parquet   frozen experiment outputs

## Linked Kaggle submission
The linked ARC-AGI-2 code submission scores **0.00 (0 of 167 pass@2)** on the verified set —
a symbolic library rarely contains any correct program for these tasks. The contribution is
the measurement and the free selection lever, not the solver.

Data: ARC-AGI-2 public corpus (1000 train / 120 eval), github.com/arcprize/ARC-AGI-2
