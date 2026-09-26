# GitHub / Mature-Project Mining — Batch 2

Status: **COMPLETED**
Selected: 2026-09-14
Completed: 2026-09-14

## Selection rule

Batch 2 was selected by missing architectural primitive, not by star count alone.

Stars are only a discovery signal. Mature standards entered the batch even with fewer stars when they defined a cross-vendor authority or interoperability boundary.

Every study used the same acceptance gates:

1. **One-sentence test** — explain the project's essential mechanism and role accurately in one sentence.
2. **Prototype test** — understand the minimum primitives, boundaries and execution path well enough to implement a small working prototype or compose the mature project directly.

Exploratory source study stopped once both gates passed; deeper study remains workload-driven.

## Completed studies and verdicts

### 1. Model Context Protocol — PASS

**Kernel:** stateless interoperability for Tools/Resources/Prompts and extensions; protocol does not own execution/domain truth.

Verdict:

`ADOPT STANDARD / DELETE PRIVATE CONNECTOR SEMANTICS WHERE MCP IS SUFFICIENT`

Registered:

- `catalogs/capabilities/providers/mcp.md`
- `catalogs/knowledge/lessons/mcp-interoperability-kernel.md`

### 2. Temporal — PASS

**Kernel:** durable Workflow Event History + deterministic replay + retryable Activities + Task Queues/Workers.

Verdict:

`USE TEMPORAL FOR DURABLE WORKFLOWS; KEEP RUNTIME ONLY FOR ITS NARROWER PHYSICAL EFFECT-COMMIT BOUNDARY`

Registered:

- `catalogs/capabilities/providers/temporal.md`
- `catalogs/knowledge/lessons/temporal-durable-execution-kernel.md`

### 3. LiteLLM — PASS

**Kernel:** provider normalization plus optional shared AI gateway for deployment routing, virtual keys, budgets, rate limits and telemetry.

Verdict:

`USE A MATURE MODEL GATEWAY WHEN SHARED MODEL POLICY EXISTS; DO NOT BUILD ORDIVON-NATIVE MODEL PROXY/ROUTER`

Registered:

- `catalogs/capabilities/providers/litellm.md`
- `catalogs/knowledge/lessons/litellm-model-gateway-kernel.md`

### 4. OpenTelemetry + OpenInference — PASS

**Kernel:** OTel/OTLP owns telemetry/context substrate; OTel GenAI is the preferred evolving AI semantic direction; OpenInference is a useful selective instrumentation/compatibility layer.

Verdict:

`STANDARDIZE ON OTEL/OTLP; USE OTEL GENAI FIRST WHEN PRACTICAL, OPENINFERENCE SELECTIVELY; KEEP OBSERVABILITY OUT OF EXECUTION TRUTH`

Registered:

- `catalogs/capabilities/providers/opentelemetry.md`
- `catalogs/capabilities/providers/openinference.md`
- `catalogs/knowledge/lessons/otel-openinference-observability-kernel.md`

### 5. Langfuse vs Phoenix — PASS / alternatives

**Kernel:** AI engineering product loop from trace -> curated dataset -> experiment -> evaluator -> regression comparison -> deployment/feedback.

Verdict:

`KEEP BOTH AS ALTERNATIVE ON-DEMAND PRODUCTS; DEPLOY NEITHER UNTIL A REAL TRACE/EVAL WORKLOAD EXISTS`

Routing:

- Phoenix first candidate for lightweight internal Agent/eval workbench;
- Langfuse first candidate for shared production AI-engineering platform.

Registered:

- `catalogs/capabilities/providers/langfuse.md`
- `catalogs/capabilities/providers/phoenix.md`
- `catalogs/knowledge/lessons/langfuse-phoenix-ai-engineering-platform-kernel.md`

### 6. LlamaIndex vs Haystack — PASS / on-demand frameworks

**Kernel:** acquire -> normalize -> provenance-preserving chunk/enrich -> derived index -> retrieve -> optional rerank -> bounded context -> synthesis/Agent -> separate retrieval/answer evaluation.

Verdict:

`EXTRACT THE CONTEXT/RETRIEVAL KERNEL; KEEP BOTH FRAMEWORKS ON-DEMAND`

Routing:

- LlamaIndex: toolkit/integration source, especially document context;
- Haystack: stronger explicit production context-pipeline candidate.

Registered:

- `catalogs/capabilities/providers/llamaindex.md`
- `catalogs/capabilities/providers/haystack.md`
- `catalogs/knowledge/lessons/llamaindex-haystack-context-retrieval-kernel.md`

### 7. Qdrant — PASS

**Kernel:** dedicated filtered/hybrid vector-search service for when similarity retrieval becomes a first-class production workload.

Verdict:

`KEEP QDRANT ON-DEMAND; PREFER EXISTING RELATIONAL/LOCAL AUTHORITY UNTIL VECTOR SEARCH BECOMES A FIRST-CLASS PRODUCTION WORKLOAD`

Routing heuristic:

`direct exact -> DuckDB/local -> PostgreSQL+pgvector -> Qdrant when specialized independent vector service is justified`

Registered:

