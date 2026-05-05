# Finance Pack Philosophical Hardening — PGI-2

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-2.06
Tags: `pgi`, `finance`, `risk`, `freedom`, `fragility`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Finance Pack asks:

```text
Does this financial decision increase freedom or fragility?
```

PGI-2.06 is review-only. It does not open broker write, live trading, execution,
or financial advice.

## Object

`PGIFinanceDecisionReview` records:

- decision type
- review posture
- thesis
- evidence summary
- base-rate note
- max loss
- time horizon
- review date
- FOMO/gambling risk
- self-proof risk
- freedom/fragility assessment
- live-trading NO-GO
- broker-write boundary
- authority boundary

## Hard Boundaries

```text
live_trading_no_go = true
broker_write_boundary includes "no broker write"
authority_boundary includes "does not authorize action" and "not financial advice"
```

## Red-Team Patterns

| Pattern | Governance response |
|---------|---------------------|
| FOMO urgency | hold/reject posture |
| self-proof trade | hold/reject posture |
| guaranteed profit language | invalid thesis |
| unknown max loss | invalid action review |
| READY treated as buy signal | authority boundary failure |

## Validator Seed

```text
scripts/validate_pgi_finance_decision_review.py
```

## Boundary

This hardening stage is a governance review surface only. No capital movement,
broker API, live execution, or personalized financial recommendation is granted.

Next stage:

```text
PGI-2.07 - Learning Pack Seed
```
