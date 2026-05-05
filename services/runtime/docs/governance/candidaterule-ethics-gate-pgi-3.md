# CandidateRule Ethics Gate — PGI-3

Status: **CURRENT** | Date: 2026-05-04
Phase: PGI-3.03
Tags: `pgi`, `candidate-rule`, `ethics`, `over-control`, `policy-boundary`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

CandidateRule Ethics Gate asks:

```text
Does this proposed rule protect the system, or does it over-control life?
```

## Object

`PGICandidateRuleEthicsReview` records:

- consequence check
- rule boundary check
- virtue check
- false-positive cost
- human cost
- exception path
- expiry or review date
- over-control risk
- candidate status
- policy activation NO-GO
- authority boundary

## Required Ethical Lenses

| Lens | Question |
|------|----------|
| consequence | What improves and what can be harmed? |
| rule boundary | Where does the rule apply and where does it not apply? |
| virtue | What kind of person/system does repeated use cultivate? |
| false positive | What useful action might be blocked? |
| human cost | Does the rule create anxiety, rigidity, or surveillance? |

## Validator Seed

```text
scripts/validate_pgi_candidate_rule_ethics.py
```

It rejects:

- block-level over-control risk left as candidate
- over-control language in candidate rules
- missing exception/review path
- disabled Policy NO-GO
- missing candidate-only/non-authorization boundary

## Boundary

This gate does not activate Policy. It keeps CandidateRule advisory, scoped,
reviewable, and human-cost aware.

Next stage:

```text
PGI-3.04 - Personal Casebook
```
