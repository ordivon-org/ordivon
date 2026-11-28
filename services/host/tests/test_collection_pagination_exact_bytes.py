"""Independent full-wire oracle for the linear page byte operator."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_host_v2.canonical_json import canonical_bytes
from ordivon_host_v2.collection_pagination import bounded_page


def _metadata(last, more):
    return {
        "schemaVersion": 1,
        "hasMore": more,
        "cursor": None if last is None else last["cursor"],
        "scope": "中☃",
    }


def _oracle(items, budget, source_more=False):
    if not items:
        result = {**_metadata(None, False), "items": []}
        if len(canonical_bytes(result)) > budget:
            raise ValueError("empty overflow")
        return result
    accepted = None
    for index, item in enumerate(items):
        result = {
            **_metadata(item, source_more or index + 1 < len(items)),
            "items": items[: index + 1],
        }
        if len(canonical_bytes(result)) > budget:
            if accepted is None:
                raise ValueError("first overflow")
            return accepted
        accepted = result
    return accepted


def _optimized(items, budget, source_more=False):
    return bounded_page(
        items,
        max_bytes=budget,
        collection_key="items",
        envelope=_metadata,
        source_has_more=source_more,
        minimum=1,
    )


item = st.fixed_dictionaries(
    {
        "cursor": st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=64),
        "payload": st.lists(
            st.one_of(
                st.integers(-(2**53 - 1), 2**53 - 1),
                st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=80),
                st.none(),
            ),
            max_size=8,
        ),
    }
)


@given(st.lists(item, max_size=30), st.integers(1, 6000), st.booleans())
@settings(max_examples=200, deadline=None)
def test_exact_prefix_matches_independent_full_wire_oracle(items, budget, more):
    more = more and bool(items)
    try:
        expected = _oracle(items, budget, more)
    except ValueError:
        with pytest.raises(ValueError, match="cannot fit"):
            _optimized(items, budget, more)
    else:
        assert _optimized(items, budget, more) == expected


def test_every_exact_byte_boundary_and_shrinking_cursor():
    items = [
        {"cursor": "𐀀" * 80, "payload": ["中", "\n", '"']},
        {"cursor": "a", "payload": [None, 42]},
        {"cursor": "z" * 12, "payload": [True, "é"]},
    ]
    for more in (False, True):
        for end in range(1, len(items) + 1):
            size = len(
                canonical_bytes(
                    {**_metadata(items[end - 1], more or end < len(items)), "items": items[:end]}
                )
            )
            for budget in (size - 1, size, size + 1):
                try:
                    expected = _oracle(items, budget, more)
                except ValueError:
                    with pytest.raises(ValueError):
                        _optimized(items, budget, more)
                else:
                    assert _optimized(items, budget, more) == expected


def test_empty_and_metadata_cannot_shadow_collection():
    assert _optimized([], 1000) == _oracle([], 1000)
    with pytest.raises(ValueError, match="empty response"):
        _optimized([], 1)
    with pytest.raises(ValueError, match="empty source"):
        _optimized([], 1000, True)
    with pytest.raises(ValueError, match="omit its array"):
        bounded_page(
            [1],
            max_bytes=100,
            minimum=1,
            collection_key="items",
            envelope=lambda *_: {"items": []},
            source_has_more=False,
        )


def test_each_item_encoded_once_and_metadata_has_no_collection(monkeypatch):
    import ordivon_host_v2.collection_pagination as pagination

    real = pagination.canonical_bytes
    seen = []

    def observe(value):
        seen.append(value)
        return real(value)

    monkeypatch.setattr(pagination, "canonical_bytes", observe)
    items = [{"cursor": str(i), "payload": ["中" * 100]} for i in range(100)]
    assert _optimized(items, 100000) == _oracle(items, 100000)
    assert len(seen) == 2 * len(items)
    assert all(
        seen[2 * i] is item and seen[2 * i + 1]["items"] == [] for i, item in enumerate(items)
    )
