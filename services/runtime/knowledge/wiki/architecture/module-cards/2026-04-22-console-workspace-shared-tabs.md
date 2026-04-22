# Module

Console Workspace Shared Tabs

## Layer

Experience

## Type

Core experience semantics

## Role

Broaden workspace behavior so dashboard and reviews share object-tab state through a console-scoped provider rather than keeping tabs trapped in `ReviewConsole`.

## Current Value

- Review console already had local object tabs.
- Dashboard and reviews did not share workspace state.
- Recommendation workspace still scanned `/recent?limit=50`.

## Remaining Gap

- Tabs were review-local instead of console-shared
- Recommendation detail lacked a direct read API

## Immediate Action

- Add workspace provider and console frame
- Add shared workspace panel
- Add `GET /api/v1/recommendations/{id}`
- Open tabs from dashboard and reviews

## Wrong Placement To Avoid

- Do not turn root layout into a full-site tab shell
- Do not add new object tab types beyond review/recommendation/trace
- Do not rebuild review detail logic from scratch

## Required Test Pack

- `pnpm --dir apps/web exec tsc --noEmit`
- `pytest -q tests/unit/test_web_workspace_tabs.py tests/unit/test_web_review_console_smoke.py tests/unit/test_web_product_surface_smoke.py tests/integration/test_api_product_surfaces.py`

## Done Criteria

- Dashboard and reviews share tab state through a console-scoped provider
- Recommendation tabs use `GET /api/v1/recommendations/{id}`
- Tabs still remain limited to review/recommendation/trace detail

## Next Unlock

Broader workspace behavior beyond dashboard/reviews shared tabs

## Not Doing

- No full-site tab shell
- No reports/audits/history tabs
- No new workspace object taxonomy
