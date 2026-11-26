"""Independent generated schema and projection invariants, no native effects."""
from pathlib import Path
import sys

import pytest
from hypothesis import given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "providers/gluetun"))
from native_selection import FILTER_FIELDS, project_settings, selected_snapshot

ALLOWED = {"Japan", "Croatia", "Mexico"}
JSON = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(max_size=12),
    lambda child: st.lists(child, max_size=4) | st.dictionaries(st.text(max_size=8), child, max_size=4),
    max_leaves=12,
)


@settings(max_examples=100, derandomize=True, database=None, deadline=None)
@given(st.lists(st.sampled_from(sorted(ALLOWED)), min_size=1, max_size=3, unique=True),
       st.booleans(), JSON)
def test_projection_preserves_order_and_only_declared_fields(names, lower, extra):
    raw = {"type":"wireguard","provider":{"name":"surfshark","server_selection":{
        "countries":[name.lower() if lower else name for name in names],
        "unrelated":extra}}, "wireguard":extra}
    projected = project_settings(raw, 200)
    assert set(projected) == {"status","type","provider"}
    assert set(projected["provider"]) == {"name","server_selection"}
    assert set(projected["provider"]["server_selection"]) == {"countries",*FILTER_FIELDS}
    assert selected_snapshot(projected, ALLOWED)["countries"] == names


@settings(max_examples=150, derandomize=True, database=None, deadline=None)
@given(st.sampled_from(FILTER_FIELDS), JSON)
def test_alternate_filter_rejection_matches_independent_empty_shape_oracle(field, value):
    raw = {"type":"wireguard","provider":{"name":"surfshark","server_selection":{
        "countries":["Japan"],field:value}}}
    if value is None or type(value) is list and len(value)==0:
        assert selected_snapshot(project_settings(raw,200),ALLOWED)["countries"] == ["Japan"]
    else:
        with pytest.raises(ValueError):
            project_settings(raw,200)
        with pytest.raises(ValueError):
            selected_snapshot(raw,ALLOWED)


@settings(max_examples=100, derandomize=True, database=None, deadline=None)
@given(JSON)
def test_arbitrary_native_envelope_is_explicit_rejection(raw):
    # Generated JSON has only short random keys and no declared native fields.
    # No AttributeError or implicit UNKNOWN-to-success conversion is permitted.
    with pytest.raises(ValueError):
        selected_snapshot(raw, ALLOWED)
