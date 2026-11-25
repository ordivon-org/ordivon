"""Deterministic metadata matching, separate from readiness and Owner I/O.

Compile immutable route metadata once per catalog. The index contains no status,
grants, sessions or independently writable state. Observed descriptors only reuse
compiled data when their complete matching metadata is identical.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from ..contracts import (
    CapabilityDescriptor,
    CapabilityProjection,
    CapabilityRoute,
    CapabilitySearchMatch,
    CapabilitySearchProjection,
)

MatchKind = Literal["exact", "prefix", "token", "substring"]
_PRIORITY = {"exact": 0, "prefix": 1, "token": 2, "substring": 3}
_WORD = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True, slots=True)
class SearchQuery:
    normalized: str
    tokens: frozenset[str]

    @classmethod
    def compile(cls, query: str) -> SearchQuery:
        normalized = query.casefold()
        return cls(normalized, frozenset(_WORD.findall(normalized)))


def _signature(item: CapabilityRoute | CapabilityDescriptor) -> tuple[str, ...]:
    return (item.capability, item.category, item.owner_id, item.description, *item.tags)


@dataclass(frozen=True, slots=True)
class SearchMetadata:
    signature: tuple[str, ...]
    name: str
    corpus: str
    tokens: frozenset[str]

    @classmethod
    def compile(cls, item: CapabilityRoute | CapabilityDescriptor) -> SearchMetadata:
        signature = _signature(item)
        corpus = " ".join(value.casefold() for value in signature if value)
        return cls(signature, item.capability.casefold(), corpus, frozenset(_WORD.findall(corpus)))

    def match(self, query: SearchQuery) -> MatchKind | None:
        if query.normalized == self.name:
            return "exact"
        if self.name.startswith(query.normalized):
            return "prefix"
        if query.tokens and query.tokens.issubset(self.tokens):
            return "token"
        if query.normalized in self.corpus:
            return "substring"
        return None


class CapabilitySearchIndex:
    """Rebuildable index of the same immutable route objects used for dispatch."""

    def __init__(self, routes: Mapping[str, CapabilityRoute]) -> None:
        self._entries = tuple((route, SearchMetadata.compile(route)) for route in routes.values())
        self._by_capability = {route.capability: metadata for route, metadata in self._entries}

    def candidates(
        self, query: SearchQuery, *, category: str | None, owner_id: str | None
    ) -> list[CapabilityRoute]:
        ranked: list[tuple[int, str, CapabilityRoute]] = []
        for route, metadata in self._entries:
            if category is not None and route.category != category:
                continue
            if owner_id is not None and route.owner_id != owner_id:
                continue
            kind = metadata.match(query)
            if kind is not None:
                ranked.append((_PRIORITY[kind], route.capability, route))
        ranked.sort(key=lambda row: (row[0], row[1]))
        return [route for _, _, route in ranked]

    def metadata_for(self, item: CapabilityDescriptor) -> SearchMetadata:
        cached = self._by_capability.get(item.capability)
        if cached is not None and cached.signature == _signature(item):
            return cached
        # A separately constructed projection may not share the route metadata.
        # Never apply a stale lexical rank merely because names happen to match.
        return SearchMetadata.compile(item)


def candidate_routes_for_search(
    routes: Mapping[str, CapabilityRoute],
    *,
    query: str,
    category: str | None,
    owner_id: str | None,
) -> list[CapabilityRoute]:
    """One-off pure selection; long-lived catalogs reuse the compiled index."""
    return CapabilitySearchIndex(routes).candidates(
        SearchQuery.compile(query), category=category, owner_id=owner_id
    )


def project_capability_search(
    projection: CapabilityProjection,
    *,
    query: str,
    category: str | None,
    owner_id: str | None,
    limit: int,
    include_unavailable: bool,
    index: CapabilitySearchIndex | None = None,
) -> CapabilitySearchProjection:
    """Rank actual observations; UNKNOWN remains included when requested."""
    compiled = SearchQuery.compile(query)
    ranked: list[tuple[int, str, CapabilityDescriptor, MatchKind]] = []
    for item in projection.capabilities:
        if category is not None and item.category != category:
            continue
        if owner_id is not None and item.owner_id != owner_id:
            continue
        if not include_unavailable and not item.available and item.observation_error is None:
            continue
        metadata = index.metadata_for(item) if index is not None else SearchMetadata.compile(item)
        kind = metadata.match(compiled)
        if kind is not None:
            ranked.append((_PRIORITY[kind], item.capability, item, kind))
    ranked.sort(key=lambda row: (row[0], row[1]))
    # Construct public match objects only for results the consumer receives.
    matches = [
        CapabilitySearchMatch(match_kind=kind, capability=item)
        for _, _, item, kind in ranked[:limit]
    ]
    return CapabilitySearchProjection(
        query=query,
        projection_digest=projection.projection_digest,
        route_digest=projection.route_digest,
        total_matches=len(ranked),
        matches=matches,
    )
