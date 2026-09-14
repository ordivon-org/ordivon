# Provider: Operations v2

- Source: `/root/projects/ordivon-operations-v2`
- Observed revision: `a2a1d8b995ff53cef8fedf1c1d40051f0582f404`
- Role: task-local execution/integration substrate provider
- Migration mode: metadata only; implementation stays external

## Capabilities

- durable workflow composition/deployment knowledge via Temporal;
- integration-edge automation via n8n;
- host desired-state/configuration via Ansible/Nix/DSC-facing composition;
- external/cloud desired-state via OpenTofu where applicable;
- standards-native telemetry composition via OTLP/OpenTelemetry semantics with current Vector/Prometheus/Loki/Grafana components;
- generic PostgreSQL/backup operational substrate;
- service lifecycle via mature OS/container facilities.

## Current observability realization — 2026-09-14

Operations v2 has an accepted OTLP ingress without introducing an OpenTelemetry Collector daemon:

```text
OTLP gRPC :4317 / HTTP :4318
        ↓
Vector 0.57.0
   ├─ logs -> Loki 3.6.6
   └─ metrics -> Prometheus 3.14.0 native OTLP receiver
```

Traces are explicitly deferred/blackholed because no trace-storage backend has been admitted. This provider must not claim trace observability until a real backend and useful trace query are accepted.

## Boundary

Operations provides mechanics and observable substrate facts. It does not establish Research, Finance, Network, Artifact, Security or other domain semantic success.

OpenTelemetry/OTLP are the telemetry interoperability substrate. Vector/Prometheus/Loki/Grafana are replaceable pipeline/backend choices. OpenInference or OTel GenAI conventions may describe AI spans but remain telemetry projections, not execution/domain state.

## Activation

Load into an active working set only when the current task needs durable orchestration, integration edge automation, host/infrastructure realization, or shared observability.
