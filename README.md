# ARC Measurement Audit v2
## How Do We Know an ARC Solution Is Right?

[![ARC measurement audit](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/arc-measurement-v2.yml/badge.svg)](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/arc-measurement-v2.yml)
[![Evidence-weighted solver](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/evidence-weighted-solver.yml/badge.svg)](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/evidence-weighted-solver.yml)
[![Paper build](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/build-paper.yml/badge.svg)](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/build-paper.yml)

**Robert Morong · Independent research · ARC Prize 2026 Paper Track**  
Task-weighted calibration, same-target controls, candidate-selection auditing, one-shot public-evaluation replication, and a publish-regardless correction record.

**Live dashboard:** https://grobestreet.github.io/arc-agi-2-occam-baseline/  
**Canonical paper:** [`PAPER.md`](PAPER.md) · **PDF:** [`ARC_Measurement_Audit_v2.pdf`](ARC_Measurement_Audit_v2.pdf)

---

## The resolved finding

The original paper reported that a demonstration-consistent program generalized at **50.0%, 86.8%, and 94.9%** after fitting one, two, and three demonstrations. Those percentages were correct for this DSL's generated candidate population, but the interpretation was too strong:

1. candidate-rich tasks received more weight;
2. the held-out target changed as `k` changed;
3. the represented task set shrank at larger `k`;
4. equal-complexity program ties were not explicitly resolved.

V2 gives every task equal weight and holds the unseen demonstration fixed while varying only the amount of fitted evidence.

| Primary result | Resolved estimate |
|---|---:|
| Training coverage, `k=1` | **7.10%** [5.71, 8.58] |
| Training candidate reliability, `k=1` | **32.8%** [25.1, 40.4] |
| Training consensus yield, `k=1` | **3.31%** [2.31, 4.40] |
| Same-target coverage change, `k=2 − k=1` | **−3.66 pp** [−4.63, −2.74] |
| Same-target consensus-yield change | **−0.37 pp** [−0.60, −0.17] |
| One-shot evaluation coverage, `k=1` | **1.03%** [0.17, 2.25] |
| Evaluation same-target coverage change | **−1.24 pp** [−2.64, −0.23] |

**Interpretation:** additional demonstrations make the rare surviving hypotheses cleaner, but this incomplete DSL loses expressible hypotheses faster than it gains reliability. The bottleneck is representation and coverage—not insufficient confidence in a good candidate set.

---

## What survived—and what was refuted

### Survived

- **Underdetermination is real.** Multiple exact-consistent programs can disagree on the same unseen grid.
- **Description length helps selection.** On 224 ambiguous subset cells across 41 training tasks, tie-aware MDL beats random candidate selection by **11.1 percentage points** [4.6, 17.9].
- **N=120 is statistically coarse.** Small adjacent leaderboard gaps require paired per-task outcomes and uncertainty intervals.

### Refuted or narrowed

- **“One demonstration is a coin flip; three are reliable.”** The marginal curve is strongly composition-confounded and does not identify the effect of another demonstration.
- **“Shortest matches the oracle.”** The candidate oracle exceeds tie-aware MDL by **3.65 points** [0.13, 9.47].
- **“Candidate agreement is calibrated confidence.”** When every candidate agrees, task-weighted accuracy is only **37.8%** [28.8, 47.0].
- **“A better tie-breaker can rescue this solver.”** The released vote baseline, pure MDL, and the frozen evidence-weighted selector all score **0/167** public-evaluation outputs. The DSL rarely represents a viable answer on the harder split.

The negative results are retained because the correction process is the contribution.

---

## Research design

### 1. Equal-task correction

`task_clustered_analysis.py` recomputes the legacy prefix experiment by averaging within task before averaging across tasks. Complete task clusters are bootstrapped.

### 2. Same-target cross-fold experiment

`crossfold_ablation.py` performs every feasible combination of:

```text
task × held-out demonstration × k fitted demonstrations × fitted subset
```

Every subset cell is recorded, including cells where the DSL generates no candidate. This separates:

- **coverage** — whether a candidate exists;
- **conditional reliability** — whether generated candidates generalize;
- **yield** — whether the complete selection rule returns the answer.

`crossfold_analysis.py` averages subsets within holdout, holdouts within task, and then gives each task equal weight. Uncertainty is a task-cluster bootstrap.

