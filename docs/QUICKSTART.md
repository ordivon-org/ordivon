---
schema_version: 1
id: harness.quickstart
title: Harness Quick Start
type: guide
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-harness
audience:
  - builder
  - operator
  - agent
updated: 2026-08-08
summary: Minimal path from a clean checkout to deterministic verification, operator inspection and live read-only acceptance.
evidence_status: verified
readiness: READY
applies_to:
  - ordivon-harness
related:
  - harness.start
  - harness.status
  - harness.compatibility
  - harness.operations
---
# Quick start

## Set up

```bash
uv sync
uvx ruff==0.15.17 check src tests scripts
uv run python -m unittest discover -s tests -v
```

Build and verify the exact installable artifact:

```bash
rm -rf dist
uv build --wheel --out-dir dist
python scripts/check_wheel.py "$(find dist -maxdepth 1 -type f -name '*.whl' -print -quit)"
```

The wheel keeps a small Host-free runtime dependency graph: the exact Ordivon Protocol pin, pinned `httpx==0.28.1` for cancellable DeepSeek HTTP/TLS transport, and `jsonschema` for opt-in local structured-result conformance verification. It does not install Host or expose a Host extra.

## Initialize independent state

```bash
ordivon-harness --state-root /var/lib/ordivon/harness store-init
ordivon-harness capabilities
```

## Run

Create one caller-authored `HarnessRunContract` JSON. Harness begins at that exact authority boundary; cross-Run planning, resource allocation, successor selection and retry policy are external.

Harness uses one current sequential Agent-loop scheduling kernel. Workloads that need an explicit deliberation phase compose a caller/domain-owned no-Tool `AgentTurnRequest` and then pass the resulting cognition evidence into the retained `DomainToolLoopRunner`; Harness no longer owns a generic two-phase deliberation lifecycle helper.

Create a caller-authored `HarnessRunContract` JSON. The CLI does not invent Objective, Context, caller identity, Tool grant, budget or completion authority. The recommended API is closed over the values required for basic Contract authoring:

```python
from anc_canonical import canonical_digest
from ordivon_harness.api import HarnessBoundReference, HarnessRunContract, RunBudget

def bound_ref(reference_id: str, kind: str, claim: object) -> HarnessBoundReference:
    return HarnessBoundReference(reference_id, kind, canonical_digest(claim))

budget = RunBudget(
    max_model_calls=2,
    max_tool_calls=0,
    max_observation_bytes=65_536,
    max_wall_time_ms=90_000,
    max_total_tokens=16_384,
)
# Supply caller/objective/context/provider/system identities, the exact Tool catalog/grant
# digests reported by the selected `ordivon-harness capabilities` execution profile, and `budget.to_contract_dict()` to
# HarnessRunContract. Persist `contract.to_dict()` as RUN_CONTRACT.json.
```

`max_tool_calls=0` is valid for a no-Tool Run. Capability comes from the Tool
catalog/grant bound by the Contract; a positive Tool budget never grants a Tool by
itself. `max_tool_corrections` bounds only model-correctable Tool-call rejection;
`max_conclusion_corrections` independently bounds caller/domain conclusion-gate
rejection. Older schema-v1 Contracts that omit `maxConclusionCorrections` remain
readable with the historical default of 3.

```bash
ordivon-harness --state-root /var/lib/ordivon/harness \
  run RUN_CONTRACT.json --message 'Start the bounded Run'

ordivon-harness --state-root /var/lib/ordivon/harness status HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness inspect HARNESS_RUN_ID
ordivon-harness --state-root /var/lib/ordivon/harness explain HARNESS_RUN_ID
```

`capabilities` reports only the execution profiles the CLI actually supports, including their exact source-owned Tool catalog/grant digests. Durable `inspect` exposes the exact retained Run/Contract/Provider/Snapshot/Recovery facts directly. CLI `explain` adds proof boundaries to that same view, while `HarnessAgentRun.explain()` reports validated in-process composition. No aggregate workbench or installed-capability registry sits between those owners and the caller.

