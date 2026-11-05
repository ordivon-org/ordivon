"""Hacker News top-ranked and new-story metadata observations.

Consumes only the public official Firebase API. Rankings and new-story
controls retain their distinct selection mechanisms.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.parse import urlparse

from .observatory_contracts import _utc_now
from .observatory_http import _fetch_json, _iso_from_epoch, _observation


def _hn_item(item_id: int, timeout: float) -> dict[str, Any] | None:
    value = _fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=timeout)
    return value if isinstance(value, dict) and value.get("type") == "story" else None


def collect_hacker_news(*, top_limit: int = 160, new_limit: int = 240, timeout: float = 20.0) -> list[dict[str, Any]]:
    observed_at = _utc_now()
    top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    new_url = "https://hacker-news.firebaseio.com/v0/newstories.json"
    top_ids = [int(value) for value in _fetch_json(top_url, timeout=timeout)[: max(0, top_limit)]]
    new_ids_all = [int(value) for value in _fetch_json(new_url, timeout=timeout)]
    top_set = set(top_ids)
    new_ids = [value for value in new_ids_all if value not in top_set][: max(0, new_limit)]
    all_ids = list(dict.fromkeys(top_ids + new_ids))
    with ThreadPoolExecutor(max_workers=16) as executor:
        items = list(executor.map(lambda item_id: _hn_item(item_id, timeout), all_ids))
    by_id = {int(item["id"]): item for item in items if isinstance(item, dict) and isinstance(item.get("id"), int)}
    observations: list[dict[str, Any]] = []
    for basis, ids, source_url in (("top-ranked", top_ids, top_url), ("new-control", new_ids, new_url)):
        for rank, item_id in enumerate(ids, start=1):
            item = by_id.get(item_id)
            if item is None:
                continue
            url = item.get("url") if isinstance(item.get("url"), str) else f"https://news.ycombinator.com/item?id={item_id}"
            host = urlparse(url).hostname or "news.ycombinator.com"
            observations.append(
                _observation(
                    observed_at=observed_at,
                    provider="hacker-news",
                    surface="topstories" if basis == "top-ranked" else "newstories",
                    encounter_form="ranked-link-feed",
                    external_id=str(item_id),
                    media_kind="article-link",
                    title=str(item.get("title") or ""),
                    canonical_url=url,
                    creator=item.get("by") if isinstance(item.get("by"), str) else None,
                    published_at=_iso_from_epoch(item.get("time")),
                    descriptors={"host": host},
                    selection_basis=basis,
                    rank=rank,
                    pool_size=len(ids),
                    signals={
                        "score": item.get("score") if isinstance(item.get("score"), int) else None,
                        "comments": item.get("descendants") if isinstance(item.get("descendants"), int) else 0,
                    },
                    context={"community": "hacker-news"},
                    source_url=source_url,
                )
            )
    return observations
