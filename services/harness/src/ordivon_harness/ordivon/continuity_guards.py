from __future__ import annotations

from anc_canonical import JsonValue, canonical_digest

from ..core_contracts import HarnessRunContract
from ..protocol import (
    HarnessDispatchFence,
    HarnessRunSnapshot,
    HarnessToolStepIntent,
    HarnessToolStepReceipt,
)
from ..run_state import HarnessRunState
from ..sqlite_store import SQLiteHarnessStore
from ..store import HarnessRunEventRecord
from .continuity_records import HarnessDispatchFenceV2
from .run_store_port import HarnessRunStoreBinding

# Contract checks and read-only Tool Event validation; callers retain SQLite leases and event writes.


_TOOL_EVENT_KINDS = frozenset(
    {
        "harness.tool-step-prepared",
        "harness.tool-step-recorded",
        "harness.tool-step-unknown",
        "harness.tool-step-reconciled",
    }
)


def require_tool_intent_binding(
    intent: HarnessToolStepIntent, run_id: str, binding: HarnessRunStoreBinding
) -> None:
    if (
        intent.harness_run_id != run_id
        or intent.assignment_id != binding.assignment_id
        or intent.assignment_generation != binding.assignment_generation
        or intent.assignment_digest != binding.assignment_digest
    ):
        raise ValueError("Tool Step Intent differs from the current Run binding")


def require_run_snapshot_binding(
    snapshot: HarnessRunSnapshot,
    run_id: str,
    binding: HarnessRunStoreBinding,
    contract: HarnessRunContract,
) -> None:
    if (
        snapshot.harness_run_id != run_id
        or snapshot.assignment_id != binding.assignment_id
        or snapshot.assignment_generation != binding.assignment_generation
        or snapshot.assignment_digest != binding.assignment_digest
        or snapshot.tool_catalog_digest != contract.tool_catalog_digest
    ):
        raise ValueError("Harness Run Snapshot differs from the current Run binding")


def require_active_budget_consistency(state: HarnessRunState, contract: HarnessRunContract) -> None:
    if state.active_elapsed_ms is None:
        return
    max_wall_time_ms = contract.budget.get("maxWallTimeMs")
    if max_wall_time_ms is None:
        return
    remaining = state.remaining_budget.get("wallTimeMs")
    if (
        type(max_wall_time_ms) is not int
        or max_wall_time_ms < 1
        or type(remaining) is not int
        or remaining != max(0, max_wall_time_ms - state.active_elapsed_ms)
    ):
        raise ValueError(
            "Harness Run active elapsed time differs from its committed wall-time budget"
        )


def validate_snapshot_state(
    snapshot: HarnessRunSnapshot,
    state: HarnessRunState,
) -> None:
    if (
        snapshot.messages_digest != state.messages_digest
        or snapshot.observation_digests != state.observation_digests
        or snapshot.remaining_budget != state.remaining_budget
        or snapshot.requested_model_id != state.requested_model_id
        or snapshot.effective_model_id != state.effective_model_id
    ):
        raise ValueError("Harness Run Snapshot differs from its bounded state")


def continuity_event_id(label: str, digest: str) -> str:
    return f"event:harness-continuity:{label}:{digest[7:31]}"


def required_event_digest(data: dict[str, JsonValue], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str):
        raise ValueError(f"Harness continuity Event field is missing: {field}")
    return value


def validate_tool_event(
    event: HarnessRunEventRecord,
    *,
    store: SQLiteHarnessStore,
    harness_run_id: str,
    binding: HarnessRunStoreBinding,
    allow_tool_content: bool,
) -> None:
    data = event.data
    intent_object_digest = required_event_digest(data, "toolStepIntentObjectDigest")
    raw_intent = store.get_object(
        intent_object_digest,
        expected_kind="harness-tool-step-intent",
    )
    if not isinstance(raw_intent, dict):
        raise ValueError("Harness Tool Step Intent event object is invalid")
    intent = HarnessToolStepIntent.from_dict(raw_intent)
    require_tool_intent_binding(intent, harness_run_id, binding)
    if data.get("toolStepIntentDigest") != intent.digest:
        raise ValueError("Harness Tool Step Intent event digest differs")
    fence_object_digest = data.get("dispatchFenceObjectDigest")
    if fence_object_digest is not None:
        if not isinstance(fence_object_digest, str):
            raise ValueError("Harness Dispatch Fence event reference is invalid")
        raw_fence = store.get_object(
            fence_object_digest,
            expected_kind="harness-dispatch-fence",
        )
        if not isinstance(raw_fence, dict):
            raise ValueError("Harness Dispatch Fence event object is invalid")
        fence = (
            HarnessDispatchFenceV2.from_dict(raw_fence)
            if raw_fence.get("schemaVersion") == 2
            else HarnessDispatchFence.from_dict(raw_fence)
        )
        if data.get("dispatchFenceDigest") != fence.digest or fence.intent_digest != intent.digest:
            raise ValueError("Harness Dispatch Fence event differs")
    receipt_object_digest = data.get("receiptObjectDigest")
    observation_object_digest = data.get("observationObjectDigest")
    if receipt_object_digest is None:
        if observation_object_digest is not None:
            raise ValueError("Harness Tool Observation event lacks its Receipt")
        return
    if not isinstance(receipt_object_digest, str):
        raise ValueError("Harness Tool Step Receipt event reference is invalid")
    raw_receipt = store.get_object(
        receipt_object_digest,
        expected_kind="harness-tool-step-receipt",
    )
    if not isinstance(raw_receipt, dict):
        raise ValueError("Harness Tool Step Receipt event object is invalid")
    receipt = HarnessToolStepReceipt.from_dict(raw_receipt)
    if data.get("receiptDigest") != receipt.digest or receipt.intent_digest != intent.digest:
        raise ValueError("Harness Tool Step Receipt event differs")
    if observation_object_digest is not None:
        if not isinstance(observation_object_digest, str):
            raise ValueError("Harness Tool Observation event reference is invalid")
        raw_observation = store.get_object(
            observation_object_digest,
            expected_kind="harness-tool-observation",
        )
        if not isinstance(raw_observation, dict):
            raise ValueError("Harness Tool Observation event object is invalid")
        if canonical_digest(raw_observation) != receipt.observation_digest:
            raise ValueError("Harness Tool Observation event differs from its Receipt")
    elif allow_tool_content and receipt.observation_digest is not None:
        raise ValueError(
            "Harness Tool Observation content was authorized but its event object is missing"
        )
