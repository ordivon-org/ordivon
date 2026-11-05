from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .observatory_analysis import (
    CLUSTER_FEATURES as CLUSTER_FEATURES,
)
from .observatory_analysis import (
    TITLE_FEATURES as TITLE_FEATURES,
)
from .observatory_analysis import (
    analyze_snapshot,
)
from .observatory_analysis import (
    build_matched_pairs as build_matched_pairs,
)
from .observatory_analysis import (
    cluster_observations as cluster_observations,
)
from .observatory_analysis import (
    paired_feature_contrasts as paired_feature_contrasts,
)
from .observatory_analysis import (
    title_features as title_features,
)
from .observatory_contracts import (
    OBSERVATION_KIND,
    SNAPSHOT_KIND,
    _canonical_digest,
    _utc_now,
)
from .observatory_contracts import (
    REPORT_KIND as REPORT_KIND,
)

USER_AGENT = "Ordivon-Studio-Cultural-Observatory/0.1 (+https://ordivon.com/)"
DEFAULT_GUARDIAN_SECTIONS = ("world", "technology", "culture", "business", "science", "lifeandstyle")

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


def collect_snapshot(
    *,
    hn_top: int = 160,
    hn_new: int = 240,
    apple_limit: int = 100,
    guardian_sections: Iterable[str] = DEFAULT_GUARDIAN_SECTIONS,
    guardian_newest: int = 40,
    timeout: float = 20.0,
) -> dict[str, Any]:
    observed_at = _utc_now()
    observations: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    collectors = (
        ("hacker-news", lambda: collect_hacker_news(top_limit=hn_top, new_limit=hn_new, timeout=timeout)),
        ("apple-music", lambda: collect_apple_music(limit=apple_limit, timeout=timeout)),
        (
            "guardian",
            lambda: collect_guardian(sections=guardian_sections, newest_per_section=guardian_newest, timeout=timeout),
        ),
    )
    for provider, collector in collectors:
        try:
            observations.extend(collector())
        except Exception as error:  # provider failure is evidence; do not erase other observations
            failures.append({"provider": provider, "errorType": type(error).__name__, "message": str(error)[:500]})
    counts: dict[str, int] = {}
    for item in observations:
        counts[item["provider"]] = counts.get(item["provider"], 0) + 1
    payload = {
        "schemaVersion": 1,
        "kind": SNAPSHOT_KIND,
        "observedAt": observed_at,
        "capabilities": [item.as_dict() for item in CAPABILITIES],
        "countsByProvider": counts,
        "failures": failures,
        "observations": observations,
    }
    payload["snapshotDigest"] = _canonical_digest(payload)
    return payload


def _write_json(path: Path | None, value: Any) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path is None:
        sys.stdout.write(rendered)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def _command_capabilities(_: argparse.Namespace) -> int:
    _write_json(None, {"schemaVersion": 1, "kind": "ordivon.studio-cultural-source-capabilities", "sources": [item.as_dict() for item in CAPABILITIES]})
    return 0


def _command_collect(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(
        hn_top=args.hn_top,
        hn_new=args.hn_new,
        apple_limit=args.apple,
        guardian_sections=args.guardian_section or DEFAULT_GUARDIAN_SECTIONS,
        guardian_newest=args.guardian_newest,
        timeout=args.timeout,
    )
    _write_json(Path(args.output) if args.output else None, snapshot)
    if args.output:
        _write_json(None, {"ok": not snapshot["failures"], "output": args.output, "snapshotDigest": snapshot["snapshotDigest"], "countsByProvider": snapshot["countsByProvider"], "failures": snapshot["failures"]})
    return 0 if not snapshot["failures"] else 1


def _command_analyze(args: argparse.Namespace) -> int:
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    report = analyze_snapshot(snapshot, clusters=args.clusters)
    _write_json(Path(args.output) if args.output else None, report)
    if args.output:
        _write_json(None, {"ok": True, "output": args.output, "reportDigest": report["reportDigest"], "corpus": report["corpus"], "matchedControls": {"pairCount": report["matchedControls"]["pairCount"], "pairsByProvider": report["matchedControls"]["pairsByProvider"]}})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ordivon_studio.observatory")
    commands = parser.add_subparsers(dest="command", required=True)
    capabilities = commands.add_parser("capabilities", help="show admitted cultural observation surfaces and access boundaries")
    capabilities.set_defaults(handler=_command_capabilities)
    collect = commands.add_parser("collect", help="collect a bounded live metadata/reference snapshot")
    collect.add_argument("--output")
    collect.add_argument("--hn-top", type=int, default=160)
    collect.add_argument("--hn-new", type=int, default=240)
    collect.add_argument("--apple", type=int, default=100)
    collect.add_argument("--guardian-section", action="append")
    collect.add_argument("--guardian-newest", type=int, default=40)
    collect.add_argument("--timeout", type=float, default=20.0)
    collect.set_defaults(handler=_command_collect)
    analyze = commands.add_parser("analyze", help="cluster a snapshot and run matched-control structural contrasts")
    analyze.add_argument("snapshot")
    analyze.add_argument("--output")
    analyze.add_argument("--clusters", type=int, default=8)
    analyze.set_defaults(handler=_command_analyze)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        raise SystemExit(args.handler(args))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
