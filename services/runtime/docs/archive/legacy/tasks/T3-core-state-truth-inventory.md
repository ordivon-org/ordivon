# Core State Truth Inventory

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
- Layer: State
- Type: Closure
- Priority: P0
- Status: Done
- Owner:
- Date: 2026-04-19
- Related Docs:
  - [Architecture Baseline](../architecture/architecture-baseline.md)
  - [Layer Module Inventory](../architecture/layer-module-inventory.md)
  - [State Truth Inventory](../architecture/state-truth-inventory.md)
- Related Files:
  - `domains/research/`
  - `domains/strategy/`
  - `domains/journal/`
  - `domains/ai_actions/`
  - `governance/audit/`
  - `state/`

## 2. Purpose
- Why now: without an explicit state truth inventory, the main chain will continue to mix canonical fact with convenience projections and partial records.
- Problem being solved: the system already has many fact objects, but they are not yet documented and reviewed as one truth set.
- If not done, what breaks or stays fake: future run records, receipts, outcomes, and knowledge extraction will attach to an unstable fact map.
- What part of the system becomes stronger: State clarity and object ownership.

## 3. Scope
### In Scope
- enumerate current canonical fact objects
- document ownership and source-of-truth boundaries
- identify missing fact objects for workflow run, intelligence run, and execution receipt

### Out of Scope
- do not fully implement all missing objects
- do not redesign UI projections
- do not move every file immediately

## 4. Main Object
- Primary object: State Record
- Upstream dependency: current object model and repositories
- Downstream effect: state transitions, lineage, outcome backfill, knowledge extraction
- Source of truth: State
- Whether side-effect exists: No

## 5. Loop Position
- Primary loop: Learning Loop
- Step in loop: fact inventory and truth hardening
- What comes before: current partial domain/state implementation
- What comes after: state transition hardening and lineage expansion
- Whether this creates reusable history: Yes

## 6. Expected Asset
- Main asset produced: State Record
- Secondary assets:
  - ownership map
  - missing-object list
- Where the asset will live:
  - `docs/architecture/`
  - state-facing modules and inventories
- How it will be reused later: all future state, outcome, and knowledge work should attach to this truth inventory.

## 7. Design Decision
- Chosen approach: inventory current fact objects and missing truth objects before implementing more loop behavior.
- Alternatives rejected:
  - adding run and receipt objects without a truth map
  - relying on domain directory names as ownership truth
- Why this approach is smallest viable move: it clarifies what exists without forcing broad code movement.
- Boundary to preserve: state truth is not the same as report narrative or knowledge summary.

## 8. Implementation Plan
1. list all current fact-bearing objects and repos
2. define canonical owners and fact boundaries
3. identify missing truth objects needed for the main chain
4. connect those findings back to the module inventory

## 9. Verification
- Unit tests: none required unless code changes are introduced
- Integration tests: not primary for this task
- Manual checks: inventory matches code and current main chain
- Failure mode checks: identify ambiguous ownership explicitly
- Truthfulness checks: no projection object is mislabeled as canonical fact

## 10. Done Criteria
- [x] current fact objects are explicitly listed and classified
- [x] owners and source-of-truth boundaries are documented
- [x] missing truth objects are named and prioritized
- [x] module inventory reflects the resulting state map

## 11. Risk Notes
- Main risk: writing a passive document that never connects back to implementation
- Drift risk: treating every domain dataclass as canonical truth
- What this task might accidentally absorb: full state-machine redesign
- Rollback plan: keep the inventory as documentation-first if code movement is not yet justified

## 12. Follow-up
- Immediate next task: state transition hardening
- Deferred work: workflow run and execution receipt implementation
- What this unlocks: explicit lineage and outcome backfill design
