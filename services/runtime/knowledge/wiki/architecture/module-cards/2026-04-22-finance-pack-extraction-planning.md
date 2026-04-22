# Module

Finance Pack Extraction Planning

## Layer

Pack Layer

## Type

Pack planning

## Role

Freeze the first explicit finance-pack boundary without moving directories or rewriting imports.

## Current Value

- Core primitives are already frozen in Phase 0.
- Phase 1 strengthened core behavior, but `orchestrator/context/*` and multiple tools/domains still carry finance-first defaults.
- The repo still has no `packs/` directory, so pack planning has not yet become a visible system asset.

## Remaining Gap

- Finance-specific files are still easy to misread as core owners.
- There is no written keep-in-core vs move-to-finance map.
- There is no finance inventory for future extraction.

## Immediate Action

- Add `docs/architecture/finance-pack-extraction-plan.md`
- Add `packs/README.md`
- Add `packs/finance/README.md`
- Add `packs/finance/inventory.md`
- Mark finance-pack candidate files with lightweight header comments only

## Wrong Placement To Avoid

- Do not put finance-pack planning into `governance/` or `intelligence/`
- Do not physically migrate finance code in this module
- Do not turn finance nouns into new core primitives

## Required Test Pack

- `python -m compileall orchestrator/context`
- `pytest -q tests/unit/test_boundary_import_hygiene.py`

## Done Criteria

- Finance extraction plan exists
- Finance inventory lists 10+ concrete candidates
- No directory migration happened
- No import graph rewrite happened
- No new finance semantics were injected into core

## Next Unlock

Hermes Runtime Adapter Extraction

## Not Doing

- No directory moves
- No import rewrites
- No finance API changes
- No workflow behavior changes
