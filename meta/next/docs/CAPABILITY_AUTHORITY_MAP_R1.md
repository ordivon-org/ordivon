# Capability / Natural-Authority Map R1

Status: **CANONICAL ROUTING VIEW**
Registered: 2026-09-14
Basis: GitHub/mature-project mining batches 1–2 plus currently registered mature providers.

## 1. Purpose

This document is a **routing view**, not a fixed Ordivon topology.

It answers five questions for a real task:

1. What semantic object or primitive is actually being managed?
2. Which mature discipline/standard/provider is its natural authority?
3. What evidence should trigger activation of that provider/product?
4. What generic Ordivon implementation should therefore **not** be built?
5. What independent verification boundary remains after the provider reports success?

The map must remain replaceable. Provider names are examples/candidates, not identity-defining Ordivon components.

## 2. Universal routing algorithm

For every new problem, provider or proposed subsystem:

```text
REAL PROBLEM / OUTCOME
        ↓
DEFINE acceptance + constraints + authority
        ↓
IDENTIFY the semantic primitive/object
        ↓
FIND the natural mature authority
        ↓
SELECT the thinnest adequate provider/product
        ↓
ACTIVATE only if workload trigger is real
        ↓
EXECUTE through provider-native semantics
        ↓
VERIFY against independent domain/reality evidence
        ↓
LEARN the successful composition
```

If a mature provider exists, Ordivon implementation order is:

```text
configure/profile
    ↓ insufficient?
reuse directly
    ↓ insufficient?
thin adapter
    ↓ insufficient on a real task?
prove substitution failure
    ↓
minimal custom implementation
```

No custom semantic owner is admitted merely because two providers need coordination.

## 3. Stable distinction: semantic authority vs projection

Many studied systems expose useful state, but that state is often a **projection** rather than the underlying authority.

Examples:

```text
OpenTelemetry trace      != Runtime Job/Attempt truth
Dagster materialization  != physical table/file content
Qdrant vector index      != source-document truth
Graphify graph           != source-repository truth
Langfuse score           != domain correctness
MCP Task                 != durable execution engine
Dify workflow success    != real-world outcome verified
```

Default rule:

> **Keep truth in the natural owner; keep cross-system views disposable and rebuildable.**

## 4. Primary authority map

