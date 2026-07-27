# Task-weighted ARC calibration with task-cluster uncertainty

The original calibration pooled candidate programs, so tasks that generated more candidates received more weight. This reanalysis first computes a generalization rate within each `(task, k)` cell, then averages those rates across tasks. The 95% intervals resample whole tasks with replacement, preserving within-task dependence across demonstration counts.

| demonstrations fit (k) | tasks | candidate programs | program-weighted | task-weighted | 95% task-cluster bootstrap CI | task minus program |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 67 | 248 | 50.0% | 45.6% | [34.2%, 57.1%] | -4.4 pp |
| 2 | 31 | 114 | 86.8% | 79.8% | [65.1%, 92.6%] | -7.0 pp |
| 3 | 11 | 39 | 94.9% | 90.9% | [nan%, nan%] | -4.0 pp |
| 4 | 2 | 2 | 100.0% | 100.0% | [nan%, nan%] | +0.0 pp |

## Adjacent-k contrasts

- **k=2 minus k=1:** +34.3 percentage points; 95% task-cluster CI [+18.5, +50.0] pp; bootstrap P(delta > 0) = 1.0000.
- **k=3 minus k=2:** +11.1 percentage points; 95% task-cluster CI [+nan, +nan] pp; bootstrap P(delta > 0) = 0.8973.
- **k=4 minus k=3:** +9.1 percentage points; 95% task-cluster CI [+nan, +nan] pp; bootstrap P(delta > 0) = 0.5469.

## Interpretation rule

The task-weighted estimate is the primary benchmark-level estimand. The program-weighted estimate remains useful as a description of this DSL's candidate population, but it should not be described as the reliability experienced by an average ARC task.

Bootstrap: 50,000 task-cluster replicates, seed 20260727.
