"""Concrete type refinement: a Python numeric alias is not a Trace integer."""

from decimal import Decimal
from fractions import Fraction

import pytest

from ordivon_harness.ordivon.events import HarnessRunEvent, HarnessTrace, TraceRecorder


@pytest.mark.parametrize("alias", [True, 1.0, Decimal("1"), Fraction(1, 1)])
def test_event_sequence_cannot_use_equal_numeric_alias(alias: object) -> None:
    with pytest.raises(ValueError, match="exact integer"):
        HarnessRunEvent(alias, "run_started", 0, {})


@pytest.mark.parametrize("alias", [True, 0.0, Decimal("0"), Fraction(0, 1)])
def test_event_timestamp_cannot_use_equal_numeric_alias(alias: object) -> None:
    with pytest.raises(ValueError, match="exact integer"):
        HarnessRunEvent(1, "run_started", alias, {})


def test_trace_identity_cannot_use_bytes_alias() -> None:
    with pytest.raises(ValueError, match="string"):
        HarnessTrace(b"harness-run:foreign", ())


def test_frozen_trace_rejects_mutable_event_container() -> None:
    with pytest.raises(ValueError, match="tuple"):
        HarnessTrace("harness-run:target", [])


@pytest.mark.parametrize("alias", [True, 1.0])
def test_runtime_clock_cannot_supply_numeric_alias(alias: object) -> None:
    recorder = TraceRecorder("harness-run:target", clock_ms=lambda: alias)
    with pytest.raises(ValueError, match="exact integer"):
        recorder.record("run_started", {})


@pytest.mark.parametrize("alias", [True, 1.0])
def test_decoded_trace_schema_version_must_be_exact_integer(alias: object) -> None:
    encoded = HarnessTrace("harness-run:target", ()).to_dict()
    encoded["schemaVersion"] = alias
    with pytest.raises(ValueError, match="version or kind"):
        HarnessTrace.from_dict(encoded)


def test_trace_recorder_cannot_admit_bytes_identity() -> None:
    with pytest.raises(ValueError, match="string"):
        TraceRecorder(b"harness-run:target", clock_ms=lambda: 1)


def test_harness_trace_payload_is_an_immutable_provenance_snapshot() -> None:
    """External aliases, reader views and serialized views cannot rewrite evidence."""
    caller = {"nested": {"effects": [{"identity": "original"}]}}
    event = HarnessRunEvent(1, "run_started", 4, caller)
    trace = HarnessTrace("harness-run:target", (event,))
    original_digest = trace.digest

    caller["nested"]["effects"][0]["identity"] = "caller-forgery"
    event.payload["nested"]["effects"][0]["identity"] = "observer-forgery"
    rendered = trace.to_dict()
    rendered["events"][0]["payload"]["nested"]["effects"][0]["identity"] = "projection-forgery"

    assert trace.digest == original_digest
    assert trace.events[0].payload == {
        "nested": {"effects": [{"identity": "original"}]}
    }
    assert trace.to_dict()["events"][0]["payload"]["nested"]["effects"][0]["identity"] == "original"


def test_harness_live_sink_cannot_mutate_canonical_trace() -> None:
    def malicious_live_sink(event: HarnessRunEvent) -> None:
        event.payload["nested"]["effects"].append({"identity": "sink-forgery"})

    recorder = TraceRecorder(
        "harness-run:target", clock_ms=lambda: 100,
        event_sink=malicious_live_sink,
    )
    nested = {"nested": {"effects": [{"identity": "original"}]}}
    recorder.record("run_started", nested)
    nested["nested"]["effects"].clear()
    trace = recorder.freeze()
    assert trace.events[0].payload == {
        "nested": {"effects": [{"identity": "original"}]}
    }


def test_canonical_payload_snapshot_preserves_exact_json_scalar_types() -> None:
    """The value-to-wire bridge may not confuse bool with int or float."""
    payload = {"present": True, "count": 2**64, "absent": None, "label": "é"}
    event = HarnessRunEvent(1, "run_started", 0, payload)
    assert event.payload == payload
    assert type(event.payload["present"]) is bool
    assert type(event.payload["count"]) is int
    assert HarnessRunEvent.from_dict(event.to_dict()).to_dict() == event.to_dict()
    with pytest.raises(ValueError, match="floating-point values are forbidden"):
        HarnessRunEvent(1, "run_started", 0, {"fraction": 1.0})
