"""Property and independent byte oracles for the Host RFC 8785 boundary."""

import hashlib
import json

from hypothesis import example, given, settings
from hypothesis import strategies as st

from ordivon_host_v2.canonical_json import canonical_bytes, canonical_digest


def _assert_expected(value: object, expected: bytes) -> None:
    assert canonical_bytes(value) == expected
    assert canonical_digest(value) == "sha256:" + hashlib.sha256(expected).hexdigest()


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
    # ASCII keys and bounded integers are a domain where stdlib JSON is an
    # independent byte oracle, rather than comparing the same encoder twice.
    expected = json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")
    _assert_expected(values, expected)
    _assert_expected(dict(reversed(list(values.items()))), expected)


@settings(max_examples=55, deadline=None)
@given(
    bmp=st.integers(min_value=0xE000, max_value=0xFFFF),
    astral=st.integers(min_value=0x10000, max_value=0x10FFFF),
    text=st.text(alphabet=st.characters(exclude_categories=("Cs",)), max_size=20),
)
@example(bmp=0xE000, astral=0x10000, text="汉字😀\n")
def test_canonical_json_orders_utf16_recursively_and_preserves_array_order(
    bmp: int, astral: int, text: str
) -> None:
    # RFC 8785 §3.2.3: an astral character starts with a UTF-16 high
    # surrogate (D800-DBFF), before this BMP range, unlike code-point order.
    # Construct the expected order directly; do not call the target encoder
    # or implement a second generic canonicalization algorithm.
    low, high = chr(bmp), chr(astral)
    value = {low: [2, 1], high: [{low: text, high: 7}, 0]}
    ordered = {high: [{high: 7, low: text}, 0], low: [2, 1]}
    expected = json.dumps(ordered, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    _assert_expected(value, expected)
    _assert_expected(ordered, expected)


def test_canonical_json_uses_rfc8785_object_key_order() -> None:
    _assert_expected({"b": 2, "a": 1}, b'{"a":1,"b":2}')
