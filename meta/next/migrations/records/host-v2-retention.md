# Host v2 retention disposition

- Source: `/root/projects/ordivon-host-v2`
- Observed revision: `756a38412a19ff1dc51d98e4857e10d0426f1db2`
- Assessed: 2026-09-14
- Disposition: **RETAIN_MINIMAL_ACTIVE**

## Evidence

On 2026-09-14 the local Host v2 service was `loaded`, `active`, and `enabled`; source main was tracked-clean. The repository's pytest suite completed successfully with its explicitly skipped integration/external cases. The remote MCP exposure separately returned HTTP 421 due an invalid Host-header path; that is an exposure/edge issue and is not evidence that the local Host v2 service or data model is unhealthy.

## Why it stays

Host v2 is now small enough that replacing it with a materially heavier work-management product would increase total system complexity without a demonstrated workload benefit. It provides a bounded durable work/continuity surface and does not need to become a universal Task ontology, scheduler, Runtime proxy, agent framework, monitoring platform or domain truth owner.

The architectural goal is therefore contraction, not deletion for its own sake. Host v1 and broad Host/Board ownership remain retired; Host v2 survives only within its narrow proven utility.

## Boundaries

- physical Workspace/Job/Attempt/process truth -> Runtime;
- bounded Agent Run/provider cognition -> Harness/provider-native agent systems;
- macro durable workflows -> Temporal when required;
- API/SaaS integration -> n8n;
- operational telemetry -> Operations observability stack;
- scientific/business/security/game/etc. semantic truth -> domain owner;
- heavyweight project/work management -> Plane/OpenProject/other mature provider only when a real workload justifies the cost.

Host v2 must not re-expand to absorb those responsibilities.

## Revisit trigger

Revisit this retention only when one of the following is observed:

1. Host v2 maintenance/security cost becomes materially higher than a proven substitute;
2. repeated workloads require collaboration/project-management behavior that Host v2 should not implement;
3. a mature provider proves equivalent continuity behavior with lower total operational complexity;
4. there are no remaining real Host v2 consumers.

Until then, migration to Plane/MAF is not architectural debt.
