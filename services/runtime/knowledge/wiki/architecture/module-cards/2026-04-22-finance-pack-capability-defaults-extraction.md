# Module

Finance Pack Capability Defaults Extraction

## Layer

Pack Layer

## Type

Pack

## Role

Move finance-specific analyze defaults out of the capability layer and into `packs/finance`.

## Current Value

- Finance context ownership has already moved into `packs/finance/context.py`.
- `AnalyzeCapability` still owned finance defaults such as `BTC/USDT` and `1h`.

## Remaining Gap

- Capability layer still looked like the owner of finance-specific analyze defaults.
- Finance defaults were still easy to mistake as generic system defaults.

## Immediate Action

- Add finance-pack analyze defaults helper
- Route `AnalyzeCapability` through that helper
- Keep public capability interface unchanged

## Wrong Placement To Avoid

- Do not move generic workflow contracts into `packs/finance`
- Do not hard-code finance defaults back into capability or orchestrator
- Do not widen this module into tool or runtime extraction

## Required Test Pack

- `python -m compileall packs/finance capabilities/workflow/analyze.py`
- `pytest -q tests/unit/test_finance_pack_analyze_defaults.py tests/integration/test_capabilities_contracts.py`

## Done Criteria

- Finance analyze defaults are owned by `packs/finance`
- Capability no longer hard-codes finance defaults directly
- Existing capability contract still works

## Next Unlock

Further finance-pack extraction of policy and tool ownership

## Not Doing

- No workflow route rewrite
- No domain migration
- No policy execution changes
