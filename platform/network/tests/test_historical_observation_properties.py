"""Generated historical window coverage and latency partition contracts."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest
from hypothesis import given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "providers/gluetun"))
from historical_observation import (
    JOBS, PairedSample, paired_matrix, parse_matrix, summarize_samples, window_coverage,
)

START = datetime(2026, 11, 13, tzinfo=timezone.utc)


@settings(max_examples=150, derandomize=True, database=None, deadline=None)
@given(st.lists(st.booleans(), min_size=13, max_size=60))
def test_regular_grid_coverage_matches_independent_missing_slot_oracle(present):
    # 30-second slots, 45-second silence budget. An interior omitted slot
    # is necessarily a 60-second gap. At most one slot may be absent at
    # each edge. This reference uses missing-slot indices, not gap arithmetic.
    end = START + timedelta(seconds=30*(len(present)-1))
    samples = tuple(PairedSample(START.timestamp()+30*i, 1.0, .1)
                    for i, available in enumerate(present) if available)
    indices = [i for i, available in enumerate(present) if available]
    expected = (len(indices) >= 12 and indices[0] <= 1
                and indices[-1] >= len(present)-2
                and all(present[indices[0]:indices[-1]+1]))
    assert window_coverage(samples, START, end, minimum=12, max_gap=45).complete == expected


@settings(max_examples=100, derandomize=True, database=None, deadline=None)
@given(st.lists(st.tuples(st.sampled_from([0.0,1.0]),
                         st.integers(min_value=0,max_value=30000)), min_size=1,max_size=80))
def test_latency_partition_preserves_counts_and_does_not_impute_empty_classes(values):
    samples = tuple(PairedSample(START.timestamp()+30*i, ok, ms/1000)
                    for i,(ok,ms) in enumerate(values))
    result = summarize_samples(samples)
    success = [ms for ok,ms in values if ok == 1]
    failure = [ms for ok,ms in values if ok == 0]
    assert result["samples"] == len(values)
    assert result["successRatio"] == len(success)/len(values)
    for key, expected in (("successfulProbeLatency",success),("failedProbeLatency",failure)):
        stats = result[key]
        assert stats["samples"] == len(expected)
        if not expected:
            assert stats["medianMs"] is None and stats["p90Ms"] is None
        else:
            assert min(expected) <= stats["medianMs"] <= max(expected)
            assert min(expected) <= stats["p90Ms"] <= max(expected)


@pytest.mark.parametrize("times,expected", [
    ([0,30,60,90,120,150,180,210,240,270,300,345], True),
    ([0,30,60,90,120,150,180,210,240,270,300,346], False),
    ([0,30,60,90,120,150,180,210,240,270,300,300], False),
    ([0,30,60,90,120,150,180,210,240,270,300,360], False),
])
def test_coverage_exact_boundary(times,expected):
    end = START + timedelta(seconds=345)
    samples = tuple(PairedSample(START.timestamp()+i,1.0,.1) for i in times)
    assert window_coverage(samples,START,end,minimum=12,max_gap=45).complete == expected


@pytest.mark.parametrize("bad", [
    {"values":None},
    {"values":[[START.timestamp(), True]]},
    {"values":[[True, "1"]]},
    {"values":[[START.timestamp()]]},
    {"values":[[START.timestamp(), "2"]]},
])
def test_malformed_native_values_never_form_pair(bad):
    j = JOBS[0]
    row = {"metric":{"job":j}, "values":[[START.timestamp(),"1"]]}
    assert j not in paired_matrix([row|bad],[row],START,START+timedelta(seconds=30))


@pytest.mark.parametrize("bad", [None, {}, {"metric":{"job":1}}, {"metric":[] }])
def test_missing_or_malformed_source_identity_rejected(bad):
    with pytest.raises(ValueError):
        parse_matrix([bad],"probe_success",START,START+timedelta(seconds=30))


def test_internal_gap_cannot_be_hidden_by_good_edge_coverage():
    times = [0,30,60,90,120,150,180,210,240,270,300,346]
    samples = tuple(PairedSample(START.timestamp()+i,1.0,.1) for i in times)
    report = window_coverage(samples,START,START+timedelta(seconds=360),minimum=12,max_gap=45)
    assert report.leading_gap_seconds == 0
    assert report.trailing_gap_seconds == 14
    assert report.max_internal_gap_seconds == 46
    assert not report.complete


def test_overflowing_latency_is_not_admitted():
    j = JOBS[0]
    stamp = START.timestamp()
    row = {"metric":{"job":j},"values":[[stamp,"1e308"]]}
    assert not parse_matrix([row],"probe_duration_seconds",START,START+timedelta(seconds=30))