For the built-in DeepSeek profile, the Contract must bind the canonical no-Tool catalog/grant and the configured DeepSeek Adapter/model. The current adapter reserves a conservative request-token upper bound equal to the serialized Provider request bytes plus its 8,192-token completion ceiling. A small Contract such as `max_total_tokens=4_096` can therefore be rejected safely before the first Provider dispatch; `16_384` is a practical starting bound for a small no-Tool Run, not a universal required value.

### Supported Python Agent Run surface

For normal Python execution, use `HarnessAgentRun` rather than composing the SQLite Store, Continuity, Provider bridge and `StandaloneHarnessRunner` yourself. The caller still owns the exact Contract and Provider choice; Harness passes the persisted Contract to the caller-supplied Adapter factory before execution. On reopen/resume, Harness mechanically reconstructs Continuity and the exact Snapshot-bound Provider source.

```python
from ordivon_harness.api import HarnessAgentRun, DeepSeekTurnAdapter

run = HarnessAgentRun.create(
    "/var/lib/ordivon/harness",
    contract,
    lambda exact_contract: DeepSeekTurnAdapter(
        settings, completion_contract=exact_contract.completion_contract
    ),
)
execution = run.run(({"role": "user", "content": "Start the bounded Run"},))

run = HarnessAgentRun.open(
    "/var/lib/ordivon/harness",
    contract.harness_run_id,
    lambda exact_contract: DeepSeekTurnAdapter(
        settings, completion_contract=exact_contract.completion_contract
    ),
)
execution = run.resume(
    additional_messages=({"role": "user", "content": "Additional caller input"},)
)
```

The Adapter factory is caller policy, not Harness policy. Static composition is admitted before durable Run creation: unsupported Tool/cognition/Runtime-binding combinations fail before the factory when the Adapter is irrelevant, and Adapter/model/structured-completion mismatches fail after the factory returns but before `harness.run-created`. This preflight does not probe Provider or Runtime liveness.

For Agent-owned durable cognition, the same surface accepts `HarnessCognitionProfile` plus an exact caller-authored `HarnessCognitionSeed`. Build seed sources with `HarnessWorkingViewSource`/`HarnessCognitionSeedSource`; Harness does not discover, rank or summarize them.

For already-selected cross-Run knowledge/procedure sources, the external application/Host/domain owns repository identity, discovery/ranking, semantic evaluation, canonical promotion, and any digest/currentness fence. After verifying one exact `HarnessWorkingViewSource`, it supplies that source directly as a `HarnessCognitionSeedSource`. Harness performs the normal Run privacy and WorkingSet admission only; there is no Harness reusable-reference/resolver/topology subsystem, and external procedure classification grants no Tool authority.

A Tool-bearing application supplies a `HarnessRuntimeClient` through the Python API instead of the primary CLI. `call_tool()` is only the success-shape Protocol. The caller must also translate its transport and Runtime rejection failures into `HarnessRuntimeClientError` / `HarnessRuntimeToolRejected` with a `HarnessRuntimeErrorDetail`. In particular, a Runtime rejection with `commit_state` `not_started` or `not_committed` remains model-correctable; passing an unrelated client exception through unchanged loses that recovery meaning and is treated as a Harness failure. The recommended API also exports `HarnessExecutionBinding`, `HarnessRuntimeReference`, and the independent search catalog/grant digests required by the current `SQLiteHarnessRuntimeBridge`.

Advanced integrations may opt a Run loop into bounded ToolProgram actions. When admitted, the Provider sees a Harness control action that can compose a linear sequence over only the exact Runtime/World Tools present on that `AgentTurnRequest`. Later step arguments may reference exact JSON values from prior observations; every inner step remains a normal physical Tool Call with the existing Tool budget, intent/fence/receipt, cancellation and UNKNOWN handling. Intermediate Tool content is consumed mechanically and is not replayed into model context; the next Provider turn receives one compact program result. This is not a new Runtime Tool, does not grant additional Tools, and is not a general code-execution surface.

