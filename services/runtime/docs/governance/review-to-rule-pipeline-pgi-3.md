# Review-to-Rule Pipeline — PGI-3

Status: **CURRENT** | Date: 2026-05-04
Phase: PGI-3.02
Tags: `pgi`, `review`, `candidate-rule`, `lesson`, `policy-boundary`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Review-to-Rule asks:

```text
When does experience justify a CandidateRule?
```

The answer is deliberately conservative. A single painful event is usually a
review item, not a rule.

## Object

`PGIReviewToRuleCandidate` records:

- source reviews
- pattern basis
- evidence count
- severity
- emotional intensity
- cool-down review
- proposed rule
- rule scope
- candidate status
- retirement path
- next review
- policy boundary
- authority boundary

## Candidate Requirements

A CandidateRule requires one of:

- multiple examples
- high-severity rationale

It also requires:

- no absolute overreaction language
- cool-down review after high/extreme emotional intensity
- retirement path
- next review
- explicit `candidate only; no policy activation` boundary

## Validator Seed

```text
scripts/validate_pgi_review_to_rule_candidate.py
```

It rejects:

- single anecdotes promoted directly to candidate rules
- emotionally intense candidates without cool-down review
- absolute language such as always/never/forever
- missing candidate-only/no-policy boundary
- missing non-authorization boundary

## Boundary

This pipeline does not activate Policy. CandidateRule remains advisory and
reviewable.

Next stage:

```text
PGI-3.03 - CandidateRule Ethics Gate
```
