# Body and Energy Pack Seed — PGI-2

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-2.05
Tags: `pgi`, `body`, `energy`, `decision-quality`, `privacy`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Body/Energy Pack asks one governance question:

```text
Does the body support the decision quality required by the current action?
```

This is not a medical system, fitness tracker, or surveillance ledger. It is a
minimal decision-quality guardrail.

## Seed Rule

```text
High-consequence decisions are blocked under exhausted, ill, high-fatigue, or
extreme-fatigue states.
```

High-consequence decisions include major finance moves, irreversible architecture
changes, public commitments, external side effects, and relationship decisions
with durable consequences.

## Object

`PGIBodyEnergyReview` records:

- energy state
- fatigue level
- decision risk level
- whether a major decision is allowed
- body signal summary
- minimum next step
- privacy boundary
- authority boundary

## Privacy Boundary

Allowed:

- coarse self-reported energy state
- coarse fatigue level
- decision-quality warning
- next safe step

Forbidden in this seed:

- intimate raw data
- medical diagnosis
- compulsive quantification
- body metrics used as self-worth

## Validator Seed

```text
scripts/validate_pgi_body_energy_review.py
```

It rejects:

- high-consequence decisions allowed under exhausted/ill/high-fatigue states
- raw private data recording
- missing non-invasive privacy boundary
- missing "not medical advice" authority boundary

## Boundary

This Pack seed does not authorize action and is not medical advice. It protects
long-term agency by treating the body as the floor of decision quality.

Next stage:

```text
PGI-2.06 - Finance Pack Philosophical Hardening
```
