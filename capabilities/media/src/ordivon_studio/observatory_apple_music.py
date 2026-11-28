"""Apple Marketing Tools RSS top-songs reference-only source adapter."""

from __future__ import annotations

from typing import Any

from .observatory_contracts import _utc_now
from .observatory_source import _fetch_json, _observation


def collect_apple_music(*, limit: int = 100, storefront: str = "us", timeout: float = 20.0) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    storefront = storefront.lower()
    source_url = f"https://rss.marketingtools.apple.com/api/v2/{storefront}/music/most-played/{limit}/songs.json"
    document = _fetch_json(source_url, timeout=timeout)
    feed = document.get("feed", {}) if isinstance(document, dict) else {}
    results = feed.get("results", []) if isinstance(feed, dict) else []
    observed_at = _utc_now()
    observations: list[dict[str, Any]] = []
    for rank, item in enumerate(results, start=1):
        if not isinstance(item, dict):
            continue
        genres = [genre.get("name") for genre in item.get("genres", []) if isinstance(genre, dict) and isinstance(genre.get("name"), str)]
        observations.append(
            _observation(
                observed_at=observed_at,
                provider="apple-music",
                surface="top-songs",
                encounter_form="music-chart",
                external_id=str(item.get("id") or rank),
                media_kind="song",
                title=str(item.get("name") or ""),
                canonical_url=item.get("url") if isinstance(item.get("url"), str) else None,
                creator=item.get("artistName") if isinstance(item.get("artistName"), str) else None,
                published_at=(str(item.get("releaseDate")) + "T00:00:00Z") if item.get("releaseDate") else None,
                descriptors={"genres": genres, "artistId": item.get("artistId"), "artworkReference": item.get("artworkUrl100")},
                selection_basis="chart-ranked",
                rank=rank,
                pool_size=len(results),
                signals={},
                context={"storefront": storefront, "chart": "most-played"},
                source_url=source_url,
            )
        )
    return observations
