# Private Cycle 001 — Mechanical Packaging Note

**Registered:** 2026-07-27, before the next authenticated Kaggle attempt.

The first blocked workflow run established that Kaggle credentials were absent; no kernel was uploaded and no competition score or rank was produced. Before authentication is supplied, the packaging layer is hardened so the code-competition kernel is self-contained.

## Allowed mechanical changes

1. Embed the already-frozen source files from commit `70672f3aa62d089bfffd072461a5713caae1e099` into one generated `.ipynb` file.
2. Change kernel metadata from a multi-file script bundle to that generated notebook.
3. Support either the current `KAGGLE_API_TOKEN` authentication variable or the legacy `KAGGLE_USERNAME` plus `KAGGLE_KEY` pair without copying one credential into the other variable.
4. Poll for kernel completion, preserve logs, and capture the exact kernel version, submission score, and public rank.
5. Prevent a second scored Cycle 001 submission after a terminal `SCORED_NONZERO` or `SCORED_NULL` result.

## Prohibited changes

- no change to `dsl.py`;
- no change to `dsl_v3.py`;
- no change to `benchmark_representation_v3.py`;
- no change to `kaggle_submission_v3.py`;
- no change to ranking, fallback, pass@2, or output validation logic;
- no use of Kaggle score feedback for representation tuning.

These are execution and reproducibility repairs only. The frozen solver and Cycle 001 interpretation remain unchanged.