# Registered correction — representation v4.1 pass@2 scoring

**Registered:** 2026-07-27, before the corrected rerun is inspected.

During code review, the v4 runner was found to implement a stricter program-level criterion on tasks with multiple test inputs: it required one candidate program to solve every test item. Standard ARC pass@2 permits either of two submitted attempts to be correct independently for each test item. The two definitions coincide on single-test tasks but can differ on multi-test tasks.

V4.1 changes **only the scoring rule**:

- pass@1: attempt 1 must solve every test item;
- pass@2: every test item must be solved by attempt 1 or attempt 2;
- oracle: every test item must be solved by at least one demonstration-consistent candidate, not necessarily the same candidate across all test items.

The task split, representation library, family priors, ranking, thresholds, bootstrap, seed, and verdict rules remain frozen. Both v4 and v4.1 results remain in the record. If the verdict changes, v4.1 supersedes v4 for contest-format claims because it implements the benchmark’s attempt semantics.