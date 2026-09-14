# Package: Data & Analytics

Last census: 2026-09-14
Standing: **READY_FOR_REAL_WORK**

## Outcome scope

Turn source data into a trustworthy query, transformation, analysis, model, visualization or decision-support result with enough identity, quality and provenance to understand what the result means and reproduce it when required.

This package does not imply one universal data platform. Research analytics, operational analytics, BI, geospatial work, ML and organizational data management may activate different working sets.

## Mature external knowledge owners

Use according to context:

- DAMA-DMBOK for broad organizational data-management/governance knowledge when that scope is relevant;
- FAIR principles for findability, accessibility, interoperability and reuse of research/digital assets when applicable;
- domain-native schemas, controlled vocabularies and quality rules;
- Apache Arrow for interoperable columnar in-memory/IPC representations where useful;
- Apache Parquet for columnar analytical file storage where useful;
- mature database/query engines and established statistical/data-science methods;
- applicable privacy, security and governance regimes for the actual data.

## Observed local capability

- Python + uv;
- DuckDB;
- SQLite;
- PostgreSQL client;
- GDAL/OGR for geospatial data;
- `statistical-analysis` and `scientific-visualization` Skills;
- Research workflows for reproducible analysis;
- Artifact dataset/table/figure validation capabilities;
- Git/content digests and task-specific schema/quality checks.

No Qdrant executable, Docker image or local Qdrant project was observed during the 2026-09-14 census.

## Vector / similarity retrieval routing

Vector search is one retrieval method, not a base data-platform requirement.

Use the thinnest adequate option:

```text
small/local exact similarity
  -> direct in-memory / SQL distance calculation

local analytical prototype
  -> DuckDB exact vector functions; VSS/HNSW only with awareness of its current experimental persistent-index limitations

application/domain data already authoritative in PostgreSQL
  -> pgvector first candidate

dedicated production filtered/hybrid vector retrieval
  -> Qdrant first candidate
```

Qdrant becomes appropriate when vector search itself needs independent production behavior such as filter-aware ANN, dense+sparse/multivector hybrid retrieval, search-specific quantization/memory tuning, tenant-aware sharding or independent horizontal scale. See `capabilities/providers/qdrant.md` and `knowledge/lessons/qdrant-vector-search-kernel.md`.

Do not duplicate authoritative relational/domain records into a separate vector service without a measured retrieval benefit and explicit source/version linkage.

## Concrete current gaps

No generic data-platform or vector-database gap is proven.

Do not install Spark, dbt, Airflow, Kafka, a lakehouse, warehouse, feature store, BI server, catalog or vector database merely to fill a conceptual slot. Activate one only when scale, collaboration, latency, lineage, governance, retrieval quality or workload shape requires it.

For future vector-search workloads, first establish a retrieval relevance/latency baseline with the simplest available implementation. Only promote to pgvector/Qdrant when measured constraints justify the operational dependency.

## Acceptance workload

Use the next real dataset from Research, Game, Market Capital or another project:

`source identity -> schema/quality checks -> transformation/query/analysis -> method-specific validation -> reproducible result -> validated table/figure/report/model artifact`

If similarity retrieval is part of the workload, separately verify:

`source/version identity -> retrieval representation -> exact/lexical baseline -> ANN/hybrid candidate -> relevance metrics + latency/resource cost -> downstream answer/domain verification`

For decision-bearing analytics, preserve the distinction between data correctness, retrieval quality, statistical validity and the downstream decision rule.

## External references

- DAMA-DMBOK: https://dama.org/learning-resources/dama-data-management-body-of-knowledge-dmbok/
- FAIR Principles: https://www.go-fair.org/fair-principles/
- Apache Arrow specifications: https://arrow.apache.org/docs/format/index.html
- Apache Parquet format: https://parquet.apache.org/docs/file-format/
- pgvector: https://github.com/pgvector/pgvector
- Qdrant: https://qdrant.tech/documentation/
