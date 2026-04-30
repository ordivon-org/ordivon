# Document Registry Schema

Status: **ACCEPTED** | Date: 2026-04-30 | Phase: DG-1
Tags: `governance`, `document`, `registry`, `schema`, `manifest`

## 1. Purpose

The Document Registry is a future manifest that links every governed document
to its metadata: type, status, authority, freshness, relationships.

This schema defines the manifest format. **Implemented** in DG-2:
`docs/governance/document-registry.jsonl` (17 entries) with checker at
`scripts/check_document_registry.py`.

**Status note**: The status `accepted` is a valid alias for `current` — a document
that has passed stakeholder acceptance is `accepted` (maps to `current`). Both
are recognized by the checker.

## 2. Registry Entry Schema

Each entry is one JSONL line:

```json
{
  "doc_id": "string",
  "title": "string",
  "path": "string",
  "doc_type": "string",
  "status": "string",
  "authority": "string",
  "phase": "string|null",
  "owner": "string|null",
  "date_created": "ISO8601",
  "date_modified": "ISO8601",
  "last_verified": "ISO8601|null",
  "staleness_days_max": "int|null",
  "supersedes": "string|null",
  "superseded_by": "string|null",
  "ai_read_priority": "int|null",
  "related_ledgers": ["string"],
  "related_receipts": ["string"],
  "related_tests": ["string"],
  "tags": ["string"],
  "notes": "string|null"
}
```

## 3. Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `doc_id` | string | Yes | Unique identifier (slug, e.g., `dg-pack-contract`) |
| `title` | string | Yes | Human-readable title |
| `path` | string | Yes | Filesystem path relative to repo root |
| `doc_type` | string | Yes | From document taxonomy (e.g., `governance_pack`) |
| `status` | string | Yes | From lifecycle (e.g., `proposed`, `current`) |
| `authority` | string | Yes | From authority model (e.g., `current_status`) |
| `phase` | string\|null | No | Associated phase (e.g., `DG-1`, `7P`, `6R`) |
| `owner` | string\|null | No | Person or role responsible |
| `date_created` | ISO8601 | Yes | When document was first created |
| `date_modified` | ISO8601 | Yes | When document was last modified |
| `last_verified` | ISO8601\|null | No | When document was last verified as current |
| `staleness_days_max` | int\|null | No | Maximum days before this doc is considered stale |
| `supersedes` | string\|null | No | `doc_id` of the document this one replaces |
| `superseded_by` | string\|null | No | `doc_id` of the document that replaces this one |
| `ai_read_priority` | int\|null | No | 0-4, per AI onboarding policy |
| `related_ledgers` | [string] | No | Linked JSONL ledger paths |
| `related_receipts` | [string] | No | Linked receipt paths |
| `related_tests` | [string] | No | Linked test file paths |
| `tags` | [string] | No | Search/discovery tags |
| `notes` | string\|null | No | Any additional context |

## 4. Registry Validation Rules

A future registry checker should validate:

1. Every `doc_id` is unique
2. Every `path` exists in the filesystem
3. Every `doc_type` is a valid taxonomy type
4. Every `status` is a valid lifecycle status
5. Every `authority` is a valid authority level
6. No document with `status=current` has `last_verified` older than `staleness_days_max`
7. Every `supersedes`/`superseded_by` reference resolves to an existing `doc_id`
8. No `root_context` or `phase_boundary` document has `status=stale`
9. No `receipt`-type document has `superseded_by` set
10. No `ledger`-type document has `live_order=true`

## 5. Sample Entries (Illustrative)

