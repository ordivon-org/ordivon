# Module

Broader Console Workspace Behavior

## Layer

Experience

## Type

Core experience semantics

## Role

Broaden shared workspace behavior from dashboard/reviews-only visibility to more console routes while keeping scope below a full-site tab shell.

## Current Value

- Dashboard and reviews already share tabs through a console-scoped provider.
- Recommendation detail already has a direct API endpoint.
- Audits, reports, and history still lived outside the visible shared console workspace.

## Remaining Gap

- Query-param object seeding did not work across console routes.
- Audit pages could not directly open related object tabs.
- Shared workspace remained too local to dashboard/reviews.

## Immediate Action

- Add a console workspace seed for `review_id`, `recommendation_id`, and `trace_ref`
- Wrap audits, reports, and history in `ConsolePageFrame`
- Let audit surfaces open related review/recommendation/trace tabs

## Wrong Placement To Avoid

- Do not turn the root app into a full-site tab shell
- Do not add report/audit/history tab types in this module
- Do not move workspace behavior into feature-local components again

## Required Test Pack

- `pnpm --dir apps/web exec tsc --noEmit`
- `pytest -q tests/unit/test_web_workspace_tabs.py tests/unit/test_web_product_surface_smoke.py tests/unit/test_web_review_console_smoke.py`

## Done Criteria

- Console workspace behavior extends beyond dashboard/reviews
- Query params can seed object tabs on console pages
- Audit surfaces can open related object tabs without inventing new tab types

## Next Unlock

Richer console navigation or future scoped object workspaces without escalating to a full-site shell

## Not Doing

- No global tab shell
- No new object taxonomy
- No reports/audits/history detail tabs
