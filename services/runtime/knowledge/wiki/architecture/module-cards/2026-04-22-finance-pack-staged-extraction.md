# Module

Finance Pack Staged Extraction

## Layer

Pack Layer

## Type

Pack

## Role

Move the ownership of finance-shaped analysis context defaults into `packs/finance` while keeping the old orchestration paths as shims.

## Current Value

- Finance pack planning and inventory already exist.
- `orchestrator/context/*` still directly owned finance-shaped defaults such as market symbol, timeframe, and portfolio state.

## Remaining Gap

- Finance context ownership still lived under orchestration.
- The repository had no pack-backed shim for market/portfolio analysis context.

## Immediate Action

- Add `packs/finance/context.py`
- Add `packs/finance/__init__.py`
- Move finance-shaped context owners there
- Keep `orchestrator/context/*` as compatibility shims

## Wrong Placement To Avoid

- Do not migrate all finance files at once
- Do not move runtime or governance primitives into `packs/finance`
- Do not rewrite broad import paths in this module

## Required Test Pack

- `python -m compileall packs/finance orchestrator/context`
- `pytest -q tests/unit/test_boundary_import_hygiene.py tests/unit/test_finance_pack_shims.py`

## Done Criteria

- Finance context owner exists in `packs/finance`
- `orchestrator/context/*` remains usable as shim layer
- No large import migration happened
- Finance semantics did not get re-injected into core

## Next Unlock

Finance pack extraction of additional candidate files

## Not Doing

- No movement of tools/domains into `packs/finance` yet
- No API change
- No workflow behavior rewrite
