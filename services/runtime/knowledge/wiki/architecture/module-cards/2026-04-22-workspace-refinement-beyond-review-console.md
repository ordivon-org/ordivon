# Module

Workspace Refinement Beyond Review Console

## Layer

Experience

## Type

Experience

## Role

Deepen the first review workspace so tabs carry real active content and can include linked recommendation views, not only shell placeholders.

## Current Value

- `/reviews` and minimal workspace tabs already existed.
- Tabs could open and close but active content stayed narrow.

## Remaining Gap

- Recommendation tabs were not rendered.
- Initial review selection could not be seeded from route state.

## Immediate Action

- Add recommendation workspace panel
- Let review selection open linked recommendation tabs
- Let route state seed initial review tab

## Wrong Placement To Avoid

- Do not build a full-site tab shell
- Do not invent a new review API
- Do not move review supervision semantics into domains

## Required Test Pack

- `pnpm --dir apps/web exec tsc --noEmit`
- `pytest -q tests/unit/test_web_review_console_smoke.py tests/unit/test_web_workspace_tabs.py tests/unit/test_web_trust_tier_semantics.py`

## Done Criteria

- Active tabs render content for review, trace, and recommendation views
- Linked recommendation tabs can open from review selection
- Workspace still stays console-local

## Next Unlock

Broader multi-object workspace behavior

## Not Doing

- No full app workspace
- No new API surface
- No route overhaul