When a caller needs a typed semantic result instead of free-form summary text, bind the result shape into the existing completion authority:

```python
from ordivon_harness.api import (
    DeepSeekTurnAdapter,
    HarnessRunContract,
    decode_structured_completion_result,
)

completion_contract = {
    "mode": "structured-result-v1",
    "resultKind": "my-domain-result",
    "resultSchema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": {"choice": {"type": "string", "enum": ["a", "b"]}},
        "required": ["choice"],
    },
}
contract = HarnessRunContract(..., completion_contract=completion_contract, ...)
adapter = DeepSeekTurnAdapter(
    settings, completion_contract=contract.completion_contract
)
# after the Run, with a non-null conclusion:
value = decode_structured_completion_result(contract, execution.loop_result.conclusion)
```

Current authoring opts into local structural validation with the standard JSON Schema Draft 2020-12 `$schema` URI. Historical `structured-result-v1` Contracts that have neither `$schema` nor the retained legacy `conformancePolicy` remain provider-constrained but **not locally schema-verified**, preserving their exact behavior. The old `local-json-schema-draft-2020-12-profile-v1` token remains reader compatibility only for already-persisted Contracts; new examples do not mint it. Local Draft 2020-12 validation rejects structurally invalid Provider results before candidate completion through the existing model-correctable conclusion path. Provider-specific schema compatibility is an Adapter/provider concern rather than a Harness conformance ontology; the DeepSeek Adapter removes the local `$schema` annotation before embedding the caller schema into its function-tool parameters. Structural conformance still does **not** establish semantic correctness, evidence sufficiency, or caller/domain admission.

A candidate-completed Run may still carry explicit unresolved unknowns in
`unresolved_unknowns`; that means the bounded Run produced its candidate while
honestly reporting facts that remain unknown. The caller/domain, not Harness,
decides whether those unknowns block acceptance, justify another strategy, or are
irrelevant. Harness-owned execution stops such as `no_progress` do not synthesize
an Agent conclusion; inspect the stop code/detail and resume state instead. This
keeps a caller-bound structured completion result distinct from Harness execution
disposition.

The exact completion Contract is part of `HarnessRunContract.digest`. `StandaloneHarnessRunner` fails closed if a `structured-result-v1` Contract is paired with an Adapter that was not bound to the same completion Contract. DeepSeek receives the caller schema as the `submit_run_conclusion.result` Tool schema. Harness carries the returned JSON in the optional versioned `AgentRunConclusion.structured_result` field, whose canonical value is explicitly bounded to one MiB; the ordinary `summary` remains compact human/control metadata containing only the result digest. When model-content retention is authorized, the existing terminal conclusion CAS object durably stores the carrier—there is no second result store and no Host-specific result type. `decode_structured_completion_result` reads the carrier first and remains backward-compatible with historical results encoded directly in `summary`; when the local conformance policy is bound it also enforces the same mechanical schema check. **Caller/domain verification remains mandatory**: a result carrier and local schema conformance are not semantic admission.

## Pause and resume

```bash
ordivon-harness --state-root /var/lib/ordivon/harness \
  resume HARNESS_RUN_ID --message 'Additional caller input'
```

## Recovery

```bash
ordivon-harness --state-root /var/lib/ordivon/harness recover HARNESS_RUN_ID
```

Recovery is evidence-driven. A dispatched Provider or Tool operation with an ambiguous physical outcome is not blindly repeated.

## Python API

Use `ordivon_harness.api` for applications. Advanced persistence/continuity composition imports the explicit caller-neutral owner modules directly; the duplicate `ordivon_harness.core` aggregation facade is retired, and the current package does not ship a Host-specific external adapter.
