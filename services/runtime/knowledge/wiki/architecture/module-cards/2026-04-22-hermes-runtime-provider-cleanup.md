# Module

Hermes Runtime Provider Cleanup

## Layer

Adapter Layer

## Type

Adapter

## Role

Make runtime resolution point directly at the Hermes adapter so the old provider path stops looking like the runtime owner.

## Current Value

- `adapters/runtimes/hermes/` already exists.
- `HermesAgentProvider` still sits in the router path and can still be misread as the runtime owner.

## Remaining Gap

- Router resolution is still provider-named rather than adapter-owned.
- The compatibility provider still feels closer to the runtime identity than it should.

## Immediate Action

- Add adapter-backed runtime resolution in the router
- Keep `HermesAgentProvider` only as a legacy shim
- Update tests to assert Hermes runtime ownership through adapter resolution

## Wrong Placement To Avoid

- Do not move Hermes ownership into `apps/api`
- Do not let governance or execution resolve Hermes directly
- Do not remove the legacy shim if callers still rely on it

## Required Test Pack

- `python -m compileall adapters intelligence`
- `pytest -q tests/unit/test_reasoning_router.py tests/unit/test_hermes_runtime_adapter.py tests/integration/test_hermes_analyze_api.py`

## Done Criteria

- Router returns the adapter-backed Hermes runtime directly
- Legacy provider remains available but no longer owns runtime resolution
- Analyze path still works through Hermes-backed runtime resolution

## Next Unlock

Broader Hermes/provider cleanup beyond shim stage

## Not Doing

- No runtime provider deletion
- No large import migration
- No new runtime vendor support
