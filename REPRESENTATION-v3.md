# ARC Representation Expansion v3
## Moving the bottleneck from selection to candidate generation

**Registered protocol:** [`HYPOTHESIS-representation-v3.md`](HYPOTHESIS-representation-v3.md)  
**Machine-readable result:** [`results/representation_v3/representation_v3_benchmark.json`](results/representation_v3/representation_v3_benchmark.json)

---

## Why v3 exists

ARC Measurement Audit v2 found an algorithmic null on the public evaluation set: the original vote baseline, pure MDL, and an evidence-weighted selector all scored 0/167 outputs. The shared failure was not ranking. The diagnostic grammar almost never generated a viable hypothesis.

V3 therefore changes the representation rather than tuning another tie-breaker.

The expanded grammar adds generic, pre-registered transformations for:

- gravity in every direction;
- internal row/column compression;
- 4- and 8-connected component selection;
- color isolation and removal;
- hole and bounding-box operations;
- separator-panel extraction and overlays;
- symmetry completion;
- line connection and extension;
- component-count encodings;
- component packing;
- block-mode reduction;
- a limited set of geometry compositions.

The 120 public evaluation tasks were excluded from development. V3 was scored once on a deterministic SHA1 holdout carved from the 1,000 public training tasks.

---

## Frozen holdout result

**Holdout:** 183 tasks, 201 test outputs.

| Endpoint | v2 baseline | v3 expanded grammar | v3 candidate oracle |
|---|---:|---:|---:|
| Output pass@1 | 4/201 (1.99%) | **5/201 (2.49%)** | — |
| Output pass@2 | 4/201 (1.99%) | **5/201 (2.49%)** | 5/201 (2.49%) |
| Whole-task pass@2 | 4/183 (2.19%) | **5/183 (2.73%)** | 5/183 (2.73%) |
| Valid-candidate coverage | 4/201 (1.99%) | **5/201 (2.49%)** | — |

Paired output comparison:

- v3-only wins: **1**;
- v2-only wins: **0**;
- exact two-sided p-value: **1.0**.

**Registered verdict: DIRECTIONAL IMPROVEMENT, not established superiority.**

V3 solves one additional output and loses none, but the holdout contains only one discordant case. The interval is far too broad for a strong performance claim.

---

## What the added representation solved

The v3-only success is training task **22168020**, a line-completion transformation in which same-colored endpoints in each row are connected. This task is outside the original grammar and is represented by v3's generic same-color line-connection family.

That matters for diagnosis:

- the extra success is traceable to an explicit representational addition;
- v3's full candidate oracle equals its ranked pass@2 result, so selection does not leave another solved holdout case on the table;
- the overall gain remains tiny because coverage rises only from 4 to 5 of 201 outputs.

The result validates the direction of the roadmap without pretending the solver is competitive.

---

## Private-test contest artifact

The pre-registration permits a private-test submission artifact after directional holdout improvement. The repository therefore includes:

- [`kaggle_submission_v3.py`](kaggle_submission_v3.py) — auto-discovers the official ARC Prize test challenge file under `/kaggle/input`;
- [`dsl_v3.py`](dsl_v3.py) — frozen representation grammar;
- [`benchmark_representation_v3.py`](benchmark_representation_v3.py) — paired holdout benchmark;
- exactly two distinct output attempts per test input;
- output-grid validation before `submission.json` is written.

Typical Kaggle notebook command:

```bash
python kaggle_submission_v3.py \
  --test-challenges /kaggle/input/arc-prize-2026/arc-agi_test_challenges.json \
  --output /kaggle/working/submission.json
```

The exact mounted competition path may differ; without `--test-challenges`, the script searches `/kaggle/input` recursively.

No private score is claimed until the artifact is actually submitted and evaluated. Public evaluation is not reused to tune v3.

---

## Honest conclusion

V3 moves the program one correct held-out task forward. It does not solve the coverage crisis.

The contest lesson is now empirically ordered:

1. **Selection auditing was necessary**: MDL helps, consensus is overconfident, and oracle equality was false.
2. **Selection alone was insufficient**: three selectors tied at zero on public evaluation.
3. **Generic representation expansion can add genuine solved tasks**: v3 gains one without a loss.
4. **The remaining frontier is much larger**: object relations, learned program proposals, test-time adaptation, and induction-transduction hybrids are required for meaningful ARC-AGI-2 performance.

This is a promoted submission baseline only in the narrow sense defined before the run: it is directionally better on the frozen training holdout and ready for the untouched private test. It is not presented as a leaderboard contender.
