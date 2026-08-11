from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


OBSERVATION_KIND = "ordivon.studio-cultural-observation"
SNAPSHOT_KIND = "ordivon.studio-cultural-snapshot"
REPORT_KIND = "ordivon.studio-cultural-analysis"
USER_AGENT = "Ordivon-Studio-Cultural-Observatory/0.1 (+https://ordivon.com/)"
DEFAULT_GUARDIAN_SECTIONS = ("world", "technology", "culture", "business", "science", "lifeandstyle")
TITLE_FEATURES = (
    "titleChars",
    "titleWords",
    "hasQuestion",
    "hasColon",
    "hasDash",
    "hasNumber",
    "hasParenthetical",
)
CLUSTER_FEATURES = TITLE_FEATURES + ("ageHoursLog",)


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


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


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


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def title_features(observation: dict[str, Any], *, reference_time: datetime | None = None) -> dict[str, float]:
    artifact = observation.get("artifact", {})
    title = str(artifact.get("title") or "")
    words = [word for word in title.replace("/", " ").split() if word]
    published = _parse_time(artifact.get("publishedAt") if isinstance(artifact, dict) else None)
    age_hours = 0.0
    if published is not None:
        now = reference_time or datetime.now(UTC)
        age_hours = max(0.0, (now - published).total_seconds() / 3600.0)
    return {
        "titleChars": float(len(title)),
        "titleWords": float(len(words)),
        "hasQuestion": float("?" in title),
        "hasColon": float(":" in title or "：" in title),
        "hasDash": float(" – " in title or " — " in title or " - " in title),
        "hasNumber": float(any(character.isdigit() for character in title)),
        "hasParenthetical": float(("(" in title and ")" in title) or ("[" in title and "]" in title)),
        "ageHoursLog": math.log1p(age_hours),
    }


