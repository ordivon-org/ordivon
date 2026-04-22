# Finance Pack Frontend Analyze Surface Extraction

## 1. Identity

- Layer: Experience
- Type: Pack
- Status: Done
- Priority: P1
- Owner: `packs/finance` + console analyze surfaces
- Date: 2026-04-22

## 2. Philosophy

- Primary doctrine carried:
  - core must stay stable while domain and adapters stay replaceable
- Secondary doctrine carried:
  - the frontend is a supervision surface
- Why this module exists as a philosophical constraint:
  - finance-specific analyze defaults and option sets should not keep leaking out of pack-owned semantics into generic UI entry surfaces

## 3. Role

- What this module is responsible for:
  - move finance-shaped analyze option ownership for console UI inputs behind `packs/finance`
- What system gap it closes:
  - `AnalyzeInput` and `QuickAnalyze` still look like owners of finance defaults and option lists
- What reusable asset it should leave behind:
  - pack-owned analyze option contract reusable by API, capability, and front-end surfaces

## 4. Ownership

- System owner:
  - Experience layer for rendering
- Truth owner:
  - none
- Policy owner:
  - none
- Runtime/adapter owner:
  - none
- Domain owner if any:
  - `packs/finance`

## 5. Classification

- Why this is Pack:
  - the work is about finance-domain input defaults and supported option ownership rather than cross-domain UI law
- Why it is not one of the other two:
  - it is not a stable cross-domain primitive, and it is not an external implementation adapter
- What stable law or domain concern it represents:
  - finance analyze input semantics must be pack-owned even when rendered through generic console pages

## 6. Affected Chain

- Primary chain:
  - dashboard/analyze input -> analyze request -> capability normalization
- Upstream input:
  - user-entered query plus finance-shaped symbol/timeframe selections
- Downstream effect:
  - analyze surfaces stop hard-coding finance option ownership
- What becomes more real after this module:
  - the pack becomes the visible owner of finance analyze input semantics all the way to the UI edge

## 7. Invariant

- Main invariant:
  - finance-specific analyze options must not be owned by generic UI components
- Secondary invariants:
  - finance semantics must not flow back into core
  - hints must not be promoted into truth or policy
  - the workspace must remain a supervision surface, not a domain owner
- Truth boundary preserved:
  - yes
- Hint/policy boundary preserved:
  - yes

## 8. Wrong Placement To Avoid

- Do not put finance analyze option ownership into `apps/web` constants with no pack owner
- Do not move generic analyze route behavior into `packs/finance`
- Do not use this module to expand workspace object taxonomy

## 9. Not Doing

- No redesign of the analyze page layout
- No new runtime/provider work
- No broad finance domain migration

## 10. Immediate Action

1. Add a pack-owned finance analyze input/options helper
2. Route `AnalyzeInput` and `QuickAnalyze` through that helper
3. Keep API/capability behavior aligned with the same pack-owned semantics

## 11. Required Test Pack

- Unit:
  - finance analyze option helper contract
- Integration:
  - analyze request path still honors pack-owned defaults
- Failure-path:
  - unsupported timeframes still degrade honestly to allowed defaults or validation behavior
- Invariant:
  - finance option ownership does not move back into generic UI modules

## 12. Done Criteria

- [x] finance analyze input options are owned by `packs/finance`
- [x] `AnalyzeInput` no longer hard-codes finance symbol/timeframe ownership
- [x] `QuickAnalyze` no longer hard-codes finance symbol ownership
- [x] analyze flow remains behaviorally stable

## 13. Next Unlock

- deeper finance extraction of recommendation-facing wording/surfaces or broader pack-owned product semantics
