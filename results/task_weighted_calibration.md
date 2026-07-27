# Task-weighted ARC calibration with task-cluster uncertainty

The original calibration pooled candidate programs, so tasks that generated more candidates received more weight. This reanalysis computes a rate within each `(task, k)` cell and averages those rates equally across represented tasks.

| k | tasks | programs | program-weighted | task-weighted | 95% task-bootstrap CI | task minus program |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 67 | 248 | 50.0% | 45.6% | [34.2%, 57.1%] | -4.4 pp |
| 2 | 31 | 114 | 86.8% | 79.8% | [64.5%, 92.7%] | -7.0 pp |
| 3 | 11 | 39 | 94.9% | 90.9% | [72.7%, 100.0%] | -4.0 pp |
| 4 | 2 | 2 | 100.0% | 100.0% | [100.0%, 100.0%] | +0.0 pp |

## Legacy prefix contrasts

These compare common tasks but still change the held-out demonstration as k changes. They diagnose the original design; they do **not** identify the effect of adding demonstrations.

- **k=2 minus k=1** on 31 common tasks: -4.6 pp, 95% CI [-17.6, +6.6] pp.
- **k=3 minus k=2** on 11 common tasks: +2.3 pp, 95% CI [+0.0, +5.6] pp.
- **k=4 minus k=3** on 2 common tasks: +0.0 pp, 95% CI [+0.0, +0.0] pp.

## Resolution

The task-weighted marginal rates remain lower than the program-weighted rates. More importantly, the apparent marginal rise with k is confounded by changing task composition and changing held-out targets. The cross-fold experiment is now the primary analysis because it holds the target demonstration fixed while varying how many of the remaining demonstrations are fitted.

Bootstrap: 50,000 task replicates, seed 20260727.
