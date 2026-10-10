# ARC Prize 2026 Submission Readiness

Status date: 2026-10-10

This file is a submission-control checklist for the existing ARC-AGI-2 measurement paper and code. It does not claim a competition submission has occurred.

## Official 2026 deadlines

- ARC-AGI competition submissions due: **2026-11-02**
- Paper Prize papers due: **2026-11-08**
- Results announced: **2026-12-04**

Official competition page: https://arcprize.org/competitions/2026

## Current repository state

Current main before this checklist: `9ff50c78c87188e03283421444ffc7d7cfa566a0`.

The repository already contains:

- `PAPER.md`
- `ARC_Paper_Draft.pdf`
- `arc_kaggle_submission.ipynb`
- `kaggle_solver.py`
- `kaggle_submission_v2.py`
- `kaggle_submission_v3.py`
- `kaggle/`
- frozen results and analysis scripts
- MIT-0 license plus third-party notices

Latest CI observed before this update: **success** on the current main branch.

## Scientific claim boundary

The paper contribution is the corrected measurement/selection analysis, not a competitive solver.

Public corrected results:

- same-holdout reliability at k=1/2/3: **32.8% / 50.8% / 63.4%**
- MDL selection vs random on ambiguous cases: **+11.1 points**
- candidate oracle above MDL: **+3.7 points**
- frozen solver: **0/167 pass@2**

The corrected same-holdout design was frozen before the first complete run. The repository does **not** claim an independently timestamped public preregistration unless separate evidence is produced.

## Competition eligibility checks

Before final submission, verify all of the following against the live Kaggle competition:

- [ ] Kaggle account has joined the 2026 ARC-AGI-2 competition and accepted current rules.
- [ ] Competition data is attached to the notebook under the current dataset paths.
- [ ] The selected submission notebook runs with **internet disabled**.
- [ ] `submission.json` is generated in the exact current competition schema.
- [ ] All test task IDs are present exactly once.
- [ ] Each test input has exactly `attempt_1` and `attempt_2`.
- [ ] Output grids stay within ARC dimensions and colors 0–9.
- [ ] Runtime and memory fit Kaggle limits.
- [ ] No paid or external API call is needed during evaluation.
- [ ] The exact submitted notebook/version is frozen to a commit SHA.
- [ ] A live Kaggle submission is accepted by the competition system.
- [ ] The paper links to that exact working Kaggle code submission.
- [ ] The final paper does not describe the solver as competitive.
- [ ] The final paper uses "pre-specified" / "frozen before run" rather than unsupported public-preregistration language.

## Current unresolved submission choice

There are multiple submission implementations in the repo. Do **not** choose one merely because it is newest.

The final Kaggle path must be selected by checking:

1. internal consistency with the corrected paper;
2. deterministic, no-network execution;
3. current Kaggle input/output contract;
4. runtime/memory limits;
5. an actual accepted Kaggle test submission.

The paper can remain a measurement contribution even if the linked code submission scores poorly.

## Next execution step

Open the live Kaggle ARC-AGI-2 2026 competition under Bobby's account, accept/join the competition if needed, attach the existing notebook or upload the frozen submission code, run it with internet disabled, and confirm that Kaggle accepts the resulting submission.

Only after that verification should a Kaggle URL or competition score be added to `PAPER.md` or the README.
