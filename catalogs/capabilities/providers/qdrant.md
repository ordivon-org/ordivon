# Provider: Qdrant

Status: **PROTOTYPE-READY / ON-DEMAND VECTOR-SEARCH PROVIDER / NOT LOCALLY INSTALLED**
Role: dedicated production vector-search/database service for filtered approximate-nearest-neighbor, dense/sparse/multivector and hybrid retrieval workloads.

## One-sentence understanding

**Qdrant stores points containing one or more vector representations plus structured payload, then serves filtered dense/sparse/multivector and hybrid top-k retrieval through dedicated ANN indexes, quantization, memory/storage tuning and optional distributed sharding/replication.**

## Current upstream observation — 2026-09-14

- repository: `qdrant/qdrant`;
- license: Apache-2.0;
- latest observed stable release: `v1.19.1` (2026-09-04);
- production service exposes REST/OpenAPI and gRPC;
- current data model supports dense, sparse and multivectors, named vector spaces, JSON payload/filtering, hybrid query fusion, quantization and distributed deployment.

## Current local observation

No `qdrant` executable, Qdrant Docker image, local Qdrant project or existing Qdrant/pgvector registration was observed in the 2026-09-14 Ordivon census.

Do not install Qdrant as a base dependency. Activate it only after a real retrieval workload demonstrates that simpler storage/query options are insufficient.

## Core data model

### Collection

A Collection is a named group of Points sharing vector/index configuration.

It is an operational/search boundary, not automatically a domain ontology or knowledge source of truth.

### Point

A Point is the fundamental stored record:

```text
Point
├─ id
├─ vector(s)
└─ payload (optional structured JSON metadata)
```

The same point may contain several named representations, including dense, sparse and multivector fields.

### Payload

Payload provides structured metadata used for filtering, grouping and returned context.

Typical fields might include:

- source/document identity;
- tenant/project;
- date/version;
- language/type;
- access/security scope;
- domain metadata.

Payload indexes should be created deliberately for fields actually used by filters. Indexing every payload key wastes memory and creates maintenance cost.

## Dense / sparse / multivector

### Dense vector

Useful for embedding-based semantic similarity.

### Sparse vector

Useful for exact/lexical-like signals such as BM25-style sparse representations. Sparse search remains distinct from dense ANN and can coexist on the same Point.

### Multivector / named vectors

Useful when one object has multiple meaningful representations, such as:

```text
paper
├─ title embedding
├─ abstract embedding
├─ chunk/late-interaction representation
└─ sparse lexical representation
```

Do not average distinct signals into one embedding merely to simplify storage when retrieval evaluation shows value in preserving them separately.

## HNSW / approximate search

Qdrant uses HNSW for dense approximate-nearest-neighbor search.

Core tradeoff:

```text
higher search/build effort
    -> better recall
    -> more CPU/memory/latency
```

Approximate search must be evaluated against exact search or a labeled relevance set. An ANN query returning quickly does not prove retrieval quality.

## Filterable HNSW

Qdrant's important differentiator is that payload filtering is integrated with its vector-search/index strategy rather than treated only as an after-the-fact predicate.

This matters when valid results must satisfy hard constraints such as tenant/project/date/access/category while still searching semantically.

Correct pattern:

```text
authorization / hard metadata scope
        ↓
filtered candidate space
        ↓
vector retrieval
```

not:

```text
retrieve globally
        ↓
ask LLM to ignore unauthorized chunks
```

Payload filtering is a retrieval mechanism, not a substitute for application authorization. The application/server must still enforce the correct filter and prevent clients from widening scope.

## Hybrid search

Qdrant can run multiple retrieval queries and fuse results server-side.

Typical text-search pattern:

```text
dense semantic retrieval
          +
sparse/BM25 retrieval
          ↓
RRF / DBSF fusion
          ↓
optional reranking
```

RRF is a safe rank-based default when raw scores from different retrievers are not directly comparable. Weighted/fusion tuning should use a labeled evaluation set when available.

Hybrid retrieval should earn its complexity through measured relevance improvement over dense-only and sparse-only baselines.

## Quantization

Quantization is an optimization for memory/storage/search speed, not a default semantic requirement.

Current Qdrant supports several tradeoff regimes including TurboQuant, scalar, binary and product quantization.

Use quantization when vectors/indexes create measured RAM/storage/latency pressure. Evaluate recall before/after compression and use rescoring/oversampling where appropriate.

Do not enable aggressive compression merely because the option exists.

## Storage / memory tiers

Qdrant separates persisted vector/payload storage from memory residency/index behavior and provides tuning for RAM-constrained deployments.

This is part of why Qdrant becomes useful once vector retrieval is a first-class production service: the system owns search-specific memory/index tradeoffs rather than forcing them into a general relational database.

## Sharding / replication

Distributed Qdrant supports:

- collection sharding;
- shard movement/transfer;
- replication;
- Raft-based cluster metadata/consensus;
- user-defined/custom sharding;
- tenant/time-oriented shard strategies.

