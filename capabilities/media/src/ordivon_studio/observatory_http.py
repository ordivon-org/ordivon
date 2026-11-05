"""Shared read-only official-source HTTP and observation contracts.

The providers own their remote metadata and rankings. No scraped audiovisual
bytes, editorial currentness, publication authority or duplicate Media truth.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import UTC, datetime
from typing import Any

from .observatory_contracts import OBSERVATION_KIND

USER_AGENT = "Ordivon-Studio-Cultural-Observatory/0.1 (+https://ordivon.com/)"


def _iso_from_epoch(seconds: int | float | None) -> str | None:
    if not isinstance(seconds, (int, float)):
        return None
    return datetime.fromtimestamp(seconds, tz=UTC).isoformat().replace("+00:00", "Z")


def _fetch_json(url: str, *, timeout: float = 20.0) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"GET {url}: HTTP {response.status}")
        return json.load(response)


def _observation(
    *,
    observed_at: str,
    provider: str,
    surface: str,
    encounter_form: str,
    external_id: str,
    media_kind: str,
    title: str,
    canonical_url: str | None,
    creator: str | None = None,
    published_at: str | None = None,
    descriptors: dict[str, Any] | None = None,
    selection_basis: str,
    rank: int | None = None,
    pool_size: int | None = None,
    signals: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    source_url: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": OBSERVATION_KIND,
        "observedAt": observed_at,
        "provider": provider,
        "surface": surface,
        "encounterForm": encounter_form,
        "artifact": {
            "externalId": str(external_id),
            "mediaKind": media_kind,
            "title": title,
            "canonicalUrl": canonical_url,
            "creator": creator,
            "publishedAt": published_at,
            "descriptors": descriptors or {},
        },
        "selection": {
            "basis": selection_basis,
            "rank": rank,
            "poolSize": pool_size,
        },
        "signals": signals or {},
        "context": context or {},
        "acquisition": {
            "mode": "metadata-reference",
            "sourceUrl": source_url,
            "bytesOwned": False,
        },
    }
