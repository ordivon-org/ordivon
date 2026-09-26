# Provider: Arize Phoenix

Status: **PROTOTYPE-READY / LIGHTWEIGHT AI OBSERVABILITY+EVAL WORKBENCH CANDIDATE / NOT LOCALLY INSTALLED**
Role: OpenTelemetry/OpenInference-compatible tracing, evaluation, datasets/experiments and prompt-development workbench for AI applications.

## One-sentence understanding

**Phoenix combines OpenTelemetry/OpenInference trace inspection with an independent evaluation library, datasets/experiments and prompt tooling in a comparatively lightweight self-hostable workbench for debugging and improving AI applications.**

## Current upstream observation — 2026-09-14

- current release stream observed in the Phoenix 19.x line;
- self-hosted Phoenix is distributed under Elastic License 2.0 (ELv2);
- Phoenix states that self-hosted functionality has no feature gates;
- local/single-user storage can use SQLite;
- production/multi-user deployments can use PostgreSQL;
- a Phoenix instance is currently modeled as one tenant; larger multi-tenant commercial SaaS concerns belong elsewhere/Arize AX.

## Current local observation

No `phoenix`/`arize-phoenix` executable, Docker image or obvious local Phoenix project was observed during this study.

Do not install Phoenix until a real Agent/evaluation debugging workload needs a trace/eval workbench.

## Core product loop

Phoenix presents a deliberately engineering-oriented loop:

```text
trace application
   ↓
understand execution
   ↓
evaluate quality
   ↓
collect failures/examples into dataset
   ↓
iterate prompt/model/application
   ↓
run experiments on same inputs
   ↓
compare results
```

This is similar in shape to Langfuse but Phoenix is notably lighter to start locally and tightly aligned with OpenInference/OpenTelemetry instrumentation.

## Tracing

Phoenix receives OpenTelemetry/OpenInference traces and provides trace/span inspection for Agents, models, tools, retrieval and evaluation operations.

It is particularly natural when the application already uses OpenInference instrumentors.

Phoenix tracing is observability, not execution truth.

## Evals library

A significant differentiator is that Phoenix evaluation tooling can run **independently** of the Phoenix server.

Current eval capabilities include:

- deterministic/code evaluators;
- custom evaluators;
- LLM-as-a-judge evaluators;
- pre-built checks such as faithfulness, correctness, retrieval relevance, tool invocation and related AI quality dimensions;
- batching/concurrency/provider adapters;
- explanations;
- evaluator tracing through OpenTelemetry.

This separation is useful: a workload may adopt Phoenix eval libraries without committing to Phoenix as the permanent trace backend/product UI.

Evaluation outputs remain hypotheses/measurements whose validity depends on benchmark/evaluator design.

## Datasets / experiments

Phoenix datasets contain examples with inputs, optional expected/reference outputs and metadata.

Datasets can be created manually, from files/dataframes, from production spans or via synthetic generation.

Experiments run application/task variants over those examples using consistent evaluators, including repeated runs to measure variance.

This makes Phoenix useful for fast local Agent/model iteration and regression analysis.

## Prompt tooling

Phoenix provides Prompt Management/Prompt Hub plus Playground capabilities and span replay.

Useful workflow:

```text
inspect failing model span
   ↓
replay/edit prompt or parameters
   ↓
save prompt version
   ↓
run against dataset
   ↓
compare evals
```

Again, prompt tooling is optional product functionality; repository instructions/Skills/code prompts remain natural authorities where remote prompt management adds no value.

## Architecture / self-host cost

Phoenix's self-host architecture is comparatively small:

```text
Phoenix application
  ├─ web UI
  ├─ trace collector/API
  └─ SQL backend
       ├─ SQLite for local/single user
       └─ PostgreSQL for production/multi-user
```

A local Docker container can expose Phoenix plus OTLP ports without introducing ClickHouse/Redis/object storage.

This makes Phoenix a strong candidate for a first local AI trace/evaluation workbench if the workload arrives.

## Tenancy/scaling boundary

Current Phoenix architecture treats one instance as one tenant. PostgreSQL/shared-instance scaling is supported, but multi-organization product isolation is not the same focus as a multi-tenant SaaS platform.

For Ordivon commercialization, do not assume one Phoenix instance should become the customer-facing observability control plane.

## Licensing boundary

Phoenix is licensed under **Elastic License 2.0 (ELv2)**.

Self-hosting/internal use is allowed and Phoenix states there are no self-host feature gates. However ELv2 prohibits providing the software to third parties as a hosted/managed service that exposes a substantial set of Phoenix functionality.

Therefore:

- internal Ordivon development/evaluation use can fit well;
- embedding Phoenix as the substantive customer-facing hosted observability/evaluation product requires legal/license review and may be prohibited without another commercial arrangement;
- do not treat “free to self-host” as equivalent to permissive MIT redistribution/SaaS rights.

## Ordivon routing rule

Prefer Phoenix when the immediate need is:

- a local/lightweight trace viewer;
- OpenInference-heavy instrumentation;
- debugging Agent/model/tool/retrieval behavior;
- developer-owned eval code;
- datasets/experiments for rapid regression work;
- prompt replay/playground iteration;
- single-team/internal workbench use;
- ability to begin with SQLite and minimal services.

Do not install Phoenix merely because OTel traces exist, and do not make it a commercial customer-facing dependency without reviewing ELv2 implications.

## Boundary with OpenTelemetry/OpenInference

```text
OTel/OTLP
= telemetry substrate

OpenInference
= optional AI semantic/instrumentation convention

Phoenix
= product UI/store/eval/experiment workbench
```

Keep telemetry producers standards-compatible so Phoenix remains replaceable.

## Boundary with Langfuse

Phoenix tends toward the lightweight developer/evaluation workbench end of the spectrum.

Langfuse tends toward the shared production AI-engineering platform end, with heavier scalable storage/queue architecture and broader collaborative production workflow.

Their features overlap substantially. Ordivon should not deploy both by default.

## Boundary with Inspect AI / research evaluation

Phoenix eval libraries are useful engineering/evaluation tools, especially for Agent and RAG behavior.

They do not replace scientific evaluation design, statistical inference, benchmark governance or specialized research-evaluation frameworks.

## Prototype recipe

A minimal Phoenix-like proof requires:

1. receive one OTel/OpenInference trace;
2. visualize Agent -> model -> retrieval/tool child spans;
3. create one evaluation in code without the UI/server;
4. attach the score/annotation to a trace;
5. turn failed spans into a dataset;
6. run two candidate implementations over the same dataset;
7. compare results and evaluator traces;
8. replay one prompt invocation with a modification.

## Prototype readiness gate

**PASS.** Trace/eval/dataset/experiment/prompt-loop semantics and lightweight deployment/license boundaries are clear enough to decide when Phoenix is appropriate.
