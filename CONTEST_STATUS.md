# ARC Prize 2026 — Contest Status

**Updated:** 2026-07-29  
**Repository:** `GrobeStreet/arc-agi-2-occam-baseline`

## ARC-AGI-2 competition

Private Cycle 001 is complete.

| Field | Verified value |
|---|---|
| Frozen solver commit | `70672f3aa62d089bfffd072461a5713caae1e099` |
| Corrected kernel | `robertmorong/grobestreet-arc-frozen-v3-cycle-001`, version 10 |
| Corrected submission | `55057282` |
| Official schema | 240 tasks / 259 outputs; sample and hidden challenge task IDs matched |
| Submission status | `COMPLETE` |
| Public score | **0.00** |
| Cycle verdict | **SCORED_NULL** |

The earlier Version 8 submission used the wrong mounted ARC challenge file and failed scoring. Version 10 changed only the input-routing wrapper, validated the official schema, and then received a valid score of zero. Therefore the 0.00 result is attributable to the frozen solver, not the prior packaging defect.

The displayed rank among many tied zero-score entries is not treated as a meaningful scientific statistic.

Authoritative result:

- [`PRIVATE_CYCLE_001_STATUS.md`](PRIVATE_CYCLE_001_STATUS.md)
- [`results/private_cycle_001/`](results/private_cycle_001/)

## Paper Prize

Verified assets:

- canonical paper source;
- generated PDF;
- public repository;
- real Kaggle code submission;
- complete reproducibility and negative-result record.

Unverified asset:

- **Kaggle Paper Track writeup submission.** No writeup URL or submission confirmation is currently recorded in the repository or connected email search.

Official status:

> **READY TO SUBMIT; NOT VERIFIED SUBMITTED**

See [`PAPER_TRACK_SUBMISSION_CHECKLIST.md`](PAPER_TRACK_SUBMISSION_CHECKLIST.md).

## Deadlines

- ARC competition submissions due: **2026-11-02**
- Paper submissions due: **2026-11-08**
- Results announced: **2026-12-04**

## Eligibility

Submitter-authored repository code is being moved to **MIT-0** for ARC 2026 eligibility. Third-party packages, data, models, and generators retain their own licenses and are inventoried in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

Before Paper Track submission:

1. merge the MIT-0 change;
2. complete the third-party license audit;
3. link the paper writeup to Kaggle submission `55057282`;
4. record the writeup URL, timestamp, repository commit, and PDF hash.

## Cycle 002

Cycle 002 is registered in [`HYPOTHESIS-representation-cycle-002.md`](HYPOTHESIS-representation-cycle-002.md).

The authorized path replaces the narrow standalone DSL with:

- a trained recursive neural grid model;
- license-compatible procedural synthetic data;
- the frozen symbolic solver as a specialist candidate source;
- a fixed two-attempt neural-symbolic router;
- a deterministic development holdout;
- one new one-shot Kaggle submission after promotion gates pass.

No public-evaluation hill climbing, private task feedback, repeated Kaggle probing, or task-specific hand rules are authorized.

## Strategic priority

1. Verify and submit the Paper Track writeup.
2. Reconcile the paper with the terminal 0.00 hidden result.
3. Complete license and eligibility hardening.
4. Reproduce a permissively licensed recursive neural baseline.
5. Train Cycle 002 with generator-family-separated validation.
6. Submit Cycle 002 once only after the registered development gates pass.

See [`ARC_TAKEOVER_2026.md`](ARC_TAKEOVER_2026.md) for the full weighted operating plan.