# Provider: LlamaIndex OSS

Status: **PROTOTYPE-READY / ON-DEMAND CONTEXT-ENGINEERING TOOLKIT / NOT LOCALLY INSTALLED**
Role: document/node ingestion, indexing, retrieval, post-processing and response-synthesis toolkit for RAG/context applications.

## One-sentence understanding

**LlamaIndex turns heterogeneous documents into provenance-bearing Nodes, applies reusable ingestion transformations, builds/query indexes through Retrievers, optionally post-processes candidates, and synthesizes responses or exposes retrieved context to higher-level Agents.**

## Current upstream direction — 2026-09-14

The OSS repository remains large and active (about 52k GitHub stars, MIT), but the project's own README now says the company's primary focus has shifted toward document parsing/extraction products such as LlamaParse/LiteParse and parsing/extraction benchmarks, while the broad OSS RAG/Agent framework remains available as a toolkit.

This matters architecturally: do not assume LlamaIndex should become Ordivon's default universal RAG framework merely because it historically occupied that category.

## Core primitives

### Document / Node

A `Document` represents an ingested source object. During indexing/ingestion, LlamaIndex commonly splits documents into `Node` objects.

Nodes carry:

- text/content;
- metadata;
- source/document relationship;
- optional relationships among chunks/nodes.

The useful design lesson is not the exact class names; it is that **retrieval chunks must retain provenance back to authoritative source material**.

### Ingestion Pipeline

The ingestion pipeline applies ordered `Transformations` such as:

```text
Document
  ↓
split / parse
  ↓
metadata extraction
  ↓
embedding / enrichment
  ↓
Node(s)
  ↓
index/vector store
```

Transformation results can be cached. The cache is an optimization over deterministic/reusable transformations, not authority for the source corpus.

### Index

An Index is a query-oriented data structure over Documents/Nodes.

A `VectorStoreIndex` is common, but vector retrieval is not the only possible index/retrieval strategy.

Keep the boundary:

```text
source document
= authority

index / embeddings
= derived retrieval structure
```

Deleting/rebuilding an index must not destroy the authoritative source unless the application deliberately chose the index store as its primary data system.

### Retriever

A Retriever maps a query to a bounded candidate set of Nodes/objects.

The abstraction can sit over vector, keyword, structured, routed/composite or provider-specific indexes.

Retriever output is **candidate context**, not a final answer and not proof that the most relevant evidence was found.

### Node post-processors / reranking

Retrieved candidates can be filtered, reordered or enriched after first-stage retrieval.

Typical uses:

- similarity thresholding;
- metadata filtering;
- reranking;
- context reordering;
- deduplication.

Use this stage when measured retrieval quality justifies the extra latency/cost. Do not add reranking by default to every lookup.

### Response Synthesizer / Query Engine

A Response Synthesizer consumes a query plus retrieved Nodes and asks an LLM to produce a response.

A Query Engine combines retrieval + post-processing + synthesis into one convenience surface.

This is an application convenience, not a necessary RAG primitive. Ordivon may instead pass bounded retrieved context directly to Codex/another Agent and preserve the source citations independently.

### Workflows / Agents

LlamaIndex also provides Agent/Workflow orchestration. Its older `QueryPipeline` abstraction is currently feature-frozen/deprecated in favor of Workflows.

Ordivon should not adopt LlamaIndex Workflows merely because retrieval code already uses LlamaIndex. Agent/workflow authority should remain with the natural execution layer (Codex, Temporal, application code, etc.).

## Ordivon routing rule

Use LlamaIndex selectively when it materially reduces glue code for a document/retrieval workload, for example:

- many existing LlamaIndex readers/integrations are useful;
- Node/index/retriever abstractions fit the application directly;
- reusable ingestion transformations/caching save implementation work;
- a query engine is sufficient for a compact RAG application;
- an existing LlamaIndex integration avoids custom adapter code.

Do not introduce it for a simple corpus that can be handled by:

```text
Firecrawl / MarkItDown / Docling
        ↓
plain source records
        ↓
PostgreSQL / DuckDB / lexical search / vector provider
        ↓
small retrieval function
        ↓
Agent
```

## Boundary with parsing providers

LlamaIndex can load/parse documents, but Ordivon already routes document understanding by required fidelity:

- Firecrawl -> public web acquisition/context;
- MarkItDown -> lightweight heterogeneous file normalization;
- Docling -> rich layout/document understanding;
- GROBID -> scholarly PDF semantics;
- LlamaParse/LiteParse -> optional document parsing providers if a real workload proves superior value.

Do not duplicate parsing solely to make documents conform to LlamaIndex classes.

## Boundary with vector stores

LlamaIndex integrates with many vector databases but does not make a dedicated vector DB mandatory.

Choose storage/retrieval according to workload. Upcoming Qdrant evaluation owns the decision of when a vector service is justified.

## Boundary with Agent memory

A retrieval index is not durable personal/Agent memory by default.

Do not mix:

```text
corpus retrieval
conversation state
workflow state
user memory
business database
```

simply because all can be converted to Nodes and embedded.

## Evaluation boundary

Evaluate retrieval separately from answer synthesis.

Useful retrieval questions include:

- was relevant evidence retrieved in top-k;
- ranking quality;
- duplicate/noise rate;
- source coverage;
- metadata/filter correctness.

Answer-level questions include groundedness/correctness/coverage and belong to an eval/domain layer.

A good generated answer cannot prove retrieval completeness; a high retrieval score cannot prove the answer is correct.

## Current local observation

No importable `llama_index` package or `uv tool` installation was observed during the 2026-09-14 census.

No current workload justifies installing it as a base dependency.

## Prototype recipe

A LlamaIndex-like architectural prototype needs only:

1. `Document{id, content, metadata}`;
2. split documents into provenance-linked `Node`s;
3. apply a reusable transformation pipeline;
4. build one lexical/vector index;
5. implement `retrieve(query, top_k)` returning nodes + scores;
6. add one post-processor/reranker;
7. pass nodes to a response synthesizer or external Agent;
8. preserve source identity/citations in final output;
9. evaluate retrieval separately from synthesis.

## Prototype readiness gate

**PASS.** Document/Node, ingestion transformation, derived index, Retriever, post-processing and response-synthesis boundaries are explicit enough to implement the kernel or use LlamaIndex selectively.
