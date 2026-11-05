"""Guardian official Open Platform ranked/editorial/control observations.

Most-viewed, editorial picks and newest articles remain different
selection mechanisms. No unsupported scraping or owned media bytes.
"""

from __future__ import annotations

import urllib.parse
from collections.abc import Iterable
from typing import Any

from .observatory_contracts import _utc_now
from .observatory_http import _fetch_json, _observation

DEFAULT_GUARDIAN_SECTIONS = ("world", "technology", "culture", "business", "science", "lifeandstyle")


def collect_guardian(
    *,
    sections: Iterable[str] = DEFAULT_GUARDIAN_SECTIONS,
    newest_per_section: int = 40,
    timeout: float = 20.0,
) -> list[dict[str, Any]]:
    observed_at = _utc_now()
    observations: list[dict[str, Any]] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        query = urllib.parse.urlencode(
            {
                "api-key": "test",
                "show-most-viewed": "true",
                "show-editors-picks": "true",
                "page-size": max(1, min(int(newest_per_section), 50)),
                "order-by": "newest",
            }
        )
        source_url = f"https://content.guardianapis.com/{urllib.parse.quote(section)}?{query}"
        document = _fetch_json(source_url, timeout=timeout)
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
