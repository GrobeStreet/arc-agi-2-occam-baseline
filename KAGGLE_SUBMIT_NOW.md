# Submit Frozen V3 to ARC Prize 2026 Now

The frozen solver, registration, notebook builder, submission runner, score collector, and ranking collector are pushed to `main`. The only remaining external gate is authenticated Kaggle execution.

## One-time account setup

1. Join `ARC Prize 2026 - ARC-AGI-2` on Kaggle and accept its rules.
2. In Kaggle account settings, create an API token.
3. In this GitHub repository, open **Settings → Secrets and variables → Actions**.
4. Add these repository secrets:
   - `KAGGLE_USERNAME` — the exact Kaggle username.
   - Either `KAGGLE_API_TOKEN` — Kaggle's current token value — **or** `KAGGLE_KEY` — the key from a legacy `kaggle.json` file.
   - `KAGGLE_TEAM_NAME` — optional; exact leaderboard team name if it differs from the username.
5. Open **Actions → Frozen v3 private Kaggle cycle 001 → Run workflow**.

The workflow will:

- read the solver only from frozen commit `70672f3aa62d089bfffd072461a5713caae1e099`;
- hash every frozen source file;
- construct a private Kaggle notebook with internet disabled;
- attach the ARC Prize 2026 competition data;
- run `kaggle_submission_v3.py` on the hidden competition test;
- validate that `submission.json` contains exactly two grids for every test input;
- submit the immutable notebook version to the code competition;
- wait for Kaggle scoring;
- query the authenticated account's visible public rank;
- download the leaderboard evidence;
- commit the sanitized result to `results/private_cycle_001/result.json` and `RESULT.md`.

## Research firewall

Private Cycle 001 is evaluation-only. Do not edit `dsl.py`, `dsl_v3.py`, `benchmark_representation_v3.py`, or `kaggle_submission_v3.py` and still call the submission Cycle 001. The runner reconstructs them from the frozen commit even if newer files exist on `main`.

Any representation expansion must begin with a new committed registration named `HYPOTHESIS-representation-cycle-002.md` or later. The Cycle 001 Kaggle score may be used as a final aggregate outcome, not as task-level tuning feedback.

## Current official status

The first automated run prepared and hashed the kernel but recorded:

> **BLOCKED_AUTH — `KAGGLE_USERNAME` and a Kaggle API token were not configured as GitHub Actions secrets.**

Until Kaggle accepts and scores the notebook:

> **Unranked — no authenticated competition submission has been scored.**
