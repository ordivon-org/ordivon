from __future__ import annotations

from anc_canonical import JsonValue

from ..core_contracts import HarnessRunContract
from ..protocol import HarnessRunSnapshot, HarnessToolStepIntent
from ..run_state import HarnessRunState
from .run_store_port import HarnessRunStoreBinding

# Pure contract checks: callers retain run ownership, SQLite leases and event writes.


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
