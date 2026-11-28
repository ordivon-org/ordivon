"""Canonical evidence accepts JSON values, never implicit Python coercions."""

import hashlib
import json
from itertools import product

import pytest

from ordivon_composition import CircuitContractError, canonical_digest


@pytest.mark.parametrize(
    "value",
    [
        {1: "x"},
        {"e": {True: "yes"}},
        {"e": (1, 2)},
        {None: "null"},
        {1.5: "float"},
        {"e": [0, {3: "nested"}]},
        {"e": {1, 2}},
        {1: "x", "1": "y"},
    ],
)
def test_non_json_representations_are_refused(value):
    with pytest.raises(CircuitContractError):
        canonical_digest(value)


def test_cycles_have_typed_refusal():
    cycle = []
    cycle.append(cycle)
    with pytest.raises(CircuitContractError):
        canonical_digest(cycle)


def test_valid_json_digest_preserves_exact_legacy_bytes():
    atoms = (None, False, True, 0, 1, -3, 0.1, -0.0, "汉字", "🚀", "1", "")
    values = [*atoms]
    for a, b in product(atoms, repeat=2):
        values += [[a, b], {"z": a, "a": b}, {"nested": [{"x": a}, b]}]
    for value in values:
        encoded = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        assert canonical_digest(value) == "sha256:" + hashlib.sha256(encoded).hexdigest()
        assert canonical_digest(json.loads(encoded)) == canonical_digest(value)


def test_shared_but_acyclic_containers_remain_valid():
    item = {"key": [1, True, None]}
    assert canonical_digest([item, item]) == canonical_digest(
        [{"key": [1, True, None]}, {"key": [1, True, None]}]
    )
