"""Independent full-serialization oracle for the linear page byte operator."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_host_v2.canonical_json import canonical_bytes
from ordivon_host_v2.collection_pagination import bounded_prefix


def _metadata(last):
    return {"schemaVersion": 1, "hasMore": True, "cursor": last["cursor"], "scope": "中☃"}


def _oracle(items, budget):
    page = []
    for item in items:
        candidate = [*page, item]
        if len(canonical_bytes({**_metadata(item), "items": candidate})) > budget:
            if not page:
                raise ValueError("first overflow")
            return page, True
        page = candidate
    return page, False


def _optimized(items, budget):
    return bounded_prefix(
        items, max_bytes=budget, collection_key="items", envelope=_metadata, minimum=1
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


@given(st.lists(item, max_size=30), st.integers(1, 6000))
@settings(max_examples=200, deadline=None)
def test_exact_prefix_matches_independent_full_wire_oracle(items, budget):
    try:
        expected = _oracle(items, budget)
    except ValueError:
        with pytest.raises(ValueError, match="cannot fit one legal item"):
            _optimized(items, budget)
    else:
        assert _optimized(items, budget) == expected


def test_every_exact_byte_boundary_and_shrinking_cursor():
    items = [
        {"cursor": "𐀀" * 80, "payload": ["中", "\n", '"']},
        {"cursor": "a", "payload": [None, 42]},
        {"cursor": "z" * 12, "payload": [True, "é"]},
    ]
    for end in range(1, len(items) + 1):
        size = len(canonical_bytes({**_metadata(items[end - 1]), "items": items[:end]}))
        for budget in (size - 1, size, size + 1):
            try:
                expected = _oracle(items, budget)
            except ValueError:
                with pytest.raises(ValueError):
                    _optimized(items, budget)
            else:
                assert _optimized(items, budget) == expected


def test_empty_and_metadata_cannot_shadow_collection():
    assert _optimized([], 1) == ([], False)
    with pytest.raises(ValueError, match="omit its array"):
        bounded_prefix(
            [1], max_bytes=100, minimum=1, collection_key="items", envelope=lambda _: {"items": []}
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
    assert _optimized(items, 100000) == (items, False)
    assert len(seen) == 2 * len(items)
    assert all(
        seen[2 * i] is item and seen[2 * i + 1]["items"] == [] for i, item in enumerate(items)
    )
