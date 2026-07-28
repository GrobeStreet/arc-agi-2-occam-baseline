# Private Cycle 001 — Mechanical Scoring Repair

**Registered after Kaggle reported a scoring error and before the repaired kernel was built.**

## Observed failure

Kaggle submission `55037417`, produced by frozen kernel version 8, reached `SubmissionStatus.COMPLETE` but was marked **Submission Scoring Error**.

A forensic comparison against the official competition download found:

- official sample submission: **240 tasks / 259 test outputs**;
- official competition test challenges: **240 tasks / 259 test outputs**;
- generated submission: **120 tasks / 172 test outputs**.

The generated task IDs matched the already-observed public evaluation corpus rather than the hidden competition test corpus.

## Root cause

The self-contained notebook's file-discovery code searched for `arc-agi_evaluation_challenges.json` before `arc-agi_test_challenges.json`. Because more than one ARC dataset was mounted under `/kaggle/input`, it selected the public evaluation file even though the official competition test file was present.

This was an input-routing and packaging defect. It was not a model-quality result.

## Authorized repair

Cycle 001 remains frozen with respect to:

- `dsl.py`;
- `dsl_v3.py`;
- `benchmark_representation_v3.py`;
- `kaggle_submission_v3.py`;
- candidate generation;
- ranking;
- fallback outputs;
- two-attempt policy.

The only authorized change is to the notebook wrapper:

1. locate an official `sample_submission.json`;
2. select the `arc-agi_test_challenges.json` whose task IDs exactly match that sample;
3. refuse to run on evaluation challenge files;
4. validate the generated `submission.json` against both the sample and challenge task/output counts before kernel completion.

No prediction logic or output ranking may change under this repair.

## Success criteria

The repaired kernel must report and validate:

- 240 task IDs;
- 259 test-output entries;
- exact equality with official sample task IDs;
- exact equality with official test-challenge task IDs;
- exactly `attempt_1` and `attempt_2` for every output;
- valid rectangular grids with integer colors 0–9.

Only after those checks pass may the repaired immutable kernel version be submitted.

## Interpretation

The original version-8 scoring error is classified as **MECHANICAL_INPUT_ROUTING_FAILURE**. The repaired submission remains Private Cycle 001 because it evaluates the identical frozen solver on the intended untouched competition endpoint.