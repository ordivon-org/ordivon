# AegisOS MVP Execution Checklist

## Scope

This checklist is for the **current MVP**, not the full future AegisOS platform.

The MVP target is:

> a single-agent, single-mainline, finance-seed, governance-aware workflow where a user can clearly complete the analyze -> recommendation -> review chain through the product surfaces.

This checklist is intentionally product-closing rather than architecture-expanding.

## Program Rule

The MVP is not blocked by missing platform ambition. It is blocked by missing product closure.

That means the work here should optimize for:

- clear entrypoints
- clear page ownership
- clean handoff between pages
- honest object continuation
- stable smoke and route validation
- clear README and demo narrative

It should not optimize for:

- new runtime breadth
- richer pack ecosystems
- broader multi-agent behavior
- more generalized platform primitives unless directly needed for MVP closure

## Batch 1: Finance Analyze Surface Finalization

### Goal

Finish the remaining front-end finance ownership cleanup so generic UI no longer owns finance analyze defaults or option semantics.

### Why this batch exists

The pack boundary is already mostly in place, but MVP should not ship with generic components still acting as domain owners.

### Files Likely Involved

- `packs/finance/analyze_surface.ts`
- `packs/finance/README.md`
- `packs/finance/inventory.md`
- `apps/web/src/components/features/dashboard/QuickAnalyze.tsx`
- `apps/web/src/components/features/analyze/AnalyzeInput.tsx`
- `apps/web/src/types/api.ts`
- `apps/web/src/types/experience.ts`
- finance-pack frontend boundary tests

### Done Criteria

1. `QuickAnalyze` does not hard-code finance symbols.
2. `AnalyzeInput` does not hard-code finance symbols or timeframes.
3. Homepage and `/analyze` consume the same pack-owned helper.
4. Generic route/page/components do not own finance analyze defaults.
5. Residual finance-specific copy or defaults in generic UI are either removed or explicitly delegated to `packs/finance`.

### Test Pack

- finance analyze options helper unit tests
- `QuickAnalyze` smoke
- `AnalyzeInput` smoke
- finance-pack frontend boundary tests
- grep-style hygiene check to confirm no generic UI finance hard-coding remains

## Batch 2: Homepage / Analyze / Reviews Role Split Finalization

### Goal

Lock product ownership so the three core pages stop overlapping in purpose.

### Target Role Split

- `/` = command center
- `/analyze` = execution workspace
- `/reviews` = supervision workbench

### Why this batch exists

The architecture is already strong, but users still need the product to tell them where work belongs.

### Files Likely Involved

- `apps/web/src/app/page.tsx`
- `apps/web/src/app/analyze/page.tsx`
- `apps/web/src/app/reviews/page.tsx`
- `apps/web/src/components/features/dashboard/*`
- `apps/web/src/components/features/analyze/*`
- `apps/web/src/components/features/reviews/*`
- `apps/web/src/components/workspace/*`
- `apps/web/src/components/layout/Sidebar.tsx`
- `apps/web/src/components/workspace/ConsolePageFrame.tsx`

### Done Criteria

1. Homepage only behaves as a command center.
2. `/analyze` only behaves as the execution workspace.
3. `/reviews` only behaves as the supervision workbench.
4. Homepage previews no longer act like deep work surfaces.
5. `/analyze` clearly states next actions after a run.
6. `/reviews` is the default deep-work page for pending supervision objects.

### Test Pack

- homepage smoke asserting command-center copy and entrypoint behavior
- analyze smoke asserting execution-workspace copy and flow
- reviews smoke asserting supervision-workbench copy and queue behavior
- route handoff smoke for homepage -> analyze and homepage -> reviews

## Batch 3: Gold Path Handoff Closure

### Goal

Turn the MVP mainline into one obvious user path instead of a set of related capabilities.

### Gold Path

`homepage -> quick analyze -> /analyze -> result / recommendation -> /reviews`

### Why this batch exists

MVP succeeds when a first-time user can follow the path without guessing where to continue.

### Files Likely Involved

- homepage dashboard entry components
- analyze result and next-action components
- review queue and review detail entrypoints
- shared workspace routing helpers
- recommendation detail and trace detail open behavior

