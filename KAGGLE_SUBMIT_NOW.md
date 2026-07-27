# Submit Frozen V3 to ARC Prize 2026 Now

The frozen solver, private-cycle registration, self-contained notebook builder, authenticated submission workflow, score collector, ranking collector, and post-private representation firewall are pushed to `main`. The only remaining external gate is authenticated Kaggle account access.

## One-time secure account setup

1. Join **ARC Prize 2026 — ARC-AGI-2** on Kaggle and accept its competition rules.
2. In Kaggle account settings, generate a current API token.
3. In this GitHub repository, open **Settings → Secrets and variables → Actions**.
4. Configure:
   - `KAGGLE_USERNAME` — the exact Kaggle username, as either a repository Actions secret or Actions variable;
   - `KAGGLE_API_TOKEN` — the current token value, as a repository Actions secret;
   - legacy alternative: `KAGGLE_KEY` as a secret together with `KAGGLE_USERNAME`.
5. Open **Actions → Frozen ARC v3 private Cycle 001 → Run workflow**.
6. Enter the exact confirmation: `SUBMIT_FROZEN_V3_CYCLE_001`.

Do not paste the token into an issue, commit, pull request, notebook, or chat message.

## What the workflow does

The single authoritative workflow is `.github/workflows/private-v3-cycle-001.yml`. It:

- reconstructs `dsl.py`, `dsl_v3.py`, `benchmark_representation_v3.py`, and `kaggle_submission_v3.py` only from frozen commit `70672f3aa62d089bfffd072461a5713caae1e099`;
- records SHA-256 hashes for every frozen source file;
- embeds the exact source in one self-contained private Kaggle notebook;
- disables internet and attaches the ARC Prize 2026 competition data;
- runs the frozen solver on the hidden competition test;
- verifies `submission.json` and the exactly-two-attempt contract;
- submits the exact immutable kernel version to the code competition;
- waits for Kaggle scoring;
- queries the authenticated account's visible public rank and preserves leaderboard evidence;
- commits the sanitized result to `results/private_cycle_001/result.json` and `RESULT.md`;
- refuses a second terminal Cycle 001 submission.

## Research firewall

Private Cycle 001 is evaluation-only. The runner reconstructs the four frozen solver files from the registered commit even when newer experimental files exist on `main`.

Any representation expansion must begin by copying `HYPOTHESIS-representation-cycle-002-TEMPLATE.md` to `HYPOTHESIS-representation-cycle-002.md`, completing every field, and committing that registration **before** source changes or a new fresh-endpoint run. The Cycle 001 aggregate Kaggle score may be used as a terminal outcome, not as task-level tuning feedback.

## Current official status

The automated run has already reconstructed and hashed the frozen source and built the self-contained notebook, but it recorded:

> **BLOCKED_AUTH — Kaggle credentials are not configured in GitHub Actions.**

Until Kaggle accepts and scores the exact code-kernel version:

> **UNRANKED — no authenticated competition submission has been scored.**
