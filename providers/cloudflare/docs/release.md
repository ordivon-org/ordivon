---
schema_version: 1
id: world.cloudflare.release
title: Release and rollback
type: release
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-world
  - ordivon-cloudflare-provider
audience:
  - operator
  - builder
  - agent
updated: 2026-08-03
summary: Canonical release contract for Worker-input identity, zero-traffic candidate admission, affected-capability smoke, ambiguous deployment reconciliation, promotion, rollback, and private receipts.
evidence_status: verified
readiness: READY
applies_to:
  - providers/cloudflare
related:
  - world.cloudflare.capabilities
  - world.cloudflare.operations
  - world.cloudflare.reliability
  - world.authority
---
# Release and rollback

## Release identity

A release is identified by the exact committed deployable Worker inputs and their digest. The source commit is provenance; unrelated documentation, tests, evidence, branch names, detached state, and non-Worker changes do not alter Worker identity.

## Changes

A changed input digest creates one immutable zero-traffic candidate. Admission verifies version-bound health, effective policy, capability identity, and only the affected Fetch or Browser operation unless shared code or configuration changed. A matching active digest produces `no_change`.

## Compatibility

The candidate must expose the expected signed capability and Receipt contracts, Cloudflare bindings, policy fingerprint, private R2 behavior, and current client expectations. Dirty Worker inputs are incompatible because the deployed bytes cannot be reconstructed.

## Verification

Run local provider CI, upload the candidate, require a stable consecutive sequence of version-bound health observations through an override, retry only read-only health and capability checks when an edge still serves the previous version, guard every external smoke POST with another stable override sequence, promote to 100 percent, verify stable unoverridden routing, query authoritative Deployment state after ambiguous responses, and write a private source- and version-bound receipt. [`operations.md`](operations.md) defines installed operation, [`reliability.md`](reliability.md) defines reconciliation, and [`../../../docs/authority.md`](../../../docs/authority.md) records authority.

## Rollback

On failed admission, restore the previous version to 100 percent and preserve a failure receipt. Operators may explicitly roll back to the prior or specified version. An uploaded candidate may remain for diagnosis but receives no ordinary traffic.

## Deployable input identity

A Worker release is identified by the committed tree of deployable inputs:

```text
src/
config/edge-policy.json
wrangler.jsonc
package.json
pnpm-lock.yaml
tsconfig.json
```

The version tag is:

```text
git-<source-prefix>-src-<worker-input-digest>-<time>
```

The source commit is provenance. The input digest decides whether a release changes the Worker. Documentation, tests, evidence, and release-tool-only changes do not require a new Worker version.

Dirty Worker inputs are rejected because they cannot be reconstructed. A branch, detached commit, unrelated dirty file, or commit not yet equal to `origin/main` is not rejected merely for organizational form.

## Flow

```text
read active Cloudflare version and deployment
→ return `no_change` when the input digest already matches
→ run local provider CI
→ upload one immutable candidate
→ deploy previous 100% + candidate 0%
→ require three consecutive candidate health observations through an override
→ retry only version-bound health and capability GETs when an edge is stale
→ guard each external smoke POST with another three-observation override sequence
→ verify policy, capabilities, and affected operations
→ promote candidate 100%
→ require three consecutive promoted health observations without override
→ write a private release receipt
```

A single matching observation does not establish stable override routing: the same deployment may still serve the previous version on the next request while edge state converges. The controller therefore requires three consecutive version-bound health observations and resets the sequence on any mismatch. This is a bounded admission guard, not a claim of global propagation.

Fetch-only and Browser-only source changes run only their corresponding operation smoke. Shared routing, authentication, policy, configuration, dependency, or build changes run both. Local tests remain broader than deployment smoke because they exercise state-machine failure paths without creating remote Effects.

## Failure and reconciliation

Cloudflare Version and Deployment state is authoritative. If Wrangler times out after submitting a deployment, the controller queries the Deployment API before deciding whether to retry. It never assumes timeout means failure.

If admission fails after the 0% split exists, the previous version is restored to 100% and a failure receipt is written. An uploaded candidate may remain available for diagnosis but receives no ordinary traffic.

An already uploaded candidate may be resumed with:

```bash
sudo ordivon-edge-release release --candidate-version-id <version-id>
```

The candidate must carry the current Worker-input digest or point to a source tree with byte-equivalent Worker inputs.

## Commands

```bash
sudo ordivon-edge-release release --message "describe the Worker change"
sudo ordivon-edge-release rollback
sudo ordivon-edge-release rollback --version-id <version-id>
```

Private receipts are stored under `/root/backups/ordivon-world/cloudflare-releases/`.

## Why this controller remains

Wrangler uploads code but does not by itself preserve Ordivon's source-input identity, reconcile ambiguous zero-percent deployment responses, bind smoke results to the exact candidate version, restore the prior version after failed admission, or produce a private recovery receipt. Delete this controller only when a maintained deployment system provides those exact behaviors.
