# Data Lifecycle Census R1

Date: 2026-09-20  
Scope: local Ordivon repositories and currently observable Linux workstation/runtime substrate  
Workspace: `ws-data-lifecycle-census-r1-20260920`  
Base revision: `b8ed8399f9411249c30f3b140e7e53741358878b`

## 1. Purpose

This census asks one concrete question:

> Can Ordivon move data from an identified external or internal source to a reproducible decision/action and then use observed outcomes to improve future collection and processing?

The answer is **PARTIAL**.

Ordivon already has strong domain-local data capabilities in Research, Market Capital, Artifact and Operations. The main deficit is not another database. The main deficit is a cross-domain lifecycle spine: interoperable catalog metadata, data contracts/products, operational lineage, rights/retention binding, and outcome-to-collection feedback.

This document does not create a new Ordivon data-management methodology. External owners remain authoritative:

- DAMA-DMBOK / DCAM for organizational data-management capability;
- NIST Big Data Reference Architecture for role/fabric decomposition;
- W3C DCAT 3 for interoperable catalog metadata;
- FAIR for reusable/findable data principles;
- W3C PROV for semantic provenance;
- OpenLineage for operational Job/Run/Dataset lineage;
- Bitol ODCS/ODPS for data contracts and data products;
- ISO 28500 WARC for web capture;
- ISO 14721 OAIS for long-term digital preservation;
- ISO 15489 for records-management concerns where applicable;
- ISO/IEC 5259 and domain-specific checks for analytics/ML data quality;
- established security/privacy controls rather than a new Ordivon data-security scheme.

## 2. Grounded local inventory

The census scanned the current Git repositories under `/root/projects` plus `/root/workstation-lab`.

### Live / executable substrate

| Capability | Observed state | Census decision |
|---|---|---|
| DuckDB | `/usr/bin/duckdb`, version 1.5.5 | KEEP |
| PostgreSQL | service running; client 18.6 | KEEP |
| Prometheus | 3.14.0 installed; `network-v2-prometheus.service` running | KEEP |
| Temporal | service + Ordivon workers running | KEEP for durable workflows; not a data catalog |
| Pandera | declared by Research and Market Capital | KEEP for dataframe/schema validation |
| PyArrow | declared by Research/Market Capital; Artifact freezes PyArrow 25.0.1 for independent Parquet reading | KEEP |
| WARC/warcio | Artifact declares `warcio>=1,<2` and has a live WARC profile | KEEP |
| Parquet | live Artifact profile + Market Capital witness Parquet files | KEEP |
| OpenTelemetry | Artifact declares OTel API/SDK 1.44.0 | KEEP, but not yet cross-domain data observability |

### Present but not a live shared data service

| Capability | Actual standing | Census decision |
|---|---|---|
| Redpanda | Finance optional compose only; no host executable/service observed | WORKLOAD_GATED |
| QuestDB | Finance optional compose only | WORKLOAD_GATED |
| Grafana | Workstation config/Ansible + generated unit; not observed running | WORKLOAD_GATED |
| OpenLineage | authority record/design references; no emitter/backend observed | ACTIVATE |
| Dagster | provider research only; no executable/package/project observed | WORKLOAD_GATED |
| ClickHouse | references only; no executable/service observed | WORKLOAD_GATED |
| Kafka | references only; no executable/service observed | WORKLOAD_GATED |
| Apache Iceberg | no grounded local implementation observed | WORKLOAD_GATED |
| dbt | references only; no executable observed | WORKLOAD_GATED |
| Great Expectations | Research comparison/reference only | DO_NOT_ADD while Pandera covers current dataframe contracts |

### Existing domain data mass

This is a working-tree census of selected structured extensions, not a claim about total retained bytes:

- `ordivon-paper2`: ~370 MB / 1,552 structured-data files observed;
- `ordivon-research-v2`: ~273 MB / 1,254 structured-data files observed;
- frozen Paper1 repository: ~96 MB / 354 structured-data files observed;
- `ordivon-market-capital-next`: 190 structured-data files including 5 Parquet files;
- Artifact v2 already has Dataset and Web Archive artifact families.

This is enough real workload to justify a lifecycle spine. No synthetic “big-data demo” is needed.

## 3. Lifecycle census

Status meanings:

- **KEEP** — mature local implementation exists and should remain.
- **PARTIAL** — real behavior exists but is domain-local or lacks cross-domain semantics.
- **MISSING** — a proven lifecycle responsibility is not represented adequately.
- **WORKLOAD_GATED** — mature external solution exists, but current workload does not justify activating it.
- **RETIRE/REPLACE** — Ordivon-local semantics should yield to an external owner.

