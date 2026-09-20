# Data Temporal / Identity / Evolution Externalization R1

Date: 2026-09-20

## Scope

This stage extends the static GitHub data pilot into temporal and identity semantics:

- source revisions and vintages;
- representation-only vs logical-data revisions;
- reference identifiers and label drift;
- schema evolution;
- processing order vs source revision order;
- activation boundaries for Iceberg, Debezium, Beam and event-stream infrastructure.

## External owners

| Concern | Owner |
|---|---|
| metadata item mapping | ISO/IEC 11179-3:2023 + Amd 1:2026 |
| master/reference identifiers | ISO 8000-115:2024 |
| organization identity/name variants | ROR Schema 2.1 |
| table schema/snapshot evolution | Apache Iceberg spec v3 |
| database CDC | Debezium stable CDC model |
| event-time / watermark / late data | Apache Beam programming model |

These owners describe different responsibilities. They are not a single stack that must all be installed.

## Real revision pilot

Dataset:

`rfordatascience/tidytuesday/data/2026/2026-02-24/sfi_grants.csv`

Observed revisions:

1. `51504577572c78cf4908371d6eff5d99f53b0698` — 2026-02-22 13:27:21Z.
2. `bb24566e57c7ac138650b23d8183ae31d351f817` — 2026-02-22 15:49:44Z, message: `Properly encode data. (#1004)`.

The old bytes are not valid UTF-8; the new bytes are valid UTF-8. Decoding the old revision as Latin-1 and the new revision as UTF-8 yields:

- 7,269 data rows in each revision;
- identical 12-column DuckDB schema;
- identical canonical logical-row hash;
- different byte hashes.

Therefore the transition is:

`REPRESENTATION_ONLY_REVISION`

This is intentionally distinct from a data revision and a schema revision.

## Identity finding

The source contains:

- `proposal_id` — unique across all 7,269 rows in this sample;
- `research_body_ror_id`;
- `crossref_funder_registry_id`.

The ROR identifier `https://ror.org/01zgghk09` occurs with two source labels:

- CoderDojo Ireland Foundation
- Hello World Foundation t/a CoderDojo Foundation

This is not treated as two entities. ROR Schema 2.1 explicitly models multiple names/aliases/labels around one organization identifier. Identity therefore follows the identifier; names remain labels.

The actual ambiguity gate is the reverse condition:

`one label -> multiple identifiers`

Such cases require explicit mapping/review and may not be resolved by fuzzy matching alone.

## Schema evolution

The real SFI revision pair has no schema change.

A small conformance matrix exercises externalized rules:

- add nullable field -> additive-compatible;
- int -> bigint -> compatible promotion;
- drop -> destructive;
- incompatible type change -> breaking;
- rename without stable field identity or explicit mapping -> ambiguous drop+add;
- rename with explicit ISO/IEC 11179-style mapping -> compatible mapped rename.

Important boundary:

CSV has no stable field IDs. Iceberg can preserve field identity through schema evolution because its table model has field IDs; a CSV pipeline must not infer a rename merely because names look similar.

## Revision time vs processing time

The pilot deliberately replays the two real Git revisions in reverse processing order.

It still orders source state by Git revision time/ancestry. Processing order is not authoritative.

Because this is a bounded historical Git source:

- no watermark is applied;
- no late revision is discarded;
- Beam is retained only as the owner for future unbounded event-time semantics.

## Component activation decision

### Iceberg — not activated

Current workload already has immutable source snapshots through Git revisions and does not demonstrate:

- concurrent table writers;
- atomic table commits across data files;
- real schema/partition evolution at table scale;
- table-level time travel beyond Git source versions;
- row-level update lineage requirements.

### Debezium — not activated

Git history is the natural change log for this source. Debezium belongs at database transaction-log boundaries.

### Beam — not activated

The workload is bounded history. Watermark/allowed-lateness machinery belongs to unbounded event-time workloads.

### Kafka / Redpanda — not activated

No decoupled unbounded replay/fan-out workload has been demonstrated.

## Result

The current thin stack remains sufficient, but for a stronger reason:

`Git identity + byte digest + explicit encoding + external identifier semantics + revision ledger + executable compatibility gates`

The next activation should be triggered by a real workload that falsifies this sufficiency, not by an architecture diagram.
