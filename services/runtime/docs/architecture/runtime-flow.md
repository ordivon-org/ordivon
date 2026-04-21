# Runtime Flow

## Main Path

1. `apps/` receives a request or scheduled trigger.
2. `capabilities/` resolves the request into a product capability contract.
3. `orchestrator/router` selects a workflow.
4. `orchestrator/context` assembles state and knowledge context.
5. `orchestrator/dispatch` selects models, skills, and tools.
6. `intelligence/` produces structured outputs.
7. `governance/guards` and `governance/risk_engine` evaluate policy boundaries.
8. `execution/` runs the required skills and tools.
9. `domains/` interpret approved outputs in business terms.
10. `state/` records truth, snapshots, and task progress.
11. `knowledge/ingestion` stores reusable learning when appropriate.
12. `tools/notifications` and `tools/reports` publish outputs back to the experience layer.

## Design Constraint

The flow is sequential in responsibility, not necessarily in runtime implementation. Individual steps can be retried or skipped, but their boundaries must remain visible.
