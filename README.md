# ARC Measurement Audit v2
## When a Calibration Curve Is a Selection Curve

**Robert Morong · Independent, AI-assisted research · ARC Prize 2026 Paper Track candidate**

A task- and target-controlled audit of demonstration value, hypothesis coverage, program selection, confidence, and leaderboard uncertainty in ARC-AGI-2.

## Canonical artifacts

- [Paper source](PAPER_V2.md)
- [Generated PDF](ARC_Measurement_Audit_v2.pdf)
- [Resolved findings ledger](RESULTS_V2.md)
- [ARC Elephant Hunt takeover plan](ARC_TAKEOVER_2026.md)
- [Paper Track submission checklist](PAPER_TRACK_SUBMISSION_CHECKLIST.md)
- [Cycle 002 registration](HYPOTHESIS-representation-cycle-002.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [Live dashboard](https://grobestreet.github.io/arc-agi-2-occam-baseline/)

## Verified contest status

Private Cycle 001 is closed.

| Item | Verified result |
|---|---:|
| Corrected Kaggle submission | `55057282` |
| Kernel | `robertmorong/grobestreet-arc-frozen-v3-cycle-001`, version 10 |
| Official hidden schema | 240 tasks / 259 outputs, validated |
| Public score | **0.00** |
| Terminal cycle verdict | **SCORED_NULL** |

The first submitted kernel version had a mechanical routing error. Version 10 changed only the input-routing wrapper, validated exact agreement with the official sample and hidden challenge IDs, and then received a valid score of zero. The zero is therefore a model result, not a packaging result.

The tied bottom-of-leaderboard rank is not scientifically meaningful. The score is.

## Paper Track status

The repository contains a paper, PDF, code, reproducibility record, and a real Kaggle code submission. However, a Paper Track writeup submission has **not yet been verified** in this repository or the connected email record.

Current status:

> **READY TO SUBMIT; NOT VERIFIED SUBMITTED**

The Paper Prize does not require a high linked code score, but the paper's accuracy rubric will incorporate the actual leaderboard result. The paper must therefore state the 0.00 score directly and compete on theory, completeness, universality, progress, and novelty.

## Main scientific result

The original draft reported that a demonstration-consistent program generalized at 50.0%, 86.8%, and 94.9% after one, two, and three fitted demonstrations. Those values described the generated program population, not the causal effect of more evidence, because candidate-rich tasks were overweighted, programs were nested within tasks, the target changed with `k`, the represented task population changed, and no-candidate failures were omitted.

The corrected same-target experiment fixes the task and held-out target, enumerates every evidence subset, keeps no-candidate cells in the denominator, and resamples complete ARC tasks.

| Primary result | Resolved estimate |
|---|---:|
| Training coverage, `k=1` | **7.10%** [5.71, 8.58] |
| Conditional candidate reliability, `k=1` | **32.8%** [25.1, 40.4] |
| Consensus yield, `k=1` | **3.31%** [2.31, 4.40] |
| Same-target coverage change, `k=2 − k=1` | **−3.66 pp** [−4.63, −2.74] |
| Same-target consensus-yield change | **−0.37 pp** [−0.60, −0.17] |
| Public-evaluation coverage, `k=1` | **1.03%** [0.17, 2.25] |
| Frozen public-evaluation pass@2 | **0/167** |
| Corrected hidden Kaggle score | **0.00** |

Interpretation:

> More evidence makes the rare surviving hypotheses cleaner, but this narrow grammar loses expressible hypotheses faster than it gains reliability. This is a precision–coverage tradeoff, not a monotone learning curve.

## Selection and confidence

Across 224 ambiguous subset cells from 41 tasks:

| Rule | Task-weighted accuracy |
|---|---:|
| Random candidate | 18.9% |
| Legacy first-shortest | 31.2% |
| Random minimum-complexity tie | 30.4% |
| Tie-aware MDL vote | 30.0% |
| Consensus | 27.4% |
| Candidate oracle | 33.7% |

Tie-aware MDL improves over random selection by 11.1 percentage points [4.6, 17.9]. The candidate oracle exceeds MDL by 3.65 points [0.13, 9.47], refuting the earlier exact oracle-equivalence claim.

Candidate agreement is not calibrated confidence:

- task-weighted Brier score: 0.542;
- mean absolute confidence-error gap: 59.5 percentage points;
- unanimous candidate sets correct: 37.8% [28.8, 47.0].

## Engineering verdict

The symbolic DSL is closed as a standalone competition solver.

- Released vote baseline: 0/167 public-evaluation pass@2
- Pure MDL: 0/167
- Evidence-weighted selector: 0/167
- Registered representation v3: 0/167
- Corrected hidden Kaggle score: 0.00

Selection changes cannot recover a transformation the candidate library never generates.

## Cycle 002

[Representation Cycle 002](HYPOTHESIS-representation-cycle-002.md) is now registered before implementation.

The authorized path is:

1. a permissively licensed recursive neural grid model;
2. license-compatible procedural synthetic data, including ARC-GEN;
3. the frozen v3 DSL retained only as a specialist candidate source;
4. a frozen two-attempt router optimized for marginal pass@2 value;
5. a deterministic development holdout and one new one-shot Kaggle submission.

No more hand-written task-specific rules, public-evaluation hill climbing, or repeated private probing are allowed.

## Reproduce the measurement audit

```bash
git clone https://github.com/GrobeStreet/arc-agi-2-occam-baseline.git
cd arc-agi-2-occam-baseline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

mkdir -p external
git clone https://github.com/arcprize/ARC-AGI-2.git external/ARC-AGI-2
```

Equal-task correction:

```bash
python task_clustered_analysis.py --bootstrap 50000 --seed 20260727
```

Same-target training audit:

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

Frozen public-evaluation reproduction:

```bash
python benchmark_representation_v3_public.py \
  --data-root external/ARC-AGI-2/data/evaluation \
  --output-dir results/representation_v3_public
```

Build the paper:

```bash
python fig_v2.py
playwright install chromium
python build_paper.py
```

## License

Submitter-authored code is released under **MIT-0**. Third-party software, data, models, and generators retain their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Claim boundaries

- The valid hidden Cycle 001 score is 0.00.
- The Paper Track writeup is not considered submitted until a writeup URL or confirmation is recorded.
- The negative same-target effect applies to this evaluated hypothesis library, not to reasoning systems generally.
- Public evaluation is already observed and cannot serve as fresh confirmation for Cycle 002.
- Cycle 001 private feedback may not be converted into task-level tuning signals.
- Historical v4/v4.1 scaffolding does not establish a valid competition result.

Reproductions, corrections, and falsifications are encouraged.