| Primitive / semantic object | Natural authority | Mature provider / standard candidates | Activate when | Do not build in Ordivon | Verification boundary |
|---|---|---|---|---|---|
| Procedural knowledge for Agents | Skill package / scoped instructions | Agent Skills standard, existing Skills | repeated procedural guidance should be reusable/discoverable | private Skill registry/trigger ontology | did the resulting work satisfy task/domain acceptance? |
| Engineering requirements-to-plan discipline | engineering method | Spec Kit lessons, Superpowers lessons | engineering task has material ambiguity/risk/coordination | mandatory private SDLC shell | code/system reality, tests, independent acceptance |
| Packaged engineering Agent loop | Agent host/harness | Codex | ordinary repo/code/build/debug work | Ordivon coding-agent runtime | build/tests/reality; Agent assertion is not completion |
| Standard multi-agent collaboration | Agent orchestration provider | Microsoft Agent Framework | sequential/concurrent/handoff/group patterns are enough | private multi-agent framework | task/domain outcome |
| Bespoke checkpointed Agent state machine | Agent application state | LangGraph | custom cycles, reducers, HITL interrupt/resume, checkpoint fork are product requirements | universal Ordivon StateGraph/thread DB | Agent-state recovery + independent external-effect/domain verification |
| Capability/context interoperability | protocol owner | MCP | external tools/resources/prompts need interoperable host access | private connector RPC protocol | provider/execution/domain evidence remains external |
| Deterministic API/SaaS/event integration | integration workflow engine | n8n | recurring connector/webhook/API graph | Ordivon integration engine/node catalog | downstream provider read-back/semantic result |
| General durable application/business process | durable workflow engine | Temporal | process must survive crashes, waits, retries, messages, Worker replacement | Runtime workflow engine, private timers/queues/signals | Activity effect semantics + domain acceptance |
| Exact local physical effect commitment/evidence | physical execution boundary | Ordivon Runtime | source/executable/input/authority binding and ambiguity-preserving local execution evidence matter | generic workflow/business state inside Runtime | external/provider/domain truth beyond process execution |
| Browser-adaptive UI control | browser Agent adapter | Browser Use | changing/unknown web UI requires semantic Agent navigation | DOM serializer/CDP browser Agent stack | resulting page/provider state |
| Public-web acquisition/context | web acquisition provider | Firecrawl | search/scrape/map/crawl and cleaned agent-ready web context needed | crawler/render/proxy stack | source quality/currentness/evidence sufficiency |
| Lightweight heterogeneous-file normalization | document converter/router | MarkItDown | ordinary files need token-efficient text/Markdown | universal parser stack | fidelity adequate for task; escalate when not |
| Rich document / scholarly parsing | specialized parser | Docling, GROBID, LlamaParse/LiteParse when justified | layout/OCR/table or scholarly citation semantics matter | one universal Ordivon document parser | source-document fidelity and task-specific extraction checks |
| Explicit multi-hop relationship context | graph-derived index | Graphify | relationship/path/impact questions recur and grep/LSP/RAG are inadequate | global Ordivon Knowledge Graph | source code/corpus + provenance of edges |
| Context/RAG application composition | retrieval framework | Haystack, LlamaIndex | multi-stage retrieval pipeline/integration framework measurably reduces glue | universal RAG framework as Core | retrieval eval separate from answer/domain eval |
| Similarity / vector retrieval inside existing relational authority | relational DB extension | PostgreSQL + pgvector | vectors are one query mode over existing authoritative relational data | second DB by default | retrieval relevance + DB/domain truth |
| Dedicated production vector retrieval | vector-search service | Qdrant | filtered ANN/hybrid/multivector/quantization/independent scale become first-class workload | private vector DB | exact/labeled retrieval baseline + source truth |
| Model-provider normalization/routing | model gateway | native SDK → LiteLLM SDK/Proxy when needed | multiple providers/apps require shared routing, keys, quota/budget policy | Ordivon model proxy/router | model response quality + provider billing/usage reconciliation when consequential |
| Telemetry/context propagation | observability standard | OpenTelemetry + OTLP | any shared traces/metrics/logs/correlation are needed | private trace/event protocol | telemetry is evidence only; owning systems retain truth |
| AI telemetry semantics/instrumentation | telemetry convention | OTel GenAI first when practical; OpenInference selectively | Agent/model/tool/retrieval traces need common semantics | permanent Ordivon AI span ontology | eval/domain truth independent |
| AI trace/eval workbench | AI engineering product | Phoenix | lightweight internal Agent debugging/evals/datasets needed | private trace UI/eval platform | evaluator validity + task/domain acceptance |
| Shared production AI engineering platform | AI engineering product | Langfuse | collaborative production tracing, datasets, experiments, prompts, annotations needed | private production LLM observability/eval suite | same as above; platform score is not truth |
| Scientific/project file DAG | scientific workflow engine | Snakemake | reproducible file/artifact computational DAG | generic workflow replacement in Research | scientific result + artifact reproducibility |
| Persistent data-product lifecycle | data-asset orchestrator | Dagster | named assets, partitions, backfills, freshness, lineage/checks are recurring | private asset catalog/materialization DB/backfill engine | physical data + data/domain quality |
| Generative-media computation graph | media inference engine | ComfyUI | reusable image/video/audio/3D/model workflows and cache/resource semantics needed | Ordivon tensor/media DAG runtime | artifact/media QC, rights, accessibility, downstream acceptance |
| AI application product shell | application platform | Dify | deliverable is a collaborative LLM/RAG/Agent Web/API app and product shell saves major work | Ordivon clone of low-code AI canvas/Knowledge admin/plugin marketplace | app success + independent domain V&V; licensing before external multi-tenant use |
| Work-item / issue coordination | work-management system | Plane | human/team work-item board/project coordination is actually useful | global Ordivon Task/Board truth | project/work outcome; board state is coordination projection |
| Standards-native business/process modeling | BPM/CMMN/DMN engine | Flowable | executable mature process/case/decision notation is the real fit | private BPM/decision language | process/domain outcome |
| Requirements traceability workbench | requirements system | StrictDoc / ReqIF-compatible tools | durable text/Git requirements and traceability are needed | private requirements database/model | requirements coverage + implementation/evidence traceability |
| JSON Schema instance validation | standards-native validator | check-jsonschema | JSON instance conformance must be enforced | custom validator | schema is only one acceptance predicate |
| Preservation package construction/conformance | archival packaging standard/tool | Commons-IP / E-ARK | preservation package needs E-ARK conformance | private preservation package format | independent package validation + preservation policy |
| Durable preservation ingest lifecycle | preservation workflow provider | Enduro / Archivematica/a3m | real archival ingest/processing workflow exists | Ordivon preservation orchestrator | preservation-system receipts + archival acceptance |
| Artifact construction/validation | artifact capability provider | Artifact v2 + native format tools | real deliverable file/package is required | one universal artifact representation | native technical validation + task/user acceptance |
| External publication/distribution effect | provider-native API/effect layer | Distribution v2, n8n/native clients where appropriate | explicitly authorized write/publish to exact destination | universal transport/protocol | provider acceptance/read-back + exact occurrence reconciliation |
| Network composition/verification | network provider/toolchain | Network v2 + mature network tools | task needs real connectivity/routing/proxy/DNS behavior | global Network semantics in Core | real endpoint/connectivity behavior |
| Security verification | security domain provider/toolchain | Security v2 + mature security tools/standards | security requirement/threat/verification is in scope | generic security ontology duplicated in Core | threat-/control-specific evidence |

