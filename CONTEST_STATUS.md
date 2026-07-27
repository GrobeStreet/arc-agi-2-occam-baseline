# ARC Prize 2026 — Contest Status

**Updated:** 2026-07-27  
**Repository:** `GrobeStreet/arc-agi-2-occam-baseline`

## Executive status

The corrected research program, canonical paper/PDF, frozen representation-v3 solver, self-contained Kaggle kernel, authenticated submission workflow, score collector, and rank collector are pushed to `main`.

The automated Cycle 001 run has executed its preflight and recorded:

> **BLOCKED_AUTH — `KAGGLE_USERNAME` and a Kaggle API token are not configured as GitHub Actions secrets.**

Therefore the current official contest status is:

> **UNRANKED — no authenticated Kaggle notebook version has been submitted and scored.**

This is an account-authorization blocker, not a solver or packaging blocker.

## Official competition boundary

ARC-AGI-2 submissions must be made through the Kaggle code competition as a Kaggle notebook with internet disabled. The competition scores exactly two predictions per test input. A GitHub JSON artifact, local holdout, or public-evaluation run does not create an official score or rank.

The Paper Prize separately requires a linked Kaggle code submission, but that linked submission does not need a high score.

Official pages:

- Competition: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2
- ARC-AGI-2 requirements: https://arcprize.org/competitions/2026/arc-agi-2
- Paper Prize: https://arcprize.org/competitions/2026/paper

## Frozen Private Cycle 001

Registration:

- `HYPOTHESIS-private-v3-cycle-001.md`

Frozen source commit:

- `70672f3aa62d089bfffd072461a5713caae1e099`

Frozen files:

- `dsl.py`
- `dsl_v3.py`
- `benchmark_representation_v3.py`
- `kaggle_submission_v3.py`

Execution and audit files:

- `.github/workflows/private-v3-cycle-001.yml`
- `scripts/kaggle_private_cycle_001.py`
- `scripts/record_private_cycle_001.py`
- `contest/kaggle_kernel_v3/`
- `kaggle/arc_v3_entrypoint.py`
- `results/private_cycle_001/result.json`
- `results/private_cycle_001/RESULT.md`
- `PRIVATE_CYCLE_001_STATUS.md`

The workflow:

1. reconstructs the kernel from the frozen source commit;
2. hashes all source files;
3. creates a private, internet-disabled Kaggle competition kernel;
4. runs the hidden competition test;
5. submits the immutable kernel version;
6. polls for a visible score;
7. downloads the authenticated leaderboard;
8. records exact rank when the team name is available, otherwise a score-derived tie range;
9. commits a sanitized immutable result.

## One remaining authorization action

In repository **Settings → Secrets and variables → Actions**, add:

- `KAGGLE_USERNAME`
- either `KAGGLE_API_TOKEN` or legacy `KAGGLE_KEY`
- optionally `KAGGLE_TEAM_NAME` when the team name differs from the username

The Kaggle account must also have joined the competition and accepted its rules.

Then run **Actions → Frozen ARC v3 private Cycle 001 → Run workflow** exactly once. The workflow guard prevents a second scored Cycle 001 submission after a terminal or submitted state.

Detailed directions: [`KAGGLE_SUBMIT_NOW.md`](KAGGLE_SUBMIT_NOW.md)

## Known evidence before private submission

- Frozen v3 deterministic training holdout: 5/201 pass@2 versus 4/201 for v2; one v3-only win; exact paired p=1.0.
- Frozen v3 public evaluation: 0/167 pass@2; registered verdict NULL.

These do not determine the hidden competition score. They do indicate that the current symbolic grammar should not be presented as a likely high-ranking solver.

## Representation firewall

Cycle 001 is evaluation-only. No change to representation, ranking, fallback policy, or output construction is authorized under its name.

Further representation work requires copying `HYPOTHESIS-representation-cycle-002-TEMPLATE.md` to `HYPOTHESIS-representation-cycle-002.md`, completing every field, and committing that registration before source changes or a new fresh-endpoint run.

## V4.1 boundary

The repository contains historical v4.1 workflow scaffolding, but the referenced frozen core branch is unavailable and no canonical v4.1 benchmark or private score was established. Do not claim a v4.1 contest score or rank.