Use these only when the workload actually requires independent vector-search horizontal scale or fault tolerance.

A single-node vector-search requirement does not justify a distributed cluster.

## Multitenancy

Current Qdrant supports multiple strategies:

- shared collection + tenant payload filter;
- tenant-aware payload indexing/co-location;
- dedicated custom shards for larger tenants;
- tiered multitenancy where small tenants share capacity and large tenants are promoted.

Tenant routing/filtering must be enforced by trusted application/gateway code. Do not accept arbitrary client-controlled tenant filters as authorization.

## Authority boundary

Qdrant should normally be a **derived retrieval index** over authoritative sources.

Preferred model:

```text
authoritative documents/records
        ↓ ingestion
Qdrant Points + vectors + payload
        ↓ retrieval
bounded context
```

Store enough source identity/version metadata to rebuild or reconcile the index.

Do not make Qdrant the sole owner of documents/business records merely because payload can store JSON/text.

## Adoption hierarchy

Choose the thinnest system that satisfies measured retrieval requirements.

### 1. Direct/in-memory similarity

Use when corpus/QPS/latency are small enough that exact scan is operationally trivial.

Advantages:

- no service;
- perfect recall;
- easiest debugging/evaluation.

### 2. DuckDB / local analytical search

Useful for local analysis/prototyping and exact vector distance queries.

DuckDB's VSS extension adds HNSW but current official documentation still treats it as experimental/secondary, with persistent HNSW recovery limitations. Do not use persistent DuckDB VSS as the default production vector authority without accepting those limitations.

### 3. PostgreSQL + pgvector

Prefer when authoritative application data already lives in PostgreSQL and vector similarity is one query mode among relational/transactional queries.

Current pgvector supports:

- exact nearest-neighbor search;
- HNSW and IVFFlat ANN;
- relational `WHERE` filtering;
- iterative HNSW/IVF scans;
- partitioning/multitenancy patterns;
- half vectors / sparse vectors / binary quantization techniques.

This often avoids duplicating rows/metadata into a second database.

### 4. Qdrant

Adopt a dedicated Qdrant service when vector retrieval itself becomes a first-class workload and one or more of these are material:

- sustained vector-search latency/QPS or corpus scale requires independent tuning/scaling;
- complex filtered ANN is central to correctness/performance;
- dense + sparse + multivector/hybrid fusion is routine;
- search-specific quantization/memory tiering materially reduces infrastructure cost;
- vector service must scale/fail independently of the transactional database;
- tenant-aware vector isolation/sharding is required;
- vector search/recommendation is itself a product capability rather than an incidental query.

Do not use a fixed row-count threshold: dimensions, filters, query rate, update rate, latency/recall targets and existing database topology matter more than raw vector count.

## Boundary with LlamaIndex / Haystack

Qdrant is a retrieval/storage engine.

LlamaIndex/Haystack may orchestrate ingestion/retrieval and call Qdrant through adapters. They should not duplicate Qdrant's ANN/index/sharding semantics.

```text
Haystack/LlamaIndex Retriever
        ↓
Qdrant query API
        ↓
Points
```

Qdrant does not own chunking policy, source parsing, answer synthesis or Agent workflow.

## Boundary with Graphify

Qdrant answers similarity/ranking queries.

Graphify answers explicit relationship/path/neighborhood questions.

Do not encode arbitrary knowledge-graph semantics into vector similarity or replace similarity retrieval with graph traversal when the question is semantic relevance.

## Retrieval evaluation

Before adopting/tuning Qdrant, establish a relevance baseline.

At minimum compare where applicable:

```text
exact / lexical baseline
vs dense ANN
vs sparse retrieval
vs hybrid retrieval
vs hybrid + reranking
```

Measure retrieval relevance (e.g. recall@k, nDCG/MRR where appropriate), latency and resource cost together.

Do not tune HNSW, fusion or quantization using latency alone.

## Security boundary

The Qdrant quick-start container is intentionally simple and can be insecure if bound broadly without authentication.

Production use requires network/auth/TLS/secrets/backups and tenant-filter enforcement appropriate to the deployment.

Embeddings can leak information about underlying content and payload may contain sensitive source metadata. Apply the same data-classification/access requirements to the derived index as to its source corpus.

## Prototype recipe

A minimal Qdrant-like architectural prototype needs only:

1. define `Point{id, dense_vector, payload}`;
2. exact cosine top-k search;
3. add payload filtering before scoring;
4. replace exact scan with HNSW/ANN;
5. store a sparse representation alongside the dense vector;
6. run dense and sparse retrieval independently;
7. fuse rankings with RRF;
8. compare ANN/hybrid results against labeled/exact baselines;
9. persist source identity in payload so the index is rebuildable.

Sharding, replication and quantization are production optimizations, not required to understand the core.

## Prototype readiness gate

**PASS.** Point/Collection/Payload, filtered ANN, dense/sparse/hybrid retrieval, quantization and scale boundaries are explicit enough to implement a small vector-search engine or consume Qdrant directly.