- `catalogs/capabilities/providers/qdrant.md`
- `catalogs/knowledge/lessons/qdrant-vector-search-kernel.md`

### 8. Dagster — PASS

**Kernel:** asset-centric data orchestration around durable Asset identity, materializations, partitions, backfills, lineage, checks and freshness/automation.

Verdict:

`DISTINCT DATA-ASSET ORCHESTRATION PRIMITIVE, BUT KEEP DAGSTER ON-DEMAND`

Routing:

```text
Snakemake -> scientific/project file DAG
n8n       -> API/SaaS integration
Temporal  -> generic durable process
Dagster   -> persistent data-product/asset lifecycle
```

Registered:

- `catalogs/capabilities/providers/dagster.md`
- `catalogs/knowledge/lessons/dagster-asset-orchestration-kernel.md`

### 9. LangGraph — PASS

**Kernel:** checkpointed programmable Agent state machine with typed State/reducers, cyclic routing, dynamic interrupts, thread persistence and state fork/time-travel.

Verdict:

`KEEP LANGGRAPH ON-DEMAND FOR BESPOKE STATEFUL AGENT APPLICATIONS; PREFER CODEX/MAF FOR EXISTING AGENT WORK AND TEMPORAL FOR MACRO DURABLE PROCESS STATE`

Registered:

- `catalogs/capabilities/providers/langgraph.md`
- `catalogs/knowledge/lessons/langgraph-agent-state-machine-kernel.md`

### 10. Dify — PASS

**Kernel:** integrated AI-application product shell combining model/provider configuration, visual AI workflow, Agent strategies, Knowledge/RAG, plugins, Workspace collaboration and app publication/API surfaces.

Verdict:

`DIFY IS A PRODUCT-LAYER COMPOSITION PLATFORM, NOT A NEW ORDIVON CORE PRIMITIVE. KEEP IT ON-DEMAND FOR PRODUCTIZED AI APPS; REVIEW LICENSE BEFORE EXTERNAL MULTI-TENANT COMMERCIAL USE.`

Registered:

- `catalogs/capabilities/providers/dify.md`
- `catalogs/knowledge/lessons/dify-ai-application-platform-kernel.md`

## Batch-level architectural result

Batch 2 did **not** reveal a missing universal Ordivon subsystem.

Instead it produced a set of natural authorities:

```text
MCP
= capability/context interoperability

Temporal
= macro durable process

Runtime
= narrow exact local physical effect commitment/evidence

LiteLLM
= shared model gateway when needed

OpenTelemetry / OTLP
= telemetry/context substrate

OTel GenAI / OpenInference
= AI telemetry semantics/instrumentation

Langfuse / Phoenix
= optional AI engineering/eval product layer

LlamaIndex / Haystack
= optional context/retrieval framework

Qdrant
= optional dedicated vector-search service

Dagster
= persistent data-asset lifecycle orchestration

LangGraph
= bespoke checkpointed Agent state machine

Dify
= integrated AI-application product/publishing shell
```

## Recurring pattern across Batch 2

The strongest repeated pattern is:

```text
natural semantic authority
        ↓
standard/provider-native interface
        ↓
thin Ordivon selection/composition
        ↓
independent verification
```

Not:

```text
all external systems
        ↓
convert into one private Ordivon ontology/runtime/database/workflow engine
```

## Product-level lesson

Batch 1 mostly showed that mature infrastructure/provider capabilities should be consumed rather than rebuilt.

Batch 2 adds a second lesson:

**Do not rebuild mature product surfaces either.**

Dify/Langfuse/Phoenix/Dagster demonstrate that substantial value can reside in integration UX, collaboration, cataloging, experimentation and publishing even when underlying primitives are known.

Therefore Ordivon should build a new product surface only when its cross-domain problem-solving/verification model cannot be adequately delivered by composing existing mature products.

## Current installation result

Batch 2 was deliberately architecture-first rather than install-first.

No new base dependency was installed merely because it passed study. Several providers remain on-demand because current workloads do not justify their operational state:

- Temporal server not activated;
- LiteLLM not installed;
- Langfuse/Phoenix not installed;
- LlamaIndex/Haystack not installed;
- Qdrant not installed;
- Dagster not installed;
- LangGraph not installed;
- Dify not installed.

This is a successful outcome, not incomplete migration.

## Deferred comparison pool

### Kestra

Event-driven declarative orchestration. Compare only if Temporal/Dagster/n8n leave unresolved orchestration requirements.

### Prefect

Python-first resilient data workflows. Compare only if Dagster/Snakemake do not fit an observed data workload.

### OpenHands

Software-development Agent platform. Compare only if Codex leaves a concrete sandbox/runtime/multi-agent/software-agent capability gap.

### Milvus

Large-scale cloud-native vector database. Compare with Qdrant only if vector retrieval becomes a real operational workload whose scale/distribution requirements exceed the lighter option.

## Batch-level success criterion

**PASS.**

Ordivon gained substantially better routing and authority boundaries while adding almost no proprietary infrastructure.

Observed direction:

`more mature external capability understood + fewer private semantics owned + clearer product-layer routing`
