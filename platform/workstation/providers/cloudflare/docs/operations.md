---
schema_version: 1
id: world.cloudflare.operations
title: Operations
type: operations
profile: provider
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-cloudflare-provider
audience:
  - operator
  - builder
  - agent
updated: 2026-11-24
summary: Canonical operational contract for Cloudflare endpoint, signed client use, Fetch and Browser bounds, request state, budgets, lifecycle, installation, Artifact verification, and policy identity.
evidence_status: verified
readiness: READY
applies_to:
  - providers/cloudflare
related:
  - world.cloudflare.capabilities
  - world.cloudflare.reliability
  - world.cloudflare.security
  - world.cloudflare.release
  - world.authority
---
# Operations

## Scope

Operate the authenticated production endpoint, local client, bounded Fetch and Browser operations, Receipt waits, Artifact downloads, R2 lifecycle, garbage collection, installed controllers, and effective policy identity.

## Normal operation

Use the root-only client configuration, preserve one stable Request ID and body across retries, query capabilities before relying on an operation, wait on pending Receipts, download only Receipt-returned Artifact keys, verify digests before atomic installation, and use installed release or GC controllers for provider state changes.

## Failure detection

Detect invalid signatures or clock windows, idempotency conflict, pending or expired leases, rate limits, policy drift, missing Receipt state, ambiguous transport or control-plane response, Artifact digest mismatch, invalid lifecycle rules, unavailable bindings, and source inputs that cannot be reconstructed.

## Recovery

Recover ambiguous operation delivery by querying the authoritative `requests/v2` state with the original Request ID. Recover deployment uncertainty through Cloudflare Version and Deployment APIs. Use generation-bound cleanup tombstones for deferred Artifact deletion, and never create a new request identity merely because a response was lost.

## Verification

