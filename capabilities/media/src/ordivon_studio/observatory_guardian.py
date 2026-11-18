"""Guardian official section most-viewed, editorial and newest-control adapter.

These are distinct selection mechanisms, not equivalent quality labels.
An actual authorized Guardian Open Platform API key is required. No fallback
to undocumented scraping or an unverified public test key is attempted.
"""

from __future__ import annotations

import os
import urllib.parse
from collections.abc import Iterable
from typing import Any

from .observatory_contracts import _utc_now
from .observatory_source import _fetch_json, _observation

DEFAULT_GUARDIAN_SECTIONS = ("world", "technology", "culture", "business", "science", "lifeandstyle")


def collect_guardian(
    *,
    sections: Iterable[str] = DEFAULT_GUARDIAN_SECTIONS,
    newest_per_section: int = 40,
    timeout: float = 20.0,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    # The prior anonymous test key returned HTTP 401 in a real provider probe.
    # Do not pretend it is a currently accepted provider capability.
    api_key = api_key or os.environ.get("GUARDIAN_API_KEY")
    if not api_key or not api_key.strip():
        raise RuntimeError("Guardian API requires a configured GUARDIAN_API_KEY")
    observed_at = _utc_now()
    observations: list[dict[str, Any]] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        query = urllib.parse.urlencode(
            {
                "show-most-viewed": "true",
                "show-editors-picks": "true",
                "page-size": max(1, min(int(newest_per_section), 50)),
                "order-by": "newest",
            }
        )
        source_url = f"https://content.guardianapis.com/{urllib.parse.quote(section)}?{query}"
        # Provenance is shareable; the actual HTTP URL is not.
        request_url = source_url + "&api-key=" + urllib.parse.quote(api_key, safe="")
        try:
            document = _fetch_json(request_url, timeout=timeout)
        except Exception as error:
            if api_key in str(error):
                raise RuntimeError("Guardian API request failed; auth query omitted") from None
            raise
        response = document.get("response", {}) if isinstance(document, dict) else {}
        groups = (
            ("most-viewed", response.get("mostViewed", [])),
            ("editors-pick", response.get("editorsPicks", [])),
            ("newest-control", response.get("results", [])),
        )
        seen_priority: set[str] = set()
        for basis, items in groups:
            if not isinstance(items, list):
                continue
            for rank, item in enumerate(items, start=1):
                if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                    continue
                external_id = item["id"]
                if basis == "newest-control" and external_id in seen_priority:
                    continue
                if basis != "newest-control":
                    seen_priority.add(external_id)
                observations.append(
                    _observation(
                        observed_at=observed_at,
                        provider="guardian",
                        surface=section,
                        encounter_form="news-section",
                        external_id=external_id,
                        media_kind=str(item.get("type") or "article"),
                        title=str(item.get("webTitle") or ""),
                        canonical_url=item.get("webUrl") if isinstance(item.get("webUrl"), str) else None,
                        published_at=item.get("webPublicationDate") if isinstance(item.get("webPublicationDate"), str) else None,
                        descriptors={"sectionName": item.get("sectionName"), "pillarName": item.get("pillarName")},
                        selection_basis=basis,
                        rank=rank,
                        pool_size=len(items),
                        signals={},
                        context={"section": section},
                        source_url=source_url,
                    )
                )
    return observations
