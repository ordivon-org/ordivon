# LlamaIndex vs Haystack — Context / Retrieval Kernel

Status: **REGISTERED / PROTOTYPE-READY**
Registered: 2026-09-14

## One-sentence model

**The durable RAG/context-engineering kernel is source acquisition and normalization followed by provenance-preserving chunk/enrichment, derived indexing, bounded retrieval, optional reranking, context consumption/synthesis and separate retrieval/answer evaluation; LlamaIndex and Haystack are convenience frameworks around this kernel, not knowledge authorities.**

## Core pipeline

```text
AUTHORITATIVE SOURCES
      ↓
ACQUIRE
      ↓
NORMALIZE / PARSE
      ↓
SPLIT / ENRICH / PROVENANCE
      ↓
DERIVED INDEX(ES)
      ↓
RETRIEVE
      ↓
RERANK / FILTER / POSTPROCESS (optional)
      ↓
BOUNDED CONTEXT
      ↓
AGENT / RESPONSE SYNTHESIS
      ↓
VERIFY / EVALUATE
```

This is the reusable method. No particular RAG framework is mandatory.

## Mechanism 1: acquisition and retrieval are different stages

Firecrawl finding/scraping pages, MarkItDown/Docling parsing files, or a database exposing records solves **acquisition/normalization**.

Retriever logic solves:

> Which subset of the already-available corpus should be placed into the current reasoning context?

Do not make a vector database responsible for crawling/parsing, and do not make a crawler responsible for retrieval quality.

## Mechanism 2: chunks/nodes are derived projections

Splitting a document creates retrieval units, not new authoritative documents.

Each chunk should preserve enough provenance to answer:

- source object identity;
- source location/page/section when available;
- ingestion/parser version when consequential;
- relevant metadata/security scope.

A chunk ID without source linkage is weak evidence.

## Mechanism 3: chunking is workload-dependent

There is no universally correct chunk size.

Tradeoffs:

- too small -> missing context/coherence;
- too large -> poor retrieval precision/context cost;
- overlap -> better continuity but duplication/cost;
- semantic/layout-aware chunks -> potentially better but parser/model complexity;
- domain-native units -> often preferable when available.

Choose based on retrieval/evaluation evidence rather than copying a framework default.

## Mechanism 4: index is acceleration, not truth

Indexes may include:

- BM25/inverted indexes;
- vector embeddings/HNSW;
- SQL/metadata indexes;
- graph projections;
- hybrid combinations.

They exist to answer retrieval queries efficiently.

```text
index corruption/deletion
should be recoverable from source corpus
```

unless the chosen storage service is intentionally also the source record system.

## Mechanism 5: RAG does not imply vector database

Use retrieval mode according to the question:

```text
exact term / identifier / rare token
  -> lexical/BM25/search

structured metadata predicate
  -> SQL/filter

semantic similarity
  -> embeddings/vector

relationship/path question
  -> graph traversal

mixed corpus
  -> hybrid / routed retrieval
```

Do not embed data merely because the application is called RAG.

## Mechanism 6: first-stage retrieval and reranking have different jobs

First-stage retrieval optimizes candidate recall/latency over a larger corpus.

Reranking applies a more expensive scoring rule to a small candidate set to improve final ordering/precision.

```text
large corpus
  ↓ cheap retrieval top-50
  ↓ expensive reranker
  ↓ top-5 context
```

Add reranking only when measured quality gains justify cost/latency.

## Mechanism 7: retrieval and synthesis should remain separable

A framework Query Engine often combines:

```text
retrieve
+ prompt
+ LLM synthesis
```

This is convenient but should not hide evidence boundaries.

Ordivon should be able to inspect:

- what candidates were retrieved;
- their source identities/scores;
- what was finally shown to the model;
- which claims cite which source material.

A higher-level Agent may consume the bounded context directly without a framework-specific response synthesizer.

## Mechanism 8: retrieval evaluation is not answer evaluation

Evaluate at least two layers separately.

### Retrieval

Examples:

- relevant-source recall@k;
- ranking/MRR/nDCG where appropriate;
- filter correctness;
- source diversity/coverage;
- duplicate/noise rate.

### Answer/task

Examples:

- correctness;
- groundedness/faithfulness;
- citation support;
- completeness;
- domain acceptance criteria.

A bad retriever can occasionally produce a good answer; a good retriever cannot force a model to answer correctly.

## Mechanism 9: metadata filtering is often more important than embeddings

Security scope, tenant, date, project, language, document type or domain constraints should usually narrow the candidate set before/alongside semantic similarity.

Do not retrieve globally and ask the LLM to ignore unauthorized/irrelevant chunks after the fact.

