from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

import pytest

from ordivon_agent.response_continuity_r1 import (
    ResponseContinuityError,
    ResponseContinuityReceipt,
    ResponseContinuityStore,
    ResponseDeliveryState,
    ResponseRevisionConflict,
)


def receipt(response_id: str = "response:r1") -> ResponseContinuityReceipt:
    return ResponseContinuityReceipt(
        response_id=response_id,
        caller_id="caller:chatgpt",
        caller_run_ref="conversation:turn-42",
        harness_run_id="harness-run:continuity-r1",
        source_run_revision=7,
        output_digest="sha256:" + "a" * 64,
        evidence_refs=("job:runtime-1", "work:host-1"),
        observed_attention_sequence=12,
        presented_attention_sequence=8,
        state=ResponseDeliveryState.PREPARED,
        revision=1,
        created_at_ms=100,
        updated_at_ms=100,
    )


def test_response_loss_does_not_advance_presentation_or_redispatch_truth() -> None:
    with tempfile.TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as store:
            initial = store.create(receipt())
            unknown = store.transition(
                initial.response_id,
                expected_revision=1,
                state=ResponseDeliveryState.DELIVERY_UNKNOWN,
                updated_at_ms=110,
            )
            assert unknown.state is ResponseDeliveryState.DELIVERY_UNKNOWN
            assert unknown.presented_attention_sequence == 8
            assert (
                store.confirmed_presentation_watermark(initial.caller_id, initial.caller_run_ref)
                == 0
            )
            assert unknown.harness_run_id == initial.harness_run_id
            assert unknown.source_run_revision == initial.source_run_revision


def test_confirmed_delivery_is_the_only_watermark_advance_path() -> None:
    with tempfile.TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as store:
            initial = store.create(receipt())
            emitted = store.transition(
                initial.response_id,
                expected_revision=1,
                state=ResponseDeliveryState.EMITTED,
                updated_at_ms=105,
            )
            with pytest.raises(ResponseContinuityError, match="watermark may advance"):
                store.transition(
                    emitted.response_id,
                    expected_revision=2,
                    state=ResponseDeliveryState.DELIVERY_UNKNOWN,
                    updated_at_ms=106,
                    presented_attention_sequence=12,
                )
            confirmed = store.transition(
                emitted.response_id,
                expected_revision=2,
                state=ResponseDeliveryState.CONFIRMED,
                updated_at_ms=110,
                presented_attention_sequence=12,
            )
            assert confirmed.presented_attention_sequence == 12
            assert (
                store.confirmed_presentation_watermark(initial.caller_id, initial.caller_run_ref)
                == 12
            )


def test_response_identity_and_revision_are_fenced() -> None:
    with tempfile.TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as store:
            initial = store.create(receipt())
            assert store.create(initial) == initial
            different = replace(initial, output_digest="sha256:" + "b" * 64)
            with pytest.raises(ResponseRevisionConflict):
                store.create(different)
            store.transition(
                initial.response_id,
                expected_revision=1,
                state=ResponseDeliveryState.EMITTED,
                updated_at_ms=101,
            )
            with pytest.raises(ResponseRevisionConflict):
                store.transition(
                    initial.response_id,
                    expected_revision=1,
                    state=ResponseDeliveryState.DELIVERY_UNKNOWN,
                    updated_at_ms=102,
                )


def test_latest_receipt_and_confirmed_watermark_survive_reopen() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with ResponseContinuityStore(root) as store:
            first = store.create(receipt("response:first"))
            emitted = store.transition(
                first.response_id,
                expected_revision=1,
                state=ResponseDeliveryState.EMITTED,
                updated_at_ms=120,
            )
            store.transition(
                emitted.response_id,
                expected_revision=2,
                state=ResponseDeliveryState.CONFIRMED,
                updated_at_ms=130,
                presented_attention_sequence=10,
            )
            second = receipt("response:second")
            second = replace(second, created_at_ms=140, updated_at_ms=140)
            store.create(second)
        with ResponseContinuityStore(root) as reopened:
            latest = reopened.latest_for_caller("caller:chatgpt", "conversation:turn-42")
            assert latest is not None and latest.response_id == "response:second"
            assert (
                reopened.confirmed_presentation_watermark("caller:chatgpt", "conversation:turn-42")
                == 10
            )