### Done Criteria

1. Homepage quick analyze always hands off into `/analyze`.
2. `/analyze` result view clearly exposes governance/result/recommendation next actions.
3. If supervision is needed, `/analyze` explicitly routes users into `/reviews`.
4. Homepage recommendation/review surfaces act as continue-work previews, not deep ownership surfaces.
5. `/reviews` can carry a full supervision continuation path.

### Test Pack

- homepage quick analyze -> `/analyze` smoke
- `/analyze` result -> `/reviews` smoke
- homepage preview -> `/reviews` smoke
- review object open smoke
- recommendation / trace / outcome supporting tab smoke

## Batch 4: User-View Route Handoff and E2E Validation

### Goal

Prove that the MVP works from a user journey perspective rather than only from a module or API perspective.

### Why this batch exists

Without route-level and user-path validation, the system is still only internally convincing.

### Files Likely Involved

- `tests/unit/test_web_*`
- `tests/integration/test_api_*`
- workspace tab and route handoff smoke tests
- analyze-path integration tests
- any minimal E2E or route navigation harness added for MVP closure

### Done Criteria

At least these paths are validated:

1. homepage -> quick analyze -> `/analyze`
2. `/analyze` -> result / governance / recommendation
3. result -> `/reviews`
4. `/reviews` -> trace / outcome supporting views
5. missing and unavailable states are shown honestly

### Test Pack

- route handoff smoke tests
- shared workspace smoke tests
- product surface integration tests
- analyze-path integration tests
- missing/unavailable honest display assertions

## Batch 5: MVP Presentation and Delivery Closure

### Goal

Make the MVP easy to explain, review, and demo without mixing current product truth with future platform ambition.

### Why this batch exists

An MVP can technically work and still fail in evaluation because its scope and intended use are not obvious.

### Files Likely Involved

- `README.md`
- `docs/architecture/current-state-report-*.md`
- `docs/architecture/layer-module-inventory.md`
- `docs/tasks/README.md`
- `docs/architecture/aegisos-overview.md`
- `docs/architecture/aegisos-layer-roadmap.md`
- new MVP brief or demo brief if needed

### Done Criteria

1. README explains the current MVP clearly.
2. The three page roles are stated explicitly.
3. The gold path is documented clearly.
4. Preview vs deep-work surfaces are described honestly.
5. Current scope, non-goals, and next-stage platform ambitions are separated.
6. CI and required checks are part of the MVP delivery story, not an afterthought.

### Test Pack

- docs consistency pass
- README entrypoint review
- CI verification on the current main branch
- `mvp-e2e` browser smoke verification
- `Delivery` workflow verification
- branch protection and required-check confirmation in GitHub settings

## Priority Summary

### P0

- Batch 1: Finance Analyze Surface Finalization
- Batch 2: Homepage / Analyze / Reviews Role Split Finalization
- Batch 3: Gold Path Handoff Closure
- Batch 4: User-View Route Handoff and E2E Validation

### P1

- Batch 5: MVP Presentation and Delivery Closure

## Non-Blocking After-MVP Work

These are valuable, but they should not delay the current MVP:

- deeper finance staged extraction beyond current surface ownership
- deeper Hermes shim cleanup
- richer scheduler triggers
- broader monitoring depth and ops refinement
- fuller knowledge flywheel behavior
- full object-console workspace expansion

## Working Definition of Done

The MVP is ready when:

1. a first-time user can start from homepage without confusion
2. the user can complete the analyze -> recommendation -> review chain clearly
3. page ownership is obvious and non-overlapping
4. finance ownership is not leaking through generic UI
5. route handoff behavior is validated from the user point of view
6. README and system docs describe the same current product truth
7. CI and branch checks enforce the minimum engineering gate

## Module Planning Reminder

As this checklist is executed, each batch should still be expressed through the AegisOS module discipline:

- philosophy carried
- layer touched
- `Core / Pack / Adapter`
- owner
- affected chain
- wrong placement to avoid
- invariant to preserve

That is how MVP closure happens without collapsing the system back into an ad hoc AI feature pile.
