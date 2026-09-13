---
schema_version: 1
id: world.cloudflare.reliability
title: Reliability model
type: reliability
profile: provider
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-world
  - ordivon-cloudflare-provider
audience:
  - builder
  - operator
  - agent
updated: 2026-08-03
summary: Canonical failure model for authoritative request state, conditional transitions, lease fencing, generation-bound Artifacts, ambiguous writes, cleanup, retention, and replay.
evidence_status: verified
readiness: READY
applies_to:
  - providers/cloudflare
related:
  - world.cloudflare.capabilities
  - world.cloudflare.operations
  - world.cloudflare.security
  - world.authority
---
# Reliability model

## Failure model

A remote request may be rejected before admission, remain pending, commit successfully while the response is lost, fail after writing some Artifacts, be taken over after lease expiry, encounter policy drift, or leave deferred cleanup. Transport failure alone does not establish whether an external Effect occurred.

## Retries

Clients may retry transient transport failures only with the same signed Request ID and exact body. Receipt replay occurs before rate-budget consumption. A different request digest under the same ID fails with conflict, and an expired request under a changed policy requires a new ID.

## Uncertainty

`requests/v2/<request-id>.json` is the sole authoritative request state. Pending, lease generation, ETag fencing, committed Receipt, policy fingerprint, capability identity, and Worker identity distinguish active, stale, ambiguous, and final work. Receipt mirrors and timestamps are not independent truth.

## Recovery

Reread authoritative state after ambiguous writes, accept a matching committed Receipt, clean only the executor's generation-bound Artifacts when commit did not win, use conditional takeover for same-policy expired leases, and process validated cleanup tombstones through bounded GC.

## Evidence

Tests inject R2, commit, takeover, cleanup, policy, rate-limit, and replay failures. Every final Receipt excludes private lease tokens and ETags, binds execution and policy identity, and references Artifacts whose bytes are independently verified by the client. See [`operations.md`](operations.md) for recovery commands, [`security.md`](security.md) for protection controls, and [`../../../docs/authority.md`](../../../docs/authority.md) for authority.

## Authoritative request state

P1.5 replaces the former independent lock and receipt objects with one authoritative state object:

```text
requests/v2/<request-id>.json
```

The object has exactly two states:

```text
pending
  → committed
```

`pending` contains the semantic request digest, operation, policy and capability versions, Worker version, lease generation, a private lease token, and an expiration time.

`committed` contains the complete final Receipt. A best-effort mirror is also written to `receipts/v2/`, but the mirror is not authoritative and its failure does not invalidate an already committed operation.

## Conditional state transitions

Creation uses an R2 conditional write equivalent to `If-None-Match: *`. Final commit and stale-lease takeover use the current state object's ETag.

```text
create pending(g1)
  → execute
  → conditional commit against g1 ETag
```

If a later executor has already replaced the pending object, the old ETag cannot commit.

## Fencing and Artifact generations

An expired lease can be replaced only when its policy and capability versions still match the current implementation. Every takeover increments `lease_generation`.

Artifact paths include that generation:

```text
fetch/v2/<request-id>/g<generation>/body
browser/v2/<request-id>/g<generation>/screenshot.png
browser/v2/<request-id>/g<generation>/content.html
browser/v2/<request-id>/g<generation>/manifest.json
```

This prevents cleanup by a stale executor from deleting a newer executor's output.

## Ambiguous writes

If an R2 commit call throws after the platform may already have accepted the write, Edge rereads the authoritative state:

- matching committed Receipt: treat the operation as committed;
- pending or different generation: clean the executor's Artifact set and fail closed.

## Pending receipt reads

`GET /v1/receipts/<request-id>` returns:

- `202` with a `pending` record while the lease is active;
- `200` with the final Receipt after commit;
- `404` when no v2 or compatible legacy record exists.

The local client can wait for final state:

```bash
ordivon-edge receipt <request-id> --wait --timeout 120
```

## Legacy compatibility

Committed `receipts/v1` objects remain readable and replayable. They are normalized with synthetic legacy execution metadata. An unfinished legacy v1 lock is not taken over automatically; the caller must use a new Request ID.

## Tested failures

The test suite injects R2 failures and proves:

- pending records are observable;
- stale leases cannot commit;
- takeover increments generation;
- stale Artifact cleanup cannot delete the current generation;
- commit failure removes newly written Artifacts;
- an ambiguous post-write error is recovered by rereading committed state;
- expired requests cannot cross a policy-version boundary;
- rate-limited operations are receipted and replay does not consume the budget again;
- Receipt serialization excludes lease tokens and ETags.

## Deferred cleanup

If immediate R2 deletion fails, Edge writes a bounded cleanup tombstone:

```text
cleanup/v2/<request-id>/g<generation>.json
```

The tombstone contains only Request ID, operation, lease generation, Artifact keys, reason, and timestamp. It contains no lease token or ETag. The GC controller validates that every requested deletion belongs to the same Request ID and generation and is under `fetch/v2` or `browser/v2` before deleting anything.

## Policy fingerprint and retention window

The execution policy is no longer a manually maintained label. Edge hashes `config/edge-policy.json` together with the effective Fetch hostname allowlist and stores the resulting `p1.6.<digest>` fingerprint in each lease and Receipt. Configuration changes therefore fence expired work even when the capability contract version itself is unchanged.

Request-ID idempotency, authoritative request state, and Receipt mirrors are retained for 90 days. Capability Artifacts are retained for 91 days, providing a one-day safety margin so a lifecycle-managed Artifact does not expire before its replayable Receipt. The retention contract is exposed by `GET /v1/capabilities`.

## Browser navigation evidence

Browser snapshot Receipts preserve the requested URL and explicitly report `final_url_observed: false` because the current provider response does not expose a trustworthy final navigation URL. Consumers must not infer final page identity from the requested URL.
