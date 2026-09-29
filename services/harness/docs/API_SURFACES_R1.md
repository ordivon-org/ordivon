---
schema_version: 1
id: harness.api-surfaces-r1
title: Harness API Surfaces R1
type: architecture
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - builder
  - integrator
updated: 2026-09-23
summary: Classifies the existing stable Host-free exports without removing compatibility or promoting low-level mechanisms into the ordinary product path.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
---
# Harness API Surfaces R1

The current 47-symbol `ordivon_harness.api` set remains compatibility-stable. R1 classifies
that surface so a future product façade can become smaller without a breaking kernel rewrite.

## Application surface

These are reasonable direct building blocks for an application that already owns exact Run
inputs:

- `HarnessAgentRun`
- `HarnessAgentExecution`
- `HarnessAgentRunCompositionError`
- `HarnessRunContract`
- `RunBudget`
- `RunStopCode`
- `HarnessPrivacyPolicy`
- `IndependentCompletionProposal`
- `IndependentHarnessRunReceipt`
- `STRUCTURED_COMPLETION_MODE`
- `decode_structured_completion_result`
- `structured_completion_contract_digest`
- `structured_completion_result_schema`

This is not yet the intended end-user Agent product façade.

## Integration surface

These are explicit integration seams for callers that already selected Providers, Skills,
Tools or Runtime bindings:

- `HarnessToolBridgeFactory`
- `PluginGatewayExecutionBridgeFactory`
- `PluginGatewayExecutionGrant`
- `AgentPluginComposition`
- `AgentPluginCompositionError`
- `OfficialMcpClient`
- `PluginMcpObservationBridge`
- `HarnessCognitionProfile`
- `HarnessCognitionSeed`
- `HarnessCognitionSeedSource`
- `HarnessWorkingViewSource`
- `AgentTurnAdapter`
- `AgentTurnRequest`
- `AgentTurnResult`
- `DeepSeekSettings`
- `DeepSeekTurnAdapter`
- `HarnessBoundReference`
- `HarnessExecutionBinding`
- `AgentToolDefinition`
- `DomainToolBridge`
- `DomainToolCatalog`
- `DomainToolLoopPlan`
- `DomainToolLoopRunner`
- `HarnessToolObservation`
- `HarnessRuntimeClient`
- `HarnessRuntimeClientError`
- `HarnessRuntimeErrorDetail`
- `HarnessRuntimeToolRejected`

## Low-level compatibility/constants

- `ToolBridgeError`
- `ToolBridgeErrorKind`
- `INDEPENDENT_SEARCH_TOOL_GRANT_DIGEST`
- `INDEPENDENT_SEARCH_TOOL_SURFACE_DIGEST`
- `NO_TOOL_AGENT_GRANT_DIGEST`
- `NO_TOOL_AGENT_SURFACE_DIGEST`

## Migration law

Classification changes no authority and removes no export. A later product façade may depend
on these public contracts, but must not duplicate their truth or silently reinterpret their
digests, grants, recovery semantics or completion boundaries.
