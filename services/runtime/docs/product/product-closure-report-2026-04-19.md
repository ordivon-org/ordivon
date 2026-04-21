# Product Closure Report 2026-04-19

## Scope

This report captures the repository work completed against `docs/product/product-closure-todo.md` in one execution pass.

## Delivered

### Experience Truthfulness and Semantic Clarity

- homepage status copy already reflected live reachability and was preserved
- shared experience state vocabulary remains active via `loading / ready / empty / unavailable / error`
- recommendation actions now send explicit action context and use consequence-forward labels such as `Adopt Recommendation`
- homepage cards already expose object type, trust tier, lineage, and time semantics; the closure pass preserved and aligned them with the new capability classifications

### Capability Boundary Freeze and Contract Cleanup

- split `capabilities/contracts.py` into:
  - `capabilities/contracts/domain.py`
  - `capabilities/contracts/workflow.py`
  - `capabilities/contracts/view.py`
  - `capabilities/contracts/diagnostic.py`
- added `capabilities/boundary.py` with `ActionContext` and required side-effect boundary validation
- reclassified capability implementations into:
  - `capabilities/domain/`
  - `capabilities/workflow/`
  - `capabilities/view/`
  - `capabilities/diagnostic/`
- kept top-level `capabilities/*.py` modules as compatibility wrappers so existing imports continue to work
- explicitly marked:
  - `AnalyzeResult` as workflow composite
  - `DashboardResult` as view aggregate
  - `ValidationSummaryResult` as diagnostic summary

### Defensive Side-Effect Boundary

- recommendation status updates now require `actor`, `context`, `reason`, and `idempotency_key`
- review submit and complete flows now require the same context
- validation issue intake now requires the same context
- validation usage sync now runs through the same boundary model

### Documentation and Inventory

- added [capability-boundary-spec.md](../architecture/capability-boundary-spec.md)
- added [capability-inventory.md](../architecture/capability-inventory.md)
- added [api-bypass-inventory.md](../architecture/api-bypass-inventory.md)
- added [capability-migration-plan.md](../architecture/capability-migration-plan.md)

## Verification

- targeted tests:
  - `pytest -q tests/integration/test_capabilities_contracts.py tests/unit/test_capability_matrix.py tests/unit/test_web_product_surface_smoke.py`
  - result: `15 passed`
- syntax check:
  - `python -m compileall capabilities apps/api/app`
  - result: success

## Remaining Manual Checks

The following closure items still require a human route/screenshot pass because they cannot be truthfully completed from repository edits alone:

- homepage visual route check
- dashboard widget screenshot check
- analyze page manual route check
- final trust-tier visual polish review across key pages

## Risk Notes

- `GET /api/v1/reviews/pending` still performs a router-local repository read and is documented in the bypass inventory
- `validation` remains intentionally classified as diagnostic even though it contains bounded issue intake; if that write path expands later, split it into a dedicated workflow capability
