# Intelligence IO Contract

## Priority Test
This task is worth doing now because it satisfies at least one:
- [x] Main-chain critical
- [x] Flywheel critical
- [x] Anti-pollution critical
- [x] Unlocks next task

This task should be delayed if:
- [ ] It only improves naming
- [ ] It only improves aesthetics
- [ ] It does not create reusable asset
- [ ] It does not clarify ownership
- [ ] It can be safely postponed without polluting future work

## 1. Task Identity
- Layer: Intelligence
- Type: Boundary
- Priority: P0
- Status: Done
- Owner:
- Date: 2026-04-19
- Related Docs:
  - [Architecture Baseline](../architecture/architecture-baseline.md)
  - [Hermes Model Layer Integration](../architecture/hermes-model-layer-integration.md)
- Related Files:
  - `intelligence/tasks/contracts.py`
  - `intelligence/tasks/hermes.py`
  - `intelligence/providers/hermes_agent_provider.py`
  - `domains/ai_actions/`
  - `orchestrator/workflows/analyze.py`

## 2. Purpose
- Why now: if intelligence input/output remains partially implicit, future AI tasks will immediately reintroduce boundary pollution.
- Problem being solved: analyze has structured IO, but not yet a stable repository-wide intelligence task contract.
- If not done, what breaks or stays fake: AI task payloads remain ad hoc and harder to validate, trace, and reuse.
- What part of the system becomes stronger: Intelligence task discipline.

## 3. Scope
### In Scope
- define stable request/output structure for intelligence tasks
- normalize shared metadata fields
- make runtime consumers use explicit structures

### Out of Scope
- do not implement every future task
- do not build evaluation dashboards
- do not redesign capability contracts

## 4. Main Object
- Primary object: AI Task
- Upstream dependency: workflow context
- Downstream effect: runtime invocation, state lineage, future task reuse
- Source of truth: State
- Whether side-effect exists: No

## 5. Loop Position
- Primary loop: Analyze Chain
- Step in loop: task contract handoff
- What comes before: context assembly
- What comes after: runtime execution and structured result consumption
- Whether this creates reusable history: Yes

## 6. Expected Asset
- Main asset produced: Contract
- Secondary assets:
  - Runtime Adapter
  - Intelligence Run Record shape
- Where the asset will live:
  - `intelligence/tasks/`
  - `intelligence/contracts/` or equivalent bounded contract files
- How it will be reused later: recommendation, review, report, and lesson task families will share the same contract model.

## 7. Design Decision
- Chosen approach: stabilize a bounded task contract rather than letting runtime payloads remain free-form dictionaries.
- Alternatives rejected:
  - leaving analyze as a special-case payload
  - pushing contract responsibility into workflows
- Why this approach is smallest viable move: it strengthens one real task and unlocks the next AI tasks without broad refactor.
- Boundary to preserve: workflows assemble context, intelligence defines AI task IO.

## 8. Implementation Plan
1. define canonical intelligence task input fields
2. define canonical output and metadata fields
3. align Hermes task builder and normalizer to those contracts
4. ensure downstream workflow/state consumers rely on explicit structure

## 9. Verification
- Unit tests: contract builder and normalizer behavior
- Integration tests: analyze path consumes only supported fields
- Manual checks: inspect returned metadata and state lineage
- Failure mode checks: missing required fields and malformed output
- Truthfulness checks: no hidden fallback fields

## 10. Done Criteria
- [x] task request and result structure are explicit and reusable
- [x] analyze path no longer depends on implicit runtime-only keys
- [x] `AgentAction` consumption uses named structured fields
- [x] at least one test covers malformed runtime payload behavior

## 11. Risk Notes
- Main risk: over-designing contracts before second task type exists
- Drift risk: contracts becoming another generic middle layer
- What this task might accidentally absorb: full AI task taxonomy expansion
- Rollback plan: keep the current analyze structure and refactor only into the smallest explicit schema set

## 12. Follow-up
- Immediate next task: `Intelligence Run` module work
- Deferred work: multi-task catalog expansion
- What this unlocks: structured AI task taxonomy
