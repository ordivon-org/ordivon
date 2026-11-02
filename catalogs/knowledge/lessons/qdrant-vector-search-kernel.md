# Qdrant Vector Search Kernel — extracted design lessons

Status: **REGISTERED / PROTOTYPE-READY**
Registered: 2026-09-14

## One-sentence model

**A dedicated vector database is justified not by the existence of embeddings, but when similarity retrieval becomes a production workload requiring specialized filtered ANN, hybrid/multi-representation search, memory/index optimization or independent scaling that simpler local/relational systems cannot satisfy.**

## Mechanism 1: vector search is a retrieval method, not a knowledge architecture

Embeddings answer a narrow class of questions:

> Which stored representations are close to this representation under a chosen distance/model?

They do not define document truth, causal relationships, business state or authorization.

Keep vector indexes derived from authoritative source objects.

## Mechanism 2: use exact search as the quality reference

Approximate ANN exists to trade some recall for speed/resource efficiency.

Before tuning HNSW, preserve an exact-search path on a representative evaluation subset so recall regressions can be measured.

```text
exact top-k
= retrieval reference

ANN top-k
= optimized approximation
```

## Mechanism 3: hard filters belong inside retrieval scope

Metadata constraints such as tenant, project, date, access class or document family often define which corpus is valid before similarity is considered.

A vector engine that handles filters efficiently is useful because:

```text
valid candidate scope
        ↓
semantic ranking
```

is safer and often faster than global ANN followed by application-side discard.

Still enforce authorization outside the vector database; filters are query mechanics, not identity proof.

## Mechanism 4: lexical and semantic retrieval are complementary

Dense retrieval captures semantic similarity but can miss rare identifiers/exact terminology.

Sparse/BM25 retrieval captures exact lexical evidence but can miss paraphrases/concepts.

Hybrid search combines them:

```text
dense candidates
  +
sparse candidates
  ↓
rank fusion
```

Use labeled retrieval evaluation to prove hybrid beats either baseline before carrying the added complexity.

## Mechanism 5: raw scores from different retrievers are not automatically comparable

Dense cosine and BM25/sparse scores live on different scales.

Rank-based fusion such as RRF avoids pretending raw score magnitudes share one unit. Distribution-based normalization is another option.

Do not choose arbitrary `0.7*dense + 0.3*sparse` without normalization/evaluation.

## Mechanism 6: preserve multiple useful representations instead of averaging them away

An object may have distinct signals:

```text
title
abstract
body chunks
image
lexical sparse vector
late-interaction multivectors
```

Named/multiple vector spaces allow each representation to remain queryable and then be fused/grouped according to the task.

Only introduce these representations when evals show they improve retrieval.

## Mechanism 7: quantization is an optimization after relevance is established

Compression reduces memory/storage and may accelerate search but adds approximation error.

Correct order:

```text
working retrieval quality
   ↓
measure RAM/storage/latency bottleneck
   ↓
quantize
   ↓
re-evaluate recall/latency/cost
```

Do not quantize first and discover later that the relevance baseline was poor.

## Mechanism 8: dedicated service threshold is workload-shaped, not row-count-shaped

There is no universal rule such as “over one million vectors -> vector DB.”

Important variables include:

- embedding dimension/representation count;
- query rate/concurrency;
- latency SLO;
- update rate;
- filter complexity/selectivity;
- required recall;
- memory/storage budget;
- tenant isolation;
- HA/replication needs;
- whether source data already has a natural relational authority.

Choose architecture by measured pressure.

## Mechanism 9: PostgreSQL + pgvector should often be tried before a second database

If application/domain records already live in PostgreSQL, pgvector keeps:

```text
relational row
+ metadata
+ vector
```

under one transactional/query authority.

Its current HNSW/IVFFlat, exact search, SQL filtering, iterative scans, partitioning and quantization options cover many ordinary semantic-search workloads.

Use Qdrant when dedicated search capabilities/scale justify data duplication and a separate operational service.

## Mechanism 10: DuckDB is useful locally but current persistent VSS remains a caution boundary