```jsonl
{"doc_id":"dg-pack-contract","title":"Document Governance Pack Contract","path":"docs/governance/document-governance-pack-contract.md","doc_type":"governance_pack","status":"proposed","authority":"current_status","phase":"DG-1","owner":null,"date_created":"2026-04-30","date_modified":"2026-04-30","last_verified":null,"staleness_days_max":30,"supersedes":null,"superseded_by":null,"ai_read_priority":2,"related_ledgers":[],"related_receipts":[],"related_tests":[],"tags":["governance","document","pack","contract"],"notes":"Phase DG-1 core deliverable"}
{"doc_id":"phase-7p-summit","title":"Alpaca Paper Dogfood Stage Summit","path":"docs/product/alpaca-paper-dogfood-stage-summit-phase-7p.md","doc_type":"stage_summit","status":"closed","authority":"current_status","phase":"7P","owner":null,"date_created":"2026-04-29","date_modified":"2026-04-29","last_verified":"2026-04-29","staleness_days_max":null,"supersedes":null,"superseded_by":null,"ai_read_priority":2,"related_ledgers":["docs/runtime/paper-trades/paper-dogfood-ledger.jsonl"],"related_receipts":["docs/runtime/paper-trades/PT-001.md","docs/runtime/paper-trades/PT-002.md"],"related_tests":["tests/unit/finance/test_paper_execution.py","tests/unit/finance/test_paper_dogfood_ledger.py"],"tags":["phase-7p","stage-summit","paper-dogfood","closure"],"notes":"Phase 7P closure document"}
{"doc_id":"paper-dogfood-ledger","title":"Paper Dogfood JSONL Ledger","path":"docs/runtime/paper-trades/paper-dogfood-ledger.jsonl","doc_type":"ledger","status":"closed","authority":"supporting_evidence","phase":"7P","owner":null,"date_created":"2026-04-29","date_modified":"2026-04-29","last_verified":"2026-04-29","staleness_days_max":null,"supersedes":null,"superseded_by":null,"ai_read_priority":3,"related_ledgers":[],"related_receipts":["docs/runtime/paper-trades/PT-001.md"],"related_tests":["scripts/check_paper_dogfood_ledger.py"],"tags":["ledger","jsonl","paper-dogfood","evidence"],"notes":"30 events, 16 invariants, all pass. Evidence only, NOT execution authority."}
{"doc_id":"phase-boundaries","title":"Current Phase Boundaries","path":"docs/ai/current-phase-boundaries.md","doc_type":"phase_boundary","status":"current","authority":"source_of_truth","phase":null,"owner":null,"date_created":"2026-04-29","date_modified":"2026-04-29","last_verified":"2026-04-29","staleness_days_max":7,"supersedes":null,"superseded_by":null,"ai_read_priority":1,"related_ledgers":[],"related_receipts":[],"related_tests":[],"tags":["boundaries","phase","status","no-go","ai-onboarding"],"notes":"Must be updated within 1 session of any phase state change."}
{"doc_id":"phase-8-tracker","title":"Phase 8 Readiness Tracker","path":"docs/runtime/paper-trades/phase-7p-readiness-tracker.md","doc_type":"tracker","status":"deferred","authority":"current_status","phase":"7P","owner":null,"date_created":"2026-04-29","date_modified":"2026-04-29","last_verified":"2026-04-29","staleness_days_max":30,"supersedes":null,"superseded_by":null,"ai_read_priority":3,"related_ledgers":[],"related_receipts":[],"related_tests":[],"tags":["phase-8","readiness","tracker","deferred"],"notes":"3/10 criteria met. Phase 8 DEFERRED."}
```

## 6. Registry Storage (Deferred)

Options for registry storage:
- **JSONL file** (simplest): `docs/governance/document-registry.jsonl`
- **DB-backed** (future): SQLite or PostgreSQL with document metadata
- **Git-tracked** (recommended for DG-1 follow-up): JSONL in repo, versioned
- **Wiki-backed** (when wiki exists): wiki pages generate from registry + docs

For DG-1, no storage is implemented. The schema is a design artifact.

## 7. Non-Goals for DG-1

- Registry implementation (JSONL file, DB, or wiki)
- Registry validation checker
- Automated registry population
- Registry integration with CI
- Registry integration with wiki

DG-1 defines the schema. Implementation is deferred.
