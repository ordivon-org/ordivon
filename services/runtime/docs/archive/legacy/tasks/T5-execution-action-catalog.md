# Execution Action Catalog

## Priority Test
This task is worth doing now because it satisfies at least one:
- [x] Main-chain critical
- [x] Anti-pollution critical
- [x] Unlocks next task

This task should be delayed if:
- [ ] It only improves naming
- [ ] It only improves aesthetics
- [ ] It does not create reusable asset
- [ ] It does not clarify ownership
- [ ] It can be safely postponed without polluting future work

## 1. Task Identity
- Layer: Execution
- Type: Closure
- Priority: P0
- Status: Done
- Owner:
- Date: 2026-04-19
- Related Docs:
  - [Architecture Baseline](../architecture/architecture-baseline.md)
  - [Layer Module Inventory](../architecture/layer-module-inventory.md)
  - [Execution Action Catalog](../architecture/execution-action-catalog.md)
- Related Files:
  - `tools/`
  - `skills/`
  - `execution/`
  - report and wiki writing paths
  - notification or sync paths if present

## 2. Purpose
- Why now: execution remains too scattered, so future request/receipt modeling has no stable action universe to attach to.
- Problem being solved: real actions exist, but they are not cataloged as first-class execution actions.
- If not done, what breaks or stays fake: governance and state can only partially reason about real action because execution remains hidden in utilities and workflows.
- What part of the system becomes stronger: Execution as a real layer instead of an architectural intention.

## 3. Scope
### In Scope
- list current real actions
- classify each action by side-effect level and ownership
- identify which ones need request/receipt models first

### Out of Scope
- do not fully implement all request/receipt objects
- do not rewrite every tool into adapters
- do not create external integrations beyond inventory

## 4. Main Object
- Primary object: Execution Adapter
- Upstream dependency: governance-approved action intent
- Downstream effect: request/receipt, audit, and state recording
- Source of truth: State
- Whether side-effect exists: Yes

## 5. Loop Position
- Primary loop: Execution Loop
- Step in loop: action naming and classification
- What comes before: governance boundary
- What comes after: request/receipt objectification and adapter consolidation
- Whether this creates reusable history: Yes

## 6. Expected Asset
- Main asset produced: Action Catalog
- Secondary assets:
  - side-effect classification
  - adapter candidate list
- Where the asset will live:
  - `docs/architecture/`
  - future `execution/` catalogs
- How it will be reused later: request/receipt and execution hook work should attach to this catalog.

## 7. Design Decision
- Chosen approach: inventory first, then objectify.
- Alternatives rejected:
  - introducing request/receipt before action naming
  - leaving side effects distributed and undocumented
- Why this approach is smallest viable move: it turns scattered action into named assets without broad rewrites.
- Boundary to preserve: execution actions are not intelligence tasks and not governance decisions.

## 8. Implementation Plan
1. identify all current meaningful actions
2. classify each by side-effect level and owning path
3. nominate the first action family for request/receipt modeling
4. connect results back to module inventory and roadmap

## 9. Verification
- Unit tests: `tests/unit/test_execution_action_catalog.py`
- Integration tests: `tests/integration/test_execution_action_catalog_integration.py`
- Manual checks: compare catalog against real write and external action paths
- Failure mode checks: duplicate action IDs and unknown action lookup
- Truthfulness checks: no narrative or analysis-only task is mislabeled as execution action

## 10. Done Criteria
- [x] current execution actions are listed and classified
- [x] side-effect levels are named for each action family
- [x] first request/receipt candidate family is selected
- [x] ambiguous ownership paths are documented, not hidden

## 11. Risk Notes
- Main risk: catalog remains too broad to drive implementation
- Drift risk: mixing artifact generation, state mutation, and AI reasoning into one action bucket
- What this task might accidentally absorb: full adapter refactor
- Rollback plan: keep it inventory-first and implementation-light

## 12. Follow-up
- Immediate next task: execution request/receipt model
- Deferred work: adapter consolidation
- What this unlocks: governance hook and state receipt integration