Authorization belongs before context disclosure.

## Mechanism 10: ingestion caching is optimization

LlamaIndex's transformation cache and similar framework caches can avoid recomputing parsing/embeddings.

Cache keys must bind all inputs that affect the transformation sufficiently to avoid stale/cross-version results.

Cache reuse does not prove source freshness. Consequential workloads need explicit corpus/index freshness policy.

## Mechanism 11: framework orchestration is optional

The complete useful pipeline can often be plain Python/functions plus mature storage APIs.

Use a framework when it reduces measured complexity:

- many replaceable pipeline components;
- integration catalog saves adapters;
- repeated pipelines benefit from graph/runtime inspection;
- application team benefits from a common framework contract.

Avoid framework introduction when the same workload is clearer as 20–50 lines of direct provider code.

## LlamaIndex current role

LlamaIndex remains a rich OSS toolkit for:

- Documents/Nodes;
- ingestion transformations;
- many readers/integrations;
- index/retriever abstractions;
- postprocessors;
- response synthesis/query engines;
- Workflows/Agents.

But its company/project README now explicitly says the primary product focus has shifted toward document parsing/extraction. Treat broad OSS RAG/Agent features as available toolkit, not a strategic reason to anchor Ordivon architecture to it.

## Haystack current role

Haystack 3 remains explicitly focused on production context engineering and Agent/RAG pipelines.

Its cleanest transferable abstraction is:

```text
Component contracts
+ explicit Pipeline graph
+ separate Document Store
+ Retriever / Ranker / Generator
```

It is the stronger candidate when a real production application genuinely needs a maintained explicit context pipeline framework.

## Existing Ordivon stack mapping

```text
Web acquisition          -> Firecrawl
Light file normalization -> MarkItDown
Rich document parsing    -> Docling
Scholarly parsing        -> GROBID
Relationship context     -> Graphify
Structured/local data    -> PostgreSQL / DuckDB / files
Vector service           -> evaluate Qdrant only when justified
Agent reasoning          -> Codex / selected Agent
Workflow durability      -> Temporal when justified
```

Therefore LlamaIndex/Haystack mostly provide optional composition/integration convenience over capabilities already available independently.

## Selection heuristic

```text
simple known corpus + simple retrieval
    -> direct provider/search code

need LlamaIndex-specific integration / compact Node+Index toolkit
    -> LlamaIndex selectively

need explicit multi-stage production context pipeline
    -> Haystack candidate

need only vector search service
    -> vector provider directly, not either framework by default
```

## What Ordivon should retain

1. Separate acquisition/normalization from retrieval.
2. Preserve source provenance through every chunk/node.
3. Keep indexes rebuildable/derived.
4. Choose lexical/SQL/vector/graph retrieval by question semantics.
5. Treat reranking as optional second-stage precision improvement.
6. Keep retrieval outputs inspectable before synthesis.
7. Evaluate retrieval and final answers separately.
8. Apply authorization/metadata scope before exposing context.
9. Make index/cache freshness explicit where consequential.
10. Introduce a RAG framework only when its composition/integration benefits exceed framework coupling.

## What Ordivon should not copy

- universal `KnowledgeIndex` as new source of truth;
- mandatory embedding of every document/record;
- global chunking policy;
- private vector database;
- framework-specific Agent state as Ordivon memory;
- another universal pipeline/DAG engine;
- response synthesizer as evidence/veracity authority;
- both LlamaIndex and Haystack as permanent base dependencies.

## Minimal prototype

```text
Source documents
  ↓
parser/normalizer
  ↓
chunks with source IDs
  ↓
BM25 + optional vector index
  ↓
retrieve top-k
  ↓
optional rerank
  ↓
Agent receives bounded context + citations
  ↓
retrieval eval + answer eval
```

Implementing this directly proves the architectural kernel without either framework.

## Project-study acceptance

### One-sentence test

PASS: LlamaIndex/Haystack package ingestion, retrieval and synthesis primitives; the durable value is provenance-preserving context selection, not the framework object model.

### Prototype test

PASS: source-linked chunks, one lexical/vector index, retrieval, optional reranking, synthesis and separate evaluation are sufficient to reproduce the core RAG architecture.

## Verdict

**PASS — EXTRACT THE CONTEXT/RETRIEVAL KERNEL; KEEP BOTH FRAMEWORKS ON-DEMAND. HAYSTACK IS THE STRONGER EXPLICIT PRODUCTION-PIPELINE CANDIDATE; LLAMAINDEX REMAINS A USEFUL TOOLKIT/INTEGRATION SOURCE, ESPECIALLY AROUND DOCUMENT CONTEXT.**
