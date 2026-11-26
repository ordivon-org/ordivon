"""Read-only original Provider evidence and complete effect source scan.

The same immutable reader serves command continuation, Journal terminal
admission and Doctor. It does not allocate a Run execution owner or write.
"""

from __future__ import annotations

from ..core_contracts import HarnessRunContract
from ..protocol import HarnessProviderCallFailureReceipt
from ..run_state import state_from_dict
from ..store import HarnessRunEventRecord, HarnessStore
from .continuity_guards import inspect_all_unsettled_effect_sources, required_event_digest
from .continuity_records import HarnessProviderCallRecordV3, HarnessProviderCallRecordV4
from .model import AgentTurnRequest, AgentTurnResult
from .run_store_port import HarnessRunStoreBinding, StoredHarnessProviderCall


def read_provider_record(
    store: HarnessStore, binding: HarnessRunStoreBinding, event: HarnessRunEventRecord,
) -> StoredHarnessProviderCall:
    """Read immutable Provider evidence without opening the Run command facade."""
    if event.harness_run_id != binding.harness_run_id:
        raise ValueError("Provider Event differs from original Run identity")
    data = event.data
    record_object_digest = required_event_digest(data, "providerCallRecordObjectDigest")
    raw_record = store.get_object(
        record_object_digest,
        expected_kind="harness-provider-call-record",
    )
    if not isinstance(raw_record, dict):
        raise ValueError("Harness Provider Call record object is invalid")
    record_version = raw_record.get("schemaVersion")
    if record_version == 3:
        record = HarnessProviderCallRecordV3.from_dict(raw_record)
    elif record_version == 4:
        record = HarnessProviderCallRecordV4.from_dict(raw_record)
    else:
        raise ValueError("independent Harness Store requires Provider Call v3 or v4")
    if (
        record.harness_run_id != binding.harness_run_id
        or record.binding_digest != binding.digest
    ):
        raise ValueError("Harness Provider Call differs from the current Run binding")
    if data.get("providerCallRecordDigest") != record.digest:
        raise ValueError("Harness Provider Call record digest differs")
    state_object_digest = required_event_digest(data, "stateObjectDigest")
    if state_object_digest != record.state_object_digest:
        raise ValueError("Harness Provider Call state reference differs")
    raw_state = store.get_object(
        state_object_digest,
        expected_kind="harness-run-state",
    )
    if not isinstance(raw_state, dict):
        raise TypeError("Harness Provider Call state object is invalid")
    state = state_from_dict(raw_state, harness_run_id=binding.harness_run_id)
    state_object = store.inspect_object(state_object_digest)

    request = None
    request_object = None
    request_object_digest = data.get("requestObjectDigest")
    retained_request_digest = getattr(record, "request_object_digest", None)
    if retained_request_digest is None:
        if request_object_digest is not None:
            raise ValueError(
                "Provider Call record without request-object binding unexpectedly references one"
            )
    else:
        if request_object_digest != retained_request_digest:
            raise ValueError("Provider Call exact request event reference differs")
        raw_request = store.get_object(
            retained_request_digest,
            expected_kind="agent-turn-request",
        )
        if not isinstance(raw_request, dict):
            raise TypeError("Provider Call exact request object is invalid")
        request = AgentTurnRequest.from_dict(raw_request)
        request_object = store.inspect_object(retained_request_digest)
        if (
            request.dispatch_digest != record.request_digest
            or request.harness_run_id != binding.harness_run_id
            or request.turn_id != record.turn_id
            or request.sequence != record.turn_sequence
        ):
            raise ValueError("Provider Call exact request differs from its record")

    result = None
    result_object = None
    result_object_digest = data.get("resultObjectDigest")
    if result_object_digest is not None:
        if not isinstance(result_object_digest, str):
            raise ValueError("Provider result object reference is invalid")
        raw_result = store.get_object(
            result_object_digest,
            expected_kind="agent-turn-result",
        )
        if not isinstance(raw_result, dict):
            raise TypeError("Provider result object is invalid")
        result = AgentTurnResult.from_dict(raw_result)
        result_object = store.inspect_object(result_object_digest)
        if (
            record.result_digest != result.digest
            or record.result_object_digest != result_object_digest
        ):
            raise ValueError("Provider result differs from its record")
    elif record.result_object_digest is not None:
        raise ValueError("Provider result object reference is incomplete")
    elif record.result_digest is not None and not isinstance(
        record, HarnessProviderCallRecordV4
    ):
        raise ValueError("Provider result content is missing from a non-redacted record")

    failure = None
    failure_object = None
    failure_object_digest = data.get("failureObjectDigest")
    if failure_object_digest is not None:
        if not isinstance(failure_object_digest, str):
            raise ValueError("Provider failure object reference is invalid")
        raw_failure = store.get_object(
            failure_object_digest,
            expected_kind="harness-provider-call-failure",
        )
        if not isinstance(raw_failure, dict):
            raise TypeError("Provider failure object is invalid")
        failure = HarnessProviderCallFailureReceipt.from_dict(raw_failure)
        failure_object = store.inspect_object(failure_object_digest)
        if (
            record.failure_digest != failure.digest
            or record.failure_object_digest != failure_object_digest
        ):
            raise ValueError("Provider failure differs from its record")
    elif record.failure_digest is not None or record.failure_object_digest is not None:
        raise ValueError("Provider failure references are incomplete")
    return StoredHarnessProviderCall(
        record,
        store.inspect_object(record_object_digest),
        state,
        state_object,
        result,
        result_object,
        failure,
        failure_object,
        request=request,
        request_object=request_object,
    )


def inspect_original_effect_sources(
    store: HarnessStore,
    contract: HarnessRunContract,
    events: tuple[HarnessRunEventRecord, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Use the original contract binding on an already qualified source cut."""
    binding = HarnessRunStoreBinding.for_contract(contract)
    return inspect_all_unsettled_effect_sources(
        events,
        store=store,
        harness_run_id=contract.harness_run_id,
        binding=binding,
        allow_tool_content=contract.privacy.allow_tool_content,
        provider_record_reader=lambda event: read_provider_record(store, binding, event),
    )
