# Module

Experience ReviewConsole + Tabbed Workspace

## Layer

Experience

## Type

Experience

## Role

Add a dedicated review supervision route and a minimal object-tab workspace without turning the whole app into a new shell.

## Current Value

- Review and trace detail surfaces already existed on the dashboard.
- There was no dedicated reviews route or shared object-tab workspace.

## Remaining Gap

- Review supervision still lived inside dashboard cards.
- No reusable object-view tabs existed.

## Immediate Action

- Add `/reviews` route
- Add `ReviewConsole` components
- Add minimal workspace shell/tabs/hook
- Support three tab kinds in v1:
  - review detail
  - recommendation detail
  - trace detail

## Wrong Placement To Avoid

- Do not copy-paste dashboard review logic without refactoring reuse
- Do not attempt full-site tabbing
- Do not invent new review/trace APIs in this module

## Required Test Pack

- `pnpm --dir apps/web exec tsc --noEmit`
- `pytest -q tests/unit/test_web_review_console_smoke.py tests/unit/test_web_workspace_tabs.py tests/unit/test_web_product_surface_smoke.py`

## Done Criteria

- `/reviews` route exists
- `ReviewConsole` exists
- Workspace shell/tabs exist
- At least review and trace views are tab-openable without losing context

## Next Unlock

Post-batch workspace refinement and broader pack/adapter extraction

## Not Doing

- No full-app tab workspace
- No new review API family
- No rewrite of all dashboard surfaces
