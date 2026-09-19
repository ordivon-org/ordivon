# Execution Fabric Workflow R1

Status: **RETIRED / SUPERSEDED 2026-09-19**

The former Runtime-SPI `WorkflowPlan`, `WorkflowStep`, compensation model, and dry-run
workflow binding resolver were removed.

Reason: these contracts duplicated mature orchestration semantics while owning no Runtime
execution truth. Durable process orchestration belongs to Temporal (or a standards-native
BPMN/DMN owner where that is the real requirement); compensation belongs to the
effect/domain owner using Saga/compensating-transaction semantics.

Runtime retains only the provider/resource/capability descriptions required at its physical
execution boundary. Runtime Job/Attempt truth remains independent of any workflow engine.

Historical forcing functions such as WSL control-plane recovery and D-drive VHD compaction
must be expressed by the owning Workstation/Operations orchestrator. Runtime participates
only through explicit capabilities and returns Runtime-owned evidence.

See `docs/STANDARDS_FIRST_W2_BOUNDARY_R1.md`.
