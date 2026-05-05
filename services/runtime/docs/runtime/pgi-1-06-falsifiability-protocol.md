# PGI-1.06 Falsifiability and Failure Path Protocol

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-1.06
Tags: `pgi`, `runtime-evidence`, `falsifiability`, `failure-path`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Prevent PGI roadmaps, rules, models, and philosophical claims from becoming
unfalsifiable doctrine.

## Constraints

- Internal prototype only.
- Does not authorize action.
- Does not reduce all values to measurements.
- Applies first to operational claims, roadmaps, rules, and model claims.

## Actions

Created:

```text
docs/governance/falsifiability-protocol-pgi-1.md
scripts/validate_pgi_failure_predicate.py
tests/fixtures/pgi_failure_predicate/valid/roadmap-claim.json
tests/fixtures/pgi_failure_predicate/invalid/non-falsifiable.json
tests/fixtures/pgi_failure_predicate/invalid/no-authority-boundary.json
tests/unit/governance/test_pgi_failure_predicate_validator.py
```

Updated:

```text
docs/governance/philosophical-governance-gap-ledger.jsonl
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| valid roadmap claim predicate | VALID |
| non-falsifiable predicate | INVALID |
| missing authority boundary | INVALID |

## Review

PGI-1.06 is locally closed as a seed falsifiability protocol. It creates a
validator-backed object that can be attached to future DecisionGate,
CandidateRule, and roadmap claims.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-006: Operational claims, roadmaps, model claims, and CandidateRules
should name what would disconfirm them before they guide high-consequence
decisions.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-1.07 - Constitution and NO-GO Extraction
```
