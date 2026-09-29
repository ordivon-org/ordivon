# OpenTelemetry + OpenInference Observability Kernel

Status: **REGISTERED / PROTOTYPE-READY**
Registered: 2026-09-14

## One-sentence model

**OpenTelemetry provides the vendor-neutral telemetry substrate and causal context; AI-specific conventions such as OTel GenAI or OpenInference add model/Agent/tool/retrieval meaning without changing execution authority or domain truth.**

## Mechanism 1: observability has three different primary questions

```text
Trace  -> what happened along this individual causal execution?
Metric -> what is happening statistically over time?
Log    -> what discrete event/record occurred?
```

Do not put every fact into all three signals.

Use the signal that naturally answers the question.

## Mechanism 2: propagation is more important than a single backend

The most durable interoperability primitive is consistent context propagation across boundaries:

```text
HTTP / MCP / model gateway / queue / Temporal / Runtime / provider
                ↓
      trace context continuity
```

A trace backend can change later if context and OTel-compatible telemetry are preserved.

## Mechanism 3: causal links are not always parent-child

Long-running queues, durable Workflows and later physical jobs often outlive the span that initiated them.

Use Span Links when the relationship is causal but not naturally nested.

Do not create artificially multi-day parent spans merely to preserve visual continuity.

## Mechanism 4: telemetry is a projection, not operational truth

Examples:

```text
Runtime Attempt -> emits trace
Temporal Workflow -> emits trace
LiteLLM request -> emits trace
```

The trace is useful evidence about these systems, but the authoritative state remains with Runtime Registry/evidence, Temporal Event History, LiteLLM gateway/provider records, etc.

Do not reconcile/repair execution from trace storage alone unless the owning system explicitly defines that contract.

## Mechanism 5: trace status is not semantic success

A successful span proves only that the instrumented operation did not report an observability-level error according to its convention.

```text
span.status = OK
!=
external effect correct
!=
model answer correct
!=
domain requirement satisfied
```

V&V remains outside observability.

## Mechanism 6: metrics require bounded dimensions

High-cardinality identifiers are attractive but operationally expensive.

Do not put raw:

- user IDs;
- task/job IDs;
- prompt IDs generated per request;
- URLs with arbitrary path/query values;
- error messages;
- model outputs;

into metric dimensions by default.

Keep aggregation dimensions deliberate and bounded. Put request identity/details in traces/logs.

## Mechanism 7: event semantics are converging toward correlated logs

OpenTelemetry's 2026 direction deprecates the separate Span Events API for new code in favor of log-based events correlated with the current span.

General lesson:

**Do not invent a parallel event store merely because an operation needs timestamped annotations.**

Use standard structured logs/events plus trace correlation unless durability/authority requirements demand a real domain ledger.

## Mechanism 8: Collector is optional infrastructure

The architectural contract is telemetry semantics + transport, not a particular daemon.

A mature alternative such as Vector or Grafana Alloy may receive/process/export OTLP.

Install `otelcol` only when its specific processors/exporters/operational model solve a real gap.

This is demonstrated locally: Ordivon Operations already has accepted OTLP logs+metrics through Vector without an OTel Collector.

## Mechanism 9: no trace backend is better than false trace claims

Current local Operations accepts OTLP ingress but deliberately blackholes traces because no trace-storage owner/use-case has been admitted.

This is preferable to deploying Tempo/Jaeger/Phoenix merely so architecture diagrams show a trace box.

When trace queries become useful, select a mature backend according to the workload.

## Mechanism 10: AI telemetry conventions are still evolving

OpenTelemetry moved GenAI semantic conventions into a dedicated fast-moving repository in 2026; current GenAI conventions are marked Development.

OpenInference also provides a mature practical AI instrumentation/convention ecosystem.

Therefore avoid freezing one present-day AI attribute taxonomy into Ordivon database schemas.

Keep instrumentation/version adapters replaceable.

## Mechanism 11: OTel GenAI and OpenInference overlap but are not identical

OTel GenAI is increasingly the standards-native target for:

- model operations;
- Agent operations;
- retrieval;
- MCP;
- provider-specific model telemetry;
- GenAI metrics/events/evaluation attributes.

OpenInference remains useful for:

- maintained framework instrumentors;
- explicit AI span-role taxonomy;
- structured prompt/tool/retrieval representations;
- evaluation annotations;
- privacy controls;
- backend compatibility such as Phoenix.

Use the convention that best fits the actual instrumentation/backend and preserve OTLP interoperability.

## Mechanism 12: AI semantic role and OTel SpanKind are different axes

For example a tool call could be semantically:

```text
OpenInference role = TOOL
```

while transport-wise its actual remote request child span may be:

```text
OTel SpanKind = CLIENT
```

Do not overload one field to answer both questions.

## Mechanism 13: raw AI content is opt-in sensitive telemetry

Prompts, responses, tool parameters, retrieved documents, screenshots and embeddings may contain private or proprietary information.

Default to metadata-first observability:

```text
model/tool/provider identity
latency/status
token counts
bounded error type
trace correlation
```

Capture full content only for explicitly scoped debugging/evaluation and redact before crossing trust boundaries.

## Mechanism 14: observability and evaluation are different systems

Telemetry can carry evaluation scores/labels/explanations, but it does not determine the validity of those evaluations.

```text
OpenTelemetry/OpenInference
= carry/correlate evidence

Eval method/platform
= produce/interpret quality measurements
```

This sets the boundary for the next study of Langfuse vs Phoenix.

## Current Ordivon mapping

```text
MCP
  -> propagate trace context; do not own logging semantics

LiteLLM
  -> emit model/gateway telemetry using standard conventions

Temporal
  -> durable workflow state remains Event History; traces observe it

Runtime
  -> Job/Attempt/Artifact evidence remains authoritative; traces observe execution

Operations
  -> OTLP ingress + logs/metrics pipeline exists today
```

## What Ordivon should retain

1. Standardize on OpenTelemetry core + OTLP for shared telemetry transport/semantics.
2. Propagate W3C trace context across provider boundaries.
3. Use Span Links for long-lived asynchronous/durable causal relationships.
4. Keep traces, metrics and logs semantically distinct.
5. Keep metric dimensions bounded.
6. Treat telemetry as derived evidence, never execution/domain authority by default.
7. Use OTel GenAI conventions when mature enough for the selected instrumentation.
8. Use OpenInference selectively where its instrumentors/AI semantics/backends add concrete value.
9. Capture sensitive AI content only when explicitly justified.
10. Do not deploy Collector or trace storage until workload evidence justifies it.

## What Ordivon should not copy

- private trace/span IDs or propagation protocol;
- custom observability event ontology;
- duplicate metrics/log schemas for each subsystem;
- a bespoke telemetry gateway;
- prompt/response warehouse disguised as tracing;
- telemetry as task/domain source of truth;
- permanent Ordivon-specific AI span taxonomy;
- a trace backend installed only for architectural completeness.

## Minimal prototype

```text
Agent request span
   ├─ model span
   ├─ retrieval span
   └─ tool span
          ↓ context propagation
       remote provider

async/durable handoff
   ↓ Span Link
Temporal/Runtime later trace

all signals
   ↓ OTLP
Vector/Collector-compatible ingress
   ├─ traces -> chosen trace backend (when admitted)
   ├─ metrics -> Prometheus-compatible backend
   └─ logs -> Loki-compatible backend
```

## Project-study acceptance

### One-sentence test

PASS: OpenTelemetry is the telemetry/causal-context substrate; OTel GenAI/OpenInference are replaceable AI semantic layers on that substrate.

### Prototype test

PASS: one correlated multi-service trace, bounded metric, structured log, OTLP export and AI span instrumentation are sufficient to reproduce the architecture without custom telemetry infrastructure.

## Verdict

**PASS — STANDARDIZE ON OTEL/OTLP; USE OTel GenAI FIRST WHEN PRACTICAL, OPENINFERENCE SELECTIVELY; KEEP OBSERVABILITY OUT OF EXECUTION TRUTH.**
