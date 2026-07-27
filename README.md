# ARC Measurement Audit v2
## When a Calibration Curve Is a Selection Curve

[![ARC measurement audit](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/arc-measurement-v2.yml/badge.svg)](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/arc-measurement-v2.yml)
[![Evidence-weighted solver](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/evidence-weighted-solver.yml/badge.svg)](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/evidence-weighted-solver.yml)
[![Paper build](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/build-paper.yml/badge.svg)](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/build-paper.yml)

**Robert Morong · Independent research · ARC Prize 2026 Paper Track candidate**  
Task- and target-controlled measurement of demonstration value, candidate selection, confidence, and leaderboard uncertainty in ARC-AGI-2.

- **Canonical paper:** [`PAPER_V2.md`](PAPER_V2.md)
- **Resolved findings ledger:** [`RESULTS_V2.md`](RESULTS_V2.md)
- **Generated PDF:** [`ARC_Measurement_Audit_v2.pdf`](ARC_Measurement_Audit_v2.pdf)
- **Registered tests:** [`HYPOTHESIS-crossfold-v2.md`](HYPOTHESIS-crossfold-v2.md) · [`HYPOTHESIS-evidence-weighted-solver.md`](HYPOTHESIS-evidence-weighted-solver.md)
- **Live-dashboard source:** [`site/`](site/)

`PAPER.md` and `RESULTS-v2.md` are retained as earlier v2 drafting artifacts. The files above are canonical whenever wording differs.

---

## The resolved finding

The first draft reported that a demonstration-consistent program generalized at **50.0%, 86.8%, and 94.9%** after one, two, and three fitted demonstrations. Those numbers accurately described the generated candidate-program population, but not the effect of adding evidence:

1. candidate-rich tasks received more weight;
2. programs nested inside one task were treated as independent observations;
3. the held-out target changed as `k` changed;
4. the represented task set became easier and smaller at larger `k`;
5. no-candidate failures were omitted from the apparent reliability story.

The corrected full-corpus experiment holds the task and target fixed, enumerates every evidence subset, counts no-candidate cells as failures, and bootstraps ARC tasks.

| Primary result | Resolved estimate |
|---|---:|
| Training coverage, `k=1` | **7.10%** [5.71, 8.58] |
| Training conditional candidate reliability, `k=1` | **32.8%** [25.1, 40.4] |
| Training consensus yield, `k=1` | **3.31%** [2.31, 4.40] |
| Same-target coverage change, `k=2 − k=1` | **−3.66 pp** [−4.63, −2.74] |
| Same-target consensus-yield change | **−0.37 pp** [−0.60, −0.17] |
| One-shot evaluation coverage, `k=1` | **1.03%** [0.17, 2.25] |
| Evaluation same-target coverage change | **−1.24 pp** [−2.64, −0.23] |

**Interpretation:** added demonstrations improve the purity of the rare hypotheses this small DSL can still express, but they reduce hypothesis coverage enough that end-to-end yield falls. This is a **precision–coverage tradeoff**, not a monotone learning curve.

---

## What survived—and what was refuted

### Survived

- **Underdetermination is real.** Exact-consistent programs can disagree on an unseen grid.
- **Description length helps.** On 224 ambiguous subset cells across 41 tasks, tie-aware MDL beats random candidate selection by **11.1 percentage points** [4.6, 17.9].
- **Coverage and selection are separate problems.** A selector cannot rescue an absent hypothesis.
- **ARC rankings need uncertainty.** Scores should identify the output denominator, release paired outcomes, and cluster uncertainty by task.

### Refuted or narrowed

- **“One example is exactly a coin flip; three are reliable.”** The original curve was composition- and target-confounded.
- **“Shortest matches the oracle.”** The candidate oracle exceeds tie-aware MDL by **3.65 points** [0.13, 9.47].
- **“Candidate agreement is calibrated confidence.”** Unanimous candidates are correct only **37.8%** [28.8, 47.0] on the task-weighted audit.
- **“A better tie-breaker can rescue this solver.”** The released baseline, pure MDL, and frozen evidence-weighted selector all score **0/167** public-evaluation outputs.
- **“The public leaderboard is 120 Bernoulli trials.”** Public evaluation contains **120 tasks but 167 test outputs**; outputs are nested within tasks.

The corrections are the contribution. No attractive claim is retained merely because it appeared in the first draft.

---

## Research design

### 1. Equal-task correction

`task_clustered_analysis.py` recomputes the legacy prefix experiment by averaging within task before averaging across tasks, with task-cluster uncertainty.

