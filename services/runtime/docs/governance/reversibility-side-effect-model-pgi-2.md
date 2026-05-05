# Reversibility and Side-Effect Model — PGI-2

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-2.02
Tags: `pgi`, `reversibility`, `side-effect`, `decision-gate`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This model classifies how undoable an action is and what side effects it may
create.

Core rule:

```text
The less reversible an action is, the slower and more evidence-heavy the gate
must become.
```

## Side-Effect Classes

| Class | Example |
|-------|---------|
| none | Pure read/inspection. |
| local_doc | Local documentation edit. |
| local_code | Local source/test edit. |
| dependency | Dependency or lockfile change. |
| public_claim | External-facing statement. |
| financial | Capital, trading, or risk-budget action. |
| health | Body/energy intervention. |
| relationship | Promise, boundary, or social commitment. |
| external_system | API, service, deployment, or third-party side effect. |

## Reversibility Levels

| Level | Meaning |
|-------|---------|
| reversible | Can be cleanly undone with low residue. |
| partially_reversible | Can be changed later but leaves cost or residue. |
| irreversible | Cannot be undone in meaningful terms. |
| unknown | Not enough evidence; high side-effect actions cannot stay here. |

## Validator Seed

```text
scripts/validate_pgi_reversibility_assessment.py
```

It rejects:

- high side-effect classes without review_required=true
- high side-effect classes with unknown reversibility
- missing blast radius, rollback path, irreversible loss, or authority boundary

## Fixtures

```text
tests/fixtures/pgi_reversibility_assessment/valid/local-doc.json
tests/fixtures/pgi_reversibility_assessment/invalid/high-side-effect-no-review.json
tests/fixtures/pgi_reversibility_assessment/invalid/unknown-external.json
```

## Boundary

This model does not authorize action. It gives DecisionGate a side-effect and
reversibility input.

Next stage:

```text
PGI-2.03 - Control Boundary Classifier
```
