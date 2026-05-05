# PGI-1.03 Evidence Ledger Model

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-1.03
Tags: `pgi`, `runtime-evidence`, `evidence`, `schema`, `validator`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Turn "evidence before belief" into a reusable EvidenceRecord object with a
schema, validator, fixtures, and tests.

## Constraints

- Internal prototype only.
- No public schema standard claim.
- No action authorization.
- No replacement for review.

## Actions

Created:

```text
docs/governance/evidence-ledger-model-pgi-1.md
src/ordivon_verify/schemas/pgi-evidence-record.schema.json
scripts/validate_pgi_evidence_record.py
tests/fixtures/pgi_evidence_record/valid/file-read.json
tests/fixtures/pgi_evidence_record/invalid/missing-authority-boundary.json
tests/fixtures/pgi_evidence_record/invalid/bad-confidence.json
tests/unit/governance/test_pgi_evidence_record_validator.py
```

Updated:

```text
docs/governance/philosophical-surface-map-pgi-1.md
docs/governance/philosophical-governance-gap-ledger.jsonl
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| valid file-read evidence | VALID |
| missing authority boundary | INVALID |
| confidence > 1 | INVALID |

## Review

PGI-1.03 is locally closed as an internal EvidenceRecord seed. It provides a
common structure that future DecisionGate, Pack receipts, and review pipelines
can reference. It does not claim complete evidence modeling across all domains.

## Rule Update

CandidateRule proposal:

```text
PGI-CR-003: Any high-consequence claim should cite EvidenceRecords or explain
why structured evidence is unavailable. Evidence must include scope,
freshness, limitations, and an authority boundary.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-1.04 - Freshness and Current Truth Protocol
```
