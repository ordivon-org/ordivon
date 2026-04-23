# Architecture Overview

This document remains as a compatibility entrypoint for older references. The active architecture description now lives in:

- [architecture-baseline](./architecture-baseline.md)
- [core-pack-adapter-baseline](./core-pack-adapter-baseline.md)
- [current-code-classification-map-v1](./current-code-classification-map-v1.md)
- [finance-pack-v1-definition](./finance-pack-v1-definition.md)
- [core-primitives-spec-v1](./core-primitives-spec-v1.md)
- [adapter-boundary-spec-v1](./adapter-boundary-spec-v1.md)
- [aegisos-working-identity](./aegisos-working-identity.md)
- [aegisos-design-doctrine](./aegisos-design-doctrine.md)
- [aegisos-overview](./aegisos-overview.md)
- [aegisos-layer-roadmap](./aegisos-layer-roadmap.md)
- [../product/aegisos-mvp-brief](../product/aegisos-mvp-brief.md)
- [../product/aegisos-mvp-execution-checklist](../product/aegisos-mvp-execution-checklist.md)
- [aegisos-phase-0-core-primitives-batch](./aegisos-phase-0-core-primitives-batch.md)
- [aegisos-phase-1-core-load-bearing-batch](./aegisos-phase-1-core-load-bearing-batch.md)
- [aegisos-next-round-execution-plan](./aegisos-next-round-execution-plan.md)
- [system-overview](./system-overview.md)
- [architecture-diagram](./architecture-diagram.md)
- [layer-definition](./layer-definition.md)
- [domain-map](./domain-map.md)
- [modularity-audit-2026-04-18](./modularity-audit-2026-04-18.md)
- [runtime-flow](./runtime-flow.md)
- [migration-map](./migration-map.md)
- [boundary-map](./boundary-map.md)
- [step-1-foundation-report-2026-04-18](./step-1-foundation-report-2026-04-18.md)
- [step-2-boundary-prep-2026-04-18](./step-2-boundary-prep-2026-04-18.md)
- [step-2-boundary-report-2026-04-18](./step-2-boundary-report-2026-04-18.md)
- [step-3-capability-prep-2026-04-18](./step-3-capability-prep-2026-04-18.md)

## Current Architectural Direction

The repository is now governed by the canonical baseline in [architecture-baseline](./architecture-baseline.md).

The repository is moving from a package-centric prototype layout toward a boundary-first root layout governed by nine canonical responsibility surfaces:

- `apps/` for the Experience Layer
- `capabilities/` and `domains/` for the Capability Layer
- `orchestrator/` for workflow control
- `governance/` for risk and policy enforcement
- `intelligence/` for model-facing capabilities
- `execution/`, `skills/`, and `tools/` for the Execution Layer
- `state/` for the State surface
- `knowledge/` for the Knowledge surface
- `infra/` for the Infrastructure Layer

Existing code under `pfios/` remains valid during migration, but new work should follow the target root structure unless there is a clear compatibility reason not to.

The next platformization step is defined in [core-pack-adapter-baseline](./core-pack-adapter-baseline.md), which distinguishes stable operating-system primitives from domain packs and replaceable adapters.

The first repo-level classification pass now lives in [current-code-classification-map-v1](./current-code-classification-map-v1.md).

The current domain-pack identity is now frozen in [finance-pack-v1-definition](./finance-pack-v1-definition.md).

The first primitive freeze and adapter-boundary rules now live in:

- [core-primitives-spec-v1](./core-primitives-spec-v1.md)
- [adapter-boundary-spec-v1](./adapter-boundary-spec-v1.md)

The current working naming and corrected next-round plan now live in:

- [aegisos-working-identity](./aegisos-working-identity.md)
- [aegisos-design-doctrine](./aegisos-design-doctrine.md)
- [aegisos-overview](./aegisos-overview.md)
- [aegisos-layer-roadmap](./aegisos-layer-roadmap.md)
- [../product/aegisos-mvp-brief](../product/aegisos-mvp-brief.md)
- [../product/aegisos-mvp-execution-checklist](../product/aegisos-mvp-execution-checklist.md)
- [aegisos-phase-0-core-primitives-batch](./aegisos-phase-0-core-primitives-batch.md)
- [aegisos-phase-1-core-load-bearing-batch](./aegisos-phase-1-core-load-bearing-batch.md)
- [aegisos-next-round-execution-plan](./aegisos-next-round-execution-plan.md)
