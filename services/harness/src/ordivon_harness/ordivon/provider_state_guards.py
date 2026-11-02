from __future__ import annotations

from anc_canonical import JsonValue

from ..run_state import HarnessRunState
from .run_store_port import HarnessProviderCallRequestMismatch, HarnessProviderCallSourceRef

# Pure Provider Call identity/settlement guards; durable state and mutation stay in the store.

def _require_provider_request_matches(
    record,
    *,
    source: HarnessProviderCallSourceRef,
    turn_id: str,
    turn_sequence: int,
    request_digest: str,
    provider_request_digest: str,
    request_object_digest: str | None,
    adapter_id: str,
    requested_model_id: str,
) -> None:
    if (
        record.source_kind is not source.kind
        or record.source_digest != source.digest
        or record.source_object_digest != source.object_digest
        or record.turn_id != turn_id
        or record.turn_sequence != turn_sequence
        or record.request_digest != request_digest
        or record.provider_request_digest != provider_request_digest
        or getattr(record, "request_object_digest", None) != request_object_digest
        or record.adapter_id != adapter_id
        or record.requested_model_id != requested_model_id
    ):
        raise HarnessProviderCallRequestMismatch(
            "Provider Call identity was reused with different immutable input"
        )


def _require_provider_settlement_state(
    previous: HarnessRunState,
    current: HarnessRunState,
    *,
    label: str,
    consume_retry: bool,
) -> None:
    """One settlement invariant; only a safe retry consumes retry budget."""
    if (
        previous.messages_digest != current.messages_digest
        or previous.observation_digests != current.observation_digests
        or previous.requested_model_id != current.requested_model_id
        or previous.effective_model_id != current.effective_model_id
        or previous.seen_model_call_ids != current.seen_model_call_ids
        or previous.seen_tool_call_ids != current.seen_tool_call_ids
        or previous.provider_usage != current.provider_usage
        or previous.effective_model_ids != current.effective_model_ids
        or set(previous.remaining_budget) != set(current.remaining_budget)
    ):
        scope = "retry accounting" if consume_retry else "active time"
        raise HarnessProviderCallRequestMismatch(
            f"{label} state changed outside {scope}"
        )
    if consume_retry:
        previous_retries = previous.remaining_budget.get("modelRetries")
        current_retries = current.remaining_budget.get("modelRetries")
        if (
            type(previous_retries) is not int
            or type(current_retries) is not int
            or current_retries != previous_retries - 1
        ):
            raise HarnessProviderCallRequestMismatch(
                "Provider Call safe retry did not consume exactly one retry"
            )
    for field, previous_value in previous.remaining_budget.items():
        if consume_retry and field == "modelRetries":
            continue
        current_value = current.remaining_budget[field]
        if field == "wallTimeMs":
            if (
                type(previous_value) is not int
                or type(current_value) is not int
                or current_value > previous_value
            ):
                raise HarnessProviderCallRequestMismatch(
                    f"{label} revived its wall-time budget"
                )
        elif current_value != previous_value:
            raise HarnessProviderCallRequestMismatch(
                f"{label} changed a non-time budget"
            )
    _require_provider_time_monotonic(previous, current, label=label)


def _require_provider_outcome_state(
    previous: HarnessRunState,
    current: HarnessRunState,
    *,
    label: str = "Provider Call outcome",
) -> None:
    _require_provider_settlement_state(
        previous, current, label=label, consume_retry=False
    )


def _require_provider_safe_retry_state(
    previous: HarnessRunState,
    current: HarnessRunState,
) -> None:
    _require_provider_settlement_state(
        previous, current, label="Provider Call safe retry", consume_retry=True
    )


