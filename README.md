# How Do We Know an ARC Solution Is Right? — code & data release

Reproduces every number and figure in the paper (`ARC_Paper_Draft.pdf`). CPU-only, minutes.
Our own code is released under **MIT-0** (see `LICENSE`); third-party deps under their own
permissive licenses (see `THIRD_PARTY_NOTICES.md`).

## What the paper shows
1. **A pre-registered self-correction.** An earlier prefix analysis suggested a strong
   calibration curve (~50%->87%->95%) and a large selection lever (~+24 pts). A stricter,
   pre-registered same-holdout design (`HYPOTHESIS-crossfold-v2.md`) — frozen before the run,
   with a publish-regardless commitment — overturned both. We report the corrected numbers.
2. **The acceptance signal is weak.** Under the same-holdout design, a demonstration-consistent
   program reproduces a held-out demonstration only **32.8% / 50.8% / 63.4%** of the time at
   k = 1 / 2 / 3 (task-weighted, task-cluster 95% intervals) — far from the near-certainty
   solvers assume.
3. **The selection lever is real but bounded.** Minimum-description-length (Occam) selection
   beats random by **+11.1 pts [95% CI +4.6, +17.9]** on ambiguous cases, but does **not**
   reach the candidate oracle (oracle - MDL = +3.7 pts [+0.1, +9.5]).
4. **The N=120 leaderboard is mostly noise:** +/-~9-pt CIs, top-two gap p=0.16 (n.s.), and
   ~1,566 tasks needed to resolve a 5-pt frontier gap at 80% power.

## Setup
    pip install numpy pandas scipy matplotlib markdown playwright
    git clone https://github.com/arcprize/ARC-AGI-2   # point the data path in the scripts at your checkout

## Reproduce
    python crossfold_analysis.py       # primary same-holdout calibration + selection -> results/crossfold/
    python crossfold_replication.py    # one-shot public-evaluation replication
    python leaderboard_stats.py        # section 4.3 CIs + significance + power -> fig_leaderboard_ci.png
    python fig_v2.py                   # paper figures (reads only committed results) -> fig_v2_*.png
    python build_paper.py              # rebuild ARC_Paper_Draft.pdf from PAPER.md + figures

## Files
    dsl.py                     over-generating CPU program-synthesis solver
    crossfold_analysis.py      same-holdout cross-fold calibration + selection (primary analysis)
    crossfold_replication.py   one-shot public-evaluation replication
    leaderboard_stats.py       section 4.3 leaderboard statistics + figure
    fig_v2.py                  paper figures, generated from committed results
    build_paper.py             PAPER.md (+figures) -> PDF
    HYPOTHESIS-crossfold-v2.md frozen pre-registration for the same-holdout analysis
    PAPER.md                   paper source ; ARC_Paper_Draft.pdf built output
    results/                   frozen machine-readable outputs

## Linked Kaggle submission
The linked ARC-AGI-2 code submission scores **0.00 (0 of 167 pass@2)** on the verified set —
a symbolic library rarely contains any correct program for these tasks. The contribution is
the measurement, the same-holdout calibration, and the honestly-sized selection lever, not the solver.

Data: ARC-AGI-2 public corpus (1000 train / 120 eval), github.com/arcprize/ARC-AGI-2
