# Module

Hermes Provider Alias Cleanup

## Layer

Adapter Layer

## Type

Adapter

## Role

Reduce the old Hermes provider path from a behavior-bearing shim to a pure compatibility alias so adapter ownership is clearer.

## Current Value

- Hermes runtime already lives in `adapters/runtimes/hermes/`.
- Router and health resolution are already adapter-first.
- Legacy provider path still existed as a wrapper class.

## Remaining Gap

- The old path could still be misread as an owner rather than a compatibility export.
- Shim behavior was still more than the minimum needed for import stability.

## Immediate Action

- Replace wrapper logic with a compatibility alias to `HermesRuntime`
- Keep adapter-owned runtime behavior unchanged
- Add regression coverage for the legacy import path

## Wrong Placement To Avoid

- Do not move task logic into adapters
- Do not let compatibility exports regain runtime ownership
- Do not reintroduce Hermes-specific behavior into API, governance, or execution

## Required Test Pack

- `python -m compileall intelligence/providers adapters/runtimes/hermes`
- `pytest -q tests/unit/test_hermes_runtime_adapter.py tests/unit/test_reasoning_router.py tests/integration/test_hermes_analyze_api.py`

## Done Criteria

- Legacy provider path is only a compatibility alias
- Adapter layer remains the runtime owner
- Hermes analyze path still works without regression

## Next Unlock

Future cleanup of legacy docs/imports that still describe provider-owned Hermes behavior

## Not Doing

- No task relocation
- No new runtime provider
- No full adapter package reorganization
