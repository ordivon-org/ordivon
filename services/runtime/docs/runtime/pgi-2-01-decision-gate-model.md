# PGI-2.01 DecisionGate Object Model

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-2.01
Tags: `pgi`, `runtime-evidence`, `decision-gate`, `practical-reason`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Unify PGI-1 objects into one operational decision gate seed.

## Constraints

- Does not authorize execution.
- Does not activate Policy.
- Does not replace human review.
- Does not create public schema standard.

## Actions

Created:

```text
docs/governance/decision-gate-model-pgi-2.md
scripts/validate_pgi_decision_gate.py
tests/fixtures/pgi_decision_gate/valid/ready-without-authorization.json
tests/fixtures/pgi_decision_gate/invalid/ready-with-missing-evidence.json
tests/fixtures/pgi_decision_gate/invalid/authorizes-execution.json
tests/unit/governance/test_pgi_decision_gate_validator.py
```

Updated:

```text
docs/governance/philosophical-governance-gap-ledger.jsonl
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| ready-without-authorization | VALID |
| ready with missing evidence | INVALID |
| authorizes execution | INVALID |

## Review

PGI-2.01 is locally closed as a seed DecisionGate. It connects the PGI-1
substrate into a single review object. The next risk is side-effect and
reversibility classification, which PGI-2.02 should handle.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-010: READY_WITHOUT_AUTHORIZATION DecisionGate posture cannot contain
missing_evidence and must not claim execution authority.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-2.02 - Reversibility and Side-Effect Classifier
```
