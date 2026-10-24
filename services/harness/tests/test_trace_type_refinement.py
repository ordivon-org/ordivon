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
