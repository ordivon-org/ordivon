---
schema_version: 1
id: harness.releases
title: Harness Releases and Versioning
type: policy
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - maintainer
  - builder
  - operator
  - agent
updated: 2026-09-20
summary: Version identities, release gates, compatibility obligations and deprecation rules for Harness.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
related:
  - harness.status
  - harness.compatibility
  - harness.verification
---
# Harness Releases and Versioning

## Independent identities

| Identity | Meaning |
| --- | --- |
| package version | public Python distribution change set |
| Git commit | exact Harness implementation |
| Harness protocol revision | owner-local Run semantic family |
| object `kind` and `schemaVersion` | retained CAS interpretation |
| Host commit | source-level authority/storage API |
| Protocol commit | promoted cross-repository value contracts |
| Runtime catalog digest | physical Tool schema used by a Run |
| Provider adapter/model identity | inference source semantics |
| receipt digest | exact tested journey |

Package SemVer does not replace these stronger identities.

## Current stage

Harness `0.6.0` is pre-1.0. Public behavior may evolve, but retained state, effect identities and uncertainty cannot be silently reinterpreted.

## Change classes

### Patch

Fix implementation, diagnostics, documentation or tests without intentionally changing supported public API, durable object meaning or Provider/Tool semantics.

### Minor

Add facade APIs, adapters, object versions or capabilities while preserving existing supported readers and safe recovery.

### Major

Remove or reinterpret supported public APIs, current independent object schemas, Provider semantics or Tool recovery. Before 1.0 this may be an intentional break, but the release must name removed authority, retained state expectations, evidence, and rollback/backup boundary.

## Release gates

A releasable commit requires:

1. `uv sync --locked`, `uv lock --check` and dependency-contract success;
2. complete deterministic tests and semantic history tests;
3. public API and Host import-boundary tests;
4. documentation/evidence validation;
5. wheel build, metadata validation, isolated installation and CLI entry-point smoke testing;
6. exact Git dependency validation and third-party PyPI vulnerability audit when such dependencies exist;
7. secret scanning and CodeQL;
8. Changelog entry;
9. live receipt when Provider, Runtime, Tool recovery, cancellation or completion semantics change;
10. named limitations and compatibility impact;
11. for Agent Automation activation, a quiescent pre-switch Browser Security pool qualification bound to the exact candidate commit and Security-v2 LKG index. Only `NO_OBSERVED_DRIFT` passes automatically; detector, shared, carrier-local, mixed drift, or collection failure holds the release and retains a private qualification receipt.
12. a Browserless image-pin change requires a paired canary receipt produced from the installed rendered production contract and the exact candidate image digest before any production substrate mutation. Active carriers are cross-checked while sleeping on-demand carriers remain valid lifecycle state. Same-image negative control must be reproducible; unexpected CF02-CF07, detector, challenge-metadata, or Network-v2 drift holds the image. Canary PASS is qualification evidence only and does not itself authorize deployment.
13. Browserless image promotion is a separate digest-fenced transaction: `apply` keeps Agent Automation admission closed after deployment, Security-v2 must reseal the per-carrier LKG from retained post-change evidence under its own authority, and Harness `finalize` may reopen admission only after the Security revision and pool-index identity both advance and a fresh live pool returns exactly `NO_OBSERVED_DRIFT`.
14. A tagged wheel release must emit native GitHub artifact attestations for build provenance and an SPDX SBOM bound to the exact wheel bytes. Manual and reusable release-acceptance runs remain verification-only and do not mint release attestations.
15. **Agent Automation MCP API compatibility is an installed-consumer gate, not a Git-branch assumption.**
    Before replacing its installed server, read the **running** official authenticated MCP
    `tools/list` (names only for the initial subtraction check), verify the installed file
    actually corresponds to that advertised tool set, and compare against the exact candidate
    source's registered tool names and accepted `CampaignSpecInput` fields. Any removed live
    Tool name or accepted input field **holds** deployment until actual identified consumers
    and an authorized replacement/deprecation have been independently qualified. An unreadable
    or dynamic registration, or installed-versus-live disagreement, is `UNKNOWN` and also holds.
    Reuse `evals/automation-mcp-surface-005/verify.py` once available in the candidate SourceCut:
    `BREAKING_NAME_OR_FIELD_SUBTRACTION_DETECTED` (exit 2) and `INDETERMINATE` (exit 3) block;
    a zero exit proves only *no observed static subtraction*, **not** semantic compatibility
    or release authorization. Qualify installed Browserless, Temporal and conversation/continuity
    consumers independently. Do not mutate production to match a smaller source catalog.
16. **Workspace-backed same-Run resume requires an actually deployed Native Workspace
    lifecycle qualification**, not merely a passing source test, merged PR or completed Job.
    Verify a bound/current Runtime PG claim before the first model turn that may pause,
    no unauthorized effect after issuer revocation, the full original PG Tool/Provider
    unresolved history, and downstream Git/Artifact byte delivery before certified release
    and native close. If the installed Runtime lacks a claim/issuer/finalizer protocol,
    keep affected PAUSED consumers' Workspaces retained. A timer, caller `consumerReleased`
    flag or terminal-looking Run is insufficient. See `ARCHITECTURE.md`,
    `docs/VERIFICATION.md` and `docs/OPERATIONS.md` for the current physical gate.

## Version source

Runtime client identity must use `ordivon_harness.version.package_version()` rather than a duplicated literal. The fallback version is tested against `pyproject.toml` for source-checkout execution.

## Dependency updates

A Host or Protocol pin update is an architecture compatibility change, not routine Dependabot churn. It requires the full Harness suite against the candidate revision and lockfile regeneration.

## Deprecation

The package root is a minimal package-identity surface and does not mirror `ordivon_harness.api`. Breaking removal of zero-consumer Python aliases is permitted before 1.0 when current-consumer census, Changelog notice, compatibility documentation, and regression gates are complete. Durable decoders remain until retained state no longer requires them.

## Publication

Tags matching `v*` trigger the portable release-acceptance workflow and retain the verified wheel as a GitHub Actions Artifact. Tagged wheels additionally receive GitHub-native signed build-provenance and SPDX SBOM attestations through `actions/attest`; the attested subject is the exact wheel produced by the release workflow.

Current distribution remains source plus repository-built wheel. These attestations do not publish to a package index, create a hosted image, or authorize deployment; those effects require their own external publication/deployment contract.
