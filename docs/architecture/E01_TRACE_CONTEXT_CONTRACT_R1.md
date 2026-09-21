# E01 W3C Trace Context Contract R1

Date: 2026-09-21
Status: T01-T04 IMPLEMENTED / T05 BLOCKED BY TRACE BACKEND

## Contract

Ordivon uses MCP request `_meta` as the transport carrier and OpenTelemetry as the telemetry owner. W3C Trace Context is correlation only.

```text
client MCP _meta
  -> MCP SDK OpenTelemetryMiddleware
  -> current OTel span/context
  -> Gateway owner call
  -> MCP SDK inject_trace_context(_meta)
  -> natural owner
```

Trace context never becomes Host Task, Harness Run, Runtime Job/Attempt, workflow, Git, authorization, or domain truth.

## T01 — frozen boundary

- W3C trace context is telemetry correlation, not execution admission.
- Missing/malformed trace context must not change correctness or retry semantics.
- No credential, Access subject, service token, or Host writerLabel is placed in trace baggage by Ordivon.
- Natural-owner IDs remain the durable navigation/evidence identities.

## T02 — inbound Gateway

Gateway uses MCP Python SDK 2.2.0. Its default middleware chain contains `mcp.server._otel.OpenTelemetryMiddleware`, which extracts inbound W3C context from MCP `_meta`. Ordivon does not register a duplicate middleware/span.

## T03 — Gateway to owner

`McpOwnerCaller` now uses the SDK-owned `mcp.shared._otel.inject_trace_context` and passes the resulting metadata through `Client.call_tool(..., meta=...)`. No Tool argument or owner-specific schema is added.

## T04 — Harness boundary

Harness schema v2 deliberately excludes transport-only correlation from execution authority and its digest. Historical schema v1 trace bytes remain readable only for exact historical verification. Harness-owned telemetry projection/CLI is retired; durable Run evidence remains `inspect`.

This means Harness can participate in ambient transport/observability correlation without creating a Harness trace ontology or gating Run truth on telemetry availability.

## T05 — not yet accepted

The current Workstation OTLP substrate exposes Vector on loopback 4317/4318, but its accepted configuration explicitly routes traces to a deferred blackhole and states that trace observability is not deployed. Gateway has no accepted OTEL exporter configuration and no Tempo/other trace backend is active.

Therefore an end-to-end persisted/queryable trace cannot currently be claimed. T05 remains blocked until a real trace backend/export path is deployed and verified.