DuckDB is excellent for local analytics and exact vector calculations. Its VSS extension offers HNSW, but current official docs still warn that persistent HNSW/WAL recovery is experimental and not recommended for production.

This makes it useful for local prototypes/analysis, not a reason to force every vector workload into DuckDB.

## Mechanism 11: vector database is usually a projection

Recommended identity:

```text
source record/document ID + version/hash
      ↓
chunk/representation ID
      ↓
embedding model/version
      ↓
Qdrant point/vector
```

This makes stale embeddings detectable and rebuild possible after model/chunking changes.

Do not keep anonymous vectors divorced from their source/version.

## Mechanism 12: embedding-model migration is a data migration

Changing embedding models can change:

- dimension;
- distance distribution;
- retrieval ranking;
- index configuration;
- every stored vector.

Treat model identity/version as part of index schema/provenance. Re-embed into a new named vector/collection or controlled migration path rather than silently mixing incompatible representations.

## Mechanism 13: multitenancy is an authorization-sensitive retrieval design

Shared collection + tenant payload is efficient for many small tenants; dedicated/custom shards can provide stronger physical isolation for larger tenants.

But every query must be scoped by trusted server-side tenant identity. Never rely on the model or untrusted client to remember the tenant filter.

## Mechanism 14: sharding/replication are operational capabilities, not retrieval semantics

Do not deploy a Qdrant cluster because distributed architecture sounds mature.

Use a cluster only when:

- data no longer fits desired single-node capacity;
- availability requirements need replicas;
- throughput benefits from horizontal scale;
- tenant/time routing benefits from explicit shards.

Backups/snapshots and recovery still need deliberate operational design.

## Current Ordivon selection ladder

```text
small/local exact similarity
  -> in-memory / NumPy / direct SQL

local analytical workload
  -> DuckDB exact; VSS cautiously for experiments

application data already in PostgreSQL
  -> pgvector first candidate

dedicated production vector retrieval
  -> Qdrant first candidate
```

This is a routing heuristic, not a mandatory migration sequence.

## Relationship to the existing context stack

```text
Firecrawl / MarkItDown / Docling / GROBID
    -> acquire / normalize

chunking / provenance
    -> produce retrieval units

Postgres/pgvector or Qdrant
    -> similarity/filter retrieval

Graphify
    -> explicit relationship traversal

Haystack / LlamaIndex
    -> optional pipeline/integration framework

Agent
    -> consumes bounded evidence
```

No new global Knowledge subsystem is required.

## What Ordivon should retain

1. Keep vector stores derived from source identity/version.
2. Use exact retrieval as a recall reference before ANN tuning.
3. Apply hard metadata/authorization scope before semantic ranking.
4. Compare lexical, dense and hybrid retrieval with labeled evals.
5. Avoid mixing unnormalized raw retriever scores.
6. Add reranking/multivector/quantization only after measured need.
7. Prefer pgvector when PostgreSQL is already natural data authority.
8. Adopt Qdrant when vector search needs independent specialized service semantics.
9. Keep tenant enforcement in trusted application boundaries.
10. Treat embedding model changes as explicit index/data migrations.

## What Ordivon should not copy

- private vector database;
- mandatory embeddings for every knowledge object;
- arbitrary corpus-size threshold for Qdrant adoption;
- Qdrant payload as universal business database;
- vector similarity as authorization;
- vector index as source of truth;
- always-on hybrid/reranker/quantization complexity;
- distributed cluster before workload evidence.

## Prototype readiness gate

### One-sentence test

PASS: Qdrant is a dedicated filtered/hybrid vector-search service whose value begins when vector retrieval itself needs specialized production indexing, memory and scaling behavior.

### Prototype test

PASS: point+payload storage, exact similarity, filtered HNSW, dense+sparse retrieval and RRF fusion are sufficient to reproduce the architectural kernel; production Qdrant adds mature optimization/distribution rather than a fundamentally different semantic model.

## Verdict

**PASS — KEEP QDRANT ON-DEMAND; PREFER EXISTING RELATIONAL/LOCAL AUTHORITY UNTIL VECTOR SEARCH BECOMES A FIRST-CLASS PRODUCTION WORKLOAD.**
