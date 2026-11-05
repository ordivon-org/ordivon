from __future__ import annotations

import math
import statistics
from datetime import UTC, datetime
from typing import Any

from .observatory_contracts import REPORT_KIND, SNAPSHOT_KIND, _canonical_digest, _utc_now

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
