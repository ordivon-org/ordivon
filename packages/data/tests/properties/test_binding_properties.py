"""Generated behavioral tests against an independent finite-list relation."""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from ordivon_data.binding_selection import LocalEvidenceBinding, select_bindings
from ordivon_data.consumer_selection import select_ports

UUID = "4b2a0b92-e9d6-5f31-8157-a1c16e4ef34b"
# Explicit generated equivalence classes, not the implementation's UUID parser.
ALIASES = {UUID: UUID, UUID.upper(): UUID, UUID.replace("-", ""): UUID}
IDS = st.sampled_from([*ALIASES, "Owner-A", "owner-a"])
VERSIONS = st.sampled_from(["1", "2", "3"])
NAMES = st.sampled_from(["manifest", "table", "other"])
OPTIONAL_VERSION = st.one_of(st.none(), VERSIONS)
PORTS = st.fixed_dictionaries(
    {
        "name": NAMES,
        "version": OPTIONAL_VERSION,
        "type": st.sampled_from(["file/json", "file/csv", "file/parquet", "api/rest"]),
    }
)
PRODUCTS = st.fixed_dictionaries(
    {"id": IDS, "version": VERSIONS, "outputPorts": st.lists(PORTS, max_size=5)}
)


def binding(row):
    pid, version, name, port_version = row
    return LocalEvidenceBinding(
        pid,
        name,
        "path",
        "sha",
        Path("/unused"),
        port_version=port_version,
        product_version=version,
    )


def reference(products, requests):
    """Slow direct relation; does not share the production index or helpers."""
    result = []
    for request in requests:
        candidates = [
            (i, p)
            for i, p in enumerate(products)
            if ALIASES.get(p["id"], p["id"])
            == ALIASES.get(request.product_id, request.product_id)
            and (
                request.product_version is None
                or p["version"] == request.product_version
            )
        ]
        if len(candidates) != 1:
            return None
        i, p = candidates[0]
        matches = [
            (j, port)
            for j, port in enumerate(p["outputPorts"])
            if port["name"] == request.port_name
            and (
                request.port_version is None
                or port.get("version") == request.port_version
            )
        ]
        if len(matches) != 1:
            return None
        j, port = matches[0]
        if port["type"] not in {"file/json", "file/csv", "file/parquet"}:
            return None
        if (i, j) in result:
            return None
        result.append((i, j))
    return result


def observed(products, requests):
    try:
        return [(i, j) for i, j, _ in select_bindings(products, tuple(requests))]
    except ValueError:
        return None


@given(
    st.lists(PRODUCTS, max_size=6),
    st.lists(st.tuples(IDS, OPTIONAL_VERSION, NAMES, OPTIONAL_VERSION), max_size=8),
)
@settings(max_examples=600, derandomize=True, database=None, deadline=None)
def test_index_matches_independent_finite_relation(products, rows):
    requests = [binding(row) for row in rows]
    assert observed(products, requests) == reference(products, requests)


@given(
    st.permutations(("1", "2", "3")),
    st.permutations(("1", "2", "3")),
    st.permutations(("manifest", "table", "other")),
    IDS,
)
@settings(max_examples=150, derandomize=True, database=None, deadline=None)
def test_exact_demands_invariant_under_product_port_and_request_permutation(
    product_order, request_order, port_order, pid
):
    products = [
        {
            "id": pid,
            "version": v,
            "outputPorts": [
                {"name": name, "version": "1", "type": "file/json"}
                for name in port_order
            ],
        }
        for v in product_order
    ]
    requests = [
        binding((pid, v, n, "1"))
        for v in request_order
        for n in ("manifest", "table", "other")
    ]
    selected = select_bindings(products, tuple(requests))
    actual = [
        (products[i]["version"], products[i]["outputPorts"][j]["name"])
        for i, j, _ in selected
    ]
    assert actual == [(r.product_version, r.port_name) for r in requests]
    assert observed(products, requests) == reference(products, requests)


@given(IDS, OPTIONAL_VERSION, NAMES)
@settings(max_examples=100, derandomize=True, database=None, deadline=None)
def test_legacy_ambiguity_and_duplicate_requests_never_collapse(pid, version, name):
    ports = [{"name": name, "version": version, "type": "file/json"}]
    product = {"id": pid, "version": "1", "outputPorts": ports}
    unique = binding((pid, None, name, None))
    assert observed([product], [unique]) == [(0, 0)]
    assert observed([product, {**product, "version": "2"}], [unique]) is None
    assert observed([product], [unique, unique]) is None
    assert observed([{**product, "outputPorts": ports * 2}], [unique]) is None


@given(st.sampled_from(list(ALIASES)), st.sampled_from(list(ALIASES)), VERSIONS)
@settings(max_examples=100, derandomize=True, database=None, deadline=None)
def test_uuid_aliases_share_identity_but_not_version(source, requested, version):
    ports = [{"name": "manifest", "version": "1", "type": "file/json"}]
    product = {"id": source, "version": version, "outputPorts": ports}
    exact = binding((requested, version, "manifest", "1"))
    assert observed([product], [exact]) == [(0, 0)]
    assert observed([product, {**product, "id": requested}], [exact]) is None
    other = {**product, "id": requested, "version": "other"}
    assert observed([product, other], [exact]) == [(0, 0)]
    assert (
        observed([product, other], [binding((requested, None, "manifest", "1"))])
        is None
    )


@given(
    st.lists(
        st.fixed_dictionaries(
            {
                "id": IDS,
                "version": VERSIONS,
                "distributions": st.lists(
                    st.fixed_dictionaries(
                        {
                            "id": st.one_of(st.none(), NAMES),
                            "verification": st.sampled_from(
                                ["UNKNOWN", "FALSIFIED", "VERIFIED"]
                            ),
                        }
                    ),
                    max_size=5,
                ),
            }
        ),
        max_size=6,
    ),
    st.lists(st.tuples(IDS, VERSIONS, NAMES), max_size=8),
)
@settings(max_examples=400, derandomize=True, database=None, deadline=None)
def test_consumer_gate_matches_direct_observation_relation(products, demands):
    requests = [list(row) for row in demands]
    normalized = [
        (ALIASES.get(pid, pid), version, port) for pid, version, port in demands
    ]
    expected = None
    if len(set(normalized)) == len(normalized):
        expected = []
        for pid, version, port in normalized:
            matches = [
                d["verification"]
                for p in products
                if ALIASES.get(p["id"], p["id"]) == pid and p["version"] == version
                for d in p["distributions"]
                if d["id"] == port
            ]
            if len(matches) > 1:
                expected = None
                break
            expected.append(matches[0] if matches else "UNKNOWN")
    try:
        result = [r["verification"] for r in select_ports(products, requests)]
    except ValueError:
        result = None
    assert result == expected
