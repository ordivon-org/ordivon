# Architecture Overview

This document remains as a compatibility entrypoint for older references. The active architecture description now lives in:

- [architecture-baseline](./architecture-baseline.md)
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
