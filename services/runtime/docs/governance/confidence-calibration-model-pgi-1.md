# Confidence Calibration Model — PGI-1

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-1.05
Tags: `pgi`, `confidence`, `calibration`, `bayesian`, `uncertainty`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This model prevents confidence from floating free of evidence.

Core rule:

```text
Confidence is a calibrated support estimate, not proof and not permission.
```

## Confidence Bands

| Band | Numeric range | Required posture |
|------|---------------|------------------|
| LOW | 0.00-0.39 | Treat as exploratory; do not rely for high-consequence action. |
| MEDIUM | 0.40-0.69 | Review required before reliance. |
| HIGH | 0.70-0.89 | Requires evidence refs, uncertainty, and numeric base rate. |
| VERY_HIGH | 0.90-1.00 | Requires strong evidence, base rate, failure path, and review trigger. |

## ConfidenceAssessment Fields

| Field | Meaning |
|-------|---------|
| assessment_id | Stable local identifier. |
| claim | Exact claim being assessed. |
| claim_type | Claim taxonomy type from PGI-1.02. |
| confidence | Numeric 0.0-1.0 confidence. |
| confidence_band | LOW, MEDIUM, HIGH, VERY_HIGH. |
| evidence_refs | EvidenceRecord, test, receipt, or file references. |
| base_rate | Prior/base-rate estimate when confidence >= 0.7. |
| uncertainty | Unknowns that remain. |
| calibration_status | uncalibrated, insufficient_history, calibrated. |
| review_trigger | What causes re-check. |
| authority_boundary | Required statement that confidence does not authorize action. |

## Validator Seed

Validator:

```text
scripts/validate_pgi_confidence_assessment.py
```

It checks:

- required fields
- confidence range
- confidence_band matches numeric range
- high confidence requires numeric base_rate
- evidence_refs and uncertainty are non-empty
- authority boundary says confidence does not authorize action

## Fixtures

```text
tests/fixtures/pgi_confidence_assessment/valid/high-confidence.json
tests/fixtures/pgi_confidence_assessment/invalid/high-confidence-no-base-rate.json
tests/fixtures/pgi_confidence_assessment/invalid/wrong-band.json
```

## Boundary

This model does not make subjective estimates objectively correct. It forces the
estimate to show evidence, uncertainty, and review triggers.

Next stage:

```text
PGI-1.06 - Falsifiability and Failure Path Protocol
```
