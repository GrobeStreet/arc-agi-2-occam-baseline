# ARC Measurement Audit v2
## When a Calibration Curve Is a Selection Curve

[![ARC measurement audit](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/arc-measurement-v2.yml/badge.svg)](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/arc-measurement-v2.yml)
[![Frozen private Cycle 001](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/private-v3-cycle-001.yml/badge.svg)](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/private-v3-cycle-001.yml)
[![Paper build](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/build-paper.yml/badge.svg)](https://github.com/GrobeStreet/arc-agi-2-occam-baseline/actions/workflows/build-paper.yml)

**Robert Morong · Independent, AI-assisted research · ARC Prize 2026 Paper Track candidate**  
A task- and target-controlled audit of demonstration value, hypothesis coverage, program selection, confidence, and leaderboard uncertainty in ARC-AGI-2.

- **Canonical paper:** [`PAPER_V2.md`](PAPER_V2.md)
- **Generated PDF:** [`ARC_Measurement_Audit_v2.pdf`](ARC_Measurement_Audit_v2.pdf)
- **Resolved findings:** [`RESULTS_V2.md`](RESULTS_V2.md)
- **Official contest status:** [`CONTEST_STATUS.md`](CONTEST_STATUS.md)
- **Frozen Cycle 001 result:** [`PRIVATE_CYCLE_001_STATUS.md`](PRIVATE_CYCLE_001_STATUS.md)
- **Kaggle authorization/run instructions:** [`KAGGLE_SUBMIT_NOW.md`](KAGGLE_SUBMIT_NOW.md)
- **Live evidence dashboard:** https://grobestreet.github.io/arc-agi-2-occam-baseline/

---

## Official contest status

The complete frozen Kaggle submission package and the score/rank collector are pushed to `main`.

The first workflow preflight recorded:

> **BLOCKED_AUTH — `KAGGLE_USERNAME` and a Kaggle API token are not configured as GitHub Actions secrets.**

Therefore the official ranking state is currently:

> **UNRANKED — no authenticated Kaggle notebook has been submitted and scored.**

This is an account-authorization blocker, not a packaging blocker. The workflow is designed to create and run the private, internet-disabled competition kernel, submit its immutable version, poll the score, download the leaderboard, and commit the sanitized rank record.

The one remaining account action is documented in [`KAGGLE_SUBMIT_NOW.md`](KAGGLE_SUBMIT_NOW.md): join/accept the Kaggle competition, add `KAGGLE_USERNAME` plus `KAGGLE_API_TOKEN` or `KAGGLE_KEY` as repository Actions secrets, then run **Frozen ARC v3 private Cycle 001** exactly once.

---

## Frozen private-test cycle

[`HYPOTHESIS-private-v3-cycle-001.md`](HYPOTHESIS-private-v3-cycle-001.md) registers the untouched competition test before submission.

Cycle 001 reconstructs these files from frozen source commit `70672f3a`:

- `dsl.py`
- `dsl_v3.py`
- `benchmark_representation_v3.py`
- `kaggle_submission_v3.py`

It does **not** permit representation, ranking, fallback, or output-policy changes.

Any later representation work must begin by copying [`HYPOTHESIS-representation-cycle-002-TEMPLATE.md`](HYPOTHESIS-representation-cycle-002-TEMPLATE.md) to `HYPOTHESIS-representation-cycle-002.md`, resolving every placeholder, and committing the completed registration before changing code or touching a fresh endpoint.

---

## The resolved measurement finding

The original draft reported that a demonstration-consistent program generalized at **50.0%, 86.8%, and 94.9%** after one, two, and three fitted demonstrations. Those values accurately described this DSL's generated program population, but they did not isolate the effect of more evidence because:

1. candidate-rich tasks received more weight;
2. programs nested inside a task were treated as independent;
3. the held-out target changed with `k`;
4. the represented task set became smaller and easier at larger `k`;
5. no-candidate failures were omitted.

The corrected experiment fixes the task and target, enumerates every evidence subset, retains no-candidate cells as failures, and bootstraps complete ARC tasks.

| Primary result | Resolved estimate |
|---|---:|
| Training coverage, `k=1` | **7.10%** [5.71, 8.58] |
| Conditional candidate reliability, `k=1` | **32.8%** [25.1, 40.4] |
| Consensus yield, `k=1` | **3.31%** [2.31, 4.40] |
| Same-target coverage change, `k=2 − k=1` | **−3.66 pp** [−4.63, −2.74] |
| Same-target consensus-yield change | **−0.37 pp** [−0.60, −0.17] |
| One-shot public-evaluation coverage, `k=1` | **1.03%** [0.17, 2.25] |
| Evaluation same-target coverage change | **−1.24 pp** [−2.64, −0.23] |

**Interpretation:** another demonstration makes the rare surviving hypotheses cleaner, but this incomplete grammar loses expressible hypotheses faster than it gains reliability. This is a **precision–coverage tradeoff**, not evidence that demonstrations generally harm reasoning.

---

## Selection and confidence

Across 224 ambiguous subset cells from 41 tasks:

| Rule | Task-weighted accuracy |
|---|---:|
| Random candidate | **18.9%** |
| Legacy first-shortest | **31.2%** |
| Random minimum-complexity tie | **30.4%** |
| Tie-aware MDL vote | **30.0%** |
| Consensus | **27.4%** |
| Candidate oracle | **33.7%** |

Tie-aware MDL beats random selection by **+11.1 percentage points** [4.6, 17.9]. The oracle exceeds MDL by **+3.65 points** [0.13, 9.47]. Therefore MDL is useful, but the earlier exact oracle-equivalence claim is refuted.

Candidate agreement is also severely overconfident:

- task-weighted Brier score: **0.542**;
- mean absolute confidence-error gap: **59.5 pp**;
- unanimous candidate sets are correct only **37.8%** [28.8, 47.0].

---

## Frozen solver evidence

A training-only evidence-weighted selector, pure MDL, and the released vote baseline were frozen and evaluated on all 167 public-evaluation outputs:

| Method | pass@1 | pass@2 |
|---|---:|---:|
| Released vote baseline | 0/167 | 0/167 |
| Pure MDL | 0/167 | 0/167 |
| Evidence-weighted selector | 0/167 | 0/167 |

The registered representation-v3 public-evaluation run also produced **0/167 pass@2**. These are negative results: better tie-breaking cannot recover a hypothesis the grammar never generates.

The deterministic v3 training holdout had one directional gain—5/201 versus 4/201 pass@2, one v3-only win, exact paired p=1.0—but this did not transfer to the public evaluation set and is not a competition ranking.

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

### Equal-task correction

```bash
python task_clustered_analysis.py --bootstrap 50000 --seed 20260727
```

### Same-target training audit

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

### Frozen v3 public-evaluation reproduction

```bash
python benchmark_representation_v3_public.py \
  --data-root external/ARC-AGI-2/data/evaluation \
  --output-dir results/representation_v3_public
```

### Paper

```bash
python fig_v2.py
playwright install chromium
python build_paper.py
```

---

## Repository map

```text
PAPER_V2.md                            canonical measurement paper
RESULTS_V2.md                          resolved findings ledger
ARC_Measurement_Audit_v2.pdf           generated paper

HYPOTHESIS-crossfold-v2.md             same-target registration
HYPOTHESIS-evidence-weighted-solver.md frozen selector registration
HYPOTHESIS-representation-v3.md        representation-v3 holdout registration
HYPOTHESIS-v3-public-eval.md           frozen public-evaluation registration
HYPOTHESIS-private-v3-cycle-001.md     untouched Kaggle cycle registration
HYPOTHESIS-representation-cycle-002-TEMPLATE.md

kaggle_submission_v3.py                frozen two-attempt solver
kaggle/arc_v3_entrypoint.py            canonical Kaggle entrypoint
contest/kaggle_kernel_v3/              self-contained private kernel package
scripts/kaggle_private_cycle_001.py    submission and ranking collector
.github/workflows/private-v3-cycle-001.yml

results/private_cycle_001/             immutable score/rank or blocker record
CONTEST_STATUS.md                      authoritative contest state
KAGGLE_SUBMIT_NOW.md                   one-time authorization instructions
```

---

## Claim boundaries

- The negative same-target effect applies to this incomplete grammar, not to reasoning systems generally.
- The public evaluation set is already observed and cannot serve as fresh confirmation for later representation changes.
- Private Cycle 001 remains frozen and unranked until Kaggle authentication is provided and the notebook is scored.
- A future aggregate Kaggle score may close Cycle 001 but may not be converted into task-level tuning feedback.
- No v4.1 competition score or rank is established by the historical scaffolding in this repository.

MIT License. AI-assisted implementation; errors remain the author's. Reproductions, challenges, and falsifications are encouraged.
