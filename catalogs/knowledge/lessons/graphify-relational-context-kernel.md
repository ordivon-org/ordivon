# Graphify Relational Context Kernel — extracted design lessons

Status: **REGISTERED / PROTOTYPE-READY**
Registered: 2026-09-14

## One-sentence model

**Graphify compresses a large corpus into a queryable relationship index whose edges preserve provenance, allowing Agents to retrieve multi-hop structure as bounded paths/subgraphs instead of reconstructing relationships from raw files on every question.**

## The central insight

The useful distinction is not `graph vs no graph`. It is:

```text
question about content/similarity
vs
question about relationships/path/impact
```

A graph pays for itself when the problem depends on how entities connect.

Examples:

- `Where is RateLimiter defined?` -> grep/LSP is enough.
- `What path connects ApiGateway to RedisClient?` -> graph traversal is natural.
- `What code discusses caching?` -> semantic/lexical retrieval may be enough.
- `If SessionStore changes, which callers/subsystems are transitively exposed?` -> graph structure is valuable.

## Mechanism 1: parse facts before asking a model to infer them

For source code, many useful relationships are syntactic facts. Use parsers/tree-sitter/LSP-style analysis to extract them deterministically rather than paying an LLM to rediscover them.

General rule:

`deterministic evidence first -> semantic inference only for residual ambiguity/cross-modal links`

This is cheaper, reproducible and easier to audit.

## Mechanism 2: an edge is a claim

Do not store a relationship without storing how it was established.

Useful provenance classes:

- **EXTRACTED** — directly established by parser/source structure;
- **INFERRED** — a model or heuristic connected evidence;
- **AMBIGUOUS** — unresolved evidence remains.

This turns graph traversal into inspectable reasoning rather than an opaque web of relationships.

The transferable Ordivon rule is:

**Derived relationships should carry evidence/provenance at the relationship itself, not only at the final answer.**

## Mechanism 3: retrieve a bounded subgraph, not the whole corpus

The graph is an index for context selection.

```text
large corpus
   ↓ build once/update
relationship graph
   ↓ query
small relevant path/subgraph
   ↓
Agent context
```

This is analogous to Firecrawl cleaning web pages and Browser Use exposing affordances: raw reality is reduced to the task-relevant representation before reasoning.

## Mechanism 4: graph traversal and similarity retrieval solve different questions

Vector/RAG retrieval answers roughly:

> Which chunks are semantically similar to my query?

Graph traversal answers roughly:

> Which entities are connected, through what typed path, and why?

Use both when a workload genuinely needs both. Do not adopt vendor claims that graph retrieval universally replaces RAG; topical/semantic lookup remains a distinct problem.

## Mechanism 5: graphs are derived projections

Repository/source data remains authoritative.

A graph should be cheap enough to rebuild or incrementally refresh. It is a cache/index of structure, not a second mutable truth store.

This matters for Ordivon because its historical failure mode was promoting useful projections into custom authorities.

## Mechanism 6: graph databases are optional infrastructure

A useful knowledge graph does not imply Neo4j/FalkorDB/another persistent graph service.

For a repo-scale prototype or local Agent context provider:

`plain graph.json + NetworkX/traversal code`

can be sufficient.

Introduce a graph database only when measured scale, concurrent access, query language, persistence or operational needs justify it.

## Mechanism 7: community/centrality are heuristics, not semantics

Community detection and high-degree nodes are useful architecture views, but they are derived graph analyses.

- high degree does not automatically mean architectural importance;
- community boundaries do not automatically equal designed subsystem boundaries;
- inferred cross-links require review according to provenance.

Treat them as navigation/prioritization hints.

## Mechanism 8: graph value increases with repeated multi-hop queries

Building/maintaining a graph has a cost. It is most justified when:

- the corpus is large;
- relationships cross many files/artifacts;
- Agents repeatedly ask impact/path/dependency questions;
- raw-file context is expensive;
- structural context can be reused across many turns/tasks.

For small one-off questions, direct read/grep/LSP is usually better.

## Minimal prototype

```text
files
  ↓
parser
  ↓
entities + typed edges + source locations
  ↓
NetworkX / adjacency lists
  ↓
JSON snapshot
  ↓
query:
  neighbors
  shortest_path
  BFS/DFS subgraph
  ↓
file:line cited context
```

Add semantic/inferred edges only after deterministic extraction works.

## Relationship to Ordivon's Knowledge layer

Graphify does **not** justify a universal Ordivon Knowledge Graph.

Ordivon Knowledge should remain representation-plural:

```text
documents/files      -> direct read/search
structured records   -> SQL/relational
semantic text        -> lexical/vector/search
explicit relationships -> graph traversal
procedures           -> Agent Skills
```

Choose representation according to the question and natural authority.

## What Ordivon should retain

1. Parse deterministic relationships before model inference.
2. Treat every derived edge as a provenance-bearing claim.
3. Use graphs for relationship/path/impact questions, not by default.
4. Return bounded subgraphs into Agent context instead of whole corpora.
5. Keep graph snapshots derived and rebuildable.
6. Avoid graph databases until operational evidence requires them.
7. Keep graph traversal complementary to grep/LSP/RAG/SQL.
8. Evaluate graph value on real repeated tasks, not visual impressiveness.

## What Ordivon should not copy

- a mandatory universal Knowledge Graph;
- a second knowledge authority detached from source artifacts;
- Neo4j/FalkorDB as base infrastructure without workload evidence;
- Graphify-specific ontology as Ordivon's global ontology;
- community/god-node metrics as architectural truth;
- model-inferred edges without explicit provenance;
- always-on graph construction for small/simple workloads.

## Project-study acceptance

### One-sentence test

PASS: Graphify is a provenance-aware relationship index for repositories/corpora that lets Agents retrieve structural paths and impact context instead of reconstructing them from raw files.

### Prototype test

PASS: deterministic parser extraction, typed/provenance-bearing edges, a local graph representation and basic traversal are enough to reproduce the architectural core.

## Verdict

**PASS — ON-DEMAND PROVIDER + EXTRACT RELATIONAL-CONTEXT RULES.**

Do not install or activate by default. Install/use when a real repository/corpus exposes repeated multi-hop structural reasoning cost that grep/LSP/search cannot handle efficiently.
