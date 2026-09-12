# Standards-first composition

## Responsibility boundaries

| Layer | Mature owner | Responsibility |
| --- | --- | --- |
| Integration edge | n8n | SaaS/API/webhook/OAuth triggers, normalization, notifications, short integration automations |
| Durable process | Temporal | long-running workflow state, retry, timer, wait, signal/update/query, recovery |
| Durable service contract | Temporal Nexus | reusable operations between Temporal applications |
| Physical execution | Ordivon Runtime | process/Git/browser/Windows/GPU/local-machine Jobs, Attempts and Artifacts |
| Async event envelope | CloudEvents 1.0 | interoperable event metadata |
| Async contract | AsyncAPI 3.0 | channel/message/operation contract |
| Sync HTTP contract | OpenAPI | synchronous HTTP contracts when a real endpoint exists |
| Reliable DB-to-event handoff | Transactional Outbox | atomically record domain mutation + event intent |
| Telemetry | OpenTelemetry | traces/metrics/log correlation and context propagation |

## Non-negotiable boundaries

1. n8n is an integration edge, not a domain authority and not a replacement for Runtime.
2. Host execution nodes are blocked in n8n; machine actions go through Runtime.
3. Temporal Activity retry uses one stable Runtime `clientRequestId` for the same logical physical operation.
4. Runtime success proves physical execution, not domain semantic success or provider acceptance.
5. Delivery is assumed at-least-once across distributed boundaries; correctness comes from stable identity, idempotent consumers, deduplication and authoritative reconciliation.
6. No Kafka/NATS/Dapr/Kubernetes is introduced until measured fan-out, replay, multi-node or scheduling pressure justifies it.
7. PostgreSQL databases/users remain logically separated even when they share the Operations-managed PostgreSQL service and pgBackRest substrate.

## Current rollout order

1. n8n + dedicated PostgreSQL database + rootless Podman/Quadlet service using official digest-pinned OCI images and external task runners.
2. CloudEvents/AsyncAPI contract baseline.
3. Thin Temporal -> Runtime Activity adapter with stable operation identity.
4. Temporal production service migration from local dev persistence to Operations-managed PostgreSQL — complete; blue/dev SQLite history archived and retired.
5. Temporal Nexus service contracts for cross-E2E durable operations — workflow-backed capability verified, adopt only on real service demand.
6. OpenTelemetry propagation into the existing Prometheus/Vector/Loki/Grafana Operations stack — logs and metrics complete; trace storage deliberately deferred.
7. Host v1 retirement — inventory, read-only archival and authority shutdown; resumable historical projections are archived rather than bulk-imported into Temporal.
## Proven integration slice

The first executable integration slice is source-controlled under `n8n/workflows/ordivon-integration-smoke-v1.json`. It proves n8n Webhook -> external task runner -> external HTTP -> correlated result, and the same integration call has been completed from a Temporal Activity on the Operations-managed production-green Temporal substrate at `127.0.0.1:17233`. See `docs/N8N_INTEGRATION_SMOKE.md`.

## Current authority cut

As of 2026-09-12, the historical Temporal blue/dev cluster and legacy Host v1 authority are both retired. Temporal PostgreSQL on `127.0.0.1:17233` is the durable-process authority; Runtime remains the physical-execution authority; n8n remains the integration edge. Host v1 state is retained only as an integrity-verifiable read-only historical archive.
