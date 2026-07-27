# Representation Cycle 002 — Registration Template

> **STATUS: INACTIVE TEMPLATE. THIS FILE IS NOT A REGISTRATION.**
>
> Copy this file to `HYPOTHESIS-representation-cycle-002.md`, replace every placeholder, and commit it **before** changing representation code. A representation change made before that commit is exploratory and cannot be described as Cycle 002 confirmatory evidence.

## Registration timestamp

- UTC date/time: `<YYYY-MM-DDTHH:MM:SSZ>`
- Registration commit: `<filled after commit>`
- Prior completed cycle: `HYPOTHESIS-private-v3-cycle-001.md`

## Scientific question

`<State one falsifiable question about representation coverage or exact ARC performance.>`

## Data firewall

Choose exactly one fresh endpoint and document why it is unobserved for this cycle:

- [ ] deterministic public-training holdout not previously inspected under this representation;
- [ ] newly released official ARC data;
- [ ] untouched semi-private or private competition test;
- [ ] organizer-provided hidden evaluation.

Endpoint definition: `<exact split/hash/competition version>`

Prohibited data and feedback: `<list all previously observed public evaluation, Cycle 001 score, task-level private labels, etc.>`

The Cycle 001 aggregate Kaggle score may be cited as a terminal outcome. It may not be converted into task-level tuning feedback.

## Frozen baseline

- Solver version: `<v3 Cycle 001 or later registered baseline>`
- Source commit: `<SHA>`
- Primary endpoint: `<pass@2 output rate, task rate, coverage, etc.>`
- Baseline estimate: `<value and uncertainty if available>`

## Allowed representation changes

Only the following changes are authorized:

1. `<family or abstraction class>`
2. `<family or abstraction class>`
3. `<family or abstraction class>`

Explicitly forbidden changes:

- post-hoc task-specific rules;
- changes inferred from private task identities or labels;
- unregistered selector/ranking changes;
- changes to fallback behavior unless separately registered;
- repeated peeking at the fresh endpoint.

## Frozen selection and execution policy

- Candidate ranking: `<exact rule>`
- Pass@2 construction: `<exact two-attempt rule>`
- Runtime/compute cap: `<CPU/GPU/time/memory>`
- Internet policy: `<off/on and justification>`
- Random seeds: `<all seeds>`

## Primary hypothesis and decision rule

Primary contrast: `<new representation minus frozen baseline>`

- **CLEAR ADVANCE:** `<minimum net wins/effect, CI/p-value threshold>`
- **DIRECTIONAL:** `<positive but inconclusive condition>`
- **NULL:** `<no meaningful change>`
- **FAILURE:** `<regression, malformed output, runtime violation, etc.>`

## Secondary analyses

List all secondary endpoints in advance:

- coverage;
- candidate oracle;
- selection regret;
- runtime;
- semantic output diversity;
- task-family breakdowns that do not use hidden labels for tuning.

## One-shot policy

The fresh endpoint will be evaluated once. Mechanical execution repairs are allowed only when they cannot depend on answer correctness. Any method change after observing outcomes requires Cycle 003 or a separately registered correction.

## Publish-regardless commitment

Commit the complete outcome table, source hashes, execution logs, and verdict whether the result is positive, null, negative, or blocked.