def _standardize(rows: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    if not rows:
        return [], [], []
    columns = list(zip(*rows))
    means = [statistics.fmean(column) for column in columns]
    scales = [statistics.pstdev(column) or 1.0 for column in columns]
    transformed = [[(value - means[index]) / scales[index] for index, value in enumerate(row)] for row in rows]
    return transformed, means, scales


def _distance(left: list[float], right: list[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right))


def _kmeans(rows: list[list[float]], *, k: int, max_iterations: int = 40) -> tuple[list[int], list[list[float]]]:
    if not rows:
        return [], []
    k = max(1, min(k, len(rows)))
    centroids = [rows[0][:]]
    while len(centroids) < k:
        next_row = max(rows, key=lambda row: min(_distance(row, centroid) for centroid in centroids))
        centroids.append(next_row[:])
    assignments = [-1] * len(rows)
    for _ in range(max_iterations):
        new_assignments = [min(range(k), key=lambda index: _distance(row, centroids[index])) for row in rows]
        if new_assignments == assignments:
            break
        assignments = new_assignments
        for cluster in range(k):
            members = [row for row, assignment in zip(rows, assignments) if assignment == cluster]
            if members:
                centroids[cluster] = [statistics.fmean(column) for column in zip(*members)]
    return assignments, centroids


def cluster_observations(observations: list[dict[str, Any]], *, k: int = 8) -> dict[str, Any]:
    usable = [item for item in observations if str(item.get("artifact", {}).get("title") or "").strip()]
    if not usable:
        return {"featureNames": list(CLUSTER_FEATURES), "clusters": []}
    reference_time = max(
        (_parse_time(item.get("observedAt")) for item in usable if _parse_time(item.get("observedAt")) is not None),
        default=datetime.now(UTC),
    )
    feature_maps = [title_features(item, reference_time=reference_time) for item in usable]
    raw_rows = [[features[name] for name in CLUSTER_FEATURES] for features in feature_maps]
    rows, _, _ = _standardize(raw_rows)
    assignments, centroids = _kmeans(rows, k=k)
    clusters: list[dict[str, Any]] = []
    for cluster_index, centroid in enumerate(centroids):
        members = [index for index, assignment in enumerate(assignments) if assignment == cluster_index]
        if not members:
            continue
        exemplars = sorted(members, key=lambda index: _distance(rows[index], centroid))[:5]
        basis_counts: dict[str, int] = {}
        provider_counts: dict[str, int] = {}
        for index in members:
            item = usable[index]
            basis = str(item.get("selection", {}).get("basis") or "unknown")
            provider = str(item.get("provider") or "unknown")
            basis_counts[basis] = basis_counts.get(basis, 0) + 1
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        mean_features = {
            name: statistics.fmean(feature_maps[index][name] for index in members) for name in CLUSTER_FEATURES
        }
        clusters.append(
            {
                "cluster": cluster_index,
                "count": len(members),
                "providers": provider_counts,
                "selectionBases": basis_counts,
                "meanFeatures": mean_features,
                "exemplars": [
                    {
                        "provider": usable[index]["provider"],
                        "basis": usable[index]["selection"]["basis"],
                        "title": usable[index]["artifact"]["title"],
                        "url": usable[index]["artifact"].get("canonicalUrl"),
                    }
                    for index in exemplars
                ],
            }
        )
    clusters.sort(key=lambda item: (-item["count"], item["cluster"]))
    return {"featureNames": list(CLUSTER_FEATURES), "clusters": clusters}


def _match_cost(candidate: dict[str, Any], control: dict[str, Any], reference_time: datetime) -> float:
    c_features = title_features(candidate, reference_time=reference_time)
    k_features = title_features(control, reference_time=reference_time)
    cost = abs(c_features["titleWords"] - k_features["titleWords"]) / 8.0
    cost += abs(c_features["ageHoursLog"] - k_features["ageHoursLog"])
    provider = candidate.get("provider")
    if provider == "guardian":
        if candidate.get("context", {}).get("section") != control.get("context", {}).get("section"):
            cost += 100.0
    elif provider == "hacker-news":
        c_host = candidate.get("artifact", {}).get("descriptors", {}).get("host")
        k_host = control.get("artifact", {}).get("descriptors", {}).get("host")
        if c_host and k_host and c_host != k_host:
            cost += 0.75
    return cost


def build_matched_pairs(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    reference_time = max(
        (_parse_time(item.get("observedAt")) for item in observations if _parse_time(item.get("observedAt")) is not None),
        default=datetime.now(UTC),
    )
    specs = (
        ("hacker-news", "top-ranked", "new-control"),
        ("guardian", "most-viewed", "newest-control"),
    )
    for provider, candidate_basis, control_basis in specs:
        candidates = [item for item in observations if item.get("provider") == provider and item.get("selection", {}).get("basis") == candidate_basis]
        controls = [item for item in observations if item.get("provider") == provider and item.get("selection", {}).get("basis") == control_basis]
        used: set[str] = set()
        for candidate in candidates:
            eligible = [
                control
                for control in controls
                if control.get("artifact", {}).get("externalId") not in used
                and control.get("artifact", {}).get("externalId") != candidate.get("artifact", {}).get("externalId")
            ]
            if provider == "guardian":
                same_section = [control for control in eligible if control.get("context", {}).get("section") == candidate.get("context", {}).get("section")]
                if same_section:
                    eligible = same_section
            if not eligible:
                continue
            control = min(eligible, key=lambda item: _match_cost(candidate, item, reference_time))
            used.add(str(control.get("artifact", {}).get("externalId")))
            pairs.append({"provider": provider, "candidate": candidate, "control": control, "matchCost": _match_cost(candidate, control, reference_time)})
    return pairs


def paired_feature_contrasts(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not pairs:
        return []
    reference_time = max(
        (
            _parse_time(item[side].get("observedAt"))
            for item in pairs
            for side in ("candidate", "control")
            if _parse_time(item[side].get("observedAt")) is not None
        ),
        default=datetime.now(UTC),
    )
    contrasts: list[dict[str, Any]] = []
    for feature in TITLE_FEATURES:
        differences: list[float] = []
        greater = 0
        equal = 0
        for pair in pairs:
            candidate_value = title_features(pair["candidate"], reference_time=reference_time)[feature]
            control_value = title_features(pair["control"], reference_time=reference_time)[feature]
            difference = candidate_value - control_value
            differences.append(difference)
            if difference > 0:
                greater += 1
            elif difference == 0:
                equal += 1
        mean_difference = statistics.fmean(differences)
        stdev = statistics.pstdev(differences)
        standardized = mean_difference / stdev if stdev else 0.0
        contrasts.append(
            {
                "feature": feature,
                "pairCount": len(differences),
                "meanCandidateMinusControl": mean_difference,
                "pairedStandardizedDifference": standardized,
                "candidateGreaterRate": greater / len(differences),
                "equalRate": equal / len(differences),
            }
        )
    contrasts.sort(key=lambda item: abs(item["pairedStandardizedDifference"]), reverse=True)
    return contrasts


def _apple_rank_contrast(observations: list[dict[str, Any]]) -> dict[str, Any] | None:
    songs = [item for item in observations if item.get("provider") == "apple-music" and item.get("selection", {}).get("basis") == "chart-ranked"]
    songs.sort(key=lambda item: item.get("selection", {}).get("rank") or 10**9)
    if len(songs) < 8:
        return None
    quarter = max(2, len(songs) // 4)
    top = songs[:quarter]
    bottom = songs[-quarter:]
    reference_time = max((_parse_time(item.get("observedAt")) for item in songs if _parse_time(item.get("observedAt")) is not None), default=datetime.now(UTC))
    features = ("titleChars", "titleWords", "ageHoursLog")
    differences = {}
    for feature in features:
        top_mean = statistics.fmean(title_features(item, reference_time=reference_time)[feature] for item in top)
        bottom_mean = statistics.fmean(title_features(item, reference_time=reference_time)[feature] for item in bottom)
        differences[feature] = {"topQuartileMean": top_mean, "bottomQuartileMean": bottom_mean, "difference": top_mean - bottom_mean}
    genre_counts = lambda items: statistics.fmean(len(item.get("artifact", {}).get("descriptors", {}).get("genres", [])) for item in items)
    differences["genreCount"] = {"topQuartileMean": genre_counts(top), "bottomQuartileMean": genre_counts(bottom), "difference": genre_counts(top) - genre_counts(bottom)}
    return {
        "kind": "rank-contrast-not-matched-control",
        "count": len(songs),
        "topSize": len(top),
        "bottomSize": len(bottom),
        "features": differences,
        "warning": "This compares positions inside an already-selected Top Songs chart; it is not a winner/loser or causal comparison.",
    }


def analyze_snapshot(snapshot: dict[str, Any], *, clusters: int = 8) -> dict[str, Any]:
    if snapshot.get("schemaVersion") != 1 or snapshot.get("kind") != SNAPSHOT_KIND:
        raise ValueError("not an Ordivon Studio cultural snapshot")
    observations = snapshot.get("observations", [])
    if not isinstance(observations, list):
        raise ValueError("snapshot observations must be an array")
    pairs = build_matched_pairs(observations)
    pair_provider_counts: dict[str, int] = {}
    costs: list[float] = []
    for pair in pairs:
        provider = pair["provider"]
        pair_provider_counts[provider] = pair_provider_counts.get(provider, 0) + 1
        costs.append(float(pair["matchCost"]))
    report = {
        "schemaVersion": 1,
        "kind": REPORT_KIND,
        "analyzedAt": _utc_now(),
        "snapshotDigest": snapshot.get("snapshotDigest") or _canonical_digest(snapshot),
        "corpus": {
            "observations": len(observations),
            "countsByProvider": snapshot.get("countsByProvider", {}),
            "providerFailures": snapshot.get("failures", []),
        },
        "matchedControls": {
            "pairCount": len(pairs),
            "pairsByProvider": pair_provider_counts,
            "meanMatchCost": statistics.fmean(costs) if costs else None,
            "featureContrasts": paired_feature_contrasts(pairs),
        },
        "clusters": cluster_observations(observations, k=clusters),
        "appleMusic": _apple_rank_contrast(observations),
        "interpretationBoundary": [
            "Selection labels are observed platform/editorial outcomes, not aesthetic truth.",
            "Matched pairs reduce obvious context mismatch but do not identify causal creative effects.",
            "Clusters are deterministic structural summaries over shallow metadata/title features, not semantic genres.",
            "Platform/distribution effects, creator priors, exposure, culture, timing, and randomness remain potential confounders.",
            "Use this report to generate falsifiable creative hypotheses; do not serialize feature directions as durable priors without intervention or repeated independent evidence.",
        ],
    }
    report["reportDigest"] = _canonical_digest(report)
    return report


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
