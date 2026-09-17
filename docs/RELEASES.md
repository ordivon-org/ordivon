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
updated: 2026-09-18
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
12. a Browserless image-pin change requires a paired canary receipt produced from the running 11/12/13 production consensus and the exact candidate image digest before any production substrate mutation. Same-image negative control must be reproducible; unexpected CF02-CF07, detector, challenge-metadata, or Network-v2 drift holds the image. Canary PASS is qualification evidence only and does not itself authorize deployment.

## Version source

Runtime client identity must use `ordivon_harness.version.package_version()` rather than a duplicated literal. The fallback version is tested against `pyproject.toml` for source-checkout execution.

## Dependency updates

A Host or Protocol pin update is an architecture compatibility change, not routine Dependabot churn. It requires the full Harness suite against the candidate revision and lockfile regeneration.

## Deprecation

The package root is a minimal package-identity surface and does not mirror `ordivon_harness.api`. Breaking removal of zero-consumer Python aliases is permitted before 1.0 when current-consumer census, Changelog notice, compatibility documentation, and regression gates are complete. Durable decoders remain until retained state no longer requires them.

## Publication

Tags matching `v*` trigger the portable release-acceptance workflow and retain the verified wheel as a GitHub Actions Artifact. This is repository provenance, not artifact signing or package-index publication.

Current distribution is source and repository-built wheel. Public package-index publication, signed artifacts, hosted images or automatic deployment require a separate provenance and release-signing contract.
