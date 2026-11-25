"""Pure matching behavior, freshness boundary, and deterministic ordering."""

from dataclasses import replace

import pytest

from ordivon_gateway.contracts import CapabilityDescriptor, CapabilityProjection
from ordivon_gateway.logic.capability_matching import (
    CapabilitySearchIndex,
    SearchMetadata,
    SearchQuery,
    project_capability_search,
)
from ordivon_gateway.logic.routing import default_routes


def descriptor(route, *, available=False, error=None):
    return CapabilityDescriptor(
        capability=route.capability,
        owner_id=route.owner_id,
        category=route.category,
        configured=True,
        available=available,
        context_mode=route.context_mode,
        truth_boundary=route.truth_boundary,
        description=route.description,
        tags=list(route.tags),
        observation_error=error,
    )


@pytest.mark.parametrize(
    ("query", "kind"),
    [
        ("TEST.STRASSE", "exact"),
        ("test.str", "prefix"),
        ("strasse alpha", "token"),
        ("中文", "substring"),
        ("Σ", "substring"),
        ("zzz", None),
    ],
)
def test_metadata_matches_unicode_and_ascii_token_contract(query, kind):
    route = replace(
        default_routes()["execution.linux"],
        capability="test.Straße",
        description="中文 alpha ς",
    )
    assert SearchMetadata.compile(route).match(SearchQuery.compile(query)) == kind


def test_index_reuses_only_matching_metadata_not_status():
    route = default_routes()["execution.linux"]
    index = CapabilitySearchIndex({route.capability: route})
    old = descriptor(route)
    new = descriptor(route, available=True)
    assert index.metadata_for(old) is index.metadata_for(new)
    changed = new.model_copy(update={"tags": ["new lexical witness"], "description": "fresh"})
    assert index.metadata_for(changed) is not index.metadata_for(new)
    projection = CapabilityProjection(projection_digest="p", capabilities=[changed])
    search = project_capability_search(
        projection,
        query="new lexical witness",
        category=None,
        owner_id=None,
        limit=1,
        include_unavailable=False,
        index=index,
    )
    assert search.total_matches == 1
    assert search.matches[0].capability.available


def test_filter_before_limit_and_unknown_is_not_unavailable():
    template = default_routes()["execution.linux"]
    routes = {
        name: replace(template, capability=name) for name in ("a.search", "b.search", "c.search")
    }
    index = CapabilitySearchIndex(routes)
    projection = CapabilityProjection(
        projection_digest="fresh",
        capabilities=[
            descriptor(routes["a.search"]),
            descriptor(routes["c.search"], available=True),
            descriptor(routes["b.search"], error="unobserved"),
        ],
    )
    result = project_capability_search(
        projection,
        query="search",
        category=None,
        owner_id=None,
        limit=1,
        include_unavailable=False,
        index=index,
    )
    assert result.total_matches == 2
    assert [m.capability.capability for m in result.matches] == ["b.search"]
    assert result.matches[0].capability.readiness_state == "unknown"
    assert result.projection_digest == "fresh"


def test_rank_is_exact_prefix_token_substring_then_name():
    template = default_routes()["execution.linux"]
    routes = {
        name: replace(template, capability=name, description=desc, tags=())
        for name, desc in (
            ("z", "searchable"),
            ("search.more", ""),
            ("a", "search"),
            ("search", ""),
            ("b", "search"),
        )
    }
    index = CapabilitySearchIndex(routes)
    selected = index.candidates(SearchQuery.compile("search"), category=None, owner_id=None)
    assert [r.capability for r in selected] == ["search", "search.more", "a", "b", "z"]
