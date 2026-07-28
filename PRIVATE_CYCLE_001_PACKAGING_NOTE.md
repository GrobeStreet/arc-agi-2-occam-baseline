# Private Cycle 001 — Mechanical Packaging Note

**Registered:** 2026-07-27, before the next authenticated Kaggle attempt.  
**Extended:** 2026-07-28, before the scoring-repair submission.

The first blocked workflow run established that Kaggle credentials were absent; no kernel was uploaded and no competition score or rank was produced. The authenticated run then created immutable kernel version 1, but Kaggle execution failed before a competition submission. The official competition file listing showed `arc-agi_evaluation_challenges.json`, while the frozen solver searched only `*test_challenges*.json`. Later notebook versions still failed before producing output. Because the frozen entrypoint uses `argparse`, executing it through Jupyter can pass the notebook kernel's own `-f <connection-file>` arguments into the script. After those repairs, kernel version 8 completed and produced a syntactically valid `submission.json`.

A subsequent plumbing assumption treated `-f` as a local path. The official Kaggle code-competition API instead treats `-f` as the **name of an output file inside the specified immutable kernel version**. The submission step therefore restored the registered filename `submission.json` while retaining the exact kernel owner, slug, and version.

Kaggle later marked version 8 as **Submission Scoring Error**. A forensic comparison against the official downloaded competition bundle identified the exact cause before any model change:

- official sample/test set: **240 tasks / 259 outputs**;
- submitted artifact: **120 tasks / 172 outputs**;
- task ID sets did not match.

The generated notebook had prioritized `arc-agi_evaluation_challenges.json`, so it solved the public evaluation split instead of the attached hidden competition test. This was a data-source selection and validation defect, not a solver result. The scoring-repair attempt is authorized to select only a challenge file whose task IDs and output multiplicities exactly match the colocated official `sample_submission.json`. The notebook must fail before submission if that equality check does not hold.

All changes in this note are corrections to execution, datasource wiring, and validation only. The frozen source commit, grammar, ranking, fallbacks, pass@2 policy, and prediction algorithm remain unchanged.

## Allowed mechanical changes

1. Embed the already-frozen source files from commit `70672f3aa62d089bfffd072461a5713caae1e099` into one generated `.ipynb` file.
2. Change kernel metadata from a multi-file script bundle to that generated notebook.
3. Support either the current `KAGGLE_API_TOKEN` authentication variable or the legacy `KAGGLE_USERNAME` plus `KAGGLE_KEY` pair without copying one credential into the other variable.
4. Poll for kernel completion, preserve logs, and capture the exact kernel version, submission score, and public rank.
5. Prevent a second **scored** Cycle 001 submission after a terminal `SCORED_NONZERO` or `SCORED_NULL` result. A scoring-error artifact is not a scored terminal result and may receive one mechanical replacement.
6. Discover the attached competition input mechanically inside `/kaggle/input`, but select only an `arc-agi_test_challenges.json` whose task ID set and per-task test-output counts exactly match a colocated `sample_submission.json`.
7. Reject `evaluation_challenges` and any challenge JSON that does not match the official sample submission one-for-one.
8. Write an input-selection manifest containing the chosen sample path, challenge path, task count, output count, and key-set validation result.
9. Validate the generated `submission.json` against the official sample before it is accepted as a kernel output and again before the code-competition submission call.
10. On kernel failure, attempt to download the executed notebook/output artifacts so the traceback is preserved before another mechanical repair.
11. Before invoking the frozen `kaggle_submission_v3.py` through `runpy`, replace Jupyter's launcher arguments with `sys.argv = ["kaggle_submission_v3.py"]`. This only prevents `argparse` from receiving the notebook kernel's unrelated `-f` connection-file argument; it does not alter any solver parameter or default.
12. For the code-competition submission, pass the kernel output filename exactly as `submission.json` together with the immutable kernel reference and version. Downloading a copy for validation and hashing remains allowed, but the local path is not substituted for the kernel-output filename in the API request.
13. Label the replacement as a scoring-error repair that supersedes submission `55037417`; do not present the failed artifact as a score or rank.

## Prohibited changes

- no change to `dsl.py`;
- no change to `dsl_v3.py`;
- no change to `benchmark_representation_v3.py`;
- no change to `kaggle_submission_v3.py`;
- no change to ranking, fallback, pass@2, or output validation logic inside the frozen solver;
- no use of Kaggle score feedback for representation tuning;
- no repeated submission after one schema-valid scoring-repair artifact receives a visible score.

These are execution and reproducibility repairs only. The frozen solver and Cycle 001 interpretation remain unchanged.