# Package: Data & Analytics

Last census: 2026-09-20

Project-scoped data work: **READY_FOR_REAL_WORK**

Cross-domain data lifecycle: **PARTIAL**

## Outcome scope

Turn source data into a trustworthy query, transformation, analysis, model, visualization or decision-support result with enough identity, quality, provenance and preservation evidence to understand what the result means and reproduce it when required.

This package does not imply one universal data platform. Research analytics, operational analytics, BI, geospatial work, ML and organizational data management may activate different working sets.

## Mature external knowledge owners

Use according to context:

- DAMA-DMBOK for broad organizational data-management/governance knowledge when that scope is relevant;
- FAIR principles for findability, accessibility, interoperability and reuse;
- W3C DCAT 3 for dataset/data-service catalog metadata;
- Bitol ODCS/ODPS for data contracts and data products;
- OpenLineage for operational Job/Run/Dataset lineage and W3C PROV for semantic derivation where needed;
- SDMX, UCUM/QUDT and domain-native vocabularies for source semantics;
- ISO/IEC 5259-2 and domain-specific acceptance rules for data quality;
- ISO 14721 OAIS, E-ARK SIP/CSIP, PREMIS/METS and mature preservation tooling for selected durable evidence;
- Apache Arrow / Parquet for analytical interchange and storage;
- applicable privacy, security, rights and records-management regimes for the actual data.

## Observed local capability

Proven project-scoped substrate includes:

- Python + uv;
- DuckDB;
- SQLite and PostgreSQL;
- PyArrow / Parquet;
- Pandera and JSON Schema;
- GDAL/OGR for geospatial data;
- Research workflows for reproducible analysis;
- Artifact dataset/table/figure verification;
- Git/content digests and source/version binding;
- ODCS 3.2.0 contracts owned by real Research and Finance products;
- ODPS 1.1.0 products owned by Research and Finance;
- DCAT 3 two-domain federated projection;
- W3C PROV-O source/product derivation, including a real Paper1 dataset-to-result edge;
- OpenLineage runtime-event emission;
- explicit source semantics, revision/vintage and reference-identifier handling;
- local durable preservation through E-ARK submission -> Archivematica PREMIS/METS AIP -> Storage Service master/replica -> scheduled fixity.

Preservation evidence is bounded: the current master and replica occupy distinct Storage Service locations but the same machine/WSL failure domain. This is **not** an offsite/disaster-resilience claim.

## Current lifecycle evidence

Authoritative current projection:

- `planning/data-lifecycle-census-r4.json`
- `docs/DATA_PRODUCTS_FEDERATION_R1.md`
- `docs/DATA_DURABLE_PRESERVATION_R1.md`
- `evidence/data-lifecycle/preservation-r1/acceptance.json`

R1–R3 census files remain historical evidence; R4 is current.

Current shape:

```text
source identity
  -> acquisition
  -> immutable/raw evidence
  -> parse/normalize
  -> semantics + quality contract
  -> revision/reference handling
  -> analysis
  -> lineage evidence
  -> selected durable preservation
```

The major remaining cross-domain gaps are **not** generic compute/storage gaps. They are:

```text
runtime product-version lineage
  -> exact claim/decision consumption
  -> outcome -> collection/quality/model feedback

Rights/privacy/retention now fail closed for the selected Research and Finance products; actual source-right resolution, formal privacy assessment and authorized retention schedules remain explicit P1 obligations.
```

## Data orchestration routing

Use orchestration according to the durable semantic object being maintained:

```text
scientific/project file DAG
  -> Snakemake

API/SaaS/webhook integration edge
  -> n8n

general long-lived durable process
  -> Temporal

persistent data-product/asset graph
with partitions, lineage, backfills, freshness/checks
  -> Dagster candidate
```

Dagster remains workload-gated. Do not migrate accepted project DAGs merely to obtain a catalog/UI.

## Heavy-substrate activation policy

Absence of the following is **not** lifecycle debt:

- Iceberg;
- Debezium;
- Beam runtime;
- Kafka / Redpanda;
- ClickHouse;
- QuestDB;
- Dagster;
- Great Expectations;
- OCFL;
- dedicated vector databases.

Activate one only when a real workload proves a requirement that the current thin substrate cannot satisfy.

Examples:

- Iceberg: atomic multi-file table snapshots, real schema/partition evolution, concurrent writers or table-native time travel/row lineage.
- Debezium: database transaction-log CDC.
- Beam: unbounded event-time/window/watermark/late-data processing.
- Kafka/Redpanda: decoupled unbounded replay/fan-out/consumer-offset workload.
- Dagster: persistent asset graph with partitions/backfills/freshness/materialization state.
- ClickHouse/QuestDB: measured latency/concurrency/ingestion limits beyond DuckDB/PostgreSQL.

## Vector / similarity retrieval routing

Vector search remains a retrieval method, not a base platform requirement.

Use the thinnest adequate implementation:

```text
small/local exact similarity
  -> memory / SQL

local analytical prototype
  -> DuckDB

authoritative PostgreSQL application/domain data
  -> pgvector candidate

dedicated production filtered/hybrid ANN
  -> Qdrant candidate
```

Do not duplicate authoritative records into a separate vector service without measured retrieval benefit and explicit source/version linkage.

## Acceptance boundary

`ProjectScopedDataWork = READY` means Ordivon can execute real acquisition, validation, transformation, analysis and selected preservation workflows.

It does **not** mean the cross-domain lifecycle is closed.

`CrossDomainDataLifecycle = PARTIAL` remains until at least:

1. real Research and Finance executions emit runtime OpenLineage events that bind the exact ODPS product/output-port version;
2. rights/privacy/retention metadata is executable at product boundaries;
3. claims/decisions bind the exact consumed data-product version;
4. outcome evidence feeds changes back to collection/quality/model policy.

## External references

See Authority Catalog records rather than maintaining another private standards list. Key owners include DCAT, ODCS/ODPS, OpenLineage, W3C PROV, SDMX, UCUM/QUDT, ISO/IEC 5259, ISO 14721, E-ARK, PREMIS and the selected mature implementations.
