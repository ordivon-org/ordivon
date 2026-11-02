# Provider: Langfuse

Status: **PROTOTYPE-READY / SHARED AI ENGINEERING PLATFORM CANDIDATE / NOT LOCALLY INSTALLED**
Role: collaborative LLM/Agent observability, evaluation, datasets/experiments and prompt-management product layer on top of OpenTelemetry-compatible tracing.

## One-sentence understanding

**Langfuse turns OpenTelemetry-compatible AI traces plus datasets, scores and prompt versions into a shared AI-engineering platform for production monitoring, collaborative evaluation, regression experiments and prompt lifecycle management.**

## Current upstream observation — 2026-09-14

- current major line: Langfuse v4;
- current release stream observed around `v4.35.0`;
- core Langfuse is MIT-licensed;
- enterprise-only features under `ee/` use separate commercial licensing;
- current self-host architecture is a substantial multi-service platform using web/worker services plus PostgreSQL, ClickHouse, Redis/Valkey and S3/blob storage.

This is materially more than a trace viewer.

## Current local observation

No `langfuse` executable, Docker image or obvious local Langfuse project was observed during this study.

Do not deploy Langfuse merely to satisfy an observability checklist. Activate it when shared production AI engineering requires the product capabilities described below.

## Core product loop

Langfuse's strongest value is the integrated feedback loop:

```text
production traces
      ↓
monitor / inspect failures
      ↓
curate examples into datasets
      ↓
run experiments on prompt/model/code variants
      ↓
score via code / human / LLM judge
      ↓
compare regressions / approve change
      ↓
deploy
      ↓
monitor production again
```

The platform productizes this loop; OpenTelemetry itself only carries telemetry.

## Observability

Langfuse ingests AI/application tracing and provides product-level views around:

- traces/observations;
- sessions/users/agents;
- latency/cost/token usage;
- model/tool/retrieval steps;
- dashboards/filters/saved views;
- scores and annotations attached to execution records.

Current SDKs are OpenTelemetry-based, and Langfuse also supports direct OpenTelemetry ingestion.

Trace storage remains observability evidence, not Runtime/Temporal/provider truth.

## Datasets

Datasets hold reusable test cases containing inputs and optional expected outputs.

A particularly useful workflow is to promote real production failures into datasets, attach human-curated expected outputs, and replay candidate implementations against the same examples.

Dataset versions help freeze the evaluation corpus used for a release comparison, but they do not make non-deterministic model outputs deterministic.

## Experiments

Experiments run a task/application/prompt variant against a dataset and attach evaluation results.

Current execution paths include:

- Python/TypeScript SDK experiment runners;
- prompt/model experiments from the UI;
- direct OpenTelemetry experiment ingestion for languages/custom pipelines.

The evaluated application can remain external to Langfuse; the platform does not need to become the application's runtime.

A sound release comparison should bind at least:

```text
dataset version
+ candidate application/commit
+ prompt/model/config identity
+ evaluator definitions/versions
+ experiment result
```

Langfuse comparison UI is useful evidence, but repository/CI release policy should remain the authority for whether a candidate ships.

## Evaluation

Langfuse supports:

- deterministic/code evaluators;
- LLM-as-a-judge;
- manual/human annotation;
- user feedback;
- custom scores via SDK/API;
- online evaluation of production traffic;
- offline evaluation on datasets;
- CI experiment/regression workflows.

Evaluation score transport/storage does not establish evaluator validity. Domain/research methodology still owns what should be measured, judge reliability, thresholds and interpretation.

## Prompt Management

Langfuse manages versioned prompts with labels/deployment targeting, playground testing, trace linkage and experiment comparison.

This can be valuable when prompts are shared production configuration that needs collaborative editing/deployment and performance tracking.

Do not migrate every local Agent instruction, Skill or repository prompt into Langfuse solely because Prompt Management exists.

Keep distinctions:

```text
Agent Skill / AGENTS.md
= procedural/project instructions

code-owned prompt
= implementation artifact

Langfuse-managed prompt
= remotely versioned shared runtime configuration when that operational model is desired
```

## Architecture / self-host cost

Langfuse v4 self-hosting is a real application platform, not a lightweight local viewer.

Current architecture includes conceptually:

```text
Web/API
  ↓
PostgreSQL          transactional/product state
Redis/Valkey        queue/cache
S3/blob storage     raw events / attachments
ClickHouse          observability/analytical data
Worker              async ingestion/evaluation processing
```

This architecture supports scale and collaborative production use but creates meaningful operational overhead.

Default to Langfuse Cloud or an already-operated deployment when policy permits. Self-host only when data-control/economics/compliance/team requirements justify the infrastructure.

## Licensing boundary

Langfuse uses an open-core model:

- core platform/APIs: MIT;
- selected enterprise features: separately licensed.

Enterprise examples include advanced RBAC, protected prompt labels, audit logs, some retention/masking/customization/admin features.

Commercial Ordivon use should verify whether the required feature is in MIT core or enterprise code rather than assuming the whole repository has one license.

## Ordivon routing rule

Use Langfuse when several of these become real shared requirements:

- persistent production AI trace exploration;
- multiple developers/operators reviewing the same Agent/model runs;
- curated datasets built from production traces;
- repeated experiment comparisons;
- annotation queues/human review;
- online/offline evaluation management;
- shared prompt version/deployment lifecycle;
- AI-specific cost/quality/latency dashboards;
- release regression workflows.

Do not use Langfuse merely because an application emits OTel spans.

## Boundary with OpenTelemetry

```text
OpenTelemetry / OTLP
= telemetry substrate and propagation

Langfuse
= AI-engineering product built on/around that telemetry
```

Instrument applications with standards-native telemetry where practical so Langfuse remains replaceable.

## Boundary with Inspect AI / scientific evaluation

Langfuse is excellent for organizing datasets, experiment runs and scores around AI applications.

It is not a substitute for scientific/evaluation methodology, benchmark design, statistical analysis or specialized evaluation frameworks such as Inspect AI when those are the natural owner of the experiment semantics.

Use Langfuse as observation/experiment-management product when useful, not as proof that an evaluation design is valid.

## Prototype recipe

A minimal Langfuse-like product proof requires:

1. ingest standard AI traces;
2. render trace hierarchy and latency/token/cost metadata;
3. create a dataset from one trace input/output;
4. run candidate task A and B over that fixed dataset;
5. attach one deterministic score and one human/judge score;
6. compare aggregate and per-item regression results;
7. version one prompt and link runs to its version;
8. preserve links from failed experiment item back to its execution trace.

This proves the product value; production Langfuse's multi-service storage/queue architecture should not be recreated by Ordivon.

## Prototype readiness gate

**PASS.** The product loop from production traces to datasets, experiments, evaluations and prompt lifecycle is explicit enough to decide when Langfuse adds value above OpenTelemetry alone.