### 2. Same-target all-subsets experiment

`crossfold_ablation.py` records every feasible:

```text
task × held-out demonstration × k fitted demonstrations × fitted subset
```

including no-candidate cells. `crossfold_analysis.py` separates:

- coverage;
- conditional candidate reliability;
- selector accuracy conditional on generation;
- end-to-end yield;
- candidate-oracle yield and selection regret.

### 3. Frozen public-evaluation replication

The interpretation gates were registered before the complete run. The same analysis was then applied once to public evaluation demonstration pairs. This is a previously observed public holdout, not a private or verified leaderboard result.

### 4. Audit-to-algorithm test

`evidence_weighted_solver.py` learns equal-task program-family reliability from training demonstrations only. `benchmark_solver_v2.py` freezes the selector and compares it against the released baseline and pure MDL using paired public-evaluation outputs. The result is a documented null.

### 5. Scoring-unit audit

`leaderboard_stats_v2.py` directly counts tasks and test outputs in the pinned corpus and replaces the legacy `N=120` calculation with an output-aware, task-dependence-aware reporting standard.

---

## Reproduce

```bash
git clone https://github.com/GrobeStreet/arc-agi-2-occam-baseline.git
cd arc-agi-2-occam-baseline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

mkdir -p external
git clone https://github.com/arcprize/ARC-AGI-2.git external/ARC-AGI-2
```

### Complete measurement audit

```bash
python leaderboard_stats_v2.py \
  --data-root external/ARC-AGI-2/data \
  --split evaluation \
  --output-dir results

python task_clustered_analysis.py --bootstrap 50000 --seed 20260727

python crossfold_ablation.py training \
  --data-root external/ARC-AGI-2/data \
  --output-dir results/crossfold

python crossfold_analysis.py \
  --input results/crossfold/crossfold_training.parquet \
  --results-dir results/crossfold/training_audit \
  --bootstrap 20000 \
  --seed 20260727
```

### Previously observed public-evaluation replication

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

### Frozen selector benchmark

```bash
python benchmark_solver_v2.py \
  --data-root external/ARC-AGI-2/data \
  --priors results/solver/family_priors.json \
  --output-dir results/solver \
  --prior-strength 8 \
  --relearn
```

### Paper

```bash
python fig_v2.py
playwright install chromium
python build_paper.py
```

The workflow pins the exact upstream ARC-AGI-2 commit in `results/arc_agi_2_data_commit.txt`.

---

## Repository map

```text
PAPER_V2.md                           canonical paper
RESULTS_V2.md                         resolved findings ledger
ARC_Measurement_Audit_v2.pdf          generated canonical PDF
HYPOTHESIS-crossfold-v2.md             same-target registration
HYPOTHESIS-evidence-weighted-solver.md frozen selector registration

leaderboard_stats_v2.py               scoring-unit correction
task_clustered_analysis.py            equal-task legacy correction
crossfold_ablation.py                 complete same-target experiment
crossfold_analysis.py                 task-cluster inference
crossfold_replication.py              one-shot train/evaluation comparison

dsl.py                                diagnostic symbolic grammar
evidence_weighted_solver.py           training-only family-prior selector
benchmark_solver_v2.py                paired frozen benchmark
kaggle_submission_v2.py               two-attempt submission entrypoint

results/task_weighted_calibration.*   corrected legacy estimates
results/crossfold/                     full-corpus and replication evidence
results/solver/                        priors, predictions, benchmark, submission
site/                                  live-dashboard source
```

---

## Claim boundaries

- The negative same-target effect applies to this incomplete diagnostic DSL, not to demonstrations or reasoning systems generally.
- The public evaluation result is a previously observed public holdout, not a private or verified score.
- The `0/167` result is scientifically useful but not contest competitive.
- The strongest contribution is measurement methodology: report coverage, conditional reliability, end-to-end yield, semantic output diversity, selector policy, calibration, cost, paired outcomes, and task-cluster uncertainty.

## Citation

```bibtex
@misc{morong2026arcmeasurement,
  title  = {When a Calibration Curve Is a Selection Curve: Task- and Target-Controlled Measurement of Demonstration Value in ARC-AGI-2},
  author = {Morong, Robert},
  year   = {2026},
  url    = {https://github.com/GrobeStreet/arc-agi-2-occam-baseline}
}
```

MIT License. AI-assisted implementation; errors remain the author's. Reproductions, challenges, and falsifications are encouraged.
