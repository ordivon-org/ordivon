"""Identity tuple boundaries: preserve normal historical IDs, reject ambiguous bytes."""

import hashlib

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_capital.accounting.durable import (
    CapitalAccountNamespace,
    CapitalAccountRole,
)
from ordivon_capital.accounting.substrate import AccountingMappingError, stable_accounting_id

COMPONENT = st.text(
    alphabet=st.sampled_from(tuple("abcxyz0123456789:-_é中🙂")), min_size=1, max_size=16
)


@settings(max_examples=128, derandomize=True, deadline=None)
@given(namespace=COMPONENT, parts=st.lists(COMPONENT, min_size=1, max_size=6))
def test_valid_components_preserve_exact_legacy_identity(namespace, parts):
    # Independent historical encoding oracle; no claim of collision-free SHA.
    payload = "\x1f".join((namespace, *parts)).encode("utf-8")
    expected = int.from_bytes(hashlib.sha256(payload).digest()[:16], "big") or 1
    assert stable_accounting_id(namespace, *parts) == expected


@settings(max_examples=128, derandomize=True, deadline=None)
@given(a=COMPONENT, b=COMPONENT, c=COMPONENT)
def test_reserved_separator_cannot_alias_component_boundaries(a, b, c):
    left = (a + "\x1f" + b, c)
    right = (a, b + "\x1f" + c)
    assert left != right
    assert "\x1f".join(left) == "\x1f".join(right)
    for pair in (left, right):
        with pytest.raises(AccountingMappingError):
            stable_accounting_id("n", *pair)
        with pytest.raises(AccountingMappingError):
            CapitalAccountNamespace(*pair).account(CapitalAccountRole.AVAILABLE)


@pytest.mark.parametrize("bad", [None, 0, True, [], b"bytes", "\ud800", "x\x1fy", "  "])
def test_invalid_identity_components_are_domain_errors(bad):
    with pytest.raises(AccountingMappingError):
        stable_accounting_id(bad, "valid")
    with pytest.raises(AccountingMappingError):
        stable_accounting_id("valid", bad)
