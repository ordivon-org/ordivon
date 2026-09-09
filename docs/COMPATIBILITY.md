---
schema_version: 1
id: harness.compatibility
title: Harness Compatibility
type: policy
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - builder
  - operator
  - maintainer
  - agent
updated: 2026-08-24
summary: Dependency graph, source-level Host boundary, persistent object compatibility and upgrade rules.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
related:
  - harness.status
  - harness.releases
  - harness.verification
---
# Harness Compatibility

## Dependency graph

The current Harness runtime dependency graph is intentionally small and Host-free: the package depends on the exact Ordivon Protocol revision, pinned `httpx==0.28.1` for cancellable DeepSeek HTTP/TLS transport, and `jsonschema` for opt-in local structured-result conformance verification. The exact third-party transitive graph is pinned by `uv.lock` and mirrored in `requirements-audit.txt`. There is no Host dependency, optional Host extra, or Host development group.

Python support is `>=3.12,<3.13`. Runtime integration is structural through the caller-supplied `HarnessRuntimeClient`; a Runtime server/version is not a Python package dependency.

## Public API

`ordivon_harness.api` is the supported application facade, and the package root mirrors that API plus `package_version`. Advanced Host-free integration uses the explicit owner modules for persistence, continuity, Provider, Runtime, recovery, cognition, and Tool composition; the duplicate `ordivon_harness.core` aggregation facade is retired. P0 adds `HarnessAgentRun.explain()` on the existing recommended Run handle. Generated installed-capability projectors live in advanced `ordivon_harness.capability_catalog`. The former experimental `ordivon_harness.capability_discovery` descriptor/candidate/ranking layer is retired; caller/owner current affordances are supplied directly to `interaction_context` and can only subtract from already-admitted Tools. Exact cross-Run reusable knowledge/procedure admission lives in advanced `ordivon_harness.knowledge_topology`, caller-bound observation-only source recovery composes directly in advanced `ordivon_harness.observation_tool_surface`, and bounded programmatic Tool composition/recovery lives in advanced `ordivon_harness.tool_program*` modules; none is added to the stable package-root facade yet. Observation source recovery verifies exact path/digest and may transport caller-bound owner/authority/version/transport evidence or exact immutable-publication subject projections; it does not establish owner truth. ToolProgram's Provider-visible control action is request-bound execution structure, not a new Runtime Tool or program-level authority owner.

H3 intentionally removed historical package-root aliases, `host_api`, `HarnessRunner`, `HarnessHost`, Assignment/TaskContract objects, cutover APIs and Host source compatibility modules. New code must not depend on them.

## Durable state

Current writers own only independent Harness state: `HarnessRunContract`, Run projection/events, Provider Call records, Tool-step intents/fences/receipts, Run snapshots, Trace, recovery assessment, Run Receipt and CompletionProposal. The former Host-era `NativeRunAbandonment`, `NativeRunDisposition`, `HarnessRunStatus.ABANDONED` and `harness.run-abandoned` application semantics are retired: current recovery records evidence and derives `safeToAbandon`, then the caller either retries/resumes or reconciles remaining UNKNOWN without a second abandonment commit. A retained schema-v1 SQLite `runs.status` CHECK may still contain the unused literal `abandoned`; that physical DDL superset is not a supported writer/decoder contract and is intentionally left unchanged rather than creating two incompatible schema-v1 DDLs.

`AgentRunConclusion` now has one optional `structuredResult` object containing the versioned `ordivon.agent-structured-result` carrier. Absence preserves the exact legacy unstructured serialization and digest. Current writers keep `summary` bounded to 8,000 UTF-8 bytes and bound the carrier value to one MiB. Current readers accept both the dedicated carrier and historical `structured-result-v1` conclusions whose canonical JSON was stored directly in `summary`; no old durable object is silently reinterpreted. The legacy summary encoder now fails closed above 8,000 bytes and directs current callers to the carrier.

Pre-H3 Host-backed state is not a current compatibility obligation. Historical receipts remain evidence of the implementation that produced them; they are not a decoder requirement for H3.

The former `ordivon_harness.tool_semantics` / `NativeToolCatalogSnapshot` line is also retired from current code. An exact current-source and cross-repository consumer census found no imports or callers; its remaining mentions are historical design/closeout documentation. Runtime Tool admission, correlation, idempotency and effect semantics now come from the retained caller/tool contracts and Runtime-facing execution paths rather than a parallel Harness-owned native Tool catalog.

The former Harness-local Finance observe/research Runtime bridge modules are not current compatibility surfaces. Finance owns the current Runtime-domain interface and its semantic operation schemas; current Finance/Workstation composition invokes that owner domain through Runtime directly. Harness retains generic Runtime execution/recovery mechanics rather than shadow Finance-specific grants/parsers. Historical source/evidence references to the retired bridges remain historical evidence.

Current Provider Call writes use schema v4. Schema v3 remains a narrow typed historical reader because the authoritative S0 freeze contains live historical v3 objects. The earlier caller-neutral schema-v2 typed codec is retired: the current estate scan found no v2 object in the S0 freeze and no current Provider head or code consumer requiring it. Older completed experiment roots may still retain immutable v2 CAS bytes and their event references; generic store doctor/events/inspect/status continue to read those Runs without reinterpreting or deleting those historical bytes.

Schema-v1 caller-neutral `HarnessRunContract` keeps one narrow compatibility rule
because it is part of the independent line: budget fields present in the Contract
are exact authority; omitted known fields use the historical defaults; unknown
fields fail closed. `maxConclusionCorrections` is a later known budget field with
historical default 3 when absent. An older Contract that explicitly binds
`maxToolCorrections` does not thereby bind conclusion correction: Tool-call
correction and caller/domain conclusion correction are separate execution
mechanics.

## Upgrade rule

Before upgrading active independent work, inspect nonterminal Runs and unresolved Provider/Tool delivery, back up the Harness root, and prove the candidate can reopen current independent state. Do not reinterpret UNKNOWN or resend an ambiguous effect merely because code changed.

Pre-1.0 breaking changes may deliberately drop unused schemas or APIs. Such deletion must be explicit in the Changelog and current tests/docs must describe only the retained authority.
