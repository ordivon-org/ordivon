# PGI-2.04 Anti-Overforce and Constraint Intake

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-2.04
Tags: `pgi`, `runtime-evidence`, `anti-overforce`, `constraint-intake`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add an AntiOverforceIntake object so Ordivon can distinguish effort, pause,
rest, redesign, refusal, help-seeking, and scope splitting when work stalls.

## Constraints

- Does not authorize action.
- Does not make rest mandatory for every blockage.
- Does not turn body or emotion signals into surveillance.
- Does not override explicit NO-GO boundaries.

## Actions

Created:

```text
docs/governance/anti-overforce-constraint-intake-pgi-2.md
scripts/validate_pgi_anti_overforce_intake.py
tests/fixtures/pgi_anti_overforce/valid/coding-blockage-redesign.json
tests/fixtures/pgi_anti_overforce/invalid/try-harder-unknown.json
tests/fixtures/pgi_anti_overforce/invalid/exhausted-continue.json
tests/unit/governance/test_pgi_anti_overforce_intake.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| coding blockage redesign | VALID |
| try harder with unknown constraints | INVALID |
| exhausted continuation | INVALID |

## Review

PGI-2.04 is locally closed as a seed anti-overforce classifier. It gives future
Pack reviews a way to say: this is not a motivation problem yet; it may be a
constraint, energy, strategy, tooling, or scope problem.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-013: Stalled work should classify constraints before escalating effort.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-2.05 - Body and Energy Pack Seed
```
