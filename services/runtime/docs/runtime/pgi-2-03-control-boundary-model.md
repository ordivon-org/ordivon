# PGI-2.03 Control Boundary Classifier

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-2.03
Tags: `pgi`, `runtime-evidence`, `control-boundary`, `review`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add a ControlBoundaryReview object so Ordivon can separate process quality from
outcome quality across coding, finance, body, learning, emotion, relationship,
project, and AI work.

## Constraints

- Does not authorize action.
- Does not turn outcomes into moral verdicts.
- Does not excuse poor process because a result was favorable.

## Actions

Created:

```text
docs/governance/control-boundary-model-pgi-2.md
scripts/validate_pgi_control_boundary_review.py
tests/fixtures/pgi_control_boundary/valid/good-process-bad-outcome.json
tests/fixtures/pgi_control_boundary/invalid/good-outcome-laundering.json
tests/fixtures/pgi_control_boundary/invalid/quadrant-mismatch.json
tests/unit/governance/test_pgi_control_boundary_review.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| good process / bad outcome | VALID |
| good outcome laundering bad process | INVALID |
| quadrant mismatch | INVALID |

## Review

PGI-2.03 is locally closed as a seed control-boundary classifier. It gives
DecisionGate and future Pack reviews a way to say: this was controllable, this
was external uncertainty, and this result should update judgment without
becoming worship or self-punishment.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-012: Reviews must not infer process quality solely from outcome quality.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-2.04 - Anti-Overforce and Constraint Intake
```
