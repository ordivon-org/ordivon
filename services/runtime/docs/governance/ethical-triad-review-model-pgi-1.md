# Ethical Triad Review Model — PGI-1

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-1.08
Tags: `pgi`, `ethics`, `review`, `consequence`, `virtue`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This model turns normative ethics into an Ordivon review object.

Core rule:

```text
High-consequence action must review consequences, rules, and character.
No single lens is enough by itself.
```

## EthicalTriadReview Fields

| Field | Meaning |
|-------|---------|
| action_or_claim | What is being reviewed. |
| consequence_review | Likely outcomes and downstream effects. |
| rule_review | Constitution, NO-GO, authority, and boundary check. |
| character_review | What kind of person/system this action trains. |
| tradeoffs | Costs, opportunity costs, and tensions. |
| decision_posture | READY_WITHOUT_AUTHORIZATION, DEGRADED, BLOCKED, NEEDS_REVIEW. |
| authority_boundary | Required statement that review does not authorize action. |

## Validator Seed

```text
scripts/validate_pgi_ethical_triad_review.py
```

It rejects:

- missing consequence/rule/character review
- missing tradeoffs
- invalid decision posture
- review language that treats good outcome as proof of good process
- missing authority boundary

## Fixtures

```text
tests/fixtures/pgi_ethical_triad/valid/review.json
tests/fixtures/pgi_ethical_triad/invalid/outcome-proves-process.json
tests/fixtures/pgi_ethical_triad/invalid/missing-character.json
```

## Boundary

This model does not make ethics mechanical. It prevents obvious single-lens
failure: results without rules, rules without consequences, or virtue language
without evidence.

Next stage:

```text
PGI-1.09 - Philosophical Red-Team Suite
```
