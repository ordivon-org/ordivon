"""Shared bounded metadata-reference observation and admitted provider surfaces.

External artifacts and media bytes remain owned by their providers; the
observations are source-labelled projections, not native content acquisition.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .observatory_contracts import OBSERVATION_KIND

USER_AGENT = "Ordivon-Studio-Cultural-Observatory/0.1 (+https://ordivon.com/)"

@dataclass(frozen=True)
class SourceCapability:
    provider: str
    surface: str
    access: str
    byte_policy: str
    status: str
    note: str

    def as_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "surface": self.surface,
            "access": self.access,
            "bytePolicy": self.byte_policy,
            "status": self.status,
            "note": self.note,
        }


CAPABILITIES = (
    SourceCapability(
        "hacker-news",
        "topstories/newstories",
        "public official Firebase API; no credential",
        "metadata/reference only",
        "live",
        "Near-real-time ranked-link observation with public score/comment signals.",
    ),
    SourceCapability(
        "apple-music",
        "Marketing Tools RSS / Top Songs",
        "public official RSS feed; no credential",
        "metadata/reference/artwork URL only; no media ownership implied",
        "live",
        "Chart rank is an attention signal, not an intrinsic music-quality label.",
    ),
    SourceCapability(
        "guardian",
        "Open Platform section mostViewed/editorsPicks/newest",
        "official API; public test developer key works for bounded research probes",
        "metadata/reference only by default",
        "live",
        "Most-viewed, editorial selection, and newest controls remain distinct selection mechanisms.",
    ),
    SourceCapability(
        "youtube",
        "Data API videos.list chart=mostPopular",
        "official API key required",
        "reference/metadata; audiovisual bytes are not acquired by this apparatus",
        "capability-only",
        "Do not fake a live acceptance when no YouTube API credential is configured.",
    ),
    SourceCapability(
        "douyin",
        "data.external.billboard_hot_video",
        "official client token plus approved scope required",
        "reference/metadata; audiovisual bytes are not acquired by this apparatus",
        "capability-only",
        "Official hot-video statistics are a recent-24h offline product and require permission.",
    ),
    SourceCapability(
        "tiktok",
        "Creative Center / TikTok One inspiration",
        "public human-facing surface; no stable public research ingestion API assumed here",
        "reference/metadata only unless a future admitted API grants more",
        "capability-only",
        "Keep platform-specific observation replaceable; do not scrape a brittle private interface into core authority.",
    ),
    SourceCapability(
        "google-trends",
        "Trends API Alpha",
        "limited alpha access",
        "aggregated attention signal only",
        "capability-only",
        "Useful attention-world context once access exists; not required for R0-R3 acceptance.",
    ),
)




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