### 3. Frozen replication

`HYPOTHESIS-crossfold-v2.md` records the interpretation thresholds before the complete run. The same code is then applied once to public evaluation demonstration pairs. `crossfold_replication.py` compares the frozen training and evaluation results without tuning.

### 4. Audit-to-algorithm test

`HYPOTHESIS-evidence-weighted-solver.md` freezes an evidence-weighted family selector before evaluation scoring. `benchmark_solver_v2.py` compares it with the released consensus baseline and pure MDL using paired outcomes. The result is an algorithmic null: all three score 0/167.

---

## Reproduce the complete audit

### Environment

```bash
git clone https://github.com/GrobeStreet/arc-agi-2-occam-baseline.git
cd arc-agi-2-occam-baseline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

mkdir -p external
git clone https://github.com/arcprize/ARC-AGI-2.git external/ARC-AGI-2
```

The committed workflow records the exact upstream data commit in `results/arc_agi_2_data_commit.txt`.

### Correct the original estimand

```bash
python task_clustered_analysis.py --bootstrap 50000 --seed 20260727
```

### Run the same-target training audit

```bash
python crossfold_ablation.py training \
  --data-root external/ARC-AGI-2/data \
  --output-dir results/crossfold

python crossfold_analysis.py \
  --input results/crossfold/crossfold_training.parquet \
  --results-dir results/crossfold/training_audit \
  --bootstrap 20000 \
  --seed 20260727
```

### Reproduce the frozen public-evaluation replication

The evaluation result has already been observed under v2. Re-running is reproduction, **not a fresh holdout for tuning**.

```bash
python crossfold_ablation.py evaluation \
  --data-root external/ARC-AGI-2/data \
  --output-dir results/crossfold

python crossfold_analysis.py \
  --input results/crossfold/crossfold_evaluation.parquet \
  --results-dir results/crossfold/evaluation_audit \
  --bootstrap 20000 \
  --seed 20260727

python crossfold_replication.py --bootstrap 20000 --seed 20260727
```

### Reproduce the frozen selector benchmark

```bash
python benchmark_solver_v2.py \
  --data-root external/ARC-AGI-2/data \
  --priors results/solver/family_priors.json \
  --output-dir results/solver \
  --prior-strength 8 \
  --relearn
```

### Build figures and paper

```bash
python fig_v2.py
playwright install chromium
python build_paper.py
```

---

## Repository map

```text
PAPER.md                              canonical revised paper
ARC_Measurement_Audit_v2.pdf          generated paper PDF
HYPOTHESIS-crossfold-v2.md            same-target preregistration
HYPOTHESIS-evidence-weighted-solver.md frozen algorithm test

task_clustered_analysis.py            equal-task legacy correction
crossfold_ablation.py                 complete same-target experiment
crossfold_analysis.py                 task-cluster inference
crossfold_replication.py              one-shot train/evaluation comparison

dsl.py                                diagnostic ARC program grammar
evidence_weighted_solver.py           family-prior two-attempt solver
benchmark_solver_v2.py                paired selector benchmark
kaggle_submission_v2.py               Kaggle-compatible entrypoint

results/task_weighted_calibration.*   corrected legacy estimates
results/crossfold/                     raw cells and resolved audit
results/solver/                        priors, predictions, benchmark, submission
site/                                  live dashboard source
```

---

## Data-use and claim boundaries

- The public evaluation split is a **previously observed one-shot public holdout**, not a private or verified leaderboard result.
- The 0/167 solver benchmark applies to this diagnostic DSL, not to ARC solvers generally.
- The same-target result does not mean demonstrations are intrinsically harmful. It means added constraints expose a misspecified hypothesis class.
- The paper's strongest contribution is measurement methodology: report coverage, conditional reliability, yield, selection rule, calibration, cost, paired outcomes, and task-cluster uncertainty.

---

## Citation

```bibtex
@misc{morong2026arcmeasurement,
  title  = {How Do We Know an ARC Solution Is Right? Coverage, Selection, Calibration, and the N=120 Problem in ARC-AGI-2},
  author = {Morong, Robert},
  year   = {2026},
  url    = {https://github.com/GrobeStreet/arc-agi-2-occam-baseline}
}
```

MIT License. AI-assisted implementation; errors remain the author's. Pull requests that reproduce, challenge, or falsify the results are encouraged.
