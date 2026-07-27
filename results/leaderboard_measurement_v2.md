# ARC-AGI-2 leaderboard measurement audit v2

The public evaluation corpus contains **120 ARC tasks but 167 test outputs**. The first paper treated the score as 120 Bernoulli trials; that denominator was wrong.

ARC accuracy is calculated over test outputs. Outputs belonging to the same ARC task are also dependent, so even an output-level binomial calculation is only an approximation.

## Worked aggregate-score example

Using 167 outputs:

- nominal 54% is represented most closely by **90/167 = 53.89%**, output-level Wilson 95% interval **46.33–61.28%**;
- nominal 45% is represented most closely by **75/167 = 44.91%**, interval **37.57–52.48%**;
- an unpaired output-level two-proportion approximation gives **z = 1.64, p = 0.101**;
- approximately **1,565 independent outputs** are required to resolve a five-point difference near 50% at 80% power under that unpaired approximation.

The output-level calculation is not the final inferential standard because some tasks contain multiple outputs.

## Correct reporting standard

1. State whether a percentage is averaged over ARC tasks or test outputs.
2. Release per-output outcomes so methods can be compared with paired tests.
3. Cluster uncertainty by ARC task whenever one task contributes multiple outputs.
4. Do not infer a ranking by eyeballing two aggregate percentages or their marginal intervals.
5. Distinguish public, semi-private, private, and verified scores and give the exact denominator for each.

## What survives from the first paper

The qualitative warning survives: a small static evaluation set cannot precisely rank systems separated by a few percentage points without paired outcome data.

What does **not** survive is the literal statement that the public leaderboard is `N = 120` independent Bernoulli trials.

Machine-readable result: [`leaderboard_measurement_v2.json`](leaderboard_measurement_v2.json).  
Recomputation script: [`../../leaderboard_stats_v2.py`](../../leaderboard_stats_v2.py).
