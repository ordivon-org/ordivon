# Module

Finance Pack Policy / Tool Ownership

## Layer

Pack Layer

## Type

Pack

## Role

Move finance-specific policy and tool namespace ownership behind `packs/finance` facades without migrating directories.

## Current Value

- Finance context and analyze defaults already live under `packs/finance`.
- Finance trading limits and finance tool namespace refs were still easy to treat as system-body concerns.

## Remaining Gap

- Finance-specific policy/tool ownership was not yet explicit.
- Governance and future orchestration reads still lacked a pack-owned owner surface for finance overlays.

## Immediate Action

- Add `packs/finance/policy.py`
- Add `packs/finance/tool_refs.py`
- Route finance overlay/tool ref reads through pack-owned helpers

## Wrong Placement To Avoid

- Do not move tool implementations into `packs/finance`
- Do not put finance policy path ownership into governance core primitives
- Do not widen this module into physical pack extraction

## Required Test Pack

- `python -m compileall packs/finance governance orchestrator`
- `pytest -q tests/unit/test_boundary_import_hygiene.py tests/unit/test_finance_pack_policy_refs.py tests/unit/test_finance_pack_shims.py tests/unit/test_finance_pack_analyze_defaults.py`

## Done Criteria

- Finance trading-limits overlay refs are owned by `packs/finance`
- Finance tool namespace refs are owned by `packs/finance`
- No new finance-specific owner was added back into core

## Next Unlock

Further staged extraction of finance wording, policy overlays, and tool wiring

## Not Doing

- No directory moves
- No tool implementation migration
- No governance truth rewrite
