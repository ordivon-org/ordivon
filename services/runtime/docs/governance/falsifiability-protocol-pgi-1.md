# Falsifiability and Failure Path Protocol — PGI-1

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-1.06
Tags: `pgi`, `falsifiability`, `failure-path`, `science-philosophy`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This protocol makes Ordivon claims revisable by requiring failure predicates.

Core rule:

```text
A claim that cannot name what would disconfirm it is not ready to govern action.
```

## FailurePredicate Fields

| Field | Meaning |
|-------|---------|
| predicate_id | Stable local identifier. |
| claim | Exact claim being tested. |
| claim_type | Claim taxonomy type from PGI-1.02. |
| would_disconfirm | Observations that would show the claim is wrong or incomplete. |
| measurement | How the disconfirming observation would be checked. |
| review_window | When the predicate should be re-checked. |
| action_if_disconfirmed | What happens if the claim fails. |
| authority_boundary | Required statement that this predicate does not authorize action. |

## Validator Seed

Validator:

```text
scripts/validate_pgi_failure_predicate.py
```

It rejects:

- empty `would_disconfirm`
- non-falsifiable markers such as none, nothing, never, cannot fail,
  impossible to disconfirm, always true, not applicable
- missing measurement/review/action path
- missing authority boundary

## Fixtures

```text
tests/fixtures/pgi_failure_predicate/valid/roadmap-claim.json
tests/fixtures/pgi_failure_predicate/invalid/non-falsifiable.json
tests/fixtures/pgi_failure_predicate/invalid/no-authority-boundary.json
```

## Boundary

Falsifiability does not mean every value claim becomes a lab experiment. It
means operational claims, roadmaps, rules, and model claims must name failure
paths before they guide high-consequence action.

Next stage:

```text
PGI-1.07 - Constitution and NO-GO Extraction
```
