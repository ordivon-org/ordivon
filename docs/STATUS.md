---
schema_version: 1
id: harness.status
title: Harness Status
type: status
profile: organization
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - user
  - builder
  - operator
  - agent
updated: 2026-08-24
summary: Current maturity claim for Harness as an independent durable cognitive execution substrate, with supported cognition, Provider and Tool continuity, composition, verification, and known limits.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
related:
  - harness.start
  - harness.architecture
  - harness.compatibility
  - harness.verification
---
# Status

## Current state

Ordivon Harness is an independent caller-neutral **durable cognitive execution substrate for bounded Agent Runs**. The Harness SQLite Journal/CAS is the current Run writer. The supported CLI authority is the independent Harness path; the former Host-backed Store/Runner/cutover path was removed.

This page states current maturity. It does not replay the research sequence that produced it. Exact experiments and receipts remain available through the linked canonical research documents and [`../evidence/index.json`](../evidence/index.json).

## Operational surface

### Run authority and continuity

- `HarnessRunContract` binds one immutable attempt to caller/objective/context, Provider/Adapter/model, Tool catalog/grants, budget, privacy, completion contract and correlation identity.
- SQLite Journal/CAS owns durable Run events, Provider Calls, Tool intents/receipts, leases, revisions, snapshots, recovery evidence and retained objects.
- Provider and Tool response loss is recovered from exact durable identity. UNKNOWN is not silently converted into success, failure, or safe redispatch.
- Run Receipt and `CompletionProposal` remain bounded-Run evidence for the caller/domain; they are not final Task/domain acceptance.

### Agent cognition

- Canonical Run history and model-visible cognition are separate.
- Durable cognition is Agent-selected through exact WorkingSet/WorkingView state; Harness does not rank or summarize sources for the Agent.
- Caller ingress is interaction cognition. The Agent may explicitly promote exact admitted caller bytes into durable cognition when that capability is present.
- Provider-authored Tool exchanges are attempt-local cognition: they survive recovery inside the attempt and disappear when a successor cognition attempt commits.
- Bounded historical recall returns exact earlier committed WorkingSet identities/pins, not semantic search results.
- Advanced cross-Run reuse accepts caller/application-selected, externally owned exact knowledge/procedure references; Harness verifies the resolved source identity/digest and compiles it into the existing cognition-seed path. Presence never implies current cognition.
- Current WorkingSet pins are addressable so an Agent can retain/drop/reselect exact sources without guessing hidden identities.

### Per-turn action authority

- `AgentTurnRequest.tools` carries exact Runtime/World Tool actions admitted now.
- provider-neutral Harness capabilities carry currently admitted conclusion/cognition actions and the advanced opt-in ToolProgram composition action.
- ToolProgram is a Harness-native mechanical action, not a Runtime Tool: it may name only the exact `AgentTurnRequest.tools` currently admitted, every inner step consumes one existing physical Tool budget unit, and UNKNOWN stops the program before later effects.
- installed mechanisms do not automatically appear as current capability; dynamic facts such as caller-ingress addressability can add or remove one action from the next request.
- Provider adapters project the request-bound surface but do not own semantic action policy.

### Supported composition

- `HarnessAgentRun` is the recommended Python state-root execution handle for normal create/open/run/resume composition.
- Capability truth has three explicit stages: package-installed mechanisms, immutable Run-admitted Contract/Binding authority, and exact turn-admitted `AgentTurnRequest` actions. Earlier stages never imply later stages.
- the former aggregate installed-capability catalog and workbench read model are retired; supported execution profiles expose exact source-owned digests directly, durable `inspect` is the single retained-state view, and in-process `explain()` reports only the composition it can validate.
- the former task-conditioned lexical capability-discovery/descriptor layer is retired; Harness keeps no generic capability search/ranking ontology.
- the experimental generic InteractionContext/InteractionAffordance compiler is retired. Current application/domain code branches directly on owner-native state; the existing turn projection remains the only generic mechanism for subtracting Provider-visible Tools from an already-admitted surface.
- preregistered fresh-Agent/currentness ablations remain historical evidence only and no longer justify a Harness-owned standing/affordance carrier.
- `HarnessAgentRun.explain()` projects validated process-local composition while reporting Provider/Runtime liveness as not probed; durable CLI `explain` projects only reconstructable Journal/CAS facts and leaves unavailable process-local facts unknown.
- the zero-current-consumer specialized `observation_tool_surface` wrapper is retired. Observation-only `search_workspace` / `workspace.read` lowering, exact Execution Binding references and digest fencing remain in the core Runtime bridge; source selection, owner/currentness claims and research-publication projection belong to the caller/domain instead of Harness.
- caller-owned Adapter factories keep Provider choice outside Harness policy.
- Tool-bearing applications provide a `HarnessRuntimeClient`; the primary CLI does not invent Runtime authority.
- structured completion binds caller-defined result shape into the Run Contract. Provider results use a versioned one-MiB-bounded terminal carrier instead of the 8,000-byte human/control summary; legacy summary-encoded results remain readable. Policy-absent v1 remains provider-constrained but not locally schema-verified; opt-in `local-json-schema-draft-2020-12-profile-v1` performs fail-closed local structural validation before candidate completion, while semantic/evidence admission remains caller/domain authority.
- the contracted current core does not expose a generic `ProviderToolContinuation`; Provider-specific opaque continuation remains integration-local unless fresh direct pressure earns a bounded Harness surface.