## 5. Graph-shaped systems: choose by semantic object, not UI shape

A recurring source of overengineering is treating every graph/DAG/canvas as one category.

```text
n8n       -> external integration/event graph
Temporal  -> durable process state/history
Snakemake -> scientific file/artifact dependency DAG
Dagster   -> persistent data-asset/partition graph
Haystack  -> context/retrieval component pipeline
LangGraph -> Agent working-state/control graph
ComfyUI   -> generative-media/model-compute graph
Dify      -> AI application composition graph/product surface
```

Do **not** build a universal Ordivon DAG engine over them.

The graph representation is incidental; the authoritative semantic object differs.

## 6. State-shaped systems: choose by whose state it is

```text
Codex thread/turn
= engineering Agent interaction state

LangGraph checkpoint/thread
= one custom Agent application's working/control state

Temporal Workflow History
= durable application/business process state

Dagster Asset/partition state
= data-product lifecycle state

Dify application/workflow state
= one AI product's application runtime/configuration state

Runtime Job/Attempt/Artifact
= physical local execution evidence

Plane issue/work item
= human/team coordination state
```

No one of these is a candidate for a universal Ordivon state database.

## 7. Retrieval / context routing

Choose retrieval by question semantics before choosing a framework/database.

```text
public web acquisition
  -> Firecrawl

ordinary heterogeneous files
  -> MarkItDown

rich layout/OCR/document hierarchy
  -> Docling

scholarly PDF metadata/citations
  -> GROBID

exact term / identifier
  -> lexical/BM25/search

structured predicate
  -> SQL/filter

semantic similarity over existing PostgreSQL data
  -> pgvector

dedicated filtered/hybrid vector workload
  -> Qdrant

explicit relationship/path question
  -> Graphify

multi-stage context pipeline framework needed
  -> Haystack / LlamaIndex selectively
```

Then hand bounded, provenance-bearing context to the selected Agent/application.

Do not create a universal `KnowledgeIndex`.

## 8. Agent routing

```text
ordinary engineering work
  -> Codex

standard multi-agent collaboration
  -> Microsoft Agent Framework

bespoke cyclic/checkpointed Agent application
  -> LangGraph

AI application with ready product shell/Knowledge/workflow/publishing
  -> Dify
```

MCP may supply capabilities to any of these. LiteLLM may supply model access when a shared gateway is justified. Temporal may wrap long-lived macro process stages around an Agent provider.

## 9. Workflow/orchestration routing

```text
API/SaaS/webhook integration
  -> n8n

long-lived general durable process
  -> Temporal

scientific/project file DAG
  -> Snakemake

persistent data-product lifecycle
  -> Dagster

AI/context in-process pipeline
  -> Haystack when warranted

bespoke Agent control state
  -> LangGraph

generative-media graph
  -> ComfyUI

AI app visual/product workflow
  -> Dify
```

If none fit, first ask whether ordinary code is simpler before studying another orchestrator.

## 10. Product-layer routing

Infrastructure/framework primitives are not the only reusable mature capabilities.

```text
need internal lightweight AI trace/eval workbench
  -> Phoenix candidate

need shared production AI engineering platform
  -> Langfuse candidate

need complete collaborative LLM/RAG/Agent application shell
  -> Dify candidate
```

Do not rebuild mature product surfaces merely because Ordivon understands their underlying primitives.

Licensing/commercial rights are part of provider selection, not an afterthought.

## 11. Activation levels

Every provider should fall into one of four operational states:

### STANDARD / METHOD ONLY

Understand/adopt semantics; no daemon required.

Examples: MCP specification, Agent Skills, Spec Kit/Superpowers lessons, OpenTelemetry semantics.

### AVAILABLE LOCALLY

Already installed/proven and may be activated task-locally.

Examples include current Codex/n8n/Browser Use and accepted local providers where registered.

### ON-DEMAND PROVIDER

Architecture understood but no current workload justifies installation/service state.

Examples: Temporal server, LiteLLM Proxy, Langfuse/Phoenix, LlamaIndex/Haystack, Qdrant, Dagster, LangGraph, Dify, ComfyUI.

### TRIGGERED REPLACEMENT / SPECIALIST

Activate only when a domain-specific threshold appears.

Examples: Enduro for preservation ingest; Commons-IP for E-ARK packaging; specialized document/vector/data providers.

Passing study is **not** an installation order.

## 12. Verification ladder

Provider success should be interpreted at the narrowest level it actually proves.

```text
protocol accepted
< request/tool/process executed
< provider state/read-back confirms effect
< artifact/data conforms technically
< domain requirement is satisfied
< real-world outcome is validated
```

Prefer the strongest applicable independent evidence, but do not claim a higher rung from a lower one.

Examples:

- HTTP 200 from Dify does not prove answer correctness;
- Temporal Activity completed does not prove exactly-once external effect;
- Runtime process exit 0 does not prove provider acceptance;
- Langfuse/Phoenix score does not prove evaluator validity;
- Qdrant top-k does not prove retrieval completeness;
- Dagster check/materialization does not prove scientific validity;
- ComfyUI generation success does not prove rights/accessibility/media quality.

## 13. New-project triage gate

Before deep-diving another GitHub project, answer in order:

1. **Primitive:** What semantic object does it naturally own?
2. **Existing authority:** Which row in this map already owns that object?
3. **Delta:** What capability remains unresolved after existing providers?
4. **Workload:** Which current real task suffers because of that delta?
5. **Threshold:** What measurable activation criterion would justify installation/adoption?
6. **Coupling:** What new persistent state, daemon, license, data copy or authority would it introduce?
7. **Replaceability:** Can we consume it through standard/provider-native interfaces?
8. **Verification:** What independent evidence will tell us it actually helped?

Decision:

```text
no unresolved primitive / no real workload
  -> DEFER

same primitive, better candidate
  -> COMPARE only against current authority

new distinct primitive + real workload
  -> STUDY with one-sentence + prototype gates

mature provider insufficient after real test
  -> prove substitution failure before custom build
```

## 14. Do-not-build list after two mining batches

Absent proven substitution failure, Ordivon should **not** build generic versions of:

- Agent Skills/portable procedural package format;
- coding Agent harness;
- MCP-like capability protocol;
- SaaS/API integration workflow engine;
- generic durable workflow/history/timers/task queues;
- generic multi-agent framework;
- universal Agent StateGraph/checkpoint database;
- browser Agent/CDP/DOM perception stack;
- web crawler/render/cleaning infrastructure;
- universal document parser;
- global knowledge graph;
- universal RAG/context framework;
- vector database;
- model gateway/router/virtual-key/budget system;
- telemetry/tracing/event protocol/backend;
- LLM observability/eval product platform;
- data-asset catalog/materialization/backfill engine;
- generative-media tensor/workflow engine;
- low-code AI application canvas/Knowledge admin/plugin marketplace;
- generic work-management board;
- private BPM/requirements/preservation standards;
- universal distribution protocol.

## 15. What Ordivon still legitimately owns

The map does **not** reduce Ordivon to zero.

The durable Ordivon-specific value remains:

```text
Problem framing
    ↓
map problem to mature knowledge/standards
    ↓
select natural authorities/providers
    ↓
compose them under explicit constraints/authority
    ↓
bridge gaps only where necessary
    ↓
verify against reality/domain acceptance
    ↓
learn which composition worked under which conditions
```

The scarce knowledge asset is increasingly:

```text
Problem class
→ applicable standards/methods
→ provider/capability selection
→ composition
→ verification strategy
→ observed outcome
```

not ownership of generic infrastructure.

## 16. Compact decision sentence

When evaluating any new technology, ask:

> **What truth or semantic object does this system naturally own, which current provider already owns that object, what real workload proves a remaining gap, and what independent evidence would justify adding another authority?**

If those questions have no clear answer, defer the technology rather than expanding Ordivon.
