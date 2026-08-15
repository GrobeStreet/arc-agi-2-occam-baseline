# Kaggle writeup correction — 2026-08-15

This file is the source of truth for correcting the stale Kaggle paper/writeup entry so it matches the current public repository.

## Corrected public result

The current primary same-holdout results are:

- Candidate reliability: **32.8% / 50.8% / 63.4%** at k=1/2/3.
- MDL selection advantage over random on ambiguous cells: **+11.1 percentage points** (95% CI [+4.6, +17.9]).
- Candidate oracle minus MDL: **+3.7 points** (95% CI [+0.1, +9.5]).
- Linked frozen solver: **0/167 pass@2** on the verified set.
- Leaderboard top-two gap in the paper's modeled comparison: **p=0.16**.

The older ~46% / +24-point story is superseded and should not remain in the Kaggle body, cover, or attached paper.

## Paste-ready Kaggle body

Every ARC-AGI-2 solver ends the same way: it keeps the candidate transformations that reproduce the demonstration pairs, and — when several survive — picks one. We ask how much this final gate, and the leaderboard used to rank solvers, can actually tell us.

Our headline results come from a **same-holdout cross-fold design that was pre-specified and frozen before the first complete run**, after an earlier analysis produced substantially more optimistic numbers. Conditional on our diagnostic solver producing a demonstration-consistent program, that program reproduces a held-out demonstration only **32.8%** of the time when fit on one other demonstration, **50.8%** on two, and **63.4%** on three. Evidence helps, but a “consistent” program is barely a third right at one demonstration and still only about two-thirds right at three.

An earlier prefix design suggested a far rosier 50%→87%→95% curve; that curve was inflated by pooling candidate programs and by letting the held-out target change with the number of demonstrations. Under the corrected design, choosing the shortest minimum-description-length program among consistent-but-disagreeing candidates is still a real lever: **+11.1 points over random selection (95% CI [+4.6, +17.9])**. But it does **not** recover the candidate oracle; the oracle remains **+3.7 points** above MDL (95% CI [+0.1, +9.5]).

We also audit the ARC-AGI-2 leaderboard. At N=120, score uncertainty is large at the scale of small frontier gaps; in the comparison modeled in the paper, the top-two gap is **not statistically significant (p=0.16)**, and resolving a 5-point difference at 80% power would require roughly **1,566 tasks** under the stated assumptions.

The project therefore became a self-correction case study: the stricter design weakened our own earlier result, we kept the adverse result, and we released the original, diagnostic, and corrected analyses side by side. The contribution is measurement, uncertainty, and corrected selection analysis — **not** a competitive ARC solver. The linked frozen solver remains **0/167 pass@2**.

Current source of truth: https://github.com/GrobeStreet/arc-agi-2-occam-baseline

## Kaggle asset checklist

1. Replace the Kaggle body with the text above (or the current `PAPER.md` abstract), keeping the wording **pre-specified/frozen before run**, not “publicly preregistered.”
2. Replace the stale attached PDF with the repository's current `ARC_Paper_Draft.pdf`.
3. Replace any cover that still says approximately **46% / +24** with a corrected cover showing **33% / +11 / p=0.16**.
4. Remove any stray `ARC_Paper_Draft_1.pdf` or older paper attachment.
5. After saving, verify that no visible Kaggle text, cover, or attachment presents the superseded ~46% / +24-point result as current.

## Claim boundary

The repository supports that the corrected same-holdout design was **pre-specified and frozen before the first complete run with a publish-regardless commitment**. It does not claim an independently timestamped public preregistration unless separate evidence is produced.
