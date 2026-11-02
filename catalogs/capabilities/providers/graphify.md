# Provider: Graphify

Status: **PROTOTYPE-READY / ON-DEMAND**
Role: local relational code-and-corpus context provider for multi-hop structural questions.

## One-sentence understanding

**Graphify turns a repository/corpus into a provenance-tagged knowledge graph so an Agent can answer relationship and impact questions by traversing explicit paths instead of repeatedly grepping or stuffing raw files into context.**

## When Ordivon should route work here

Prefer Graphify when the question is primarily relational and multi-hop, for example:

- what connects component A to component B;
- who calls/imports/inherits from this symbol across many files;
- what may be affected if this core abstraction changes;
- which subsystems/communities exist in a large repository;
- where architectural cross-links or god nodes appear;
- how code, docs, schemas/configuration and other project artifacts relate;
- when repeated repository reasoning is spending large amounts of context reconstructing the same dependency structure.

Do not make Graphify a mandatory preprocessing step for:

- small repositories;
- one-file or one-symbol questions;
- simple lexical lookup;
- direct LSP/symbol navigation;
- ordinary SQL/relational data problems;
- semantic similarity retrieval where relation paths are not important;
- every Ordivon Knowledge task merely because a graph representation exists.

## Core pipeline

The upstream architecture is intentionally simple:

`detect -> extract -> build -> cluster -> analyze -> report/export`

The stages communicate through ordinary Python data structures and a NetworkX graph. The default local artifact is a `graph.json` plus human-readable/report visualizations; a graph database is optional, not required.

### Detect

Inventory the corpus and classify supported files.

### Extract

Convert source material into typed nodes and edges.

For code, deterministic tree-sitter parsing yields structural relationships such as calls/imports/inheritance. Non-code material can use a semantic/model-assisted pass when configured.

### Build

Merge extraction results into a graph.

Minimal model:

```text
Node = entity/symbol/document/object
Edge = typed relationship between nodes
```

Examples:

- function -> calls -> function;
- module -> imports -> module;
- class -> inherits -> class;
- code symbol -> documented_by -> document/rationale;
- table/config/resource -> related_to -> consuming component.

### Provenance / confidence

Graphify's strongest design choice is to treat **an edge as a claim** and label how that claim was established:

- `EXTRACTED` — deterministic source/parser evidence;
- `INFERRED` — model/semantic inference;
- `AMBIGUOUS` — evidence exists but resolution is uncertain.

Do not flatten deterministic and model-inferred relationships into one undifferentiated graph.

### Cluster / analyze

Graph structure can be analyzed for:

- communities/subsystems;
- high-degree / central nodes;
- surprising cross-community links;
- cycles;
- changes between graph snapshots;
- potential blast radius / PR overlap.

These are derived views, not new sources of truth.

### Query / traversal

The useful query primitives are structural:

- natural-language query -> seed nodes -> bounded BFS/DFS subgraph;
- neighbors of a node;
- shortest path between two nodes;
- explain a node/edge with source citations;
- community membership;
- graph statistics/central nodes.

The result should return a **bounded relevant subgraph with source locations**, not the whole graph.

## Boundary with grep, LSP and RAG

### grep / lexical search

Best for exact strings and small/local questions.

### LSP / language-native code intelligence

Best for precise symbol definition/reference/type navigation in supported languages.

### RAG / vector retrieval

Best when the key problem is semantic similarity or topical retrieval from text.

### Graphify

Best when the answer depends on explicit relationships, paths, neighborhoods or multi-hop impact across a larger corpus.

Graph retrieval is complementary to lexical, LSP and vector retrieval. Do not claim one representation universally replaces the others.

## Ordivon use rule

Use the thinnest adequate context method:

```text
small exact question -> grep/read
symbol navigation -> LSP
semantic/topical lookup -> search/RAG
multi-hop structural relation -> Graphify
```

Escalate to a graph only when the graph answers a question that is materially harder or more expensive in the thinner representation.

## Authority boundary

Graphify's graph is a **derived index/snapshot**, not the authority for repository truth.

- source files/repository remain authoritative;
- parsed `EXTRACTED` edges are reproducible projections of that source state;
- inferred/ambiguous edges are hypotheses with provenance;
- `graph.json` can be rebuilt/refreshed when source changes;
- Graphify's reports/communities/centrality are derived analysis.

Do not turn Graphify into a second configuration/task/domain source of truth.

## Incremental freshness

A graph snapshot can become stale. Prefer incremental re-scan/update when a real workload benefits from persistent graph context.

The freshness question is task-dependent: rebuild/update before relying on graph structure for consequential current-state reasoning.

## Prototype recipe

A minimal Graphify-like code prototype needs only:

1. walk a repository and select supported code files;
2. parse each file with tree-sitter or another language parser;
3. emit nodes for files/modules/classes/functions;
4. emit typed edges for imports/calls/inheritance/references;
5. attach source location and provenance to every edge;
6. merge into a NetworkX-style graph;
7. serialize to JSON;
8. implement `neighbors(node)` and `shortest_path(a,b)`;
9. implement a bounded BFS query from lexical/name-matched seed nodes;
10. return paths/subgraphs with `file:line` evidence.

Optional layers:

- community detection;
- centrality/god-node analysis;
- semantic extraction from docs;
- MCP interface;
- Neo4j/FalkorDB export;
- visualization.

No graph database, embedding store or hosted service is required for the architectural prototype.

## Prototype readiness gate

**PASS.** The entity/edge model, deterministic extraction path, provenance model, traversal/query primitives and routing boundary are explicit enough to implement a functional prototype without deeper production-source study.
