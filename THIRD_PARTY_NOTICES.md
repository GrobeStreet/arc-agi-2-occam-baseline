# Third-Party Notices and License Inventory

**Scope:** current repository plus explicitly planned Cycle 002 dependencies  
**Status:** initial eligibility audit; update whenever code, weights, data, or generators are added

The original code authored by Robert Morong in this repository is licensed under **MIT-0**. Third-party software, data, models, and generated assets remain governed by their own licenses.

## Current runtime dependencies

The repository declares the following Python dependencies. No source code from these packages is intentionally vendored in this repository.

| Dependency | Expected license | Use |
|---|---|---|
| NumPy | BSD-3-Clause | arrays and numerical operations |
| pandas | BSD-3-Clause | tabular analysis |
| SciPy | BSD-3-Clause | statistics and optimization |
| PyArrow | Apache-2.0 | parquet I/O |
| Matplotlib | PSF-based/BSD-compatible | publication figures |
| Python-Markdown | BSD-3-Clause | paper HTML generation |
| Playwright for Python | Apache-2.0 | PDF rendering automation |

Exact installed versions should be pinned in release artifacts. Each package's own license and notices govern redistribution.

## Data

| Source | License/status | Use |
|---|---|---|
| `arcprize/ARC-AGI-2` | Apache-2.0 | official public training and evaluation tasks |
| Kaggle ARC Prize 2026 competition data | competition rules plus applicable ARC data license | private code-competition evaluation; hidden data are not redistributed |

The repository must never commit hidden Kaggle test inputs or outputs.

## Planned Cycle 002 components

These components are authorized by the Cycle 002 registration but are **not yet incorporated**. Their license terms must be preserved if used.

| Component | Reported license | Planned role |
|---|---|---|
| `google/ARC-GEN` | Apache-2.0 | procedural synthetic ARC training data |
| `SamsungSAILMontreal/TinyRecursiveModels` | MIT | recursive neural baseline/reference implementation |

Before merging either component:

1. pin the exact upstream commit;
2. preserve its license and copyright notices;
3. document whether code is copied, adapted, invoked as a dependency, or used only as methodological reference;
4. record model-weight and generated-data licenses separately;
5. verify compatibility with ARC Prize 2026 open-source requirements.

## Submitter-authored assets

Unless a file carries a different notice, submitter-authored source code, analysis scripts, documentation, and configuration are released under MIT-0.

## Exclusions

The following are not granted under this repository's MIT-0 license:

- third-party package source code;
- ARC-AGI task data beyond its own license;
- Kaggle hidden competition data;
- third-party pretrained weights;
- logos, trademarks, or externally sourced media;
- content that carries an explicit separate license.

## Release checklist

Before any prize-eligible release or Paper Track submission:

- [ ] Pin every dependency and upstream repository commit.
- [ ] Include all required third-party license texts and notices.
- [ ] Verify no hidden competition data are present.
- [ ] Verify every model weight can be redistributed publicly.
- [ ] Verify every synthetic-data generator and generated dataset has documented provenance.
- [ ] Re-run a clean-room license inventory over the final release tree.

This inventory is a reproducibility and eligibility record, not legal advice.