| Stage | Current evidence | Standing | Next owner/action |
|---|---|---|---|
| 0. Information / decision requirement | Research profiles, finance contracts, task goals | PARTIAL | Keep domain-native requirements; require new shared data products to name consumer, decision/use, freshness and evidence boundary |
| 1. Source discovery | OpenAlex/Crossref/etc. in Research; provider discovery in Finance; external-news paths | KEEP/PARTIAL | Preserve source-native discovery; add source metadata to catalog |
| 2. Acquisition | API clients, Browserless paths, Runtime InputAuthorities, finance observer materials | KEEP/PARTIAL | API/feed first; bind rights, acquisition method, timestamps and source IDs |
| 3. Ingestion | raw files + Runtime materialization; no shared event bus | PARTIAL | Do not install Kafka/Redpanda by default; activate Redpanda only for demonstrated replay/fan-out/streaming need |
| 4. Raw preservation | extensive research raw JSON, Artifact WARC, Finance raw witness records | PARTIAL | Standardize immutable/raw identity and retention semantics; WARC for web evidence |
| 5. Parse / normalize | GROBID/research parsers, artifact readers, domain parsers | KEEP/PARTIAL | Keep domain parsers replaceable; never overwrite raw evidence |
| 6. Clean / validate | Pandera, JSON Schema, Artifact Dataset Contract, independent Parquet readers | KEEP | Reuse executable contracts; quarantine invalid/unknown rather than silently deleting |
| 7. Integrate / entity resolution | ad-hoc domain joins/mappings | MISSING | Add explicit canonical-ID mapping with source identity, method and confidence only when cross-source joining demands it |
| 8. Metadata / catalog | Authority Catalog exists, but it catalogs external authorities rather than datasets | MISSING | Adopt DCAT 3 as the shared dataset/data-service metadata model |
| 9. Provenance / lineage | Git/digests, domain lineage, W3C PROV authority, OpenLineage authority | PARTIAL | Emit OpenLineage for actual transformations; use PROV for semantic derivations |
| 10. Data contract / product | Artifact Dataset Contract; domain outputs | PARTIAL | Align new shared producer/consumer contracts to ODCS 3.2 and products to ODPS 1.1 rather than expanding a private contract language |
| 11. Exploration / analytics | DuckDB, Pandas/PyArrow, PostgreSQL, statistical tooling | KEEP | DuckDB remains the default local analytical waist |
| 12. Modeling / synthesis | Research statistics/ML, Finance model lineage, Agent synthesis | KEEP/PARTIAL | Preserve model/method/run identity and validation separately from dataset quality |
| 13. Serving / retrieval | files, SQL, domain APIs, artifact delivery | PARTIAL | Add serving surfaces only per consumer; no universal warehouse/API required |
| 14. Decision / action | Runtime/Host/Distribution/Finance effect boundaries | KEEP/PARTIAL | Bind decision/action receipts to the exact data product/version used |
| 15. Outcome measurement | Prometheus + domain acceptance/evidence | PARTIAL | Define outcome metrics per consumer; telemetry is not automatically business/scientific outcome |
| 16. Feedback / recollection | mostly manual/domain-local | MISSING | Persist outcome -> source/collection/quality/model policy changes and feed them into the next requirement cycle |

## 4. Cross-cutting fabrics

| Fabric | Standing | Evidence / gap |
|---|---|---|
| Governance + rights | PARTIAL | strong authority/effect boundaries exist; dataset-level owner, license, retention and permitted-use binding is inconsistent |
| Metadata + catalog | MISSING | no shared DCAT-compatible data catalog; current Authority Catalog has a different purpose |
| Quality | KEEP/PARTIAL | Pandera + JSON Schema + independent Artifact readers are real; quality remains use-case-specific |
| Provenance + lineage | PARTIAL | Git/digests/domain lineage are strong; OpenLineage is not yet emitted end-to-end |
| Security + privacy | PARTIAL | strong system/security substrate exists; data classification/PII propagation must be bound to catalog/contracts |
| Observability | PARTIAL | Prometheus is live and OTel exists in Artifact; data freshness/volume/schema/quality/lineage-break metrics are not unified |

## 5. External-owner substitutions

The lifecycle spine must reduce Ordivon-owned semantics:

| Need | External owner |
|---|---|
| dataset/data-service catalog | W3C DCAT 3 |
| semantic provenance | W3C PROV |
| runtime transformation lineage | OpenLineage |
| producer/consumer data contract | Bitol ODCS 3.2 |
| data-product description | Bitol ODPS 1.1 |
| raw web preservation | ISO 28500 WARC |
| long-term preservation | ISO 14721 OAIS |
| analytical file interchange | Apache Parquet / Arrow |
| local analytical execution | DuckDB |
| dataframe validation | Pandera |
| durable workflow | Temporal / domain-native workflow owner |
| security/privacy | existing NIST/ISO-aligned Ordivon Security/Workstation controls |

Do **not** create `OrdivonDatasetOntology`, `OrdivonLineageProtocol`, `OrdivonDataContractLanguage`, or a generic Ordivon ETL engine.

## 6. First implementation waves

### P0 — shared metadata + lineage spine

1. Add authoritative records/observations for DCAT 3 and current Bitol ODCS/ODPS.
2. Define the minimum mapping from existing Artifact Dataset Contracts to ODCS without breaking existing acceptance evidence.
3. Add an OpenLineage emission adapter at transformation boundaries; do not deploy a heavy backend until events exist.
4. Bind catalog entries to raw/source identity, version, rights, quality evidence and lineage pointers.
5. Preserve W3C PROV only for semantic derivations that exceed operational dataflow.

Acceptance: one Research flow and one Finance flow can be traced from source bytes -> validated data -> transformation -> data product -> decision/claim using external-standard identifiers.

### P1 — Research pilot

Use a real existing literature/data flow:

`source API response -> immutable raw -> normalized record -> Pandera/schema gate -> analytical dataset -> statistical/LLM transformation -> paper evidence/claim`.

Acceptance requires:
- exact source/version/capture identity;
- retained raw material;
- catalog metadata;
- explicit quality result;
- OpenLineage Job/Run/Dataset edges;
- semantic provenance for a derived claim where needed;
- reproducible final artifact.

### P1 — Finance pilot

Use the existing Market Capital witness path:

`provider observation -> raw witness -> same-cut validation -> Parquet -> Pandera/contract -> DuckDB query/model -> decision-support output`.

Acceptance requires the same lifecycle spine while preserving the current rule that storage ACKs/offsets do not establish Economic/Capital Truth or external write authority.

### P2 — outcome feedback

For both pilots, link consumed data-product version to:
- downstream action/claim;
- outcome/acceptance evidence;
- any resulting change to source priority, collection policy, validation, model or retention.

This is the first point at which the system becomes a closed learning loop instead of a data warehouse.

## 7. Explicit non-goals / activation gates

Do not install infrastructure merely to fill an architecture box.

- **Redpanda/Kafka:** activate only when sustained stream replay, fan-out or decoupled consumers are demonstrated.
- **Iceberg:** activate only when multi-writer/table snapshots/schema or partition evolution/time-travel materially exceed plain Parquet + Git/object identity.
- **ClickHouse:** activate only when measured analytical concurrency/volume/latency exceeds DuckDB/PostgreSQL.
- **QuestDB:** activate only for measured high-frequency time-series ingestion/query requirements.
- **Dagster:** activate only for persistent data-product graphs requiring partitions/backfills/freshness/materialization state.
- **Grafana:** activate data dashboards only after actionable data-observability metrics exist.
- **Great Expectations:** do not duplicate Pandera unless a workload proves a suite/validation-store requirement Pandera does not cover.

## 8. Architectural placement

Do not create a new `ordivon-data` repository yet.

Ownership should remain:

- domain repositories own domain semantics and source adapters;
- Artifact owns bounded artifact-format verification;
- Workstation/Operations owns commodity services and deployment;
- Runtime/Temporal owns execution mechanics;
- Security owns access/security/privacy enforcement;
- `ordivon-next` owns only composition records, authority bindings and cross-domain acceptance evidence.

A dedicated data-platform repository becomes justified only if shared executable code emerges that cannot be naturally owned by one of these external/domain owners.

## 9. Census conclusion

Current state:

`strong domain-local data legs + weak cross-domain metadata/lineage/feedback spine`.

Therefore the next build should **not** begin with Spark, Kafka, Iceberg, ClickHouse or a new warehouse. It should begin by making two existing real flows interoperably traceable end-to-end using DCAT + ODCS/ODPS + OpenLineage + PROV where necessary, while retaining Parquet/DuckDB/Pandera/WARC as the current thin local substrate.
