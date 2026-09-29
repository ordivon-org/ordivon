# Provider: Dify

Status: **PROTOTYPE-READY / ON-DEMAND AI-APPLICATION PLATFORM / NOT LOCALLY INSTALLED**
Role: integrated collaborative product surface for composing, operating and publishing LLM/Agent/RAG applications.

## One-sentence understanding

**Dify packages model providers, visual AI workflows, Agent strategies, Knowledge/RAG, plugins, telemetry integrations and application publishing into one collaborative Workspace so teams can turn AI compositions into usable Web/API applications without assembling every product surface themselves.**

## Current upstream observation — 2026-09-14

- repository: `langgenius/dify`;
- roughly 155k GitHub stars observed around 2026-09-13/14;
- current stable release observed: `1.17.1` (2026-09-10);
- Dify's own README describes it as an LLM app development platform combining AI workflow, RAG pipeline, Agent capabilities, model management and observability integrations;
- current self-host stack includes a substantial web/API/worker/plugin/agent/sandbox/data-store topology rather than a lightweight library.

## Licensing boundary

Dify is **not plain Apache-2.0**.

The repository uses the Dify Open Source License: Apache-2.0 plus additional conditions.

Important current restrictions include:

1. using Dify source code to operate a **multi-tenant environment** requires written authorization/commercial licensing;
2. when using Dify's source frontend, Dify logo/copyright information may not be removed or modified under the stated license conditions;
3. some commercial/enterprise use cases therefore require explicit license review rather than assuming ordinary Apache SaaS rights.

This is material for Ordivon commercialization. Do not make Dify the customer-facing multi-tenant platform without resolving these terms.

## What Dify actually integrates

Dify is most useful as a **product integration layer** over several already-understood capability classes.

### Model provider management

Dify exposes model providers and model types through provider/plugin abstractions and Workspace-level credentials.

Supported provider/plugin concepts include:

- LLMs;
- embeddings;
- rerank models;
- TTS/STT;
- moderation;
- image/other provider-specific models.

Current product features also include multiple credentials and some load-balancing/governance capabilities.

Architectural mapping:

```text
Dify model management
≈ LiteLLM/model-gateway concerns + product UI/workspace configuration
```

Dify's model layer is useful inside the Dify product. It does not create a reason for Ordivon to replace a separate mature model gateway when shared cross-application gateway semantics are required.

### Workflow / Chatflow

Dify provides a visual graph-based AI workflow runtime.

Current node families include concepts such as:

- LLM;
- Knowledge Retrieval;
- Tool;
- HTTP request;
- Code;
- conditions/routes;
- iteration;
- loop;
- parameter extraction;
- document extraction;
- variable aggregation/assignment;
- human input;
- start/end/answer.

Current source uses a GraphEngine and persists workflow/node execution state through repositories/layers.

This is an **AI application workflow engine**, not a general universal workflow authority.

Do not replace:

- Temporal macro durable-process semantics;
- n8n integration automation;
- Dagster asset lifecycle;
- ComfyUI media graph execution;
- LangGraph bespoke Agent-state semantics

merely because Dify can visually connect nodes.

### Agent

Dify provides Agent capabilities and, in current architecture, dedicated Agent runtime/backend support plus plugin-defined Agent Strategies.

Agent Strategy plugins can implement reasoning patterns such as ReAct/function-calling variants.

This is useful when the Agent is part of a Dify application.

It does not supersede Codex for engineering Agent work, MAF for general multi-agent orchestration, or LangGraph for bespoke checkpointed Agent state machines outside Dify.

### Knowledge / RAG

Dify Knowledge provides an integrated RAG product surface around:

```text
data sources
→ document processing/chunking
→ indexing
→ vector/keyword retrieval
→ metadata filtering
→ reranking
→ workflow/Agent context
```

Current configuration supports provider/internal or external knowledge, embedding/retrieval models, multiple chunk structures and metadata-based retrieval policies.

Current self-host deployments can select among multiple vector stores through configuration.

Architectural mapping:

```text
Dify Knowledge
≈ acquisition/ingestion + chunk/index/retrieval product + Workspace UI
```

