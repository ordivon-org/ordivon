# Module

Finance Pack Analyze Profile Ownership

## Layer

Pack Layer

## Type

Pack

## Role

Move finance-specific analyze request/profile defaults and supported-option ownership behind the finance pack instead of leaving them scattered across API and workflow entrypoints.

## Current Value

- Finance context defaults already live in `packs/finance/context.py`.
- Finance capability defaults already live in `packs/finance/analyze_defaults.py`.
- API request schema and workflow entry still looked like implicit owners of finance analyze shape.

## Remaining Gap

- `1h` timeframe default still appeared at the API schema edge.
- Supported finance analyze options were not explicitly owned by the finance pack.

## Immediate Action

- Add `packs/finance/analyze_profile.py`
- Route API request defaults and workflow normalization through that profile
- Reduce orchestration imports that still pointed at finance compatibility shims

## Wrong Placement To Avoid

- Do not move generic `AnalysisRequest` into `packs/finance`
- Do not hard-code finance defaults back into API or workflow layers
- Do not treat front-end finance widgets as core primitive owners

## Required Test Pack

- `python -m compileall packs/finance apps/api/app/schemas/requests.py capabilities/workflow/analyze.py orchestrator/context/context_builder.py`
- `pytest -q tests/unit/test_finance_pack_analyze_profile.py tests/unit/test_finance_pack_analyze_defaults.py tests/unit/test_boundary_import_hygiene.py`

## Done Criteria

- Finance analyze request/profile defaults are owned by `packs/finance`
- API request validation uses pack-owned timeframe semantics
- Workflow entrypoint no longer hard-codes finance analyze shape

## Next Unlock

Further finance pack extraction of front-end finance-specific analyze surfaces or deeper domain/tool ownership

## Not Doing

- No tool migration
- No front-end route redesign
- No broad domain extraction
