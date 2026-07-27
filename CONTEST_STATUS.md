# ARC Prize 2026 — Contest Status

**Updated:** 2026-07-27  
**Repository:** `GrobeStreet/arc-agi-2-occam-baseline`

## Executive status

The corrected research program, canonical paper/PDF, frozen representation-v3 solver, private Kaggle code-kernel runner, authenticated submission workflow, score collector, rank collector, and next-cycle registration template are pushed to `main`.

The automated Cycle 001 run has executed and recorded:

> **BLOCKED_AUTH — `KAGGLE_USERNAME` and `KAGGLE_API_TOKEN` are not configured as GitHub Actions secrets.**

Therefore the current official contest status is:

> **UNRANKED — no authenticated Kaggle code-kernel version has been submitted and scored.**

This is an account-authorization blocker, not a solver-freeze or packaging blocker.

## Official competition boundary

The official code-competition path runs a Kaggle kernel with internet disabled, produces exactly two predictions per test input, and submits a specific immutable kernel version for scoring. A GitHub artifact, local holdout, or public-evaluation run does not create an official Kaggle score or rank.

The Paper Prize separately requires a linked Kaggle code submission; that linked submission does not need to achieve a high score.

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

Authoritative execution and audit files:

- `.github/workflows/private-v3-cycle-001.yml`
- `scripts/kaggle_private_cycle_001.py`
- `contest/kaggle_kernel_v3/run.py`
- `results/private_cycle_001/result.json`
- `results/private_cycle_001/RESULT.md`
- `PRIVATE_CYCLE_001_STATUS.md`

The workflow:

1. reconstructs the kernel from the frozen source commit;
2. hashes all source files;
3. creates a private, internet-disabled Kaggle competition kernel;
4. runs the hidden competition test;
5. verifies the required `submission.json` output;
6. submits the immutable kernel version;
7. waits for a visible score;
8. queries the authenticated user's rank and downloads leaderboard evidence;
9. commits a sanitized publish-regardless result;
10. prevents another scored Cycle 001 submission.

## One remaining secure authorization action

In repository **Settings → Secrets and variables → Actions**, add:

- `KAGGLE_USERNAME`
- `KAGGLE_API_TOKEN`
- optionally `KAGGLE_TEAM_NAME` when the team name differs from the username

The Kaggle account must also have joined the competition and accepted its rules. Then run **Actions → Frozen ARC v3 private Cycle 001 → Run workflow** exactly once.

Detailed directions: [`KAGGLE_SUBMIT_NOW.md`](KAGGLE_SUBMIT_NOW.md)

## Known evidence before private submission

- Frozen v3 deterministic training holdout: 5/201 pass@2 versus 4/201 for v2; one v3-only win; exact paired p=1.0.
- Frozen v3 public evaluation: 0/167 pass@2; registered verdict NULL.

These do not determine the hidden competition score. They do indicate that the current symbolic grammar should not be described as a likely high-ranking solver.

## Representation firewall

Cycle 001 is evaluation-only. No change to representation, ranking, fallback policy, or output construction is authorized under its name.

Further representation work requires copying `HYPOTHESIS-representation-cycle-002-TEMPLATE.md` to `HYPOTHESIS-representation-cycle-002.md`, completing every field, and committing that registration before source changes or a new fresh-endpoint run.

## V4.1 boundary

The repository contains historical v4/v4.1 scaffolding. Those files do not replace the frozen Cycle 001 artifact and do not establish a private competition score or rank. Any future representation advance must be admitted only through a new registered cycle and fresh endpoint.
