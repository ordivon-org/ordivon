# Standard / Provider: OpenTelemetry

Status: **ADOPT STANDARD / LOCALLY PARTIALLY REALIZED**
Role: vendor-neutral telemetry API/data model/protocol/context-propagation standard for traces, metrics and logs, with optional Collector or compatible telemetry pipelines.

## One-sentence understanding

**OpenTelemetry standardizes how software emits, correlates, propagates and exports traces, metrics and logs through shared context and OTLP, while leaving telemetry storage/query backends and domain truth to external systems.**

## Current upstream state — 2026-09-14

- OpenTelemetry Specification observed at **1.60.0**;
- OTLP specification observed at **1.11.0**;
- core Semantic Conventions observed at **1.44.0**;
- Generative AI semantic conventions have moved to the dedicated `open-telemetry/semantic-conventions-genai` repository and are currently marked **Development**;
- the dedicated GenAI conventions cover model operations, agent operations, retrieval, MCP, metrics/events and provider-specific conventions.

Treat stable core OTel semantics separately from still-evolving GenAI conventions.

## Signals

### Traces

Represent causal execution paths as spans.

Use traces for questions such as:

- which operation called which downstream operation;
- where latency accumulated;
- which model/tool/retrieval operation failed;
- how an Agent turn crossed MCP, LiteLLM, Temporal, Runtime and external providers.

A trace is observability evidence, not execution authority or domain-completion truth.

### Metrics

Represent aggregated measurements over time.

Use metrics for bounded-cardinality operational questions such as:

- request/error rates;
- latency distributions;
- queue depth;
- token/cost aggregates;
- CPU/memory/resource use;
- retry/cooldown/throughput trends.

Do not put high-cardinality identities such as raw user IDs, task IDs, prompt text or per-request UUIDs into metric attributes by default. Metrics SDK cardinality is finite; high-cardinality data belongs in traces/logs or another purpose-built store.

### Logs

Represent discrete records/events, ideally structured and correlated to trace context.

For new event-like telemetry, prefer correlated log/event records over inventing new private event ledgers. OpenTelemetry announced deprecation of the Span Events API direction in 2026 in favor of log-based events correlated with spans.

### Baggage / Context

Context is the execution-scoped propagation mechanism. `traceparent`, `tracestate` and Baggage allow causally related operations to correlate across process/network boundaries.

Baggage is propagated context, not a secure secret store or durable business state. Keep sensitive/high-volume data out unless explicitly required and protected.

## Span model

A span carries:

- operation name;
- start/end time;
- attributes;
- status;
- context/trace identity;
- parent relationship;
- optional Links to causally related spans.

Use parent/child when one operation logically executes inside/under another.

Use **Span Links** for asynchronous/durable causal relationships where strict parent-child lifetime nesting is wrong, for example:

```text
HTTP request trace
    ↓ enqueue/start durable work
Temporal Workflow / later Worker trace
```

or when a Runtime/queue execution occurs long after the initiating request.

Do not distort traces into a permanent task graph merely to keep one giant trace alive.

## Resources and instrumentation scope

Use Resource attributes for stable identity of the telemetry-producing entity, such as service/deployment/environment.

Use instrumentation scope to identify the library/component producing telemetry.

Use span/log/metric attributes for operation-specific facts.

This separation reduces accidental duplication and metric-cardinality abuse.

## OTLP

OTLP is the standard transport/data-export path for OpenTelemetry telemetry.

Typical deployment:

```text
instrumented application
      ↓ OTLP gRPC/HTTP
collector / compatible ingress
      ↓
processing / filtering / sampling / redaction
      ↓
backend(s)
```

OTLP is not a storage backend and does not imply that every signal reaching an ingress is persisted.

## Collector boundary

The OpenTelemetry Collector is one mature implementation of a telemetry pipeline:

```text
Receivers
   ↓
Processors
   ↓
Exporters
```

It can run as an agent or gateway and can fan out traces/metrics/logs to multiple backends.

**OpenTelemetry does not require deploying an OpenTelemetry Collector.** Any mature component that correctly receives/processes/exports the required protocols may satisfy the workload.

Do not install `otelcol` merely for architectural purity if Vector/Alloy/vendor agents already provide the required OTLP path.

## Current Ordivon local reality — 2026-09-14

Workstation v2 has already accepted a real OTLP logs+metrics path without `otelcol`:

```text
OTLP gRPC :4317 / HTTP :4318
        ↓
Vector 0.57.0
   ├─ logs -> Loki 3.6.6
   └─ metrics -> Prometheus 3.14.0 native OTLP receiver
```

Host/system metrics also retain the existing node_exporter scrape path.

**Traces are deliberately not accepted as observable/persisted locally yet.** The shared OTLP ingress currently routes traces to an explicitly deferred blackhole because no trace backend/use-case has been admitted.

No `otelcol`, `otelcol-contrib`, Jaeger or Tempo executable was observed in the current shell during this study.

This is a valid standards-native state: logs and metrics are real; trace storage remains a workload-triggered gap.

## Sampling / processing / redaction

Telemetry volume and sensitivity should be controlled before expensive export/storage when possible.

Typical processing concerns:

- sampling;
- batch/retry buffering;
- removal/redaction of sensitive attributes;
- resource normalization;
- attribute filtering/transformation;
- routing to different backends.

Do not assume observability justifies exporting raw prompts, responses, credentials, file contents or personal data.

## GenAI semantic conventions

OpenTelemetry now has a dedicated GenAI semantic-conventions project covering model and Agent operations, including attributes such as:

- provider/model identity;
- operation name;
- token usage;
- conversation/agent identity;
- tool definitions/execution;
- retrieval/data-source details;
- evaluation fields;
- MCP-related telemetry.

These conventions are currently marked **Development**, so do not freeze their current exact field names into Ordivon business schemas. Keep instrumentation adapters/version mappings replaceable.

Prefer OTel GenAI conventions when the relevant instrumentation already supports them and interoperability is sufficient.

## Authority boundary

OpenTelemetry owns:

- telemetry signal/data-model semantics;
- context propagation;
- standard trace/metric/log APIs;
- OTLP transport semantics;
- shared semantic conventions.

OpenTelemetry does **not** own:

- Runtime Job/Attempt truth;
- Temporal Event History;
- MCP tool/task state;
- LiteLLM budget/accounting authority;
- provider receipts;
- business/domain state;
- semantic task completion;
- evaluation methodology;
- telemetry backend retention/query truth.

A span saying `OK` does not prove the underlying business/scientific effect is correct.

## Prototype recipe

A minimal OTel architecture proof requires only:

1. instrument one service with a Tracer/Meter and structured logger;
2. attach stable Resource identity;
3. propagate W3C trace context across one process/network boundary;
4. emit one trace with a child span and one asynchronous Span Link;
5. emit one low-cardinality metric;
6. emit one correlated log record;
7. export through OTLP;
8. receive/process/export the signals using a mature pipeline;
9. verify traces/logs/metrics remain distinguishable and correlated.

No Ordivon telemetry database or private event ontology is required.

## Prototype readiness gate

**PASS.** Signal roles, context propagation, span/link semantics, OTLP, Collector/pipeline boundaries, cardinality and authority limits are explicit enough to instrument real providers without deeper architecture study.
