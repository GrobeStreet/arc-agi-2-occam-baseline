# ARC Cycle 001 — Version 10 Scoring Repair

**State:** `REPAIRED_SUBMISSION_SCORE_PENDING`  
**Kernel:** `robertmorong/grobestreet-arc-frozen-v3-cycle-001` version `10`  
**Frozen solver commit:** `70672f3aa62d089bfffd072461a5713caae1e099`  
**Supersedes scoring-error submission:** `55037417`  
**Accepted repaired submission:** `55057282`  
**Accepted:** 2026-07-28T14:17:46.087000Z  
**Last authenticated observation:** 2026-07-28T14:22:59.791547Z

## Root cause of version 8 failure

Kernel version 8 accidentally selected `arc-agi_evaluation_challenges.json`, producing 120 tasks / 172 outputs. The official code-competition schema requires 240 tasks / 259 outputs. Kaggle therefore marked submission `55037417` as a scoring-format error.

## Mechanical repair

The prediction grammar, ranking, fallbacks, and two-output policy remain unchanged. The version-10 wrapper now selects the official `arc-agi_test_challenges.json` only when its task IDs exactly match `sample_submission.json`, and refuses kernel completion unless the generated output matches the official schema.

## Official schema proof

- 240 tasks: **validated**
- 259 test outputs: **validated**
- Sample task IDs match: **true**
- Test-challenge task IDs match: **true**
- Submission SHA-256: `457a36b6ed4b360a3e7d95a79c4de144b1c27051ce3559473901b33d6fc60a6d`

## Competition record

- Submission ref: `55057282`
- Submission status: `SubmissionStatus.PENDING`
- Public score: **not available yet**
- Public rank: **not available yet**
- Teams at last observation: **1,290**

## Interpretation

Kaggle accepted the schema-correct mechanically repaired submission. Later duplicate submission calls returned HTTP 400, but those calls occurred after submission `55057282` already existed and did not invalidate it. The accepted repair is awaiting scoring.

The machine-readable authoritative snapshot is `results/private_cycle_001/submission_55057282_status.json`.
