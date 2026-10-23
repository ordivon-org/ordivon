# Persistent Trace Backend Acceptance — 2026-09-21

Status: **ACCEPTED / DEPLOYED ON DEMAND**

This is a supplemental deployment acceptance after `E01_E02_TRACE_IDENTITY_ACCEPTANCE_20260921.md`. The earlier acceptance correctly stated that no persistent/queryable trace backend had been admitted at that time; this record documents the later deployment change rather than rewriting historical evidence.

## Authority boundary

- OpenTelemetry owns trace/export semantics.
- MCP 2.x owns W3C trace-context extraction/injection for Gateway server/client calls.
- Vector is the Workstation OTLP carrier.
- Tempo 3.0.3 owns trace persistence/query behavior; Workstation owns its local deployment.
- Runtime Job/Attempt, Host Task/Checkpoint, authentication/authorization, and domain truth remain outside telemetry authority.

## Supply-chain admission

`grafana/tempo:3.0.3` was resolved through the existing Network-owner Surfshark/WireGuard carrier before image admission. The observed registry manifest matched the frozen digest:

`sha256:0296560ac66f8a3600d7fb3014a52c189d4d9c3549ad6ff441bf2409855d68d5`

## Deployed path

```text
Gateway -> OTLP/HTTP 127.0.0.1:4318 -> Vector
        -> OTLP/HTTP 127.0.0.1:14318 -> Tempo 3.0.3
        -> query API 127.0.0.1:3200 -> Grafana Tempo datasource
```

All trace ingress/query listeners are loopback-only. Vector must preserve OTLP trace envelopes with `use_otlp_decoding.traces: true`.

## Differential falsification

Before the fix, a direct control span reached Tempo (`ec7c5e668553041a5cc317b47c39288b`, HTTP 200) while the same standard OTel path through Vector did not (`f66f18873786bb72b7cd4f611e69ed76`, HTTP 404). Vector reported that the trace event lacked the OTLP top-level `resourceSpans` field.

Root cause: `use_otlp_decoding.traces: false` converted incoming traces to Vector-native events while the downstream OpenTelemetry sink expected a preserved OTLP envelope.

After changing `traces: true` and restarting the profile, both the direct Tempo control trace (`3e59be31b2cbb658d378ab46de3b6b75`) and Vector-forwarded trace (`5c17c945cbb1e081d715f62bf0776dfd`) returned HTTP 200, with no Vector warnings.

## Authenticated live trace

A real Cloudflare-authenticated Gateway `execution.submit` produced Runtime operation:

`ordivon-exec:v1:runtime.linux:job-01a0c454-d438-7122-9df4-ebf27cb44422`

The Runtime Job succeeded with exit code 0. Gateway audit selected trace `5e4ab79372e017988f1d720d77325442`, span `4d1088536291c876`.

Tempo returned the trace by exact ID; TraceQL matched the exact `ordivon.operation_ref`; the accepted Gateway span correlated the verified pseudonymous principal, verified Access issuer, Runtime owner ID, operation reference, and native Job ID. Tempo reported four spans under root service `ordivon-gateway`.

This correlation is observability-only. It does not create delegated Runtime authority or make Tempo an execution/continuity owner.

## Operational posture

The backend is deployed **on demand**. The base Gateway profile remains `OTEL_TRACES_EXPORTER=none`; Workstation heavy observability remains cold by default; the existing opt-in trace profile enables standard OTLP export only when tracing is intentionally activated. Product correctness remains independent from telemetry availability.

Tempo 3.0.3 required more than Podman's default 10-second container stop budget during single-binary shutdown. The Quadlet therefore uses standard `StopTimeout=60` under systemd `TimeoutStopSec=75`. Live start → ready → stop acceptance completed graceful shutdown in 31 seconds with `ActiveState=inactive`, `Result=success`, and `ExecMainStatus=0`.

## Result

Persistent/queryable trace storage is now an admitted deployed capability of the Workstation observability plane. The previous current-state statement `persistent-queryable-trace-backend = not admitted` is superseded.
