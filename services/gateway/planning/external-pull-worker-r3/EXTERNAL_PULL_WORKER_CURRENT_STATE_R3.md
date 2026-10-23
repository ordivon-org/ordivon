# External Pull Worker R3 — Current State

Date: 2026-09-22
Baseline: 97424e9ec87ec8251bb6f8470e57b6830429beaa
Workspace: ws-muse-external-pull-worker-r3-20260922

## Observed before implementation

Gateway 0.3.0 already owned the stable northbound execution waist:
execution.submit, execution.resolve, execution.get, execution.cancel,
artifact.read, capability projection, Runtime owner routing, Host continuity routing,
Cloudflare Access ingress attribution, and HTTP transport.

The repository did not contain an External Pull Worker implementation, worker registry,
worker heartbeat, pull queue, external lease/attempt store, worker request signing, worker
revocation, or worker HTTP adapter.

Runtime already owns its own Job/Attempt/Reservation/Artifact truth. Those types are
Runtime-local physical execution semantics and are not imported into Gateway.

Admission Fabric R1 is canonical and explicitly records AF-S2 capability authorization and
AF-S3 unattended workload identity as OPEN. R3 therefore does not claim to close northbound
capability AuthZ merely by authenticating a worker.

## R3 implementation standing

| LEGO | Standing |
|---|---|
| Worker identity | IMPLEMENTED, transport identity only |
| Operator-admitted capability ceiling | IMPLEMENTED |
| Heartbeat/current capability projection | IMPLEMENTED |
| Durable queue | IMPLEMENTED as Gateway transport mechanics |
| Pull claim / attempt / expiry | IMPLEMENTED |
| Stale-attempt fence | IMPLEMENTED |
| Idempotent completion | IMPLEMENTED |
| Worker generation fence | IMPLEMENTED |
| Revocation | IMPLEMENTED |
| Ed25519 signed worker requests | IMPLEMENTED |
| Nonce replay rejection | IMPLEMENTED |
| Events/artifacts | IMPLEMENTED |
| execution.submit/get/cancel/artifact.read integration | IMPLEMENTED |
| Real HTTP MCP -> worker -> completion E2E | PASS |
| WSS wake optimization | NOT IMPLEMENTED; not required for correctness |
| Muse native-browser worker | NOT IMPLEMENTED; intentionally separate |
| Muse cron | NOT DEPLOYED |
| Production worker ingress edge policy | NOT DEPLOYED |
| AF-S2 northbound capability AuthZ | OPEN, pre-existing Admission Fabric gap |
| AF-S3 production workload identity | OPEN; R3 worker signature is bounded transport AuthN |

No production Gateway, Runtime, Host, Cloudflare policy, Muse cron, or Muse account was changed.
