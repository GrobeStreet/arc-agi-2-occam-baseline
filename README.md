# How Do We Know an ARC Solution Is Right? — Code & Data Release
Reproduces every number and figure in the paper (ARC_Paper_Draft.pdf). CPU-only, minutes.

## Setup
pip install numpy pandas scipy matplotlib markdown playwright
Clone ARC-AGI-2 data:  git clone https://github.com/arcprize/ARC-AGI-2  (edit the /home/claude path in the scripts to your checkout)

## Reproduce
python ablate.py training        # §4.1 calibration curve + §4.2 selection  -> ablate_*_training.parquet
python leaderboard_stats.py      # §4.3 confidence intervals + significance + power
python run_solver.py training     # solver coverage
python kaggle_solver.py evaluation --score   # linked Kaggle baseline (pass@2)
# figures: fig1_calibration.png, fig_leaderboard_ci.png ; paper: python build_paper.py

## Files
dsl.py               program-synthesis solver (grid primitives + derived ops)
ablate.py            demonstration-ablation calibration experiment
run_solver.py        full-solve coverage over a split
kaggle_solver.py     ARC-AGI-2 submission (MDL/Occam selection, pass@2)  <- linked baseline
leaderboard_stats.py §4.3 statistics
PAPER.md             paper source ; ARC_Paper_Draft.pdf built output

Data: ARC-AGI-2 public corpus (1000 train / 120 eval), github.com/arcprize/ARC-AGI-2
