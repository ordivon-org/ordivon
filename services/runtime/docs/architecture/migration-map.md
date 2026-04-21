# Migration Map

This document describes migration movement only. The canonical architectural target is defined in [architecture-baseline](./architecture-baseline.md).

## Why This Exists

The repository already contains working code. A full rename-and-move refactor would add risk without enough payoff. This map defines where new code should go and how old code should be migrated over time.

## Current To Target

- `apps/*` remains the Experience Layer implementation root
- new product-facing feature modules should land in `capabilities/*`
- initial extracted capability modules now exist for analyze, recommendations, reviews, and reports
- migrated root implementations now exist for shared settings/logging/time, orchestrator context/runtime, intelligence engine/provider routing, and governance risk engine
- migrated root governance implementations now exist for `governance/risk_engine` and `governance/audit`
- migrated root domain implementations now exist for `domains/research` (analysis), `domains/strategy` (recommendation and outcome), and `domains/journal` (review, lesson, issue)
- migrated root state implementations now exist for `state/db` and `state/usage`
- `pfios/reasoning/*` -> `intelligence/*`
- `pfios/context/*` -> `orchestrator/context/*` or `knowledge/retrieval/*` depending on ownership
- `pfios/orchestrator/*` -> `orchestrator/*`
- `pfios/governance/*` -> `governance/*`
- `pfios/audit/*` -> `governance/audit/*` or `domains/journal/*` depending on usage
- `pfios/core/db/*` -> `state/db/*` now, then later `state/repositories/*`, `state/schemas/*`, `state/migrations/*` as the State Domain fills out
- `pfios/core/config/*`, `logging/*`, `utils/time.py` -> `shared/*`
- `pfios/expression/*` -> `domains/reporting/*` plus `tools/reports/*`
- `pfios/domain/*` -> `domains/*`
- state-like operational facts such as usage snapshots can migrate directly into `state/*` instead of `domains/*`
- `skills/*` and `tools/*` are grouped under the Execution Layer through `execution/`
- `knowledge/*` and `state/*` are grouped under the Knowledge and State Layer through `knowledge_state/`
- `prompts/` -> `intelligence/prompts/`
- `policies/` -> `governance/policies/`
- `wiki/` -> `knowledge/wiki/`
- `workflows/` -> `orchestrator/workflows/`
- business logic in `scripts/` -> `skills/`, `tools/`, `domains/`, or `orchestrator/`

## Migration Rules

1. Move boundaries before moving files.
2. Prefer adding adapter imports over breaking working paths in one shot.
3. New product functionality should start in a named capability module rather than a route handler.
4. Do not move prompt text into domain modules.
5. Do not move state truth into wiki-backed storage.
6. Any move that changes ownership must update docs and tests together.
