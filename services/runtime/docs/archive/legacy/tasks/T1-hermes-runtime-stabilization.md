# Hermes Runtime Stabilization

## Priority Test
This task is worth doing now because it satisfies at least one:
- [x] Main-chain critical
- [x] Flywheel critical
- [x] Anti-pollution critical
- [x] Reliability critical
- [x] Unlocks next task

This task should be delayed if:
- [ ] It only improves naming
- [ ] It only improves aesthetics
- [ ] It does not create reusable asset
- [ ] It does not clarify ownership
- [ ] It can be safely postponed without polluting future work

## 1. Task Identity
- Layer: Intelligence
- Type: Reliability
- Priority: P0
- Status: Done
- Owner:
- Date: 2026-04-19
- Related Docs:
  - [Architecture Baseline](../architecture/architecture-baseline.md)
  - [Layer Module Inventory](../architecture/layer-module-inventory.md)
  - [Hermes Model Layer Integration](../architecture/hermes-model-layer-integration.md)
- Related Files:
  - `intelligence/runtime/hermes_client.py`
  - `intelligence/providers/hermes_agent_provider.py`
  - `intelligence/tasks/hermes.py`
  - `apps/api/app/api/v1/health.py`
  - `projects/hermes-runtime/hermes_cli/pfios_bridge.py`

## 2. Purpose
- Why now: analyze must remain on a real Hermes runtime path or the AI sample chain collapses back to stub quality.
- Problem being solved: Hermes integration exists, but failure handling, runtime trace clarity, and operational stability are still thin.
- If not done, what breaks or stays fake: analyze may technically use Hermes but still behave like an unstable or weakly observable adapter.
- What part of the system becomes stronger: Intelligence runtime reliability and main-chain trustworthiness.

## 3. Scope
### In Scope
- harden Hermes analyze runtime path
- improve failure-path behavior and operational diagnostics
- make runtime status and model/provider visibility more reliable

### Out of Scope
- do not add new AI task types
- do not add execution tool calling
- do not refactor the whole intelligence directory

## 4. Main Object
- Primary object: Runtime Adapter
- Upstream dependency: Analyze request
- Downstream effect: Structured analysis and recommendation creation
- Source of truth: State
- Whether side-effect exists: Yes
  The task affects runtime calls, audit lineage, and persisted `AgentAction`.

## 5. Loop Position
- Primary loop: Analyze Chain
- Step in loop: runtime execution
- What comes before: capability request and workflow context assembly
- What comes after: governance evaluation and recommendation generation
- Whether this creates reusable history: Yes

## 6. Expected Asset
- Main asset produced: Runtime Adapter
- Secondary assets:
  - Diagnostic Signal
  - Audit Trail
  - Runtime health behavior
- Where the asset will live:
  - `intelligence/`
  - `apps/api/app/api/v1/health.py`
  - Hermes bridge files
- How it will be reused later: as the stable runtime foundation for additional AI task types.

## 7. Design Decision
- Chosen approach: keep Hermes behind bounded task contracts and stabilize that boundary instead of letting runtime details leak upward.
- Alternatives rejected:
  - direct free-form runtime calls from workflow steps
  - mixing execution/tool behavior into Hermes analyze path
- Why this approach is smallest viable move: it strengthens the existing real path without expanding system scope.
- Boundary to preserve: Intelligence owns runtime execution, not business truth and not execution side effects.

## 8. Implementation Plan
1. audit Hermes client timeout, error mapping, and retry policy
2. harden health and runtime status reporting
3. improve analyze-path runtime metadata and run trace clarity
4. add verification for degraded and unavailable cases

## 9. Verification
- Unit tests: Hermes client timeout/error mapping and provider behavior
- Integration tests: analyze path against Hermes bridge or mocked runtime
- Manual checks: `/api/v1/health`, `/api/v1/analyze-and-suggest`
- Failure mode checks: Hermes unavailable, timeout, malformed response
- Truthfulness checks: no fake success on runtime failure

## 10. Done Criteria
- [x] analyze path remains Hermes-backed under normal operation
- [x] runtime failures surface as real degraded or failed states
- [x] runtime provider/model and action lineage remain visible
- [x] at least one integration path validates Hermes unavailable behavior

## 11. Risk Notes
- Main risk: over-stabilizing the bridge instead of the real bounded runtime path
- Drift risk: Hermes client becoming a hidden universal system entrypoint
- What this task might accidentally absorb: task taxonomy expansion
- Rollback plan: keep the current adapter shape and limit changes to failure handling and observability

## 12. Follow-up
- Immediate next task: [T2 Intelligence IO Contract](./T2-intelligence-io-contract.md)
- Deferred work: multi-task runtime expansion
- What this unlocks: reliable AI task execution lineage