### Exact Run authority

The experimental LoopDriver/morphology selection layer is retired. Current cross-repository DomainToolLoopRunner consumers all use the ordinary sequential loop, while explicit deliberation remains a separate composition rather than a core scheduling mode.

The current product begins at one exact caller-authored `HarnessRunContract`. The former Mandate/Profile/Strategy/Consumption/CompiledAttempt layer is retired along with the generic Strategy-selection subsystem. Cross-Run evidence aggregation, aggregate resource allocation, profile discovery, successor selection and retry policy remain caller/domain/workflow or mature-orchestrator responsibilities.

## Retained laws from research

The research programme is large; the current product result is smaller.

The following conclusions survive into current behavior:

- **history is not cognition** — exact recovery history need not be replayed into every model turn;
- **compact cognition is not source truth** — terminal causal claims still require exact admitted evidence/verification appropriate to the caller;
- **cognition admission and effect admission are distinct** — invalid physical action does not require erasing an otherwise valid Agent cognition update;
- **objective completion is rooted** — a true subclaim cannot silently replace the caller-bound Objective;
- **semantic correctness is not authority** — a model can guess correctly without having evidence sufficient to authorize mutation or completion;
- **Tool-surface optimization is not semantic policy** — pruning that can hide the correct action requires Agent-owned recovery or it changes meaning;
- **Provider wire state may exceed semantic messages** — current Harness does not turn that fact into a generic opaque-continuation authority; Provider-local continuation remains outside the contracted core unless direct evidence earns a bounded surface;
- **deliberation-before-Tool composition is not automatically the recommended core** — it remains an advanced/internal composition until independent consumer pressure justifies promotion;
- **no generic Memory/RAG/Skill or reusable-reference topology subsystem was earned** — external owners verify/select exact `HarnessWorkingViewSource` values and pass them through the existing cognition-seed path; semantic evaluation, promotion, canonical identity and currentness remain external.

The exact P/R/H/X experiment chronology remains evidence, not a prerequisite for using Harness.

## Removed

The old Host-backed Runner, TaskContract/Assignment persistence, Host compatibility package/dependency/extra, Host CLI namespace, cutover/rollback machinery and Host-coupled execution drivers are not supported current paths and have no compatibility aliases. The unreachable Host-era abandonment/disposition layer is also retired: current independent recovery persists `NativeRunRecoveryAssessment` and derives whether retry/resume is safe, but does not create a separate `NativeRunAbandonment`, `ABANDONED` Run state, or `harness.run-abandoned` event.

## Known limits

- Harness is pre-1.0; public schemas and advanced exports may still change under the documented compatibility policy.
- The primary CLI does not create Tool-bearing Runtime clients.
- Harness begins at one exact `HarnessRunContract`; higher-level multi-Run orchestration/resource allocation and generic Strategy selection/evidence aggregation remain outside Harness.
- Harness intentionally has no generic capability discovery/ranking service. Large heterogeneous capability ecologies should use their actual owner/tool substrate discovery surfaces; Harness receives exact caller/owner facts only where needed for one Run/turn.
- Fresh-Agent V1/V2 did not earn a Harness semantic retriever. Reopen retrieval research only when a real owner substrate produces a discriminating discovery failure; current Harness pressure is compact consumption of already-current owner facts.
- Source/tool discovery and ranking, large-WorkingSet inspection strategy, reusable-source repository ownership, procedure evaluation and canonical promotion remain Agent/application/Host/domain or mature-substrate questions. Already-selected cross-Run sources enter only through the normal exact cognition-seed path.
- `CompletionProposal` cannot prove caller/domain completion.
- structured output constrains Provider shape but does not make Harness a domain or JSON-Schema truth authority.
- Provider/Tool UNKNOWN may require external reconciliation by the owner that can observe the consequence.
- Provider-specific opaque continuation is not a current generic Harness surface; integrations that require it must preserve their own Provider-local authority without assuming metadata-only Harness continuity can recover private transcript state.
- cache hit rate, prompt locality and Provider-specific request efficiency are measured properties rather than correctness thresholds.

## Verification

Current code/test/evidence binding is defined by [`VERIFICATION.md`](VERIFICATION.md). Exact source, deterministic tests and digest-bound receipts outrank historical summaries.

Repository acceptance includes the main deterministic suite, isolated Ruff, documentation/dependency checks, wheel verification, privacy/recovery tests and the dedicated stress/Provider acceptance appropriate to the changed boundary. Exact counts are intentionally not duplicated here because they change faster than the semantic status.

## Operator check

```bash
ordivon-harness --state-root /var/lib/ordivon/harness status HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness inspect HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness doctor
```

For operation/recovery detail see [`OPERATIONS.md`](OPERATIONS.md). For public API and upgrade boundaries see [`COMPATIBILITY.md`](COMPATIBILITY.md). For exact document ownership see [`authority.md`](authority.md).
