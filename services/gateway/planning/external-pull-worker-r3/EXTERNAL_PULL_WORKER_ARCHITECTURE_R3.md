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

Correctness depends on durable queue + attempt identity + lease fencing + explicit
reconciliation of unknown execution. Worker heartbeat renews only still-valid active
attempt leases; it never resurrects an expired lease.

An expired **claimed but not started** attempt may be marked `expired_unstarted`, returned
to the queued state, and claimed again. An expired **started** attempt is different: it may
already have produced external side effects, so Gateway marks the attempt and operation
`reconcile_required`, retains the active-attempt fence, and does not issue a replacement
attempt. A late terminal report from that same fenced attempt may resolve the uncertainty.
Rejecting stale terminal results is not treated as protection against duplicate external
side effects.

WSS may later wake a worker but cannot own lifecycle truth. Before this transport is enabled
in production, the durable execution-state owner and provider-specific reconciliation path
must be explicitly qualified.

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
