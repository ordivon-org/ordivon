# Temporal Nexus acceptance

Date: 2026-09-12

## Standing

**WORKFLOW-BACKED NEXUS E2E VERIFIED; ADOPT ON REAL CROSS-E2E DEMAND.**

Temporal Server 1.31.2 and the installed Temporal Python SDK 1.32.0 can execute a real Nexus service contract on the production cluster. However, the current Python `temporalio.nexus.temporal_operation` API is explicitly documented as experimental/unstable. Nexus is therefore a proven mature-substrate capability, not a mandatory Ordivon semantic waist.

## Proof

An ephemeral Nexus Endpoint `ordivon-operations-nexus-smoke` targeted namespace `default` and task queue `ordivon-operations-nexus-smoke` on `127.0.0.1:17233`.

The proof used:

- a typed `nexusrpc.service` definition;
- a `workflow_run_operation` handler;
- a handler-started durable Temporal Workflow;
- a caller Workflow using `workflow.create_nexus_client`;
- the production PostgreSQL-backed Temporal cluster.

Accepted caller:

- Workflow ID: `nexus-smoke-caller-f97313e3-bbc5-496f-b168-30e86bb71150`;
- Run ID: `01a093f5-aa9c-7a0a-91b9-c022b73e29da`;
- status: `COMPLETED`;
- result: `handled:f97313e3-bbc5-496f-b168-30e86bb71150`.

The caller Event History contains `NexusOperationScheduled`, `NexusOperationStarted`, and `NexusOperationCompleted`, followed by Workflow completion. Visibility independently returned the caller as `Completed`.

The ephemeral Endpoint was deleted after the proof so Operations does not create a fake permanent service contract before a real E2E owns one.

## Adoption rule

Use Nexus when two Temporal applications need a stable reusable durable operation boundary and an actual owner can name the service and operation semantics. Do not introduce a generic `Ordivon Nexus Gateway`, do not route ordinary Runtime execution through Nexus, and do not replace CloudEvents/AsyncAPI for event publication with request/operation semantics.
