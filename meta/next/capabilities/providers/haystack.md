# Provider: Haystack

Status: **PROTOTYPE-READY / ON-DEMAND PRODUCTION CONTEXT-PIPELINE FRAMEWORK / NOT LOCALLY INSTALLED**
Role: explicit component/pipeline framework for production RAG, search, context engineering and Agent applications.

## One-sentence understanding

**Haystack composes typed Components into explicit executable Pipelines around Document Stores, Retrievers, Rankers, Generators and Tools so ingestion/query/Agent behavior can be inspected, replaced and productionized without hiding retrieval behind one monolithic RAG object.**

## Current upstream direction — 2026-09-14

Haystack 3.0 is the current major generation. The project continues to position itself explicitly as a production-ready context-engineering/LLM orchestration framework for RAG, search, multimodal applications and Agents.

The main repository currently has about 26.5k GitHub stars and is Apache-2.0 licensed.

## Core primitives

### Document

A `Document` carries content plus metadata and optional embeddings/related fields.

Documents flowing through preprocessing/retrieval are projections of source material. Keep original source identity/provenance independently when the source matters.

### Document Store

Haystack explicitly distinguishes a Document Store from a Pipeline Component.

A Document Store is an interface to a persistence/search system. Retrievers interact with it, but it is not itself a pipeline step.

This is a useful boundary:

```text
Document Store
= storage/query capability

Retriever
= selection policy over that capability
```

Do not conflate database choice with retrieval semantics.

### Components

Components declare named inputs and outputs and implement one focused operation, for example:

- converters;
- cleaners;
- splitters;
- embedders;
- retrievers;
- rankers;
- routers;
- prompt builders;
- generators;
- writers;
- tool invokers.

This makes pipeline dependencies explicit and inspectable.

### Pipeline

A Haystack Pipeline is a directed multigraph of Components. Current pipelines can support branches, loops, routing and other control structures rather than only a linear RAG chain.

Typical indexing pipeline:

```text
Converter
  ↓
Cleaner
  ↓
Splitter
  ↓
Embedder / metadata enrichment
  ↓
DocumentWriter
  ↓
Document Store
```

Typical query pipeline:

```text
Query
  ↓
Embedder / query transform
  ↓
Retriever
  ↓
Ranker
  ↓
Prompt builder
  ↓
Generator
```

Use explicit pipeline graphs when they improve production clarity/testing/reuse. Do not introduce a second graph engine around Haystack.

### Retriever

Haystack retrievers are commonly coupled to a Document Store's supported search methods.

Retrieval modes include:

- sparse keyword/BM25;
- dense embeddings;
- sparse embeddings;
- hybrid/provider-specific approaches.

This confirms an important Ordivon rule:

**RAG does not imply vector search.** Exact wording, metadata or structured filters may make lexical/relational retrieval superior.

### Ranker

A Ranker receives a candidate set and reorders/reduces it using a more expensive relevance model or deterministic metadata policy.

This is a second-stage precision improvement, not a replacement for first-stage retrieval.

### Generator / Agent / Tools

Haystack includes model generators plus an Agent abstraction that can iteratively choose Tools and maintain invocation state.

Ordivon should use these only when a self-contained Haystack application benefits from them. Existing Codex/MCP/Temporal infrastructure remains the default owner of general Agent/execution semantics.

A Haystack Tool may wrap a Component, Pipeline or Python function; this does not make Haystack the universal Tool Registry for Ordivon.

## Ordivon routing rule

Prefer Haystack when a real application needs an explicit, testable context pipeline with several replaceable stages, such as:

- multiple converters/preprocessors;
- hybrid retrieval;
- filters/routing;
- reranking;
- multimodal/document pipelines;
- repeated ingestion/query flows maintained as application code;
- a production RAG service where component contracts and pipeline inspection are useful.

Prefer thinner composition when the workload is simple:

```text
source acquisition
  ↓
normalize
  ↓
store/search
  ↓
retrieve few records
  ↓
Agent
```

Do not install Haystack only to obtain a wrapper around one vector query and one model call.

## Boundary with n8n / Temporal / ComfyUI

Haystack Pipeline is an AI/context application graph.

- n8n owns external integration/event graphs;
- Temporal owns durable business/system workflows;
- ComfyUI owns media/model tensor graphs;
- Haystack owns in-process/context-engineering component graphs.

Their visual/graph similarity does not justify a universal Ordivon DAG engine.

## Boundary with storage systems

Document Store is an adapter boundary over actual databases/search engines.

Natural authority remains with the selected storage provider. Haystack should not become a second source of truth for the same corpus.

## Evaluation boundary

Measure separately:

1. ingestion fidelity/provenance;
2. retrieval quality;
3. reranking quality;
4. generated answer quality;
5. end-task/domain success.

Pipeline completion only proves the graph executed.

## Current local observation

No importable `haystack` package or `uv tool` installation was observed during the 2026-09-14 census.

No current workload proves that a production RAG pipeline framework is needed locally.

## Prototype recipe

A Haystack-like prototype needs only:

1. define a Component interface with typed/named inputs and outputs;
2. build a graph of components;
3. topologically execute ready components;
4. define a Document Store interface;
5. implement one lexical Retriever and one vector Retriever;
6. add one Ranker;
7. create separate indexing and query pipelines;
8. preserve provenance through Document metadata;
9. test each stage independently and evaluate retrieval/synthesis separately.

## Prototype readiness gate

**PASS.** Components, Pipeline, Document Store, Retriever/Ranker/Generator boundaries and Agent overlap are explicit enough to implement the kernel or adopt Haystack for a real production context pipeline.