The underlying source corpus remains authoritative. Knowledge-base chunks/indexes remain derived retrieval projections just as in LlamaIndex/Haystack/Qdrant analysis.

Do not make Dify Knowledge the universal Ordivon Knowledge authority.

### Plugins

Dify's plugin system is one of its most meaningful product-level capabilities.

Current plugin categories include:

- **Model** — model providers/types;
- **Tool** — callable capabilities for Agents/workflows;
- **Agent Strategy** — custom Agent reasoning strategies;
- **Extension / Endpoint** — external HTTP-facing extension points;
- **Datasource** — sources for Knowledge ingestion;
- **Trigger** — external webhook/event inputs.

Plugins can be distributed through:

- Dify Marketplace;
- GitHub repository;
- local `.difypkg` package.

Marketplace submissions receive review; GitHub/local installation do not provide the same review boundary.

A Dify plugin is a platform-specific capability package, not equivalent to MCP or Agent Skills:

```text
MCP
= cross-host capability/context protocol

Agent Skill
= portable procedural knowledge package

Dify Plugin
= Dify-specific executable/application extension
```

Use the Dify plugin ecosystem when deploying Dify applications; do not elevate its plugin contract into Ordivon Core.

### Triggers / integration edges

Dify Trigger plugins convert external webhook events into Dify workflow inputs and may manage provider subscription lifecycle.

This overlaps partially with n8n-style event integration.

Use Dify triggers when the event exists to drive a Dify application. Use n8n when the integration/event graph exists independently of any Dify AI app.

### Observability

Dify supports observability and current documentation/README highlights integrations with products such as Opik, Langfuse and Phoenix. Current source also contains OpenTelemetry support and GenAI/retrieval semantic mapping.

Correct boundary:

```text
Dify
= emits application/workflow/model/retrieval telemetry

OpenTelemetry / GenAI conventions
= telemetry substrate

Langfuse / Phoenix / other backend
= optional observability/eval product
```

Do not make Dify execution history the universal Ordivon observability store.

### Publishing surface

A major product-level advantage is that an AI composition can be turned into a usable application rather than remaining a graph/configuration artifact.

Dify provides publication surfaces including its app experience and APIs, allowing teams to move from Studio composition to a shareable/consumable application.

This is one of the genuinely valuable integrated capabilities:

```text
compose AI application
   ↓
test/debug
   ↓
publish version
   ↓
Web/API consumer surface
```

For Ordivon this makes Dify potentially useful as a **bounded AI-app delivery surface**, especially for internal tools or explicitly licensed single-tenant/customer deployments.

## Dify's real architectural value

After decomposing the underlying primitives, Dify's distinctive value is primarily **product integration and UX cohesion**, not a new low-level primitive.

It combines:

```text
Model access/configuration
+ AI workflow canvas/runtime
+ Agent strategies
+ RAG/Knowledge
+ Tool/plugin ecosystem
+ Credentials/Workspace/team model
+ observability hooks
+ app publishing/API
+ marketplace
```

into one product.

This is substantial value because productizing these surfaces independently is expensive even when the underlying primitives are already mature.

General lesson:

**Composition itself can be a mature product capability even when none of the underlying primitives are novel.**

## Dify vs Ordivon

Dify and Ordivon should not be made equivalent.

### Dify

A coherent AI-application development/publishing platform.

### Ordivon

A broader problem-to-verified-outcome composition system spanning research, engineering, operations, security, media, games, data, distribution and other domains.

Dify can therefore be one **application/product provider** used by Ordivon when the desired deliverable is naturally a Dify-style AI application.

Recommended relationship:

```text
real problem
  ↓
Ordivon chooses methods/providers
  ↓
if deliverable = interactive LLM/Agent/RAG application
  ↓
Dify may provide product shell + application runtime + publishing
  ↓
independent domain V&V
```

Do not put Ordivon's global decision/knowledge/verification semantics inside Dify.

## Comparison with the already-studied stack

### LiteLLM

LiteLLM is a model gateway/provider-normalization layer.
Dify provides model management as one feature inside an application platform.

Use LiteLLM when cross-application model gateway policy is the real requirement; use Dify's model configuration for apps living inside Dify.

