# Evidence Ledger Model — PGI-1

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-1.03
Tags: `pgi`, `evidence`, `ledger`, `epistemology`, `authority-boundary`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This model defines a shared evidence record for philosophical governance.

Core rule:

```text
Evidence can support a claim. Evidence does not authorize action.
```

## EvidenceRecord Fields

| Field | Meaning |
|-------|---------|
| object_type | Must be `PGIEvidenceRecord`. |
| schema_version | Prototype schema version. |
| evidence_id | Stable local identifier. |
| evidence_kind | file_read, command_output, test_result, human_review, receipt, external_source, observation, absence, contradiction. |
| source | Path, command, reference, or description. |
| observed_at | Exact time/date of observation. |
| actor | Who observed or recorded it. |
| scope | What the evidence can and cannot cover. |
| reproducibility | reproducible, contextual, non_reproducible, unknown. |
| freshness | CURRENT, STALE, DEGRADED, or MISSING, with last_verified/stale_after_days where available. |
| confidence | 0.0 to 1.0 support strength, not correctness proof. |
| supports_claims | Claims this evidence supports. |
| limitations | What remains unproven. |
| authority_boundary | Required statement that evidence does not authorize action. |

## Schema and Validator

Schema:

```text
src/ordivon_verify/schemas/pgi-evidence-record.schema.json
```

Validator:

```text
scripts/validate_pgi_evidence_record.py
```

The validator checks:

- required fields
- evidence kind enum
- file_read requires `source.path`
- command_output requires `source.command`
- confidence range
- CURRENT evidence requires `freshness.last_verified`
- authority boundary must say evidence does not authorize action

## Fixtures

```text
tests/fixtures/pgi_evidence_record/valid/file-read.json
tests/fixtures/pgi_evidence_record/invalid/missing-authority-boundary.json
tests/fixtures/pgi_evidence_record/invalid/bad-confidence.json
```

## Missing Evidence Semantics

| Evidence state | Trust consequence |
|----------------|-------------------|
| CURRENT | Can support selected claim within stated scope. |
| STALE | Claim requires review before reliance. |
| DEGRADED | Trust report must explain missing/weak evidence. |
| MISSING | Claim cannot be treated as established. |

Missing evidence should become one of:

- `DEGRADED` if action is low-risk and review can proceed
- `BLOCKED` if claim is high-consequence or required evidence is absent
- registered debt if the gap is accepted temporarily

## Boundary

EvidenceRecord is a prototype internal object. It is not a public standard,
does not authorize action, and does not replace human review.

Next stage:

```text
PGI-1.04 - Freshness and Current Truth Protocol
```
