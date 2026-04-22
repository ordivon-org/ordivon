# Module

Hermes Runtime Adapter Extraction

## Layer

Adapter Layer

## Type

Adapter

## Role

Introduce a real Hermes runtime adapter home without breaking the current intelligence entrypoints.

## Current Value

- Hermes already works through `intelligence/providers/hermes_agent_provider.py`
- `AgentRuntime` exists
- analyze already depends on Hermes behavior in production mode

## Remaining Gap

- Hermes still lives only under `intelligence/`
- provider and runtime ownership are too close
- there is no explicit adapter home under `adapters/`

## Immediate Action

- Add `adapters/runtimes/hermes/`
- Implement `HermesRuntime`
- Make `HermesAgentProvider` a shim/facade over `HermesRuntime`
- Keep router behavior stable while ensuring Hermes resolution is adapter-backed

## Wrong Placement To Avoid

- Do not move Hermes ownership into `apps/api`
- Do not let `governance` or `execution` depend on Hermes runtime internals
- Do not move task contracts or task builders out of `intelligence/`

## Required Test Pack

- `python -m compileall adapters intelligence`
- `pytest -q tests/unit/test_hermes_client.py tests/unit/test_hermes_runtime_adapter.py`
- `pytest -q tests/integration/test_hermes_analyze_api.py`

## Done Criteria

- `adapters/runtimes/hermes/` exists
- Hermes adapter implements runtime contract
- `HermesAgentProvider` is adapter-backed
- analyze path still works unchanged

## Next Unlock

Orchestration | HandoffArtifact

## Not Doing

- No physical task relocation
- No provider pluralization
- No runtime routing overhaul beyond Hermes-backed shim behavior
