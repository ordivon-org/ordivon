# Task Cards

Use this directory for active execution-ready task cards.

These task cards should follow:

- [Task Template System](../product/task-template-system.md)
- [Module Definition Template v2](../product/module-definition-template-v2.md)
- [Architecture Baseline](../architecture/architecture-baseline.md)
- [AegisOS Design Doctrine](../architecture/aegisos-design-doctrine.md)
- [Layer Module Inventory](../architecture/layer-module-inventory.md)
- [Status Sync Workflow](../workflows/status-sync-workflow.md)
- [AI Financial Assistant Roadmap](../product/ai-financial-assistant-roadmap.md)

## Completed Foundation Cards

1. [T1 Hermes Runtime Stabilization](./T1-hermes-runtime-stabilization.md)
2. [T2 Intelligence IO Contract](./T2-intelligence-io-contract.md)
3. [T3 Core State Truth Inventory](./T3-core-state-truth-inventory.md)
4. [T4 Side-Effect Boundary Expansion](./T4-side-effect-boundary-expansion.md)
5. [T5 Execution Action Catalog](./T5-execution-action-catalog.md)
6. [T6 Intelligence Run](./T6-intelligence-run.md)
7. [T7 Execution Request / Receipt](./T7-execution-request-receipt.md)
8. [T8 State Transition](./T8-state-transition.md)
9. [T9 Orchestration Run Lineage](./T9-orchestration-run-lineage.md)

## Latest Completed Strengthening

1. State Lineage / Trace
2. Governance Decision Language
3. Execution Request / Receipt (second family)
4. Knowledge Definition
5. State Outcome Backfill
6. Knowledge Lesson Extraction
7. Orchestration Retry / Fallback / Compensation
8. Capability API Boundary Cleanup
9. Knowledge Feedback
10. Experience Trace / Outcome / Knowledge Surface
11. Execution Additional Action Families / Adapter Consolidation
12. Governance Decision Language Centralization
13. Execution Review Family Execution
14. Knowledge Feedback Consumption into Governance
15. Experience Review / Outcome / Feedback Surface Extension
16. State Trace Graph Deepening
17. Execution Review Submit Execution
18. Execution Validation Family Execution
19. Knowledge Feedback Consumption into Intelligence
20. Governance Policy Source of Truth
21. Experience Trace Detail Surface
22. Experience Trust-tier / Semantic Discipline
23. Knowledge Feedback Packet Objectization
24. Execution Success Audit Ownership Consolidation
25. Orchestration Recovery Policy Object
26. Experience Review Detail Surface
27. State Trace Relation Hardening
28. Knowledge Retrieval / Recurring Issue Aggregation
29. Infrastructure Health / Monitoring
30. Phase 0 Core Primitive Freeze
31. Phase 1 Core Load-Bearing Batch
32. Finance Pack Extraction Planning
33. Hermes Runtime Adapter Extraction
34. Orchestration HandoffArtifact
35. Orchestration WakeResume / Fallback
36. Infrastructure Scheduler
37. Infrastructure Monitoring History / Runbook Discipline
38. Experience Global Trust-tier Rollout
39. Experience ReviewConsole + Tabbed Workspace
40. Finance Pack Staged Extraction
41. Hermes Runtime Provider Cleanup
42. Scheduler Persistence / Trigger Orchestration
43. Monitoring History Depth / Ops Refinement
44. Workspace Refinement Beyond Review Console
45. Finance Pack Capability Defaults Extraction
46. Finance Pack Policy / Tool Ownership
47. Hermes Runtime Shim Reduction
48. Scheduler Backend Refinement
49. Monitoring Ops History Endpoint
50. Console Workspace Shared Tabs
51. Finance Pack Analyze Profile Ownership
52. Hermes Provider Alias Cleanup
53. Broader Console Workspace Behavior
54. Finance Pack Frontend Analyze Surface Extraction
55. MVP Gold Path / Homepage-Analyze-Reviews Role Split
56. MVP Gold Path Handoff Closure
57. MVP Route Handoff Validation
58. MVP Presentation and Delivery Closure

## Current Priority Batch

1. Phase 4 Batch 0 | Personal control loop rebaseline
2. Phase 4 Batch 1 | Finance-seeded decision intake
3. Phase 4 Batch 2 | Governance pre-action gate
4. Phase 4 Batch 3 | Action-plan receipt
5. Phase 4 Batch 4 | Outcome capture + review depth
6. Phase 4 Batch 5 | Advisory knowledge + candidate-rule follow-through

## Selected Next Module

- `Phase 4 Batch 1 | Finance-seeded decision intake`

Latest completed module card:

- [2026-04-22-finance-pack-frontend-analyze-surface-extraction](../../knowledge/wiki/architecture/module-cards/2026-04-22-finance-pack-frontend-analyze-surface-extraction.md)

## Execution Discipline

Every new module should follow this order:

1. choose the doctrine and layer first
2. classify the module as `Core / Pack / Adapter`
3. write the design card into wiki using `Module Definition Template v2`
4. implement the smallest real version
5. add tests
6. run checks
7. write module completion report
8. sync status docs

Status sync is mandatory after each completed module.

Required docs:

- `knowledge/wiki/architecture/module-cards/`
- `docs/architecture/layer-module-inventory.md`
- latest `docs/architecture/current-state-report-YYYY-MM-DD.md`
- `docs/tasks/README.md`

See:

- [Status Sync Workflow](../workflows/status-sync-workflow.md)

## Phase Batch Note

The repository has now completed:

- `Phase 0 | Freeze Core Primitives`
- `Phase 1 | Core Load-Bearing Batch`

See:

- [AegisOS Phase 0 Core Primitive Freeze](../architecture/aegisos-phase-0-core-primitives-batch.md)
- [AegisOS Phase 1 Core Load-Bearing Batch](../architecture/aegisos-phase-1-core-load-bearing-batch.md)
- [AegisOS Next Batch Serial Modules 2026-04-22](../architecture/aegisos-next-batch-serial-modules-2026-04-22.md)

The next implementation wave should now be tracked as post-serial-batch extraction/refinement rather than reopening Phase 0, Phase 1, or this completed 8-module wave.

Current refinement note:

- `Audit Event Strictification` has started landing as a core governance/state hardening step. New audit writes now normalize into a structured envelope, while legacy rows are marked honestly instead of being inferred back into modern semantics.
- Current MVP-closing work is now focused on:
  - page role split finalization
  - gold-path handoff closure
  - user-view route validation
  - MVP presentation and delivery closure
- Current MVP delivery note:
  - CI now includes an `mvp-e2e` browser smoke path and a `Delivery` workflow bundles the current MVP docs/config surface after validated main-branch CI.

## Phase 4 Rebaseline

Phase 4 now reads as:

- not a finance pivot
- a finance-seeded pressure test for the general control loop
- no repo-wide Ordivon rename
- no `/control` page
- no broker execution
- no multi-agent
- no candidate-rule-to-policy automation

Batch 1 scope is intentionally narrow:

- structured intake only
- finance-pack-owned validation
- persisted intake truth
- `/analyze` intake panel

Deferred beyond Batch 1:

- governance
- execution receipt
- outcome
- review checklist
- knowledge feedback

## Daily Planning

- [Today Board Template](./today-board-template.md)
