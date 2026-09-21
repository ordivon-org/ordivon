---
schema_version: 1
id: cloudflare-provider.capabilities
title: Ordivon Cloudflare Provider
type: capabilities
profile: provider
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-cloudflare-provider
audience:
  - builder
  - operator
  - agent
updated: 2026-08-03
summary: Canonical capability contract for signed bounded Cloudflare Fetch, Browser snapshot, Receipt, private Artifact, release, rollback, lifecycle, and garbage collection operations.
evidence_status: verified
readiness: READY
applies_to:
  - providers/cloudflare
related:
  - cloudflare-provider.operations
  - cloudflare-provider.reliability
  - cloudflare-provider.security
  - cloudflare-provider.release
---
# Ordivon Cloudflare Provider

## Scope

Provide a signed adapter for bounded remote Fetch and same-origin Browser snapshot work, authoritative request state, replayable Receipts, private R2 Artifacts, and version-bound release operations.

## Supported operations

The supported surface is `fetch.v2`, `browser.snapshot.v2`, `receipt.v2`, authenticated Artifact retrieval, release, rollback, lifecycle configuration, and bounded garbage collection. The exact callable set is reported by the deployed capability endpoint and must match local policy and source identity.

## Authority boundary

Cloudflare Provider owns Worker versions, Deployments, Browser and Fetch execution, R2 request state, lease generations, Receipts, Artifact objects, lifecycle/GC and its physical client/control surfaces. A consuming system owns its own intent/request binding and maps provider evidence into its own domain semantics. The provider does not own consumer Task meaning, verification, or completion authority.

## Limitations

Fetch is allowlisted HTTPS GET with bounded redirects, time, and bytes. Browser supports navigation and snapshot only; no caller scripts, cookies, credentials, arbitrary headers, clicks, forms, or downloads are accepted. The provider is not a general browser automation service, callback authority, provider broker, or workflow engine.

A signed provider adapter for bounded remote Fetch and Browser work.

## Active capabilities

- `fetch.v2` — allowlisted HTTPS fetch with bounded redirects, time, and bytes;
- `browser.snapshot.v2` — same-origin Browser Rendering snapshot;
- `receipt.v2` — pending state, fenced leases, exact Request ID/input binding, replay, and reconciliation;
- private R2 Artifact retrieval with digest and byte verification;
- versioned release, rollback, lifecycle, and garbage collection.

The provider owns Cloudflare execution state and objects. It does not own Host Task meaning or completion.

## Commands

```bash
ordivon-edge health
ordivon-edge capabilities
ordivon-edge fetch https://example.com/
ordivon-edge browser-run https://example.com/ --full-page
ordivon-edge receipt <request-id> --wait
ordivon-edge artifact-get <key> --output ./artifact.bin --sha256 <digest>

sudo ordivon-edge-release release
sudo ordivon-edge-release rollback
sudo ordivon-edge-gc run
ordivon-edge-lifecycle --check
```

The canonical maintained source is `/root/projects/ordivon/platform/workstation/providers/cloudflare` inside the canonical monorepo Workstation owner. `ORDIVON_CLOUDFLARE_PROVIDER_ROOT` may override it explicitly; the historical `ORDIVON_WORLD_REPO` variable remains a compatibility fallback only. Operations owns maintenance/installation of these provider bytes; Cloudflare remains authoritative for provider-native remote state, and consumers retain their own task/semantic authority. Historical release and GC receipts remain private under `/root/backups/ordivon-world/` for continuity.

## Release behavior

A release is skipped when the active Worker already has the same Worker-input digest. The controller accepts any reconstructable Git commit; unrelated repository state does not block a Worker release, while dirty Worker inputs do.

For a changed Worker, the controller uploads a zero-traffic candidate, verifies one version-bound health observation, checks policy and capability identity, runs only the affected Fetch or Browser smoke where the change is capability-local, promotes the candidate, verifies one non-override health observation, and writes a private receipt. Ambiguous control-plane responses are reconciled through Cloudflare before any retry.

## Why retained

Fetch and Browser could be called directly, but direct calls would lose Ordivon's stable signed Request ID, exact input binding, transactional Receipt, response-loss reconciliation, private Artifact contract, and source-input release identity. These are the adapter's non-replaceable functions.

See `docs/operations.md`, `docs/reliability.md`, `docs/release.md`, and `docs/security.md`.
