# Data LEGO inventory — bounded source census

This is a **consumer-oriented inventory**, not a new registry, formal admission
ledger or claim that every named tool is installed. A capability only becomes
a separately admitted LEGO if the existing Recursive LEGO R2.1 method proves
an independently contractable responsibility, public seam, verifier and
consumer. A Skill is instructional knowledge, not an executable LEGO.

| Responsibility | Mature external binding | Local observed carrier | Verdict |
| --- | --- | --- | --- |
| API/market acquisition | provider REST/WebSocket, OAuth/API semantics | Capital Binance/OKX adapters and Research source tools | REUSE domain-native |
| Web evidence capture | ISO 28500 WARC | Artifact WARC + independent warcio checks | REUSE |
| Columnar analytics | Apache Parquet/Arrow, DuckDB | DuckDB 1.5.5, Artifact independent PyArrow carrier | REUSE |
| Dataset conformance | Dataset Contract, Arrow/Parquet readers | Artifact Dataset R1, six negative/positive cases | REUSE, bounded flat profile |
| Data product description | Bitol ODPS / ODCS | Existing Research, Capital and Episode 1.1/3.2 consumers | REUSE existing; version migration candidate |
| Dataset discovery | W3C DCAT 3 | Three-product R2 federation + read-only inspection | COMPOSE, not authority |
| Semantic provenance | W3C PROV-O | Federated product graph | REUSE recorded scope |
| Operational lineage | OpenLineage | Selected producer/consumer run events | REUSE recorded scope |
| Domain data quality | ISO/IEC 5259, Pandera, SDMX, UCUM/QUDT | Research/Finance checks, TidyTuesday pilot | REUSE domain-specific |
| Revision/vintage semantics | Git commits, source event/observation time | Temporal evolution pilot | KEEP as partial study |
| Historical preservation | OAIS/E-ARK/PREMIS/METS, fixity | Archivematica/local master and replica evidence | REUSE, same host only |
| SQL persistence and analytical projection | PostgreSQL 18, Alembic, Psycopg | Experimental Episode Store | REUSE, domain projection |
| Agent exploration and statistical methods | existing trusted Skills | EDA/statistics/experimental design/visualization | ADVISORY |
| Pipeline throughput optimization | existing data-throughput-accelerator Skill | instruction available; no deployed Data accelerator service | ADVISORY |

## Formal carrier qualification

`formal/DataProduct.lean` specializes existing Lean/Recursive LEGO formal
methodology to Data's digest-evidence and `(id, version)` uniqueness
properties. `src/ordivon_data/verification.py` uses ordinary PEP 316
contracts and bounded CrossHair/Z3 symbolic exploration; `catalog.py`
consumes this pure predicate. These are a **bounded model and implementation
candidate**, not a newly admitted universal LEGO, proof of filesystem I/O,
or independent data producer. See `docs/FORMAL_VERIFICATION.md`.

## Current read-only ODPS-to-DCAT composition

The `odps_projection.py` + `scripts/project_owned_products.py` pair is
a thin capability candidate that consumes real owner ODPS 1.1 records and
produces deterministic DCAT 3 discovery metadata. Its only global discovery
source is Git's tracked-file index; no central dataset registry or file store
is created. It preserves declared policy references while omitting physical
URLs and per-port digests unless producers explicitly bind them. Real Bitol
ODPS 1.1 permits absent port IDs and versions, and port versions are
independent of product versions. Its correctness remains bounded by
upstream metadata, native parsing and downstream consumer read-back; the
DataProduct Lean digest proof does **not** prove RDF conversion.

## Qualified current-byte evidence

The optional `local_evidence.py` is a small **file-evidence adapter**, not
a new owner/registry or generic provenance service. It accepts explicit
operator-selected ODPS source-path and SHA-256 properties, binds one exact
named output port and a canonical owner root, checks actual regular-file
bytes, and emits only a short-lived local URI. The existing Artifact
family remains natural owner of durable, format-level Dataset verification.
The adapter does not certify the environment against later path replacement;
recheck bytes at consumer read-back.

## Thought LEGO source laws

- **Representation:** W3C DCAT/PROV, ODCS/ODPS, SDMX and Arrow/Parquet are
  the first choice for existing identity and format semantics.
- **Data quality:** source/format validity, schema contract, domain fitness
  for use and factual truth are independent propositions.
- **Temporal information:** event time, observation time, ingestion time,
  known-as-of vintage and source revision must not be collapsed.
- **Lifecycle:** immutable source evidence, reproducible transformation,
  explicit materialization, consumer outcome and version-aware retirement.
- **Composition:** SourceCut + consumer + replacement boundary; avoid
  universal scheduler/catalog/database creation.
- **Evidence:** emitted readback, falsifiers and typed UNKNOWN supersede
  self-reported PASS. A container/image import does not prove live provider
  readiness.

## Not automatically installed

Dagster, Iceberg, Kafka/Redpanda, Beam, Debezium, ClickHouse,
Great Expectations, dlt and full Airbyte are workload-gated candidates.
A README, provider survey or GitHub star count is not installation evidence.

## Current upstream version caution

ODPS 4.2 became final on 2026-10-26 with `schema` / `version` /
`product` root, and has a different access model. The historical
ODPS 1.1 consumer schemas cannot be changed in place. Use a new
producer-version and real consumer compatibility witness first.
