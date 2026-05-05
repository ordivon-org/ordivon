# Self-Model Ledger — PGI-3

Status: **CURRENT** | Date: 2026-05-04
Phase: PGI-3.01
Tags: `pgi`, `self-model`, `identity`, `pattern`, `non-punitive`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Self-Model Ledger asks:

```text
Who is the system helping the creator become?
```

The ledger exists to learn patterns, not to issue identity verdicts.

## Object

`PGISelfModelEntry` records:

- domain
- update type
- observation
- evidence references
- pattern status
- self-language
- verdict-language flag
- next review
- authority boundary

## Update Types

```text
capability
bias
value
recurring_failure
strength
constraint
direction
```

## Pattern Status

| Status | Meaning |
|--------|---------|
| not_enough_evidence | One or more observations exist but should not become pattern yet. |
| candidate_pattern | Pattern hypothesis exists and needs future review. |
| confirmed_pattern | Multiple evidence references support a stable pattern. |
| retired | Pattern is no longer useful or has been superseded. |

## Non-Punitive Language Rule

Forbidden:

```text
I am always...
I am never...
I am broken...
I am a failure...
This proves who I am.
fixed identity
```

Allowed:

```text
A candidate pattern may exist...
The current evidence suggests...
Not enough evidence yet...
Review after the next comparable case...
```

## Validator Seed

```text
scripts/validate_pgi_self_model_entry.py
```

It rejects:

- fixed or punitive identity verdicts
- `verdict_language_present=true`
- confirmed patterns with fewer than two evidence references
- not-enough-evidence entries that fail to name evidence insufficiency
- missing "not a verdict" authority boundary

## Boundary

This ledger does not authorize action, diagnose the self, or freeze identity. It
keeps Ordivon's self-learning humble and revisable.

Next stage:

```text
PGI-3.02 - Review-to-Rule Pipeline
```
