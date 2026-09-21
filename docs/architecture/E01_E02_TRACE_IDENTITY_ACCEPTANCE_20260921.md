# E01 Trace + E02 Identity Acceptance — 2026-09-21

Status: **ACCEPTED**

Post-acceptance D02 note: T05 below records the exact acceptance topology at the time it was executed. A later accepted observability slice added an **optional, cold-by-default Vector → Tempo heavy profile**. Current deployed standing is authoritative in `CURRENT_ARCHITECTURE.md`; Gateway still defaults to `OTEL_TRACES_EXPORTER=none`, so product correctness remains independent of trace storage.

This acceptance closes the cross-layer trace-correlation and authenticated-principal gates without creating new Ordivon tracing or IAM authority.

## Authority boundary

The accepted split is:

```text
Cloudflare Access / OAuth
        │ authenticated public principal
        v
      Gateway
        │ MCP W3C trace context + Gateway machine credential
        v
 Runtime / Host owners

Harness canonical lifecycle events
        │ best-effort caller projection
        v
 OpenTelemetry
```

The following remain separate authorities:

- authenticated user/public principal: Cloudflare Access/OAuth;
- Gateway downstream machine credential: systemd-projected Runtime bearer or Cloudflare service identity;
- owner semantic truth: Runtime Job/Attempt and Host Task/Checkpoint;
- Harness semantic truth: canonical Harness events, observations, and trace digest;
- telemetry correlation: W3C Trace Context + OpenTelemetry.

Telemetry IDs never become completion, replay, currentness, authorization, or ownership truth.

## E01 — standards-native trace correlation

### T01 — trace-context contract

Current Harness Run Contract schema v2 excludes transport-only correlation. Legacy schema-v1 `traceparent` / `tracestate` remains readable only for exact historical replay.

Current correlation uses the standard transport/observability boundary:

- MCP request `_meta` carries W3C Trace Context;
- OpenTelemetry owns spans and export;
- Harness, Runtime, and Host retain their native semantic IDs.

### T02 — Gateway inbound server tracing

The deployed MCP 2.2 server already installs its OpenTelemetry server middleware by default. Gateway does not reimplement server-span creation or W3C extraction.

Gateway is launched through the standard Python OpenTelemetry zero-code launcher. Its base production profile keeps export disabled so product correctness does not depend on the intentionally cold local observability stack:

```text
OTEL_SERVICE_NAME=ordivon-gateway
OTEL_TRACES_EXPORTER=none
OTEL_METRICS_EXPORTER=none
OTEL_LOGS_EXPORTER=none
```

An opt-in systemd drop-in enables OTLP trace export to the local Workstation receiver.

### T03 — Gateway → owner propagation

MCP's client dispatcher creates the outbound client span and injects the ambient W3C trace context into request `_meta`. Gateway therefore does not maintain a second trace propagation protocol.

Live acceptance proved one exact trace contained both:

- SERVER `tools/call execution.submit`;
- CLIENT `MCP send tools/call workspace.exec`.

Accepted live trace:

```text
traceId = b12a2ad95542d9754ded8ad14e4cd91b
server span = 04c93b617029223a
client parent = 04c93b617029223a
```

### T04 — Harness Tool lifecycle correlation

A first implementation attempt placed OpenTelemetry inside the `ordivon_harness` package and changed its dependency contract. Full Harness verification correctly rejected that design:

- `ordivon_harness.telemetry` is required to remain absent;
- Harness production/test package dependency shape is frozen.

That implementation was fully reverted.

The accepted design uses the existing `TraceRecorder.event_sink` boundary. Harness records its canonical lifecycle event first and then makes a best-effort live projection; projection failure cannot invalidate Harness evidence.

The caller-owned adapter is:

```text
services/harness/scripts/harness_otel_event_sink.py
```

Its optional external dependency is isolated in:

```text
services/harness/config/harness-otel-event-sink-requirements.txt
```

It maps existing `tool_call_dispatched` and terminal Tool lifecycle events to OpenTelemetry spans using bounded identifiers only:

- `gen_ai.operation.name = execute_tool`;
- `gen_ai.tool.name`;
- `gen_ai.tool.call.id`;
- Harness Run ID;
- Harness step ID when present;
- Runtime Job reference when present;
- bounded terminal status.

Tool arguments, observation content, result content, credentials, and tokens are not copied into span attributes.

Acceptance tests proved:

- two real ToolProgram physical Tool calls inherited one supplied W3C parent trace;
- the same run with and without the OTel event sink produced byte-equivalent canonical Harness Trace content and the same trace digest;
- observations were unchanged;
- the complete Harness suite passed **886 tests + 122 subtests**;
- package/dependency/documentation/evidence boundary contracts all passed.

Canonical T04 implementation commit:

```text
ee99dbd93955ea01a528ca594e8a04356c35eecc
```

### T05 — existing OTLP pipeline

The existing Workstation owner remains the observability carrier:

- Vector 0.57 OTLP gRPC: loopback 4317;
- Vector 0.57 OTLP HTTP: loopback 4318;
- `otel.traces` is intentionally routed to `otel_traces_deferred` blackhole.

For acceptance only, the existing heavy-observability profile was activated and a temporary transparent loopback capture-forwarder recorded standard OTLP protobuf before forwarding it unchanged to Vector. Vector returned HTTP 200 for the observed trace exports.

This proves trace transport through the existing OTLP pipeline. It does **not** claim persisted or queryable trace storage. No Tempo, Jaeger, custom trace database, or new telemetry gateway was admitted.

After acceptance, the temporary proxy and runtime override were removed and Gateway returned to `OTEL_TRACES_EXPORTER=none`.

## E02 — authenticated-principal boundary

### I01 — principal contract

Gateway Cloudflare Access verification requires the expected issuer, audience, RS256 signature/key ID, expiry, and subject before deriving a stable pseudonymous principal.

The principal is an ingress authentication projection. It is not a Host writer label, Runtime authority, or Agent identity.

### I02 — non-forgeable request projection

The verified principal and issuer are stored in HTTP request state by Access middleware. Gateway audit middleware reads only this verified state.

Tool arguments are not an identity source. Tests explicitly supplied forged principal/JWT-like argument fields and proved they do not influence audit identity and are not logged.

### I03 — downstream machine identity remains separate

Gateway → owner authentication remains a separate machine-credential boundary:

- Linux Runtime: systemd-projected bearer credential;
- Windows Runtime: systemd-projected Cloudflare Access service identity.

The end-user/public Access JWT is not replayed as an owner credential. No principal is silently treated as delegated downstream authorization.

### I04 — authenticated audit correlation

Gateway's audit middleware runs inside the MCP SDK OpenTelemetry server span. It records a bounded observability-only correlation:

- verified pseudonymous principal;
- trace ID / span ID;
- MCP tool name;
- exact owner `operationRef`, `ownerId`, and `nativeId` when returned.

Live acceptance job:

```text
job-01a0c435-3e5f-7a81-b88a-4ead9a4afba3
```

Live correlated audit:

```text
traceId     = 0fc24bde37de4e82373ff124d5e81b5a
spanId      = 6df972e4d25a230a
principal   = principal:cf-access:9a688f59beb4f27da72d4eaa15de073180b7ea024d15b4baa38662dbf741f8a3
ownerId     = runtime.linux
nativeId    = job-01a0c435-3e5f-7a81-b88a-4ead9a4afba3
operationRef= ordivon-exec:v1:runtime.linux:job-01a0c435-3e5f-7a81-b88a-4ead9a4afba3
```

The OTLP capture for the same trace contained both the Gateway `execution.submit` server span and Gateway → Runtime `workspace.exec` client span.

## Explicit non-claims

This acceptance does not claim:

- persistent/queryable trace storage;
- production OTLP export while the Workstation observability profile is cold;
- Temporal cross-process trace propagation;
- that Host `writerLabel` is authenticated identity;
- that the public principal is delegated owner authorization;
- that telemetry availability is required for product correctness.

## Result

E01 T01–T05 and E02 I01–I04 are accepted. The remaining architecture convergence work is documentation/deployed-reality convergence under D02.
