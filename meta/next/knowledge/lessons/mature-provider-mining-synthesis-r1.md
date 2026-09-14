# Mature Provider Mining Synthesis R1

Status: **REGISTERED**
Registered: 2026-09-14
Scope: cross-project synthesis after GitHub/mature-project mining batches 1–2.

## Thesis

Twenty study slots spanning standards, infrastructure, frameworks and product platforms converged on the same architectural result:

> **Ordivon should maximize problem-to-provider routing and verification knowledge while minimizing Ordivon-owned generic infrastructure and product surfaces.**

The durable pattern is:

```text
semantic primitive
   ↓
natural authority
   ↓
mature provider/standard
   ↓
thin composition
   ↓
independent verification
```

## Finding 1: UI/implementation shape is a poor classifier

Many mature systems expose nodes, graphs, workflows, tasks, threads or dashboards. Those similarities are not enough to unify them.

The stable classifier is the **semantic object whose lifecycle the system naturally owns**.

Examples:

```text
Temporal  -> durable process
Dagster   -> data asset / partition
LangGraph -> Agent working/control state
n8n       -> external integration event/action
ComfyUI   -> media/model computation
Haystack  -> context pipeline
Dify      -> AI application composition/product state
```

Therefore Ordivon should not infer a universal graph runtime from visual similarity.

## Finding 2: mature systems increasingly expose thin kernels plus registries/adapters

Repeated architecture pattern:

```text
small stable kernel
  +
registry/catalog of replaceable implementations
  +
provider-native execution
```

Examples observed across the studies include tool/action/converter/node/provider/component registries.

The transferable lesson is **replaceable capability registration**, not one global Ordivon registry containing every semantic class.

## Finding 3: representation is a first-class boundary

Agents benefit when raw external reality is projected into a task-appropriate representation:

```text
web        -> cleaned context / structured page
browser    -> indexed affordances + optional vision
files      -> Markdown/document model
repo graph -> bounded relationship subgraph
media flow -> typed generative workflow
retrieval  -> bounded provenance-bearing chunks
```

But every representation is lossy/derived. It must not silently become source truth.

## Finding 4: exact same words mean different guarantees

Words such as `durable`, `task`, `workflow`, `retry`, `success`, `memory`, `thread`, `asset`, `trace` and `state` recur across projects with different contracts.

Example:

```text
MCP Task       = protocol projection of long-running work
Temporal Task  = work scheduled inside durable workflow machinery
Runtime Job    = exact physical execution evidence object
Plane Task     = human coordination item
```

Therefore provider integration must preserve provider-native semantics instead of mapping every noun into one Ordivon object.

## Finding 5: retries require semantic ownership

Multiple mature systems independently reinforce:

> **Retry belongs to the layer that understands the effect contract.**

Examples:

- LiteLLM owns model-request retries and disables nested SDK retry where appropriate;
- Temporal retries Activities but expects idempotent/reconcilable effects;
- Runtime fails closed on ambiguous opaque local dispatch rather than blindly redispatching;
- provider-native APIs may own idempotency keys/transaction IDs.

A generic Ordivon retry button is unsafe.

## Finding 6: durable state is plural

There is no single correct durability store.

```text
Temporal Event History
= durable process state

LangGraph checkpoint
= Agent working-state recovery/debug state

Dagster materialization history
= data-asset lifecycle state

Runtime Registry
= physical execution/effect evidence

Git / source store
= code/document authority
```

Natural authority over global state is therefore not only a design preference; it is demanded by incompatible durability semantics.

## Finding 7: indexes/projections should usually be rebuildable

Repeated examples:

- Graphify graph;
- Qdrant/pgvector embeddings/indexes;
- RAG chunks;
- OpenTelemetry traces/metrics/log projections;
- search/visibility metadata;
- AI experiment dashboards.

Default design should bind projections to source identity/version so they can be regenerated and drift detected.

## Finding 8: standards often shrink protocols over time

MCP deprecating/relocating capabilities and OTel absorbing AI conventions show a mature pattern:

> If a more natural authority emerges, remove or narrow the abstraction rather than preserve compatibility forever.

Ordivon should actively delete private semantics when a mature standard/provider becomes the better owner.

## Finding 9: frameworks are optional composition conveniences

LlamaIndex, Haystack, LangGraph and similar frameworks are valuable when their abstractions reduce real glue/maintenance cost.

They should not become mandatory layers simply because they cover a category called RAG/Agents/Workflow.

Sometimes ordinary provider calls + a small amount of code are the thinnest solution.

## Finding 10: products matter as much as primitives

Batch 1 mainly demonstrated infrastructure/provider substitution.

Batch 2 demonstrated **product-surface substitution**:

- Phoenix/Langfuse productize trace→dataset→eval→experiment loops;
- Dify productizes AI app composition→Workspace→publishing;
- Dagster productizes data-asset catalog/lineage/operation.

Understanding how a product is built is not evidence that Ordivon should rebuild it.

## Finding 11: installation is not proof of maturity

A successful study can correctly end with **no installation**.

Most Batch 2 providers remained on demand because current workloads do not justify their daemon/storage/state/licensing costs.

This is a positive architectural result:

`knowledge acquired > operational debt added`.

## Finding 12: licensing is an architecture input

Technical fit alone is insufficient.

Examples found during studies include:

- MIT/open core with enterprise-only modules;
- ELv2 restrictions on providing substantial functionality as a hosted service;
- Dify's additional multi-tenant/frontend conditions.

Commercial/product routing must include license rights before a provider becomes customer-facing infrastructure.

## Finding 13: verification stays outside the provider claim

Across every layer:

```text
provider says success
!=
problem solved
```

Useful ladder:

```text
protocol/transport success
→ execution success
→ provider read-back/effect evidence
→ technical artifact/data conformance
→ domain acceptance
→ real-world outcome
```

Ordivon's persistent role is to know which rung is actually required and how to obtain evidence for it.

## Finding 14: Ordivon's defensible IP is composition knowledge

As mature infrastructure and product surfaces absorb generic implementation work, the increasingly valuable proprietary asset is the mapping:

```text
problem conditions
→ standards/methods
→ provider selection
→ composition constraints
→ authority boundaries
→ verification strategy
→ outcome evidence
```

This can be learned across Research, Engineering, Security, Media, Game, Finance and future domains without forcing those domains into one private ontology.

## New-project default policy

Before opening another broad mining batch, prefer **gap-driven discovery**.

Search/study a new project only if at least one is true:

1. a real workload has an unresolved capability gap;
2. an existing natural authority is clearly failing measured acceptance;
3. a new standard materially changes interoperability/security/compliance;
4. a product surface can remove substantial custom delivery work;
5. a provider change materially improves cost, quality, latency, reliability or licensing.

Otherwise defer.

## Canonical routing view

Use `docs/CAPABILITY_AUTHORITY_MAP_R1.md` as the current cross-project routing map.

That map is intentionally a view, not a topology. It should evolve as providers and standards change while the core principles remain stable.

## Verdict

**TWO-BATCH SYNTHESIS PASS.**

The mining program found many mature capabilities but no evidence that Ordivon needs a large new generic subsystem. The next research should be driven by real capability gaps or product-delivery requirements rather than collecting another fixed list of popular repositories.
