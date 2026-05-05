# Control Boundary Model — PGI-2

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-2.03
Tags: `pgi`, `control-boundary`, `stoicism`, `review`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This model turns the Stoic control distinction into an Ordivon review object:

```text
Judge process by controllable factors.
Treat outcomes as evidence, not as automatic verdicts.
```

## Object

`PGIControlBoundaryReview` classifies:

- `controllable_factors`
- `uncontrollable_factors`
- `mixed_factors`
- `process_quality`
- `outcome_quality`
- `process_outcome_quadrant`
- `outcome_interpretation`
- `review_posture`

## Quadrants

| Quadrant | Meaning |
|----------|---------|
| good_process_good_outcome | Keep the process, but still inspect repeatability. |
| good_process_bad_outcome | Investigate uncertainty without self-punishment. |
| bad_process_good_outcome | Do not let luck launder a weak process. |
| bad_process_bad_outcome | Repair process and review downside. |
| mixed_or_pending | Hold judgment until evidence improves. |

## Validator Seed

```text
scripts/validate_pgi_control_boundary_review.py
```

It rejects:

- process/outcome quadrant mismatches
- claims that good outcome proves good process
- claims that bad outcome proves bad process
- missing controllable or mixed factors
- authority boundaries that fail to say the review does not authorize action

## Boundary

This model does not authorize action, excuse negligence, or deny outcome
evidence. It prevents both outcome worship and outcome self-punishment.

Next stage:

```text
PGI-2.04 - Anti-Overforce and Constraint Intake
```
