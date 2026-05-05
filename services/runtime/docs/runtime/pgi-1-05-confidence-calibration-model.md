# PGI-1.05 Confidence Calibration Model

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-1.05
Tags: `pgi`, `runtime-evidence`, `confidence`, `calibration`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Turn Bayesian confidence discipline into a validator-backed
ConfidenceAssessment object.

## Constraints

- Internal prototype only.
- Confidence does not authorize action.
- Does not prove correctness.
- Does not replace EvidenceRecord or review.

## Actions

Created:

```text
docs/governance/confidence-calibration-model-pgi-1.md
scripts/validate_pgi_confidence_assessment.py
tests/fixtures/pgi_confidence_assessment/valid/high-confidence.json
tests/fixtures/pgi_confidence_assessment/invalid/high-confidence-no-base-rate.json
tests/fixtures/pgi_confidence_assessment/invalid/wrong-band.json
tests/unit/governance/test_pgi_confidence_assessment_validator.py
```

Updated:

```text
docs/governance/philosophical-governance-gap-ledger.jsonl
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| valid high confidence | VALID |
| high confidence without base rate | INVALID |
| wrong confidence band | INVALID |

## Review

PGI-1.05 is locally closed as a seed model. It creates a bridge between
EvidenceRecord and future DecisionGate work by making high confidence carry
base-rate and uncertainty obligations.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-005: Confidence >= 0.7 requires evidence references, uncertainty, and a
numeric base rate. Confidence never authorizes action.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-1.06 - Falsifiability and Failure Path Protocol
```
