"""Upstream Hypothesis tests for the real Host RFC 8785 boundary."""

from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_host_v2.canonical_json import canonical_bytes, canonical_digest


@settings(max_examples=55, deadline=None)
@given(
    st.dictionaries(
        keys=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=9),
        values=st.integers(min_value=-1_000_000, max_value=1_000_000),
        min_size=2,
        max_size=9,
    )
)
def test_canonical_json_is_invariant_under_insertion_order(values: dict[str, int]) -> None:
    reversed_values = dict(reversed(list(values.items())))
    assert canonical_bytes(values) == canonical_bytes(reversed_values)
    assert canonical_digest(values) == canonical_digest(reversed_values)


def test_canonical_json_uses_rfc8785_object_key_order() -> None:
    assert canonical_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
