# Builder / Ordivon Pack Hardening — PGI-2

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-2.08
Tags: `pgi`, `builder`, `ordivon-pack`, `complexity`, `debt`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Builder Pack asks:

```text
Does this change strengthen Ordivon, or create hidden complexity and debt?
```

This is Ordivon governing its own construction.

## Object

`PGIBuilderChangeReview` records:

- change surface
- intent
- files touched
- truth impact
- value impact
- action impact
- complexity delta
- debt declaration
- anti-overforce check
- whether the change improves the decision maker
- tests or receipts
- authority boundary

## Surfaces

```text
cli
checker
schema
fixture
docs
architecture
ai_onboarding
pack
adapter
roadmap
```

## Validator Seed

```text
scripts/validate_pgi_builder_change_review.py
```

It rejects:

- complexity-increasing changes without declared debt
- complexity-increasing changes without anti-overforce review
- missing tests or receipts
- vague "vision" expansion with no evidence surface
- missing authority boundary

## Boundary

Builder hardening does not stop ambition. It makes ambition pay rent in tests,
receipts, explicit debt, and decision-maker improvement.

Next stage:

```text
PGI-2.09 - Relationship and Emotion Pack Boundary
```
