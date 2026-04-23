# MVP Presentation and Delivery Closure

## Philosophy

- Experience is a supervisor surface, not an ambiguous page collection.
- Capability closure requires route-level validation, not only internal confidence.
- Delivery discipline is part of product truth for MVP, not an afterthought.

## Layer

- Experience
- Infrastructure

## Type

- Core

## Owner

- Experience product surface owner
- Infrastructure delivery/quality gate owner

## Affected Chain

- `homepage -> quick analyze -> /analyze -> recommendation handoff -> /reviews`
- `validated main branch -> CI checks -> delivery bundle`

## Change Summary

- Locked homepage, analyze, and reviews into distinct MVP roles.
- Strengthened recommendation-aware handoff into the review workbench.
- Added a browser E2E smoke path for the MVP gold path.
- Added a delivery workflow that packages the current MVP docs/config surface after validated CI.
- Updated README, current-state reporting, and MVP brief so the repository explains the same product truth that the code and workflows enforce.

## Invariant

- Homepage remains the command center, not the deep supervision surface.
- `/analyze` remains the execution workspace, not a queue or system overview page.
- `/reviews` remains the primary supervision workbench.
- Finance semantics were not re-injected into core.
- Hermes was not re-promoted into system identity.
- Hints were not promoted into truth or policy.

## Wrong Placement To Avoid

- Do not turn dashboard previews into deep review or trace work surfaces.
- Do not add fake E2E that only reasserts source strings without exercising the running product path.
- Do not treat delivery workflow artifacts as a production deployment claim.

## Not Doing

- No new backend product APIs in this module.
- No full-site tab shell expansion.
- No broader pack extraction or Hermes cleanup in this module.
- No production cloud deploy target.

## Required Test Pack

- `pnpm --dir apps/web exec tsc --noEmit`
- `python -m pytest -q tests/unit/test_web_product_surface_smoke.py tests/unit/test_web_review_console_smoke.py tests/unit/test_web_workspace_tabs.py`
- `python -m pytest -q tests/integration/test_api_product_surfaces.py tests/integration/test_api_semantic_outputs.py tests/integration/test_hermes_analyze_api.py tests/integration/test_health_monitoring_api.py tests/integration/test_scheduler_persistence.py tests/integration/test_workflow_run_lineage_api.py`
- `pnpm test:e2e -- tests/e2e/mvp-gold-path.spec.ts`

## Done Criteria

1. README and MVP brief describe the same gold path and page-role split as the running product.
2. CI includes a browser-validated MVP path, not only unit and integration checks.
3. A delivery workflow packages the current MVP docs/config surface from validated `main`.
4. Route handoff from homepage and analyze into reviews is object-aware and test-enforced.
5. MVP closure improves delivery clarity without widening workspace scope or changing backend contracts.
