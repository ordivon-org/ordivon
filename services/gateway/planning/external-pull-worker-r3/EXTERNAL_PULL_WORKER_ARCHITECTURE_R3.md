# External Pull Worker Architecture R3

## Stable northbound waist

~~~text
caller
  -> Gateway execution.submit
  -> capability projection/router
  -> external.pull transport
  -> durable queued operation
  <- normal ExecutionReceipt

worker --outbound HTTPS--> claim
worker --outbound HTTPS--> started/events/artifacts/complete
caller -> execution.get / execution.cancel / artifact.read
~~~

Push versus pull is not exposed to Gateway callers.

## Authority boundaries

The Gateway external worker store owns only transport mechanics:
worker endpoint identity, operator-admitted capability ceiling, heartbeat freshness,
queued operation delivery, attempt/lease fencing, request replay fencing, and retained
transport evidence.

It does not establish Task ownership, priority, semantic completion, Human identity,
Principal identity, or domain EffectAuthority.

The worker may reduce its advertised capabilities at heartbeat time but cannot expand
beyond the operator-admitted enrollment ceiling.

## Recovery

Correctness depends on durable queue + attempt identity + lease expiry + stale-attempt
rejection. A worker process may disappear. A later claim expires the abandoned attempt,
returns the operation to queued state, and creates a new attempt. WSS may later wake a
worker but cannot own lifecycle truth.

## Browser boundary

R3 admits shell-style external capabilities only. Muse native Chromium remains a separate
native-agent authority lane. No Python worker is granted browser broker authority by R3.

## Edge boundary

The existing public Gateway hostname is Cloudflare Access protected for interactive MCP.
A production worker route must not silently inherit an interactive browser requirement.
The worker HTTP paths need a deliberate H3 edge policy: network reachability to
/v1/workers/* and /v1/operations/*, while application-layer Ed25519 signatures remain
mandatory. Enrollment additionally requires an operator bootstrap credential and should be
disabled after enrollment.

This edge change is not performed in R3.
