# Private Cycle 001 — Mechanical Packaging Note

**Registered:** 2026-07-27, before the next authenticated Kaggle attempt.

The first blocked workflow run established that Kaggle credentials were absent; no kernel was uploaded and no competition score or rank was produced. The authenticated run then created immutable kernel version 1, but Kaggle execution failed before a competition submission. The official competition file listing showed `arc-agi_evaluation_challenges.json`, while the frozen solver searched only `*test_challenges*.json`. Later notebook versions still failed before producing output. Because the frozen entrypoint uses `argparse`, executing it through Jupyter can pass the notebook kernel's own `-f <connection-file>` arguments into the script. After those repairs, the latest kernel completed and produced a validated `submission.json` inside the downloaded kernel-output directory. The competition CLI must therefore receive that exact downloaded path rather than a nonexistent repository-root filename. These changes are limited to execution plumbing; the frozen solver, grammar, ranking, fallback, validation, submission bytes, and predicted outputs are unchanged.

## Allowed mechanical changes

1. Embed the already-frozen source files from commit `70672f3aa62d089bfffd072461a5713caae1e099` into one generated `.ipynb` file.
2. Change kernel metadata from a multi-file script bundle to that generated notebook.
3. Support either the current `KAGGLE_API_TOKEN` authentication variable or the legacy `KAGGLE_USERNAME` plus `KAGGLE_KEY` pair without copying one credential into the other variable.
4. Poll for kernel completion, preserve logs, and capture the exact kernel version, submission score, and public rank.
5. Prevent a second scored Cycle 001 submission after a terminal `SCORED_NONZERO` or `SCORED_NULL` result.
6. Discover the attached ARC challenge JSON mechanically inside `/kaggle/input`, accepting official `evaluation_challenges` or `test_challenges` naming, verify that the selected JSON contains ARC task objects with `train` and `test` fields, and set `ARC_TEST_CHALLENGES` before executing the frozen entrypoint.
7. On kernel failure, attempt to download the executed notebook/output artifacts so the traceback is preserved before another mechanical repair.
8. Before invoking the frozen `kaggle_submission_v3.py` through `runpy`, replace Jupyter's launcher arguments with `sys.argv = ["kaggle_submission_v3.py"]`. This only prevents `argparse` from receiving the notebook kernel's unrelated `-f` connection-file argument; it does not alter any solver parameter or default.
9. Pass the exact validated downloaded file path, `results/private_cycle_001/kernel_output/submission.json`, to `kaggle competitions submit -f`, or copy those identical bytes to the CLI working location. No regeneration or alteration of the submission is permitted.

## Prohibited changes

- no change to `dsl.py`;
- no change to `dsl_v3.py`;
- no change to `benchmark_representation_v3.py`;
- no change to `kaggle_submission_v3.py`;
- no change to ranking, fallback, pass@2, or output validation logic;
- no use of Kaggle score feedback for representation tuning.

These are execution and reproducibility repairs only. The frozen solver and Cycle 001 interpretation remain unchanged.
