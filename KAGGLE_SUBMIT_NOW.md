# Submit Frozen V3 to ARC Prize 2026 Now

The frozen solver, registration, notebook builder, score collector, and ranking collector are in the repository. The only external gate is authenticated Kaggle execution.

## One-time account setup

1. Join the Kaggle competition and accept its rules:
   `https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2`
2. In Kaggle account settings, create an API token.
3. In this GitHub repository, open **Settings → Secrets and variables → Actions**.
4. Add repository secrets:
   - `KAGGLE_USERNAME` — your Kaggle username.
   - `KAGGLE_KEY` — the API token value from `kaggle.json`.
   - `KAGGLE_TEAM_NAME` — optional; use the exact leaderboard team name when it differs from the username.
5. Open **Actions → Frozen ARC v3 private Cycle 001 → Run workflow**.

The workflow will:

- hash the frozen source files;
- construct a private Kaggle notebook with internet disabled;
- attach the ARC Prize 2026 competition data;
- run `kaggle_submission_v3.py` on the hidden competition test;
- submit notebook version 1 to the code competition;
- poll until Kaggle scores the submission;
- download the leaderboard;
- calculate the exact public rank when the team name is available, or the tied score rank interval otherwise;
- commit `results/private_v3_cycle_001/status.json` and the sanitized score/ranking records.

## Research firewall

Cycle 001 is evaluation only. Do not edit `dsl.py`, `dsl_v3.py`, `benchmark_representation_v3.py`, or `kaggle_submission_v3.py` after the registration and still call the submission Cycle 001.

Any representation expansion must begin with a new committed registration based on `HYPOTHESIS-representation-cycle-002-TEMPLATE.md`. The Cycle 001 Kaggle score may be used as a final aggregate outcome, not as task-level tuning feedback.

## Current official status

Until the workflow returns a scored Kaggle submission:

> **Unranked — no authenticated competition submission has been scored.**
