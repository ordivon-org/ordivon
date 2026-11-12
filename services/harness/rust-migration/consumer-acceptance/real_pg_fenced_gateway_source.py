#!/usr/bin/env python3
"""Produce a REAL Harness Run/Intent/DispatchFenceV2 from disposable PG18.

Called only by the opt-in Gateway native PG consumer test. The producer uses
the EXISTING Harness contracts, one PostgreSQL Store, canonical CAS/Journal,
and the real pre-call physical request qualifier. It does NOT execute a tool,
grant Runtime authority, or manufacture a physical Owner Receipt.
"""

from __future__ import annotations

import json
import os
import secrets
import time

from anc_canonical import canonical_digest
from ordivon_harness.core_contracts import (
    HarnessBoundReference,
    HarnessPrivacyPolicy,
    HarnessRunContract,
)
from ordivon_harness.execution_binding import HarnessExecutionBinding
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.ordivon.runtime_bridge import (
    HarnessRuntimeBridge,
    _require_exact_owner_effect_handoff,
)
from ordivon_harness.ordivon.runtime_lowering import _build_workspace_exec_request
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.protocol import HarnessRecoveryConsequence, HarnessToolStepIntent
from ordivon_harness.run_state import HarnessRunState

dsn = os.environ["ORDIVON_R22_HARNESS_PG_DSN"]
workspace = os.environ["ORDIVON_R22_RUNTIME_WORKSPACE"]
output = os.environ["ORDIVON_R22_EXEC_OUTPUT"]
schema = "harness_r22_source"
run_id = "harness-run:r22-" + secrets.token_hex(9)


class Clock:
    def __init__(self) -> None:
        # The issuer-current real PG admission profile must use an actual
        # cluster-comparable clock. Historical R22 fixtures keep synthetic time.
        self.current = (
            int(time.time() * 1000) - (
                31_000 if os.getenv("ORDIVON_R25_EXPIRED_ISSUER") == "1" else 1
            )
            if os.getenv("ORDIVON_R25_REAL_EPOCH_ISSUER") == "1"
            else 20_000
        )

    def __call__(self) -> int:
        self.current += 1
        return self.current


def sha(label: str) -> str:
    return canonical_digest({"source": "real-pg-r22", "field": label})


contract = HarnessRunContract(
    harness_run_id=run_id,
    harness_implementation_id="ordivon-harness@r22-native-consumer",
    caller_id="caller:r22-pg-native",
    caller_run_ref="trial:" + run_id.removeprefix("harness-run:"),
    objective_ref=HarnessBoundReference("objective:r22", "objective", sha("objective")),
    context_refs=(HarnessBoundReference("context:r22", "context", sha("context")),),
    provider_id="provider:scripted",
    adapter_id=ScriptedTurnAdapter.adapter_id,
    requested_model_id=ScriptedTurnAdapter.model_id,
    tool_catalog_digest=sha("gateway-tool-catalog"),
    tool_grant_digest=sha("gateway-tool-grant"),
    budget={
        "maxModelCalls": 2,
        "maxToolCalls": 1,
        "maxObservationBytes": 65536,
        "maxWallTimeMs": 30000,
        "maxTotalTokens": 4096,
    },
    completion_contract={"mode": "record"},
    system_manifest_ref=HarnessBoundReference(
        "manifest:r22", "system-manifest", sha("system-manifest")
    ),
    created_at_ms=20_000,
    privacy=HarnessPrivacyPolicy(
        content_policy="bounded-private-content",
        allow_model_content=True,
        allow_tool_content=False,
    ),
)
references = (
    {"namespace": "ordivon.harness", "type": "harness_run", "id": run_id},
    {
        "namespace": "ordivon.harness",
        "type": "run_contract",
        "id": run_id,
        "digest": contract.digest,
    },
    {
        "namespace": "ordivon.harness",
        "type": "tool_grant",
        "id": "tool-grant:r22-real-source",
        "digest": contract.tool_grant_digest,
    },
)
binding = HarnessExecutionBinding(
    harness_run_id=run_id,
    workspace_ref=workspace,
    runtime_references=references,
)
original = _build_workspace_exec_request(
    binding,
    step_id="gateway-native-owner-r22",
    executable="/usr/bin/printf",
    args=(output,),
    cwd_relative=".",
    timeout_ms=30_000,
    wait_ms=0,
)
clock = Clock()
with PostgresHarnessStore(dsn, schema=schema, initialize=True) as store:
    assert store.create_run(contract).value == "created"
    continuity = EventSourcedRunContinuity(store, contract, clock_ms=clock)
    continuity.bind_state(
        HarnessRunState(
            messages=(),
            observations=(),
            remaining_budget={"maxTurns": 2},
            requested_model_id=contract.requested_model_id,
            effective_model_id=None,
        )
    )
    binding_run = continuity.binding
    intent = HarnessToolStepIntent(
        intent_id="harness-tool-step-intent:r22-" + secrets.token_hex(6),
        harness_run_id=run_id,
        assignment_id=binding_run.assignment_id,
        assignment_generation=binding_run.assignment_generation,
        assignment_digest=binding_run.assignment_digest,
        turn_id="turn:r22-owner-gateway",
        tool_call_id="tool-call:r22-real-native-pg",
        tool_name="execute_opaque",
        tool_call_digest=sha("tool-call"),
        runtime_operation="workspace.exec",
        runtime_arguments_digest=canonical_digest(original),
        client_request_id=original["clientRequestId"],
        recovery_consequence=HarnessRecoveryConsequence.PROCESS_OR_EXTERNAL_EFFECT_POSSIBLE,
        created_at_ms=clock(),
    )
    continuity.prepare_tool_step(intent, original_request=original)
    actual = continuity.load_current_tool_step()
    assert actual.intent == intent
    assert actual.receipt is None
    assert actual.fence is not None
    continuity.assert_dispatch_fence_current(actual.fence)
    owner_request = HarnessRuntimeBridge._with_dispatch_fence(original, actual.fence)
    _require_exact_owner_effect_handoff(intent, actual.fence, original, owner_request)
    assert owner_request["clientRequestId"] == intent.client_request_id
    assert owner_request["execution"]["foreignReferences"][:-1] == [
        dict(reference) for reference in binding.runtime_references
    ]
    assert owner_request["execution"]["foreignReferences"][-1]["digest"] == actual.fence.digest
    store.validate_run_history(run_id)
    # A fresh reader must see the same authoritative current Tool step.
    loaded = EventSourcedRunContinuity.open(store, run_id).load_current_tool_step()
    assert loaded.intent.digest == intent.digest
    assert loaded.fence.digest == actual.fence.digest
    prepared_revision = store.load_run(run_id).revision
    assert prepared_revision == actual.fence.authority_generation

print(
    json.dumps(
        {
            "runId": run_id,
            "clientRequestId": intent.client_request_id,
            "intentDigest": intent.digest,
            "fenceDigest": actual.fence.digest,
            "foreignReferences": owner_request["execution"]["foreignReferences"],
            "execution": owner_request["execution"],
            "preparedRevision": prepared_revision,
        },
        sort_keys=True,
    )
)
