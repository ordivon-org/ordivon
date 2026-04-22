# Module

Hermes Runtime Shim Reduction

## Layer

Adapter Layer

## Type

Adapter

## Role

Make runtime-owned health and descriptor behavior live on the adapter path and reduce the legacy provider shim to compatibility-only behavior.

## Current Value

- Hermes already resolves through `adapters/runtimes/factory.py`.
- Legacy provider shim still looked too close to the runtime owner on health/metadata behavior.

## Remaining Gap

- API health still instantiated runtime details directly.
- `AgentRuntime` did not yet require runtime-owned health.

## Immediate Action

- Add `health()` to `AgentRuntime`
- Implement health on Hermes and mock runtimes
- Route API health through `resolve_runtime()`
- Remove shim-owned metadata mutation

## Wrong Placement To Avoid

- Do not move Hermes task logic into adapters
- Do not let API own Hermes client construction
- Do not promote shim metadata into system identity

## Required Test Pack

- `python -m compileall adapters intelligence apps/api/app/api/v1/health.py`
- `pytest -q tests/unit/test_hermes_runtime_adapter.py tests/unit/test_reasoning_router.py tests/unit/test_health.py tests/integration/test_hermes_analyze_api.py`

## Done Criteria

- Runtime health is owned by `AgentRuntime` implementations
- API health no longer instantiates Hermes client directly
- Legacy provider remains compatibility-only

## Next Unlock

Further Hermes provider cleanup or future multi-runtime expansion

## Not Doing

- No runtime relocation beyond current adapter home
- No new model provider
- No Hermes task migration
