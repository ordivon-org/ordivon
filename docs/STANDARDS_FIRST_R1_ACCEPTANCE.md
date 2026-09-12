# Standards-first composition R1 acceptance

Date: 2026-09-12

## Standing

**SUPPORTED FOR INTEGRATION-EDGE + CONTRACT-BASELINE SLICE.**

This standing does not claim Temporal production persistence, Nexus cutover, OpenTelemetry end-to-end propagation, or Host retirement. Those remain later gates.

## n8n integration edge

The canonical local authority is a single `n8n.service` using Workstation's immutable Nix/Home Manager n8n 2.36.7 materialization and Operations-managed lifecycle/configuration.

Verified live after convergence:

- service: active + enabled;
- restart count after convergence: `NRestarts=0`;
- listener: `127.0.0.1:5678` only;
- `/healthz`: `200`, body `{"status":"ok"}`;
- PostgreSQL database: `n8n`, owner/user `n8n`, 129 public tables at the accepted cut;
- secrets file: `/etc/n8n/n8n-secrets.env`, root-owned mode `0600`;
- machine-bypass nodes explicitly excluded in the running process environment: Execute Command, Local File Trigger, Read/Write Files, SSH;
- Runtime remains the machine-execution authority.

The first deployment attempt exposed a false-green hazard: a second n8n service could fail/restart on port conflict while `/healthz` was served by another instance. Acceptance was therefore strengthened to require the canonical service state plus initialized PostgreSQL schema, not HTTP health alone. The duplicate systemd unit was disabled and removed; the canonical service remained active.

A transient empty duplicate account/database/state namespace created by that rejected attempt is not an authority and is not referenced by the accepted service. Destructive cleanup was intentionally not used as an acceptance prerequisite.

## Standards baseline

Versioned contracts now establish:

- CloudEvents 1.0 JSON envelope for asynchronous integration boundaries;
- AsyncAPI 3.0 logical async contract, with no broker implied;
- OpenAPI for real synchronous HTTP APIs only;
- Transactional Outbox as a per-domain pattern, not a shared Ordivon event database;
- Temporal Nexus as the selected durable application-to-application contract mechanism;
- OpenTelemetry as the selected telemetry propagation/semantic standard.

Kafka, NATS, Dapr and Kubernetes remain deferred until concrete fan-out, replay, multi-node, or scheduling pressure exists.

## Remaining gates

1. thin Temporal Activity -> Runtime MCP adapter with stable Runtime request identity;
2. Temporal service migration from dev SQLite persistence to Operations-managed PostgreSQL with backup/recovery acceptance;
3. Temporal Nexus contract cutover where cross-E2E durable calls actually exist;
4. OpenTelemetry propagation into the existing Prometheus/Vector/Loki/Grafana substrate;
5. active Host task migration + terminal/history archive + Host retirement.
