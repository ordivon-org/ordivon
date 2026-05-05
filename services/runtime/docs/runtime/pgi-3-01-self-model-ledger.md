# PGI-3.01 Self-Model Ledger

Status: **CLOSED** | Date: 2026-05-04
Phase: PGI-3.01
Tags: `pgi`, `runtime-evidence`, `self-model`, `identity`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add a SelfModelEntry object so Ordivon can learn from repeated experience
without turning review into self-punishment.

## Constraints

- Does not authorize action.
- Does not diagnose the creator.
- Does not freeze identity.
- Does not convert single events into confirmed patterns.

## Actions

Created:

```text
docs/governance/self-model-ledger-pgi-3.md
scripts/validate_pgi_self_model_entry.py
tests/fixtures/pgi_self_model/valid/not-enough-evidence.json
tests/fixtures/pgi_self_model/invalid/punitive-verdict.json
tests/fixtures/pgi_self_model/invalid/confirmed-with-one-evidence.json
tests/unit/governance/test_pgi_self_model_entry.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| not enough evidence | VALID |
| punitive verdict | INVALID |
| confirmed pattern with one evidence ref | INVALID |

## Review

PGI-3.01 is locally closed as a seed Self-Model Ledger. It makes self-knowledge
revisable, evidence-backed, and non-punitive.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-019: Self-model entries must distinguish patterns from verdicts and
support confirmed patterns with multiple evidence references.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-3.02 - Review-to-Rule Pipeline
```
