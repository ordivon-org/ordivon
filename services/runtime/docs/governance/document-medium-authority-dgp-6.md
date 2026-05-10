# Document Medium Authority — DGP-6

Status: **CURRENT** | Date: 2026-05-09 | Phase: DGP-6
Authority: current_status | Owner: Governance

## Purpose

Define authority boundaries for each document and artifact medium in Ordivon. The format of a document does not determine its authority — but certain formats are structurally incapable of being source_of_truth.

## Medium Authority Table

| Medium | Source/Generated | Authority Default | current_truth_allowed | Notes |
|---|---|---|---|---|
| Markdown (.md) | Source | Depends on doc registration | Can be T0/T1 if registered | Primary governance prose medium |
| JSONL ledger (.jsonl) | Source | supporting_evidence | Only if schema-governed and registered | Machine-readable data, not prose truth |
| JSON Schema (.schema.json) | Source | supporting_evidence | No | Validation contract, not business authority |
| Generated Registry Index | Generated | generated_view | No | Compiled from source adapters. Non-truth. |
| HTML | Generated from .md | supporting_evidence | No (unless explicit source provenance exists) | Review surface, not source. |
| Typst/PDF | Generated snapshot | generated_view | No | Publication snapshot, not live truth. |
| Mermaid/D2 diagram | Source or generated | supporting_evidence | Only if registered as architecture doc | Visualization, not structural authority. |
| Excalidraw canvas | Source (exploration) | supporting_evidence | No | Design exploration, not truth. |
| SQLite/DuckDB | Generated query substrate | generated_view | No | Index/query surface, not source. |
| Image/screenshot | Generated capture | supporting_evidence | No | Evidence, not truth. |
| Notebook (.ipynb) | Generated output | supporting_evidence | No | Analysis output, not governance. |

## Hard Invariants

1. Generated media must not be current_truth_allowed unless explicit source provenance is declared and registered in current-truth-entry-map.
2. HTML/dashboard defaults to generated_view — no self-upgrade to truth.
3. PDF snapshot defaults to generated_view — no self-upgrade to truth.
4. JSONL ledgers with schema can be current_status if registered and active.
5. Schema files (.schema.json) are validation contracts, not business authorization.
6. Diagrams support architecture docs but do not replace them.
7. SQLite/DuckDB generated indexes are queryable derivatives, not source of truth.

## Relationship to Existing Checks

- `authority-boundary` (DGP-3): blocks generated + proposal from being current truth.
- `lifecycle-invariants` (DGP-2): blocks archived/tombstoned from being truth.
- `generated-as-truth` (RG-3): blocks generated views marked as source_of_truth.
- Current truth entry map (DGP-3): the single authoritative register of truth documents.
