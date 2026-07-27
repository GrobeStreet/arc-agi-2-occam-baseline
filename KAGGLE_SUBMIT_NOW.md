# Submit Frozen V3 to ARC Prize 2026 Now

The frozen solver, registration, code-kernel runner, score collector, ranking collector, and post-private representation firewall are pushed to `main`. The only remaining external gate is authenticated Kaggle account access.

## One-time secure account setup

1. Join **ARC Prize 2026 — ARC-AGI-2** on Kaggle and accept its competition rules.
2. In Kaggle account settings, generate a current API token.
3. In this GitHub repository, open **Settings → Secrets and variables → Actions**.
4. Add repository secrets:
   - `KAGGLE_USERNAME` — the exact Kaggle username;
   - `KAGGLE_API_TOKEN` — the current token value from Kaggle settings;
   - `KAGGLE_TEAM_NAME` — optional, only when the leaderboard team name differs from the username.
5. Open **Actions → Frozen ARC v3 private Cycle 001 → Run workflow**.

Do not paste the token into an issue, commit, pull request, notebook, or chat message.

## What the workflow does

The authoritative workflow is `.github/workflows/private-v3-cycle-001.yml`. It:

- reconstructs the solver only from frozen commit `70672f3aa62d089bfffd072461a5713caae1e099`;
- hashes every frozen source file;
- creates a private, internet-disabled Kaggle code kernel attached to the ARC Prize 2026 competition;
- runs `kaggle_submission_v3.py` on the hidden competition test;
- verifies that the kernel produced `submission.json`;
- submits the exact immutable kernel version to the code competition;
- waits for Kaggle scoring;
- queries the authenticated account's visible public rank;
- downloads the leaderboard evidence;
- commits the sanitized result to `results/private_cycle_001/result.json` and `RESULT.md`;
- prevents a second scored Cycle 001 run.

## Research firewall

Private Cycle 001 is evaluation-only. The runner reconstructs `dsl.py`, `dsl_v3.py`, `benchmark_representation_v3.py`, and `kaggle_submission_v3.py` from the frozen commit even when newer experimental files exist on `main`.

Any representation expansion must begin by copying `HYPOTHESIS-representation-cycle-002-TEMPLATE.md` to `HYPOTHESIS-representation-cycle-002.md`, completing every field, and committing that registration **before** source changes or a new fresh-endpoint run. The Cycle 001 Kaggle score may be used as a terminal aggregate outcome, not as task-level tuning feedback.

## Current official status

The automated run has already prepared and hashed the frozen source, but it recorded:

> **BLOCKED_AUTH — `KAGGLE_USERNAME` and `KAGGLE_API_TOKEN` are not configured as GitHub Actions secrets.**

Until Kaggle accepts and scores the code-kernel version:

> **UNRANKED — no authenticated competition submission has been scored.**
