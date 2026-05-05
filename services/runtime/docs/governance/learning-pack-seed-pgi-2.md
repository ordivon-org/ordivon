# Learning Pack Seed — PGI-2

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-2.07
Tags: `pgi`, `learning`, `capability`, `output`, `judgment`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Learning Pack asks:

```text
Is knowledge becoming capability, judgment, and work?
```

The Pack does not reward endless intake. Study must eventually connect to an
output, skill transfer, decision improvement, or Ordivon object.

## Object

`PGILearningReview` records:

- learning track
- intent
- input materials
- output artifact
- skill transfer
- application context
- consumption-loop risk
- next application
- authority boundary

## Tracks

```text
philosophy
software_engineering
ai_systems
finance
writing
product
communication
health
```

## Validator Seed

```text
scripts/validate_pgi_learning_review.py
```

It rejects:

- output artifacts that are `none`, `not yet`, or consumption-only
- next actions that only say read/watch/study more
- block-level consumption loops without pause or application-first next step
- missing authority boundary

## Boundary

This Pack seed does not authorize action. It keeps learning from becoming
information hoarding or self-soothing disguised as progress.

Next stage:

```text
PGI-2.08 - Builder / Ordivon Pack Hardening
```
