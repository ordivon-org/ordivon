# Side-Effect Boundary Expansion

## Priority Test
This task is worth doing now because it satisfies at least one:
- [x] Main-chain critical
- [x] Flywheel critical
- [x] Anti-pollution critical
- [x] Reliability critical

This task should be delayed if:
- [ ] It only improves naming
- [ ] It only improves aesthetics
- [ ] It does not create reusable asset
- [ ] It does not clarify ownership
- [ ] It can be safely postponed without polluting future work

## 1. Task Identity
- Layer: Governance
- Type: Boundary
- Priority: P0
- Status: Done
- Owner:
- Date: 2026-04-19
- Related Docs:
  - [Architecture Baseline](../architecture/architecture-baseline.md)
  - [Capability Boundary Spec](../architecture/capability-boundary-spec.md)
  - [Layer Module Inventory](../architecture/layer-module-inventory.md)
  - [Side-Effect Boundary Inventory](../architecture/side-effect-boundary-inventory.md)
- Related Files:
  - `capabilities/boundary.py`
  - `capabilities/domain/`
  - `orchestrator/workflows/analyze.py`
  - report/wiki writing paths

## 2. Purpose
- Why now: key mutations already improved, but uncovered side effects will still pollute auditability and the future flywheel.
- Problem being solved: boundary discipline exists for some write paths, but not yet for all meaningful side effects.
- If not done, what breaks or stays fake: some mutations remain attributable while others stay weakly governed, which creates inconsistent trust.
- What part of the system becomes stronger: Governance as a real control surface.

## 3. Scope
### In Scope
- inventory remaining consequential side effects
- expand boundary coverage to missing critical paths
- align audit context and responsibility chain for those paths

### Out of Scope
- do not build the full policy source of truth
- do not redesign UI consequence language
- do not implement execution request/receipt yet

## 4. Main Object
- Primary object: Policy Hook
- Upstream dependency: capability and workflow write paths
- Downstream effect: auditability, authorization clarity, cleaner execution objectification
- Source of truth: State
- Whether side-effect exists: Yes

## 5. Loop Position
- Primary loop: Execution Loop
- Step in loop: pre-mutation governance boundary
- What comes before: candidate decision and actor intent
- What comes after: execution, receipt, and audit
- Whether this creates reusable history: Yes

## 6. Expected Asset
- Main asset produced: Policy Hook
- Secondary assets:
  - Audit Trail
  - Boundary coverage inventory
- Where the asset will live:
  - `capabilities/boundary.py`
  - governance and workflow write paths
- How it will be reused later: execution request/receipt will depend on the same responsibility contract.

## 7. Design Decision
- Chosen approach: expand the existing boundary model instead of inventing a second governance gate.
- Alternatives rejected:
  - route-local action checks
  - side-effect-specific ad hoc guards
- Why this approach is smallest viable move: it extends a real boundary already in the main system.
- Boundary to preserve: governance decides whether side effects may proceed; execution performs them later.

## 8. Implementation Plan
1. enumerate uncovered critical side effects
2. extend boundary enforcement to those paths
3. ensure actor/context/reason/idempotency are carried through
4. verify audit payloads reflect the same lineage

## 9. Verification
- Unit tests: boundary validation for expanded paths
- Integration tests: affected main-chain writes
- Manual checks: API routes or workflows that trigger those writes
- Failure mode checks: missing context and duplicate request behavior
- Truthfulness checks: writes fail honestly when context is missing

## 10. Done Criteria
- [x] all currently critical side effects use the unified boundary model
- [x] missing boundary context causes honest failure
- [x] audit payloads carry aligned responsibility lineage
- [x] remaining uncovered side effects are documented, not hidden

## 11. Risk Notes
- Main risk: broadening boundary coverage without a clear action inventory
- Drift risk: governance checks diverging across layers
- What this task might accidentally absorb: policy-source implementation
- Rollback plan: expand coverage incrementally and keep uncovered actions explicitly listed

## 12. Follow-up
- Immediate next task: execution action catalog
- Deferred work: authorization/actor system
- What this unlocks: controlled request/receipt execution model
