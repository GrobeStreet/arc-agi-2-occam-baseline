# Registered Hypothesis — Representation Cycle 002

**Status:** ACTIVE REGISTRATION  
**Registered:** 2026-07-29 UTC  
**Prior completed cycle:** Private Cycle 001, valid Kaggle score `0.00`

## Scientific question

Can a trained recursive neural candidate generator, augmented with license-compatible procedural ARC data and paired with the frozen v3 symbolic specialist, increase exact pass@2 coverage enough to produce a nonzero hidden ARC-AGI-2 score without using public-evaluation or private-test feedback for tuning?

## Data firewall

Cycle 002 uses two evaluation layers.

### Development holdout

A deterministic 20% task holdout will be created from the official 1,000 public training tasks using:

```text
holdout(task_id) := int(SHA256("arc-cycle-002:" + task_id)[0:8], 16) mod 5 == 0
```

The exact task-ID list and its SHA-256 digest must be committed before model fitting. The split may be used once for model-family promotion after all hyperparameters and routing rules are frozen on the remaining 80% and synthetic development data.

The public training tasks were used in earlier measurement work, so this is a **development holdout**, not a claim of fully untouched external confirmation.

### Fresh endpoint

The fresh endpoint is one new ARC Prize 2026 Kaggle code submission made only after the complete Cycle 002 code, weights, router, hashes, and runtime package are frozen.

### Prohibited feedback

The following may not be used for Cycle 002 tuning:

- ARC-AGI-2 public evaluation task outputs or repeated public-evaluation score feedback;
- task-level information from private Cycle 001;
- hidden task identities, labels, visual inspection, or reverse engineering;
- repeated Kaggle probing;
- post-hoc task-specific rules;
- aggregate private score beyond closing the cycle after the one allowed submission.

The Cycle 001 score `0.00` may be cited only as the terminal baseline outcome.

## Frozen baseline

- Baseline solver: representation v3 Cycle 001
- Frozen source commit: `70672f3aa62d089bfffd072461a5713caae1e099`
- Kaggle submission: `55057282`
- Hidden public-leaderboard score: `0.00`
- Public-evaluation pass@2: `0/167`
- Prior deterministic holdout pass@2: `5/201` on the earlier v3 split; this is contextual only because Cycle 002 uses a new split

Before neural training begins, v3 must be scored on the exact Cycle 002 holdout to establish the matched development baseline.

## Allowed representation changes

Only these families are authorized:

1. **Recursive neural grid model**
   - A permissively licensed Tiny Recursive Model-style or equivalent recurrent refinement architecture.
   - Color permutation and geometric augmentations fixed before holdout evaluation.

2. **Synthetic procedural training**
   - Apache-2.0 ARC-GEN and other explicitly license-compatible generators.
   - Generator family, composition, color, size, and seed provenance recorded.
   - Entire generator families held out for synthetic stress testing.

3. **Neural-symbolic portfolio**
   - Frozen v3 may contribute a distinct second attempt when its candidate passes the pre-specified routing rule.
   - The router may use only training-derived confidence, augmentation stability, candidate agreement, complexity, and runtime-safe metadata.

4. **Calibration and abstention**
   - Confidence calibration may use only development OOF/holdout predictions.
   - No test-collection aggregation or private feedback.

## Explicitly forbidden changes

- Hand-authored rules targeted to specific public, private, or holdout tasks.
- New DSL primitives added after Cycle 002 holdout inspection.
- Changes inferred from Kaggle rank or aggregate score before the cycle closes.
- Changes to pass@2 routing after the development holdout is opened.
- Using public-evaluation tasks as a training set or iterative benchmark.
- Internet or external API calls during Kaggle evaluation.

## Frozen selection and execution policy

The final policy must be committed before the Cycle 002 holdout is scored.

Required properties:

- exactly two distinct attempts per test input;
- candidate 1 chosen by the frozen neural scoring rule;
- candidate 2 chosen to maximize pre-estimated marginal pass@2 value, not merely duplicate candidate 1;
- frozen symbolic candidate considered only under a pre-specified gate;
- deterministic seeds listed in the final model card;
- no inference-time training on the test collection as a whole;
- runtime target: within the enforced Kaggle code-competition limits, with a preferred engineering target of one GPU and less than eight hours;
- internet disabled during evaluation.

## Primary hypothesis and decision rules

### Development gate

Primary development endpoint: exact output-level pass@2 on the deterministic Cycle 002 holdout.

- **CLEAR DEVELOPMENT ADVANCE:** at least 5.0% pass@2, at least 10 net solved outputs above matched v3, and a task-cluster 95% interval for the paired difference that excludes zero.
- **DIRECTIONAL DEVELOPMENT ADVANCE:** positive net wins over v3 and at least 3.0% pass@2, but uncertainty includes zero.
- **NULL DEVELOPMENT RESULT:** less than 3.0% pass@2 or no positive net wins.
- **FAILURE:** regression versus v3, malformed outputs, data-firewall violation, or runtime failure.

A Kaggle submission is permitted only after at least a directional development advance and every packaging gate passes.

### Fresh Kaggle endpoint

- **CLEAR CYCLE ADVANCE:** valid hidden score at least 1.0% and higher than Cycle 001.
- **DIRECTIONAL CYCLE ADVANCE:** valid nonzero score below 1.0%.
- **NULL:** valid score `0.00`.
- **FAILURE:** scoring-format error, runtime error, rules violation, or no accepted submission.

The Kaggle outcome closes Cycle 002. It may not trigger another Cycle 002 modification.

## Secondary analyses

All are pre-specified:

- pass@1 and pass@2;
- output-level and task-level exact accuracy;
- candidate-oracle coverage;
- neural-only, symbolic-only, and portfolio ablations;
- selection regret;
- semantic output diversity between attempts;
- augmentation stability;
- runtime and memory;
- accuracy by pre-defined generator family;
- repeated-seed training variability;
- paired task-cluster bootstrap intervals.

## Required artifacts

Before holdout evaluation:

- exact holdout task list and digest;
- training code and configuration;
- model weights and hashes;
- synthetic data manifests and generator licenses;
- deterministic seeds;
- router code and decision thresholds;
- matched v3 baseline results;
- offline Kaggle package test.

After evaluation:

- complete per-output development table;
- bootstrap results;
- Kaggle submission reference and score;
- execution logs;
- verdict;
- updated paper limitations and result ledger.

## One-shot policy

The Cycle 002 development holdout is opened once after the architecture and router are frozen. Mechanical repairs are allowed only when they cannot depend on answer correctness. Any model or routing change after observing the holdout requires Cycle 003.

The Kaggle endpoint is submitted once under Cycle 002. Any substantive change afterward requires a new registered cycle.

## Publish-regardless commitment

Every positive, null, negative, blocked, or malformed outcome will be committed. A zero score or failed neural baseline will not be hidden or rebranded as success.