Verify local provider CI, policy coupling, capability identity, one version-bound release observation, affected capability smoke, Receipt replay, R2 lifecycle reread, Artifact SHA-256 and byte length, private file modes, and exact release or GC receipts. [`../README.md`](../README.md) defines capabilities, [`reliability.md`](reliability.md) defines uncertainty, and [`../README.md#authority-boundary`](../README.md#authority-boundary) records authority.

## Production endpoint

The first production surface is the HMAC-authenticated custom domain:

```text
https://edge.ordivon.com
```

Workers.dev and preview URLs remain disabled.

## Client configuration

The local client reads a root-only file:

```text
/root/.config/ordivon/secrets/edge-client.json
```

Schema:

```json
{
  "endpoint": "https://edge.ordivon.com",
  "key_id": "runtime-v1",
  "secret": "base64url-encoded-32-byte-secret"
}
```

The same secret is installed as the Worker secret `EDGE_HMAC_SECRET`. It must never enter Git, logs, receipts, or command output.

## Signed request contract

Each request carries:

```text
Authorization: Ordivon-HMAC <key-id>:<base64url-hmac-sha256>
X-Ordivon-Request-Id: <bounded-id>
X-Ordivon-Timestamp: <unix-seconds>
```

The canonical payload is:

```text
ordivon-edge-v1
<METHOD>
<PATH-AND-QUERY>
<REQUEST-ID>
<TIMESTAMP>
<SHA256-BODY>
```

Requests outside a five-minute clock window are rejected. Reusing a Request ID with the same signed content replays the stored receipt; reusing it with different content returns `409 idempotency_conflict`.

## Client commands

```bash
ordivon-edge health
ordivon-edge status --repo /root/projects/ordivon/platform/workstation/providers/cloudflare --expected-ref HEAD
ordivon-edge capabilities
ordivon-edge fetch https://developers.cloudflare.com/ --maximum-bytes 262144
ordivon-edge receipt <receipt-id>
ordivon-edge artifact-get <artifact-key-from-receipt> \
  --sha256 <sha256-from-receipt> \
  --output /tmp/result.bin
```

## Fetch boundary

P0 fetch allows only:

- HTTPS;
- port 443;
- hostnames in `FETCH_ALLOWED_HOSTS`;
- three validated redirects;
- request bodies up to 8 KiB;
- response bodies up to 1 MiB;
- execution time up to 15 seconds;
- fixed GET semantics with no caller-provided cookies or authorization headers.

Every accepted request conditionally creates an authoritative R2 `requests/v2` Pending state. Successes, failures, and policy rejections commit a final Receipt into that same state object and write a best-effort Receipt mirror.

## Browser Run P1

The P1 endpoint is:

```text
POST /v1/browser/run
```

The client invocation is:

```bash
ordivon-edge browser-run https://example.com/ \
  --viewport-width 1365 \
  --viewport-height 768 \
  --wait-until domcontentloaded \
  --timeout-ms 15000
```

A successful run creates three private artifacts:

```text
browser/v2/<request-id>/g<generation>/<bundle-uuid>/screenshot.png
browser/v2/<request-id>/g<generation>/<bundle-uuid>/content.html
browser/v2/<request-id>/g<generation>/<bundle-uuid>/manifest.json
```

The manifest is the receipt's primary `artifact`; all three references appear in `artifacts`. Download each object with `ordivon-edge artifact-get`.

P1 intentionally supports only one action: navigate to an allowlisted HTTPS URL and capture a snapshot. It does not accept scripts, cookies, credentials, arbitrary headers, clicks, form input, selectors, or file downloads. Browser subresources are restricted to the requested hostname.

## P1.5 operation state

New operations persist an authoritative state under `requests/v2/`. Receipt queries can return HTTP `202` while the execution lease is pending. Use:

```bash
ordivon-edge receipt <request-id> --wait
```

New Artifact paths include the lease generation and an independent execution bundle UUID. Consumers must use the opaque keys returned by the Receipt rather than constructing paths. Existing generation-only keys remain readable. Each new Artifact is written with an R2 create-only condition; a preexisting key is not overwritten. After the bounded provider retention window, durable consumers must rely on their own verified copies, not on indefinite Edge custody.

## Execution budgets

Cloudflare Rate Limit bindings apply per HMAC key ID:

```text
Browser Run: 1 new execution / 10 seconds
Fetch:       30 new executions / 60 seconds
```

Receipt replay occurs before budget consumption. A rate-limited first execution produces a failed Receipt and a `Retry-After` response header.

## R2 lifecycle

Read the current managed lifecycle state without mutation through the installed provider projection:

```bash
ordivon-edge-lifecycle --check
```

Apply the managed lifecycle rules explicitly through the same provider-owned controller:

```bash
ordivon-edge-lifecycle
```

Retention is defined once in `config/edge-policy.json`. Request states, Receipt mirrors, cleanup tombstones, and Request-ID idempotency are retained for 90 days. Fetch and Browser Artifacts are retained for 91 days so a replayable Receipt does not outlive its result. Legacy Receipt objects remain untouched until their existing lifecycle expires.

When immediate Artifact cleanup is deferred, inspect the bounded cleanup-record audit:

```bash
python3 scripts/ordivon_edge_gc.py --dry-run
python3 scripts/ordivon_edge_gc.py
```

Both GC invocations are remote-read-only. A valid legacy tombstone is reported as `deferred` with disposition `native_retention`, not as a completed deletion. The audit binds exact Request ID, operation, lease generation, and generated Artifact paths. The existing R2 expiration rules own deferred deletion; an unreadable or invalid record is a diagnostic failure, never deletion authority.

## Local operational installation

Install the client, the exact provider policy snapshot, release controller, lifecycle controller, GC controller, and daily cleanup-audit timer:

```bash
scripts/install-edge-operations
```

The timer runs after WSL boot and approximately once every 24 hours with randomized delay:

```bash
systemctl status ordivon-edge-gc.timer
systemctl list-timers ordivon-edge-gc.timer
```

The service is root-only, uses a `0077` umask, and audits at most 100 cleanup tombstones per run. It writes a private local audit receipt and performs no remote deletion.

## Client transport and Artifact integrity

For `fetch` and `browser-run`, the client flushes a JSON `edge_request` event containing the original `request_id` and `operation` to stderr before dispatch. stdout remains the response-only JSON interface. Agents should retain the event or provide their own stable `--request-id`; on an uncertain outcome, query `ordivon-edge receipt <request-id> --wait` rather than create a new identity. The event identifies intent, not provider acceptance or completion.

The client retries transient transport failures up to three times. A POST retry preserves the original Request ID and request body, so the Edge state machine returns a first execution, Pending state, or deterministic Receipt replay rather than creating a second operation. HTTP policy failures are not retried automatically.

Artifact downloads fail closed unless `X-Ordivon-Sha256` is present and matches the downloaded bytes. `--sha256` additionally verifies the digest carried by the operation Receipt. The client writes through a same-directory temporary file, fsyncs it, atomically renames it, and applies mode `0600`.

## Effective policy version

`config/edge-policy.json` is the single source for execution bounds, lease durations, expected rate limits, and retention. The Worker combines that document with the effective `FETCH_ALLOWED_HOSTS` binding and reports a fingerprint such as `p1.6.<digest>`. An expired Pending request cannot be taken over when that fingerprint changed. `pnpm check:policy` rejects drift between the policy document and Wrangler configuration.

The installed lifecycle controller reads the installed provider policy at `/usr/local/lib/ordivon-operations/cloudflare-provider/edge-policy.json`; checkout execution uses the checkout policy, and `ORDIVON_EDGE_POLICY` is an explicit override. The install/doctor path digest-checks that materialized policy against current source. The lifecycle controller owns both observation and mutation semantics. `--check` performs exactly one GET and compares provider-owned expected/actual managed rules without PUT; the no-flag path preserves non-Ordivon rules, replaces all rules whose IDs begin with `edge-v2-`, then rereads the API and requires an exact match. It does not depend on Wrangler or the local Node dependency tree.

## Installed release source

`ordivon-edge status --repo <repository-or-provider-path> --expected-ref <git-ref>` resolves Worker input paths from the selected Git commit, preferring the canonical `platform/workstation/providers/cloudflare` tree over legacy layouts. A dirty checkout or removal of a working-tree file does not change the selected commit digest. The `worker_inputs` observation and `source_relation` are distinct: an unresolved historical source commit does not establish a commit ancestry relation; the reported input digest can still be compared independently.


`ordivon-edge-release` resolves `/root/projects/ordivon/platform/workstation/providers/cloudflare` by default. `ORDIVON_CLOUDFLARE_PROVIDER_ROOT` is the explicit override; legacy `ORDIVON_WORLD_REPO` remains a compatibility fallback and does not confer World ownership.
