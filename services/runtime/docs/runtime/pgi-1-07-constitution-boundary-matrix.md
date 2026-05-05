# PGI-1.07 Constitution and NO-GO Extraction

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-1.07
Tags: `pgi`, `runtime-evidence`, `constitution`, `boundary`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Classify the ten personal constitution rules so values do not silently become
active Policy or remain vague slogans.

## Constraints

- No active Policy.
- No new action authorization.
- Existing NO-GO boundaries remain unchanged.
- Classifications are prototype governance guidance.

## Actions

Created:

```text
docs/governance/constitution-boundary-model-pgi-1.md
docs/governance/constitution-boundary-matrix-pgi-1.json
scripts/validate_constitution_boundary_matrix.py
tests/fixtures/pgi_constitution_boundary/invalid/active-policy.json
tests/unit/governance/test_pgi_constitution_boundary_matrix.py
```

Updated:

```text
docs/governance/philosophical-governance-gap-ledger.jsonl
```

## Evidence

Expected validator behavior:

| Payload | Expected |
|---------|----------|
| PGI constitution matrix | VALID |
| active-policy fixture | INVALID |

## Review

PGI-1.07 is locally closed as a boundary classification stage. It makes the
ten constitution rules usable for future DecisionGate and Pack work without
turning them into active enforcement.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-007: A personal constitution rule must carry classification and
activation_status before it is referenced by a DecisionGate or Pack.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-1.08 - Ethical Triad Review
```
