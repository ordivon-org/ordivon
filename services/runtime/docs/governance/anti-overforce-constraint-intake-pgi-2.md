# Anti-Overforce Constraint Intake — PGI-2

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-2.04
Tags: `pgi`, `anti-overforce`, `constraint-intake`, `practical-reason`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This model prevents Ordivon from treating stalled progress as automatic proof
that more force is required.

Core rule:

```text
When work stalls, classify the constraint before increasing effort.
```

## Constraint Classes

| Class | Meaning |
|-------|---------|
| physical | fatigue, sleep debt, pain, illness, recovery need |
| emotional | panic, shame, comparison spiral, anger, grief |
| strategic | unclear goal, wrong sequence, bad tradeoff |
| environmental | noise, context switching, missing time block |
| conceptual | confused abstraction, weak model, ambiguous object |
| tooling | tool failure, missing dependency, slow feedback loop |
| social | unclear commitment, boundary conflict, support gap |
| financial | risk budget, cash pressure, downside exposure |
| unknown | not enough classification yet |

## Object

`PGIAntiOverforceIntake` records:

- stalled work
- constraint classes
- body/energy signal
- emotion signal
- strategic signal
- current impulse
- chosen response
- next safe step
- review time
- authority boundary

## Valid Responses

```text
continue_with_smaller_step
pause
rest
redesign
refuse
seek_help
split_scope
```

## Validator Seed

```text
scripts/validate_pgi_anti_overforce_intake.py
```

It rejects:

- effort-only continuation under unknown constraints
- continuation under exhaustion, panic, acute pain, or unsafe stop signals
- next steps that encode overforce language
- missing authority boundary

## Boundary

This intake does not authorize action and does not pathologize ambition. It
protects effort from becoming blind force.

Next stage:

```text
PGI-2.05 - Body and Energy Pack Seed
```