def _require_provider_time_monotonic(
    previous: HarnessRunState,
    current: HarnessRunState,
    *,
    label: str,
) -> None:
    previous_elapsed = previous.active_elapsed_ms
    current_elapsed = current.active_elapsed_ms
    if previous_elapsed is not None and (
        current_elapsed is None or current_elapsed < previous_elapsed
    ):
        raise HarnessProviderCallRequestMismatch(f"{label} active elapsed time decreased")
    previous_wall = previous.remaining_budget.get("wallTimeMs")
    current_wall = current.remaining_budget.get("wallTimeMs")
    if (
        type(previous_wall) is not int
        or type(current_wall) is not int
        or current_wall > previous_wall
    ):
        raise HarnessProviderCallRequestMismatch(f"{label} remaining wall time increased")


def _require_failure_matches(record, failure) -> None:
    if (
        failure.provider_call_id != record.provider_call_id
        or failure.request_digest != record.request_digest
        or failure.provider_request_digest != record.provider_request_digest
    ):
        raise HarnessProviderCallRequestMismatch(
            "Provider failure receipt differs from the current attempt"
        )


def require_provider_continuation_state(
    record,
    *,
    snapshot_state: HarnessRunState,
    provider_state: HarnessRunState,
    additional_messages: tuple[dict[str, JsonValue], ...],
    max_model_calls: JsonValue,
) -> None:
    expected_prefix = snapshot_state.messages + tuple(
        dict(message) for message in additional_messages
    )
    ordered_sequences = (
        (snapshot_state.observations, provider_state.observations),
        (snapshot_state.provider_usage, provider_state.provider_usage),
        (snapshot_state.effective_model_ids, provider_state.effective_model_ids),
    )
    if (
        provider_state.requested_model_id != snapshot_state.requested_model_id
        or provider_state.requested_model_id != record.requested_model_id
        or provider_state.messages[: len(expected_prefix)] != expected_prefix
        or any(current[: len(previous)] != previous for previous, current in ordered_sequences)
        or not set(snapshot_state.seen_model_call_ids).issubset(
            provider_state.seen_model_call_ids
        )
        or not set(snapshot_state.seen_tool_call_ids).issubset(
            provider_state.seen_tool_call_ids
        )
    ):
        raise HarnessProviderCallRequestMismatch(
            "Provider Call state is not a continuation of the resume Snapshot"
        )
    _require_provider_time_monotonic(
        snapshot_state,
        provider_state,
        label="Provider Call continuation",
    )
    max_calls = max_model_calls
    snapshot_remaining = snapshot_state.remaining_budget.get("modelCalls")
    provider_remaining = provider_state.remaining_budget.get("modelCalls")
    if (
        type(max_calls) is not int
        or type(snapshot_remaining) is not int
        or type(provider_remaining) is not int
    ):
        raise HarnessProviderCallRequestMismatch(
            "Provider Call state omitted its model-call budget"
        )
    snapshot_calls = max_calls - snapshot_remaining
    provider_calls = max_calls - provider_remaining
    if (
        snapshot_calls < 0
        or provider_calls < snapshot_calls
        or record.turn_sequence != provider_calls + 1
    ):
        raise HarnessProviderCallRequestMismatch(
            "Provider Call turn differs from its saved Run state"
        )
    durable_caller_ingress = False
    if provider_state.messages[: len(snapshot_state.messages)] == snapshot_state.messages:
        for message in provider_state.messages[len(snapshot_state.messages) :]:
            if (
                set(message) == {"role", "content"}
                and message.get("role") == "user"
                and isinstance(message.get("content"), str)
            ):
                durable_caller_ingress = True
                continue
            break
    resettable = (
        {"observationOnlyTurns", "noProgressTurns"}
        if additional_messages or durable_caller_ingress
        else set()
    )
    for field, snapshot_value in snapshot_state.remaining_budget.items():
        if field in resettable:
            continue
        provider_value = provider_state.remaining_budget.get(field)
        if type(snapshot_value) is int and (
            type(provider_value) is not int or provider_value > snapshot_value
        ):
            raise HarnessProviderCallRequestMismatch(
                "Provider Call budget is not a continuation of the Snapshot"
            )
