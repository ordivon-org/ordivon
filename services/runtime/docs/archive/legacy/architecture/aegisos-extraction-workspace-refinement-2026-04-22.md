# AegisOS Extraction / Workspace Refinement 2026-04-22

## Purpose

This batch records the next refinement step after the post-serial-batch wave.

It captures three further reductions in system-body ownership:

- more finance analyze profile ownership behind `packs/finance`
- less Hermes behavior hidden behind a legacy provider path
- broader console-scoped workspace behavior without turning the app into a full-site tab shell

## Completed Modules

### 1. Finance Pack Analyze Profile Ownership

- `packs/finance/analyze_profile.py` now owns:
  - default finance symbol
  - default finance timeframe
  - supported finance symbols
  - supported finance timeframes
- API analyze request validation now reads finance timeframe defaults from pack-owned profile data
- workflow analyze capability now normalizes symbol/timeframe through pack-owned finance profile semantics
- orchestration context builder now imports finance context types directly from `packs/finance/context.py`

### 2. Hermes Provider Alias Cleanup

- `intelligence/providers/hermes_agent_provider.py` is now a compatibility alias to `HermesRuntime`
- adapter-owned runtime behavior stays in:
  - `adapters/runtimes/hermes/runtime.py`
- router and health paths remain adapter-first
- legacy provider path no longer carries behavior-level ownership

### 3. Broader Console Workspace Behavior

- `ConsoleWorkspaceSeed` now seeds tabs from:
  - `review_id`
  - `recommendation_id`
  - `trace_ref`
- audits, reports, and history are now wrapped in `ConsolePageFrame`
- audit surfaces can now open related review/recommendation/trace tabs
- workspace still remains console-scoped and still supports only:
  - `review_detail`
  - `recommendation_detail`
  - `trace_detail`

## Boundary Reading

What changed:

- finance analyze request/profile semantics moved further into `packs/finance`
- Hermes legacy provider path lost more owner-shaped behavior
- shared workspace moved one step beyond dashboard/reviews while staying scoped

What did **not** change:

- no full finance directory migration
- no new runtime provider
- no full-site tab shell
- no promotion of hints into truth or policy

## References

- [Current State Report 2026-04-22](./current-state-report-2026-04-22.md)
- [Layer Module Inventory](./layer-module-inventory.md)
- [Architecture Baseline](./architecture-baseline.md)
