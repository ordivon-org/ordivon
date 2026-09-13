# GitHub / Mature-Project Mining — Batch 2

Status: **QUEUED**
Selected: 2026-09-14

## Selection rule

Batch 2 is selected by missing architectural primitive, not by star count alone.

Stars are only a discovery signal. Mature standards may enter the batch even with fewer stars when they define a cross-vendor authority or interoperability boundary.

Every study keeps the existing acceptance gates:

1. **One-sentence test** — explain the project's essential mechanism and role accurately in one sentence.
2. **Prototype test** — understand the minimum primitives, boundaries and execution path well enough to implement a small working prototype or compose the mature project directly.

Stop exploratory source study once both gates pass. Deeper study becomes workload-driven.

## Primary queue

### 1. Model Context Protocol — specification + reference servers

Repository family:
- `modelcontextprotocol/modelcontextprotocol`
- `modelcontextprotocol/servers`

Question:

**What exactly belongs to MCP transport/protocol/resource/tool/prompt semantics, and what must remain provider/domain security and execution semantics?**

Why first:
- Ordivon already relies heavily on MCP;
- the reference-server repository explicitly distinguishes reference implementations from production-ready systems;
- this can remove remaining private connector/provider semantics before studying higher platforms.

Likely comparison targets: Agent Skills, Codex tools, Ordivon Runtime MCP surface.

### 2. Temporal

Repository: `temporalio/temporal`

Question:

**What is the irreducible durable-execution kernel: workflow history, deterministic replay, activities, retries/timers/signals, task queues and workers — and which Runtime semantics are actually still unique?**

Why now:
- directly tests Ordivon's historical Job/Attempt/recovery/effect machinery against a mature durable-execution platform;
- likely highest-value project for shrinking Runtime further without losing proven durability requirements.

### 3. LiteLLM

Repository: `BerriAI/litellm`

Question:

**What belongs in a model-provider gateway versus the Agent/application itself?**

Focus:
- OpenAI-compatible provider normalization;
- routing/fallback/load balancing;
- credentials/virtual keys/budgets/rate limits;
- observability/hooks;
- caching/policy;
- proxy versus SDK boundary.

Likely role: use provider rather than create an Ordivon model gateway.

### 4. OpenTelemetry + OpenInference

Repositories:
- `open-telemetry/opentelemetry-specification`
- `open-telemetry/opentelemetry-collector`
- `Arize-ai/openinference`

Question:

**What is the standards-native observability model for ordinary systems and AI/Agent executions?**

Focus:
- traces / metrics / logs;
- context propagation;
- resource/span/event/attribute semantics;
- OTLP and Collector pipelines;
- AI semantic conventions for model/tool/retrieval spans;
- privacy/redaction and cardinality boundaries.

This is a standards study first, product study second.

### 5. Langfuse vs Arize Phoenix

Repositories:
- `langfuse/langfuse`
- `Arize-ai/phoenix`

Question:

**Given OpenTelemetry/OpenInference as the semantic substrate, what additional product capabilities justify an AI-observability/evaluation platform?**

Compare:
- tracing;
- evals;
- datasets/experiments;
- prompt management;
- replay/debugging;
- self-hosting and storage cost;
- interoperability with OTEL/OpenInference.

Goal: choose/use at most what real workloads need; do not create Ordivon-native LLM observability semantics.

### 6. LlamaIndex vs Haystack

Repositories:
- `run-llama/llama_index`
- `deepset-ai/haystack`

Question:

**What is the mature context-engineering / RAG kernel, and which parts are merely framework convenience?**

Compare:
- ingestion/readers;
- parsing/chunking;
- indexes;
- retrievers/rerankers;
- query/pipeline composition;
- metadata/provenance;
- agents/tools;
- evaluation.

Goal: keep Ordivon Knowledge representation-plural rather than adopt a universal RAG framework.

### 7. Qdrant

Repository: `qdrant/qdrant`

Question:

**When does semantic/vector retrieval justify a dedicated vector-search engine rather than DuckDB/PostgreSQL/lexical search/in-memory indexes?**

Focus:
- collections/points/payloads;
- vector indexes/HNSW;
- filters and hybrid retrieval;
- persistence/distribution;
- query versus storage authority;
- operational threshold for adopting a service.

### 8. Dagster

Repository: `dagster-io/dagster`

Question:

**What does asset-centric orchestration add beyond Snakemake, n8n and ordinary workflow engines?**

Focus:
- software-defined assets;
- lineage/materialization;
- partitions;
- sensors/schedules;
- resources/IO managers;
- observability/backfills;
- data-asset authority.

Goal: determine whether Research/Data workloads expose a real gap or whether existing task-local tools are sufficient.

### 9. LangGraph

Repository: `langchain-ai/langgraph`

Question:

**What is the useful kernel of stateful Agent orchestration after Codex and Temporal are already understood?**

Focus:
- state graphs;
- checkpoints;
- cycles;
- interrupts / human-in-the-loop;
- durable agent threads;
- subgraphs;
- difference between Agent state and durable business workflow state.

Do not assume stateful graph orchestration belongs in Ordivon itself.

### 10. Dify

Repository: `langgenius/dify`

Question:

**After the underlying primitives are understood, what value remains in an integrated LLM-application product platform?**

Focus:
- visual AI workflows;
- model/provider management;
- RAG;
- agents/tools;
- observability;
- backend-as-a-service;
- product/application publishing surface;
- collaboration/governance.

Study last so that product packaging can be distinguished from genuinely new primitives.

## Comparison / deferred pool

### Kestra

Event-driven declarative orchestration. Compare only if Temporal/Dagster/n8n leave unresolved orchestration requirements.

### Prefect

Python-first resilient data workflows. Compare only if Dagster/Snakemake do not fit an observed data workload.

### OpenHands

Software-development Agent platform. Compare only if Codex leaves a concrete sandbox/runtime/multi-agent/software-agent capability gap.

### Milvus

Large-scale cloud-native vector database. Compare with Qdrant only if vector retrieval becomes a real operational workload whose scale/distribution requirements exceed the lighter option.

## Proposed study order

```text
MCP
 ↓
Temporal
 ↓
LiteLLM
 ↓
OpenTelemetry + OpenInference
 ↓
Langfuse vs Phoenix
 ↓
LlamaIndex vs Haystack
 ↓
Qdrant
 ↓
Dagster
 ↓
LangGraph
 ↓
Dify
```

The order intentionally moves from protocol/primitive -> execution/provider -> observability -> context/data -> agent/product platform.

## Batch-level success criterion

Batch 2 is successful if Ordivon gains better routing/verification knowledge while adding little or no proprietary infrastructure.

Desired outcome:

`more mature external capability understood + fewer private semantics owned`
