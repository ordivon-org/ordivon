# Standards-first composition R1 acceptance

Date: 2026-09-12

## Standing

**SUPPORTED FOR INTEGRATION-EDGE + CONTRACT-BASELINE SLICE.**

This standing now includes the separately accepted Temporal production-green PostgreSQL substrate and the n8n composition slice on that substrate. It still does not claim global Temporal application cutover, Nexus cutover, OpenTelemetry end-to-end propagation, or Host retirement.

## n8n integration edge

The canonical local authority is a rootless Podman/Quadlet pod owned by Operations. Workstation may still materialize an n8n CLI for operator convenience, but the service runtime authority is the official digest-pinned n8n OCI image plus the matching official distroless external task-runner image.

Verified live after convergence:

- rootless user manager: `ordivon-n8n-pod.service`, `ordivon-n8n.service`, and `ordivon-n8n-runners.service` active;
- linger: enabled for the dedicated `n8n` system identity; Quadlet links the pod into the user `default.target`;
- main image: `ghcr.io/n8n-io/n8n@sha256:770da605a7dfdda55838fb2b66b701435690ffcce5d3067585fc7e3cb17b168f`;
- runner image: `ghcr.io/n8n-io/runners@sha256:f171bd9b3bb8e4668f2ec4293307043987140b26ebc2f7d8ec81b6738953a7e1`;
- main and runner root filesystems: read-only; main writable state is bounded to `/home/node/.n8n` plus ephemeral `/home/node/.cache`;
- host listener: `127.0.0.1:5678` only; task broker 5679 and runner launcher 5680 remain private inside the pod network namespace;
- `/healthz` and `/healthz/readiness`: HTTP 200;
- external JavaScript and Python runners both register successfully; the deprecated host-native/internal-Python-runner path is gone;
- PostgreSQL database: `n8n`, owner/user `n8n`, 129 public tables at the accepted cut;
- pgBackRest stanza: `ok` after cutover;
- exact second Ansible convergence: `changed=0`, `failed=0`;
- rootless n8n can reach an external HTTPS API;
- machine-bypass nodes remain excluded: Execute Command, Local File Trigger, Read/Write Files, SSH;
- Runtime remains the machine-execution authority.

The first container cut exposed a read-only-rootfs cache requirement; the accepted topology supplies only an ephemeral cache tmpfs. A second cut exposed a Podman tmpfs-option incompatibility; the accepted form uses a portable mode-only tmpfs. Both failed cuts rolled back to the prior service, and the rollback path was corrected to keep host-native and container environment files separate until acceptance.

The previous host-native `n8n.service` and its host-native environment were retired after container readiness passed. Rootful staging images and the incidental `/root/.n8n` CLI state were also removed after proving they had no consumers.

## n8n vertical-slice acceptance

A source-controlled acceptance workflow now proves the integration composition rather than only service health. A direct run completed:

`CloudEvent JSON -> n8n webhook -> external JS runner -> httpbin.org -> external JS runner -> correlated CloudEvent result`.

The accepted direct n8n execution was successful and preserved the request ID as `correlationid`. A second run completed through the Operations-managed Temporal production-green cluster at `127.0.0.1:17233` and returned the same correlated result to the Temporal Workflow. The Workflow was independently present in PostgreSQL-backed Temporal visibility with completed status. This proves the `Temporal -> n8n -> external -> result` composition boundary on the production-green substrate. Global application cutover from the existing `7233` dogfood/dev cluster remains a separate gate.

The local webhook uses a CloudEvents 1.0 JSON envelope with `application/json`; n8n 2.36.7 maps `application/cloudevents+json` webhook bodies to binary input, so HTTP structured-mode media binding remains unclaimed in this slice.

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
2. application cutover from the dev `7233` Temporal cluster to the accepted production-green `17233` cluster, with active-workflow drain/bootstrap disposition;
3. Temporal Nexus contract cutover where cross-E2E durable calls actually exist;
4. OpenTelemetry propagation into the existing Prometheus/Vector/Loki/Grafana substrate;
5. active Host task migration + terminal/history archive + Host retirement.