### Haystack / LlamaIndex

They are context/RAG programming frameworks/toolkits.
Dify Knowledge is a productized managed RAG surface integrated into its Studio/apps.

### Qdrant

Qdrant is a dedicated retrieval engine.
Dify may use Qdrant or other vector stores underneath Knowledge.

### LangGraph / MAF / Codex

These are Agent runtime/orchestration providers with different semantic centers.
Dify provides an Agent/application surface as part of a larger product.

### n8n

n8n is general SaaS/API integration automation.
Dify workflows are optimized for AI application composition.

### Temporal

Temporal is durable general workflow execution.
Dify workflow execution persistence is application-platform workflow state, not a substitute for a macro business process engine.

### Langfuse / Phoenix

These are AI observability/evaluation products.
Dify can integrate with such systems; it does not need to own their semantic role.

## Self-hosting / operational cost

Dify's convenience comes from operating a substantial platform.

Current Compose architecture includes multiple responsibilities/services such as:

- web frontend;
- API service;
- workers;
- relational database;
- Redis/cache/queue state;
- plugin daemon/runtime;
- sandbox/code execution;
- current Agent backend/runtime components;
- storage;
- one selected vector store / search service as required;
- proxy/network/security helpers and optional telemetry infrastructure.

Minimum README requirements are modest, but production operation is not conceptually equivalent to installing a Python package.

Do not self-host Dify merely to obtain one RAG query, one Agent loop or one workflow graph.

## Security boundary

Dify is intentionally extensible and can execute meaningful operations through Tools, HTTP, Code, Plugins and Agent runtime.

Therefore production use requires attention to:

- plugin supply chain/signatures/review source;
- provider credentials and Workspace access;
- sandbox isolation;
- HTTP/SSRF/network boundaries;
- webhook/trigger signature validation;
- Knowledge access/RBAC;
- uploaded documents/data privacy;
- model/provider data handling;
- publication/API authentication;
- secret rotation and deployment hardening.

Marketplace review is a useful signal but not proof that a plugin is safe for a particular authority level.

## Ordivon adoption threshold

Use Dify when the **productized application surface** is the requirement, especially when several are simultaneously needed:

- non-engineers need visual AI composition;
- one application combines LLM + RAG + tools + workflow;
- team collaboration/Workspace configuration matters;
- the same composition needs a ready Web/API product surface;
- plugin/Marketplace integrations materially reduce delivery work;
- prompt/model/Knowledge/application settings need one operational UI;
- a bounded AI app should be delivered faster than building a custom frontend/backend.

Do not use Dify merely because the workload involves an LLM.

## Commercialization rule

Before exposing a Dify-derived deployment to external Ordivon customers, perform an explicit license/product review.

In particular:

```text
internal / development / appropriately licensed deployment
  -> potentially suitable

customer-facing multi-tenant Dify source deployment
  -> NOT assumed permitted; obtain required authorization/license
```

Also consider whether Dify's product UX/branding is actually meant to be visible to customers or whether Ordivon's own product surface should call lower-level providers directly.

## Prototype recipe

A minimal Dify-like product proof requires:

1. Workspace containing provider credentials/configuration;
2. app definition containing a visual/serializable AI workflow graph;
3. node registry for LLM, retrieval, tool, condition, code and human-input operations;
4. plugin registry for model/tool/datasource/trigger extensions;
5. small Knowledge dataset with chunk/index/retrieval lifecycle;
6. workflow executor and persisted execution history;
7. sandboxed code/tool boundary;
8. one Agent strategy/runtime path;
9. app draft/published version distinction;
10. published API/Web endpoint using the exact application version;
11. standard telemetry export;
12. RBAC/credential boundary around Workspace resources.

This is enough to reproduce the architectural product model. Rebuilding the full Dify platform would be counterproductive because the integration/product surface is precisely the mature capability to consume.

## Prototype readiness gate

**PASS.** The model/workflow/Agent/Knowledge/plugin/publishing/Workspace boundaries are explicit enough to explain Dify accurately, reproduce a small application-platform prototype, and decide when consuming Dify is superior to composing lower-level providers directly.
