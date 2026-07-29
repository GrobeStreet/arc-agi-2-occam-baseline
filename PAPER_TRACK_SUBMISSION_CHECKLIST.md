# ARC Prize 2026 Paper Track — Submission Checklist

**Status:** READY TO PREPARE; SUBMISSION NOT YET VERIFIED  
**Paper deadline:** 2026-11-08  
**Competition deadline:** 2026-11-02  
**Tie-break:** earlier paper entry wins ties

## Eligibility prerequisites

- [x] Public repository exists.
- [x] A real ARC-AGI-2 Kaggle code submission exists.
- [x] Corrected submission `55057282` executed on the official hidden schema.
- [x] Terminal public score recorded: `0.00`.
- [ ] Submitter-authored code licensed under ARC-compatible public-domain-style terms, preferably MIT-0 or CC0.
- [ ] Third-party code/data licenses inventoried and compatible with public sharing.
- [ ] Kaggle Paper Track joined under the intended account/team.
- [ ] Paper writeup linked to the exact Kaggle code submission.

## Required paper content

- [ ] Abstract states the actual contribution and the valid Kaggle score.
- [ ] Introduction explains ARC-AGI-2 and why measurement of candidate generation/selection matters.
- [ ] Prior work distinguishes this study from TRM, SOAR, CompressARC, ARChitects, and other calibration/MDL work.
- [ ] Approach gives an algorithm-level description of the same-target all-subsets audit.
- [ ] Results emphasize public evaluation and Kaggle outcomes; training analyses are clearly identified as diagnostic methodology rather than capability claims.
- [ ] Conclusion states what was learned and how it changes solver design.
- [ ] Limitations state that the submitted symbolic solver scored 0.00 and is not competitive.
- [ ] Reproducibility section includes exact commits, hashes, seeds, environment, and one-command routes.

## Rubric optimization

### Accuracy

- [ ] Link submission `55057282`.
- [ ] State public score `0.00` without euphemism.
- [ ] Explain that accuracy is weak and not the paper's primary contribution.

### Universality

- [ ] Show how coverage, conditional reliability, selector regret, and task-clustered uncertainty apply to neural, symbolic, and ensemble ARC systems.
- [ ] Include a concise protocol other teams can adopt.

### Progress

- [ ] Translate each negative result into a concrete solver-design implication.
- [ ] Include at least one stronger-baseline experiment if completed before submission.

### Theory

- [ ] Define the candidate-population estimand and equal-task estimand.
- [ ] Formalize the precision–coverage tradeoff.
- [ ] Explain why unanimous candidates can be overconfident under shared misspecification.

### Completeness

- [ ] Reconcile README, paper, PDF, status, and result ledgers.
- [ ] Include failed Version 8 routing and repaired Version 10 outcome as a transparent reproducibility note.
- [ ] Link all machine-readable outputs.

### Novelty

- [ ] Explicitly state what is new: same-target all-subsets design, nested-program correction, no-candidate denominator, selector-regret audit, and publish-regardless reversal.
- [ ] Avoid claiming novelty for standard bootstrap, MDL, or calibration concepts alone.

## Submission record

Fill this section immediately after submission.

- Kaggle Paper Track writeup URL: `<pending>`
- Paper submission timestamp UTC: `<pending>`
- Linked code submission URL/ref: `55057282`
- Repository commit submitted: `<pending>`
- PDF SHA-256: `<pending>`
- Writeup title: `<pending>`
- Team/account name: `<pending>`
- DOI opt-in: `<pending>`

## Final pre-submit checks

- [ ] No statement says the Cycle 001 score is pending, unranked, or blocked.
- [ ] No statement implies the 5/201 training holdout result transferred to hidden data.
- [ ] No subjective probability of winning.
- [ ] No unsupported claim that the paper has already been submitted.
- [ ] Every leaderboard fact is dated.
- [ ] Every external method and dataset has a citation and license note.
- [ ] PDF renders correctly and all links work.
- [ ] Repository is public and reproducible from a clean environment.
- [ ] Paper writeup submitted early rather than waiting for the deadline.