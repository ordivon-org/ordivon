# MCP Release Identity and Connector Catalog Freshness Acceptance — 2026-09-21

Status: ACCEPTED IN ISOLATED SOURCE / LIVE DEPLOYMENT PENDING CONCURRENCY CHECK

## Problem

The current ChatGPT connector snapshot exposes retired MCP tools from older Ordivon surfaces, including Host `news.*` and Gateway `capability.list`, while current owner servers no longer expose those tools.

This acceptance keeps the fault boundary outside Host and Gateway semantic kernels.

## Standards-backed findings

- MCP 2026-07-28 `tools/list` results carry cache hints. The Python SDK default is `ttlMs=0`, `cacheScope=private`: immediately stale and authorization-context-local.
- `notifications/tools/list_changed` is a standard refresh signal for connected clients. On 2026-07-28 it reaches clients that opened a `subscriptions/listen` stream for tool-list changes.
- Those mechanisms do not repair a connector/platform snapshot that was materialized outside the live MCP response cache or is not currently subscribed.
- Therefore Ordivon must not reintroduce private `surfaceVersion`, Tool registries, or copied catalog truth inside Host/Gateway merely to compensate for a stale client.

Primary upstream references:
- Model Context Protocol Python SDK caching documentation
- Model Context Protocol 2026-07-28 tools/list_changed specification
- Model Context Protocol Python SDK subscriptions documentation

## Source-current surfaces

Gateway exact northbound Tool surface:

- system.describe
- capability.describe
- execution.submit
- execution.get
- execution.cancel
- artifact.read
- continuity.get
- continuity.list

Host exact Tool surface:

- host.status
- attention.delta
- board.list
- board.search
- board.post
- task.observe
- task.list
- task.resume
- task.adopt
- task.checkpoint

Retired names such as `capability.list` and `news.list` are explicitly absent.

## Release identity correction

Before this change:

- Gateway package version = 0.1.0
- Gateway MCP `serverInfo.version` = empty string
- Host package/serverInfo version = 0.1.0 despite the completed API contraction

The candidate release moves Gateway and Host to `0.2.0`.

Gateway now constructs:

`MCPServer("ordivon-gateway", version=package_version("ordivon-gateway"))`

Host already used the same standard package-version binding.

Gateway `system.describe.gateway_version` is derived from the same package metadata; the Pydantic contract no longer owns a duplicate hard-coded version default.

This is standard release identity. It is not a private catalog epoch and does not claim to force-refresh an already stale external connector snapshot.

## Harness boundary

Harness `runtimeJobRef` remains Runtime-specific.

It participates in physical dispatch, reconciliation, cancellation, and Runtime evidence. It is therefore not generalized into a cross-owner reference merely for naming symmetry. Host Task, Runtime Job, Harness Run, Workflow, Git Revision, and Trace identities remain federated.

## Verification

- Gateway targeted RED proved the prior empty server version.
- Gateway full verify: PASS.
- Host database-independent exact surface/server identity test: PASS.
- Host full verify: PASS.
- Repository CI: PASS.
- Gateway tools/list cache hint: ttlMs=0 / private.
- Host tools/list cache hint: ttlMs=0 / private.

## Boundary conclusion

Owner source and live MCP `tools/list` remain authoritative for server capabilities.

Connector catalog freshness is a connector/client responsibility. Ordivon may expose correct standard release identity and standard MCP notifications/cache hints, but it must not absorb client cache ownership into Host or Gateway.
