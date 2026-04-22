# Module

Experience Global Trust-tier Rollout

## Layer

Experience

## Type

Core experience semantics

## Role

Roll current dashboard-local truthful semantics into shared TrustTier types and rendering helpers.

## Current Value

- Trust-tier / semantic discipline already existed on active dashboard surfaces.
- Semantics were still partially encoded as local component assumptions.

## Remaining Gap

- No unified `TrustTier` type owned the page-level semantics.
- Missing/unavailable/hint/outcome surface behavior still depended on component-local patterns.

## Immediate Action

- Add shared `TrustTier` type
- Centralize semantics in `semanticSignals.ts`
- Centralize state rendering in `SurfaceStates.tsx` and `ProductSignals.tsx`
- Roll through key dashboard surfaces before adding new workspace UI

## Wrong Placement To Avoid

- Do not invent trust tiers inside each component
- Do not do tabbed workspace work in this module
- Do not treat hints as fact or outcome as closed truth

## Required Test Pack

- `pnpm --dir apps/web exec tsc --noEmit`
- `pytest -q tests/unit/test_web_product_surface_smoke.py tests/unit/test_web_trust_tier_semantics.py`

## Done Criteria

- Shared `TrustTier` type exists
- Shared state rendering exists
- Key review/recommendation/trace surfaces use the same semantics

## Next Unlock

Experience ReviewConsole + Tabbed Workspace

## Not Doing

- No workspace shell yet
- No new API contract
- No UI rewrite
