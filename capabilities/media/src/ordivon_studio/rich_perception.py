from __future__ import annotations

import hashlib
import json
import math
import random
import re
import statistics
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Sequence

from .assets import probe_media
from .observatory import TITLE_FEATURES, build_matched_pairs, collect_guardian, title_features
from .perception import analyze_temporal_change


RICH_ARTICLE_KIND = "ordivon.studio-rich-article-experiment"
RICH_MEDIA_KIND = "ordivon.studio-rich-media-experiment"
USER_AGENT = "Ordivon-Studio-Rich-Perception/0.1 (+https://ordivon.com/)"

ARTICLE_RICH_FEATURES = (
    "bodyWordsLog",
    "sentenceCountLog",
    "avgSentenceWords",
    "sentenceWordsCv",
    "paragraphCountLog",
    "avgParagraphWords",
    "paragraphWordsCv",
    "rootTypeTokenRatio",
    "meanWordChars",
    "questionSentenceRate",
    "digitTokenRate",
    "linkPerKWords",
    "compressionRatio",
    "firstLastVocabularyJaccard",
    "leadWordsLog",
)

AUDIO_PROFILE_KEYS = ("rmsAmplitude", "zeroCrossingRate", "spectralCentroid", "spectralEntropy", "spectralFlatness", "spectralFlux")

_WORD = re.compile(r"[^\W_]+(?:[’'-][^\W_]+)*|\d+", re.UNICODE)
_SENTENCE_BREAK = re.compile(r"(?<=[.!?。！？])(?:[\"'”’)]*)\s+")
_META_FRAME = re.compile(r"^frame:\d+\s+pts:\S+\s+pts_time:(?P<time>-?[0-9.]+)$")
_META_VALUE = re.compile(r"^(?P<key>lavfi\.[^=]+)=(?P<value>.+)$")
_SIGNAL_YAVG = "lavfi.signalstats.YAVG"
_SIGNAL_SATAVG = "lavfi.signalstats.SATAVG"
_AUDIO_KEY_MAP = {
    "lavfi.astats.1.RMS_level": "rmsDb",
    "lavfi.astats.1.Zero_crossings_rate": "zeroCrossingRate",
    "lavfi.aspectralstats.1.centroid": "spectralCentroid",
    "lavfi.aspectralstats.1.entropy": "spectralEntropy",
    "lavfi.aspectralstats.1.flatness": "spectralFlatness",
    "lavfi.aspectralstats.1.flux": "spectralFlux",
}


class _GuardianBodyParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraph_words: list[int] = []
        self._paragraph_chunks: list[str] | None = None
        self.subheadings = 0
        self.blockquotes = 0
        self.links = 0
        self.list_items = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower == "p":
            self._paragraph_chunks = []
        elif lower in {"h2", "h3", "h4"}:
            self.subheadings += 1
        elif lower == "blockquote":
            self.blockquotes += 1
        elif lower == "a":
            self.links += 1
        elif lower == "li":
            self.list_items += 1

    def handle_data(self, data: str) -> None:
        if self._paragraph_chunks is not None:
            self._paragraph_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "p" and self._paragraph_chunks is not None:
            words = _tokenize(" ".join(self._paragraph_chunks))
            if words:
                self.paragraph_words.append(len(words))
            self._paragraph_chunks = None


def _tokenize(text: str) -> list[str]:
    return [match.group(0).casefold() for match in _WORD.finditer(text)]


def _split_sentences(text: str) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    sentences = [item.strip() for item in _SENTENCE_BREAK.split(normalized) if item.strip()]
    return sentences or [normalized]


def _mean(values: Sequence[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _cv(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = statistics.fmean(values)
    return statistics.pstdev(values) / abs(mean) if mean else 0.0


def _quantile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = min(len(ordered) - 1, lower + 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _correlation(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    mx = statistics.fmean(left)
    my = statistics.fmean(right)
    dx = sum((value - mx) ** 2 for value in left)
    dy = sum((value - my) ** 2 for value in right)
    if dx == 0.0 or dy == 0.0:
        return 0.0
    return sum((a - mx) * (b - my) for a, b in zip(left, right)) / math.sqrt(dx * dy)


def _normalized_entropy(values: Sequence[float]) -> float:
    positive = [max(0.0, float(value)) for value in values]
    total = sum(positive)
    if total <= 0.0 or len(positive) < 2:
        return 0.0
    probabilities = [value / total for value in positive if value > 0.0]
    entropy = -sum(value * math.log(value) for value in probabilities)
    return entropy / math.log(len(positive)) if len(positive) > 1 else 0.0


def _z_profile(values: Sequence[float]) -> list[float]:
    if not values:
        return []
    mean = statistics.fmean(values)
    scale = statistics.pstdev(values) or 1.0
    return [(float(value) - mean) / scale for value in values]


def profile_signature(values: Sequence[float]) -> dict[str, float]:
    sequence = [float(value) for value in values]
    if not sequence:
        return {
            "coefficientVariation": 0.0,
            "normalizedEntropy": 0.0,
            "lag1Correlation": 0.0,
            "peakPosition": 0.0,
            "earlyLateDeltaZ": 0.0,
            "turningPointRate": 0.0,
        }
    z = _z_profile(sequence)
    peak_index = max(range(len(sequence)), key=lambda index: sequence[index])
    third = max(1, len(z) // 3)
    early = _mean(z[:third])
    late = _mean(z[-third:])
    turning_points = 0
    for index in range(1, len(sequence) - 1):
        before = sequence[index] - sequence[index - 1]
        after = sequence[index + 1] - sequence[index]
        if before and after and before * after < 0:
            turning_points += 1
    return {
        "coefficientVariation": _cv(sequence),
        "normalizedEntropy": _normalized_entropy(sequence),
        "lag1Correlation": _correlation(sequence[:-1], sequence[1:]) if len(sequence) > 1 else 0.0,
        "peakPosition": peak_index / max(1, len(sequence) - 1),
        "earlyLateDeltaZ": early - late,
        "turningPointRate": turning_points / max(1, len(sequence) - 2),
    }


def _bin_series(samples: Sequence[tuple[float, float]], *, duration: float, bins: int) -> list[float]:
    if bins < 2:
        raise ValueError("bins must be at least two")
    grouped: list[list[float]] = [[] for _ in range(bins)]
    if duration <= 0.0:
        return [0.0] * bins
    for time_seconds, value in samples:
        index = min(bins - 1, max(0, int((float(time_seconds) / duration) * bins)))
        grouped[index].append(float(value))
    result: list[float] = []
    last = 0.0
    for values in grouped:
        if values:
            last = statistics.fmean(values)
        result.append(last)
    return result


def _resample_profile(values: Sequence[float], bins: int) -> list[float]:
    if not values:
        return [0.0] * bins
    if len(values) == bins:
        return [float(value) for value in values]
    grouped: list[list[float]] = [[] for _ in range(bins)]
    for index, value in enumerate(values):
        target = min(bins - 1, int(index * bins / len(values)))
        grouped[target].append(float(value))
    return [_mean(group) for group in grouped]


def _vector_distance(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vector lengths differ")
    if not left:
        return 0.0
    return math.sqrt(statistics.fmean((a - b) ** 2 for a, b in zip(left, right)))


def article_structure_features(*, body_text: str, body_html: str, trail_text: str = "") -> dict[str, Any]:
    tokens = _tokenize(body_text)
    sentences = _split_sentences(body_text)
    sentence_words = [len(_tokenize(sentence)) for sentence in sentences]
    parser = _GuardianBodyParser()
    parser.feed(body_html or "")
    paragraphs = parser.paragraph_words or ([len(tokens)] if tokens else [])
    lead_words = _tokenize(trail_text)
    unique = len(set(tokens))
    raw = body_text.encode("utf-8")
    first_tokens = set(tokens[: max(1, len(tokens) // 4)])
    last_tokens = set(tokens[-max(1, len(tokens) // 4) :])
    union = first_tokens | last_tokens
    features = {
        "bodyWordsLog": math.log1p(len(tokens)),
        "sentenceCountLog": math.log1p(len(sentences)),
        "avgSentenceWords": _mean(sentence_words),
        "sentenceWordsCv": _cv(sentence_words),
        "paragraphCountLog": math.log1p(len(paragraphs)),
        "avgParagraphWords": _mean(paragraphs),
        "paragraphWordsCv": _cv(paragraphs),
        "rootTypeTokenRatio": unique / math.sqrt(len(tokens)) if tokens else 0.0,
        "meanWordChars": _mean([len(token) for token in tokens]),
        "questionSentenceRate": sum("?" in sentence or "？" in sentence for sentence in sentences) / len(sentences) if sentences else 0.0,
        "digitTokenRate": sum(any(character.isdigit() for character in token) for token in tokens) / len(tokens) if tokens else 0.0,
        "linkPerKWords": parser.links * 1000.0 / len(tokens) if tokens else 0.0,
        "compressionRatio": len(zlib.compress(raw, level=9)) / len(raw) if raw else 0.0,
        "firstLastVocabularyJaccard": len(first_tokens & last_tokens) / len(union) if union else 0.0,
        "leadWordsLog": math.log1p(len(lead_words)),
    }
    positional = _resample_profile(paragraphs, 12)
    return {
        "features": features,
        "positionProfile": positional,
        "positionSignature": profile_signature(positional),
        "structure": {
            "words": len(tokens),
            "sentences": len(sentences),
            "paragraphs": len(paragraphs),
            "subheadings": parser.subheadings,
            "blockquotes": parser.blockquotes,
            "links": parser.links,
            "listItems": parser.list_items,
        },
        "contentDigest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "contentBytes": len(raw),
    }


def _guardian_content(content_id: str, *, timeout: float = 25.0, attempts: int = 3) -> dict[str, Any]:
    query = urllib.parse.urlencode({"api-key": "test", "show-fields": "body,bodyText,trailText,wordcount"})
    url = f"https://content.guardianapis.com/{urllib.parse.quote(content_id, safe='/')}?{query}"
    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json", "Connection": "close"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                value = json.load(response)
            content = value.get("response", {}).get("content", {}) if isinstance(value, dict) else {}
            fields = content.get("fields", {}) if isinstance(content, dict) else {}
            if not isinstance(fields, dict) or not isinstance(fields.get("bodyText"), str):
                raise RuntimeError(f"Guardian content has no bodyText: {content_id}")
            return {
                "bodyText": fields.get("bodyText", ""),
                "body": fields.get("body", ""),
                "trailText": fields.get("trailText", ""),
                "wordcount": fields.get("wordcount"),
            }
        except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(0.5 * (2**attempt))
    raise RuntimeError(f"Guardian content fetch failed after {attempts} attempts: {content_id}: {last_error}")


def _pair_feature_maps(pair: dict[str, Any], enrichment: dict[str, dict[str, Any]]) -> tuple[dict[str, float], dict[str, float], dict[str, float], dict[str, float]]:
    candidate = pair["candidate"]
    control = pair["control"]
    candidate_id = candidate["provider"] + ":" + candidate["artifact"]["externalId"]
    control_id = control["provider"] + ":" + control["artifact"]["externalId"]
    reference = max(
        datetime.fromisoformat(candidate["observedAt"].replace("Z", "+00:00")),
        datetime.fromisoformat(control["observedAt"].replace("Z", "+00:00")),
    )
    candidate_shallow = title_features(candidate, reference_time=reference)
    control_shallow = title_features(control, reference_time=reference)
    candidate_rich = enrichment[candidate_id]["features"]
    control_rich = enrichment[control_id]["features"]
    return candidate_shallow, control_shallow, candidate_rich, control_rich


def _cv_from_differences(differences: list[list[float]], labels: Sequence[str] | None = None) -> dict[str, Any]:
    if len(differences) < 4:
        raise ValueError("at least four pairs are required for held-out discrimination")
    predictions: list[dict[str, Any]] = []
    for held_index, held in enumerate(differences):
        training = [row for index, row in enumerate(differences) if index != held_index]
        columns = list(zip(*training))
        means = [statistics.fmean(column) for column in columns]
        scales = [statistics.pstdev(column) or 1.0 for column in columns]
        score = sum((means[index] / scales[index]) * (held[index] / scales[index]) for index in range(len(held)))
        predictions.append({"pair": held_index, "score": score, "correct": score > 0.0, "label": labels[held_index] if labels else None})
    accuracy = sum(item["correct"] for item in predictions) / len(predictions)
    by_label: dict[str, dict[str, float | int]] = {}
    if labels:
        for label in sorted(set(labels)):
            items = [item for item in predictions if item["label"] == label]
            by_label[label] = {"pairs": len(items), "accuracy": sum(item["correct"] for item in items) / len(items) if items else 0.0}
    return {
        "pairCount": len(differences),
        "accuracy": accuracy,
        "meanMargin": statistics.fmean(item["score"] for item in predictions),
        "medianMargin": statistics.median(item["score"] for item in predictions),
        "byLabel": by_label,
        "predictions": predictions,
    }


def _permutation_p_value(differences: list[list[float]], observed_accuracy: float, *, permutations: int = 1000, seed: int = 20260811) -> float:
    randomizer = random.Random(seed)
    exceed = 0
    for _ in range(permutations):
        flipped = []
        for row in differences:
            sign = -1.0 if randomizer.random() < 0.5 else 1.0
            flipped.append([value * sign for value in row])
        accuracy = _cv_from_differences(flipped)["accuracy"]
        if accuracy >= observed_accuracy:
            exceed += 1
    return (exceed + 1) / (permutations + 1)


def paired_discrimination(
    records: Sequence[dict[str, Any]],
    *,
    feature_names: Sequence[str],
    candidate_key: str,
    control_key: str,
    permutations: int = 1000,
) -> dict[str, Any]:
    differences: list[list[float]] = []
    labels: list[str] = []
    for record in records:
        candidate = record[candidate_key]
        control = record[control_key]
        differences.append([float(candidate[name]) - float(control[name]) for name in feature_names])
        labels.append(str(record.get("section") or record.get("provider") or "unknown"))
    result = _cv_from_differences(differences, labels=labels)
    result["featureNames"] = list(feature_names)
    result["permutationP"] = _permutation_p_value(differences, result["accuracy"], permutations=permutations)
    del result["predictions"]
    return result


def run_guardian_article_experiment(
    *,
    sections: Iterable[str],
    pairs_per_section: int = 8,
    newest_per_section: int = 30,
    timeout: float = 25.0,
    permutations: int = 1000,
) -> dict[str, Any]:
    observations = collect_guardian(sections=sections, newest_per_section=newest_per_section, timeout=timeout)
    pairs = build_matched_pairs(observations)
    selected: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for pair in pairs:
        if pair.get("provider") != "guardian":
            continue
        section = str(pair["candidate"].get("context", {}).get("section") or "unknown")
        if counts.get(section, 0) >= pairs_per_section:
            continue
        counts[section] = counts.get(section, 0) + 1
        selected.append(pair)
    external_ids = sorted(
        {
            side["artifact"]["externalId"]
            for pair in selected
            for side in (pair["candidate"], pair["control"])
        }
    )
    enrichment: dict[str, dict[str, Any]] = {}
    fetch_failures: list[dict[str, str]] = []

    def fetch(content_id: str) -> tuple[str, dict[str, Any] | None, str | None]:
        try:
            return content_id, _guardian_content(content_id, timeout=timeout), None
        except Exception as error:
            return content_id, None, f"{type(error).__name__}: {error}"[:800]

    with ThreadPoolExecutor(max_workers=4) as executor:
        for external_id, content, error in executor.map(fetch, external_ids):
            if error is not None or content is None:
                fetch_failures.append({"id": external_id, "error": error or "unknown fetch failure"})
                continue
            enrichment["guardian:" + external_id] = article_structure_features(
                body_text=content["bodyText"], body_html=content["body"], trail_text=content["trailText"]
            )
    records: list[dict[str, Any]] = []
    realized_counts: dict[str, int] = {}
    for pair in selected:
        candidate_id = "guardian:" + pair["candidate"]["artifact"]["externalId"]
        control_id = "guardian:" + pair["control"]["artifact"]["externalId"]
        if candidate_id not in enrichment or control_id not in enrichment:
            continue
        candidate_shallow, control_shallow, candidate_rich, control_rich = _pair_feature_maps(pair, enrichment)
        section = str(pair["candidate"].get("context", {}).get("section") or "unknown")
        realized_counts[section] = realized_counts.get(section, 0) + 1
        records.append(
            {
                "section": pair["candidate"].get("context", {}).get("section"),
                "matchCost": pair["matchCost"],
                "candidate": {
                    "id": pair["candidate"]["artifact"]["externalId"],
                    "title": pair["candidate"]["artifact"]["title"],
                    "shallow": candidate_shallow,
                    "rich": candidate_rich,
                    "contentDigest": enrichment[candidate_id]["contentDigest"],
                    "contentBytes": enrichment[candidate_id]["contentBytes"],
                    "positionSignature": enrichment[candidate_id]["positionSignature"],
                },
                "control": {
                    "id": pair["control"]["artifact"]["externalId"],
                    "title": pair["control"]["artifact"]["title"],
                    "shallow": control_shallow,
                    "rich": control_rich,
                    "contentDigest": enrichment[control_id]["contentDigest"],
                    "contentBytes": enrichment[control_id]["contentBytes"],
                    "positionSignature": enrichment[control_id]["positionSignature"],
                },
            }
        )
    shallow_records = [{"section": item["section"], "candidate": item["candidate"]["shallow"], "control": item["control"]["shallow"]} for item in records]
    rich_records = [{"section": item["section"], "candidate": item["candidate"]["rich"], "control": item["control"]["rich"]} for item in records]
    combined_records = [
        {
            "section": item["section"],
            "candidate": {**item["candidate"]["shallow"], **item["candidate"]["rich"]},
            "control": {**item["control"]["shallow"], **item["control"]["rich"]},
        }
        for item in records
    ]
    shallow = paired_discrimination(shallow_records, feature_names=TITLE_FEATURES, candidate_key="candidate", control_key="control", permutations=permutations)
    rich = paired_discrimination(rich_records, feature_names=ARTICLE_RICH_FEATURES, candidate_key="candidate", control_key="control", permutations=permutations)
    combined_names = tuple(TITLE_FEATURES) + tuple(ARTICLE_RICH_FEATURES)
    combined = paired_discrimination(combined_records, feature_names=combined_names, candidate_key="candidate", control_key="control", permutations=permutations)
    gain = combined["accuracy"] - shallow["accuracy"]
    return {
        "schemaVersion": 1,
        "kind": RICH_ARTICLE_KIND,
        "observedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "provider": "guardian",
        "selection": "most-viewed-vs-same-section-newest-control",
        "pairCount": len(records),
        "requestedPairsBySection": counts,
        "pairsBySection": realized_counts,
        "contentFetchFailures": fetch_failures,
        "rawContentRetention": "feature-only; full Guardian article bytes were processed transiently and are not serialized",
        "shallow": shallow,
        "richOnly": rich,
        "combined": combined,
        "accuracyGainOverShallow": gain,
        "equipmentDecision": "earned-discriminatory-gain" if gain >= 0.05 and combined["accuracy"] >= 0.55 else "no-strong-selection-gain",
        "records": records,
        "boundary": [
            "Most-viewed is an observed attention-world selection, not an aesthetic-quality label.",
            "Full-text structural features remain observational and do not identify causal creative effects.",
            "Raw article body bytes are not retained in the report; only feature summaries and exact content digests are serialized.",
        ],
    }


def _media_duration(probe: dict[str, Any]) -> float:
    value = (probe.get("format") or {}).get("duration") if isinstance(probe.get("format"), dict) else None
    if value is not None:
        return float(value)
    streams = probe.get("streams")
    if isinstance(streams, list):
        durations = [float(item["duration"]) for item in streams if isinstance(item, dict) and item.get("duration") is not None]
        if durations:
            return max(durations)
    raise ValueError("media duration unavailable")


def _video_stream(probe: dict[str, Any]) -> dict[str, Any]:
    streams = probe.get("streams")
    videos = [item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"] if isinstance(streams, list) else []
    if len(videos) != 1:
        raise ValueError("exactly one video stream required")
    return videos[0]


def _video_geometry(probe: dict[str, Any]) -> tuple[float, int, float]:
    stream = _video_stream(probe)
    frame_rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate")
    if not isinstance(frame_rate, str) or "/" not in frame_rate:
        raise ValueError("video frame rate unavailable")
    numerator, denominator = frame_rate.split("/", 1)
    fps = float(numerator) / float(denominator)
    duration = _media_duration(probe)
    frame_count = stream.get("nb_frames")
    total_frames = int(frame_count) if isinstance(frame_count, str) and frame_count.isdigit() else max(1, int(round(duration * fps)))
    return fps, total_frames, duration


def _parse_signal_metadata(text: str) -> list[dict[str, float]]:
    records: list[dict[str, float]] = []
    current: dict[str, float] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        frame = _META_FRAME.match(line)
        if frame:
            if current is not None:
                records.append(current)
            current = {"timeSeconds": float(frame.group("time"))}
            continue
        value = _META_VALUE.match(line)
        if value and current is not None and value.group("key") in {_SIGNAL_YAVG, _SIGNAL_SATAVG}:
            try:
                current[value.group("key")] = float(value.group("value"))
            except ValueError:
                pass
    if current is not None:
        records.append(current)
    return records


def analyze_video_signal(
    path: Path,
    *,
    sample_step_frames: int = 6,
    ffmpeg: str = "/usr/bin/ffmpeg",
) -> list[dict[str, float]]:
    with tempfile.NamedTemporaryFile(prefix="ordivon-video-signal-", suffix=".txt", delete=False) as handle:
        metadata = Path(handle.name)
    try:
        filter_graph = f"select='not(mod(n\\,{sample_step_frames}))',signalstats,metadata=print:file={metadata}"
        result = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(path), "-vf", filter_graph, "-an", "-f", "null", "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg signalstats failed")
        return _parse_signal_metadata(metadata.read_text(encoding="utf-8"))
    finally:
        metadata.unlink(missing_ok=True)


def video_structure_features(
    path: Path,
    *,
    bins: int = 24,
    sample_step_frames: int = 6,
    ffmpeg: str = "/usr/bin/ffmpeg",
    ffprobe: str = "/usr/bin/ffprobe",
) -> dict[str, Any]:
    probe = probe_media(path, ffprobe)
    fps, total_frames, duration = _video_geometry(probe)
    change = analyze_temporal_change(path, fps=fps, total_frames=total_frames, sample_step_frames=sample_step_frames, ffmpeg=ffmpeg)
    signal = analyze_video_signal(path, sample_step_frames=sample_step_frames, ffmpeg=ffmpeg)
    change_profile = _bin_series(
        [(float(item["timeSeconds"]), float(item["meanAbsoluteLumaDifference"])) for item in change],
        duration=duration,
        bins=bins,
    )
    luma_profile = _bin_series(
        [(float(item["timeSeconds"]), float(item.get(_SIGNAL_YAVG, 0.0))) for item in signal],
        duration=duration,
        bins=bins,
    )
    saturation_profile = _bin_series(
        [(float(item["timeSeconds"]), float(item.get(_SIGNAL_SATAVG, 0.0))) for item in signal],
        duration=duration,
        bins=bins,
    )
    vector = _z_profile(change_profile) + _z_profile(luma_profile) + _z_profile(saturation_profile)
    stream = _video_stream(probe)
    audio_streams = sum(1 for item in probe.get("streams", []) if isinstance(item, dict) and item.get("codec_type") == "audio")
    return {
        "technical": {
            "durationSeconds": duration,
            "width": stream.get("width"),
            "height": stream.get("height"),
            "frameRate": stream.get("avg_frame_rate") or stream.get("r_frame_rate"),
            "audioStreams": audio_streams,
        },
        "profiles": {"change": change_profile, "luma": luma_profile, "saturation": saturation_profile},
        "signatures": {
            "change": profile_signature(change_profile),
            "luma": profile_signature(luma_profile),
            "saturation": profile_signature(saturation_profile),
        },
        "structuralVector": vector,
        "interpretationBoundary": "Temporal change, average luma, and saturation are mechanical visual signals. They detect temporal/content reordering but do not identify semantic scene boundaries or visual quality.",
    }


def _finite_number(text: str, *, floor: float | None = None) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    if math.isfinite(value):
        return value
    return floor


def _parse_audio_metadata(text: str) -> list[dict[str, float]]:
    frames: list[dict[str, float]] = []
    current: dict[str, float] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        frame = _META_FRAME.match(line)
        if frame:
            if current is not None:
                frames.append(current)
            current = {"timeSeconds": float(frame.group("time"))}
            continue
        value = _META_VALUE.match(line)
        if value and current is not None:
            key = _AUDIO_KEY_MAP.get(value.group("key"))
            if key:
                parsed = _finite_number(value.group("value"), floor=-120.0 if key == "rmsDb" else 0.0)
                if parsed is not None:
                    current[key] = parsed
    if current is not None:
        frames.append(current)
    for frame in frames:
        rms_db = frame.get("rmsDb", -120.0)
        frame["rmsAmplitude"] = 10.0 ** (rms_db / 20.0)
    return frames


def analyze_audio_frames(path: Path, *, ffmpeg: str = "/usr/bin/ffmpeg") -> list[dict[str, float]]:
    with tempfile.NamedTemporaryFile(prefix="ordivon-audio-structure-", suffix=".txt", delete=False) as handle:
        metadata = Path(handle.name)
    try:
        filter_graph = (
            "aresample=16000,asetnsamples=n=1600:p=1,"
            "astats=metadata=1:reset=1,"
            "aspectralstats=win_size=1024:measure=centroid+entropy+flatness+flux,"
            f"ametadata=print:file={metadata}"
        )
        result = subprocess.run(
            [ffmpeg, "-v", "error", "-i", str(path), "-vn", "-af", filter_graph, "-f", "null", "-"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg audio structural analysis failed")
        return _parse_audio_metadata(metadata.read_text(encoding="utf-8"))
    finally:
        metadata.unlink(missing_ok=True)


def audio_structure_features(
    path: Path,
    *,
    bins: int = 24,
    ffmpeg: str = "/usr/bin/ffmpeg",
    ffprobe: str = "/usr/bin/ffprobe",
) -> dict[str, Any]:
    probe = probe_media(path, ffprobe)
    duration = _media_duration(probe)
    frames = analyze_audio_frames(path, ffmpeg=ffmpeg)
    profiles: dict[str, list[float]] = {}
    for key in AUDIO_PROFILE_KEYS:
        profiles[key] = _bin_series([(item["timeSeconds"], item.get(key, 0.0)) for item in frames], duration=duration, bins=bins)
    vector: list[float] = []
    for key in AUDIO_PROFILE_KEYS:
        vector.extend(_z_profile(profiles[key]))
    streams = probe.get("streams")
    audios = [item for item in streams if isinstance(item, dict) and item.get("codec_type") == "audio"] if isinstance(streams, list) else []
    if not audios:
        raise ValueError("audio structure requires an audio stream")
    audio = audios[0]
    return {
        "technical": {
            "durationSeconds": duration,
            "sampleRate": audio.get("sample_rate"),
            "channels": audio.get("channels"),
            "codec": audio.get("codec_name"),
        },
        "profiles": profiles,
        "signatures": {key: profile_signature(values) for key, values in profiles.items()},
        "structuralVector": vector,
        "frameCount": len(frames),
        "interpretationBoundary": "Energy, zero crossing, centroid, entropy, flatness, and spectral flux are mechanical audio structure signals. They do not establish musical quality, speech meaning, emotion, or listener preference.",
    }


def structural_distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    return _vector_distance(left["structuralVector"], right["structuralVector"])


def technical_fingerprint(features: dict[str, Any]) -> dict[str, Any]:
    return dict(features.get("technical", {}))


def cue_boundary_silence_score(audio: dict[str, Any], timed_text: dict[str, Any], *, window_seconds: float = 0.35) -> dict[str, float]:
    cues = timed_text.get("cues")
    time_base = timed_text.get("timeBase")
    ticks = time_base.get("ticksPerSecond") if isinstance(time_base, dict) else None
    if not isinstance(cues, list) or not isinstance(ticks, int) or ticks <= 0:
        raise ValueError("invalid timed text")
    rms = audio.get("profiles", {}).get("rmsAmplitude")
    duration = float(audio.get("technical", {}).get("durationSeconds") or 0.0)
    if not isinstance(rms, list) or not rms or duration <= 0.0:
        raise ValueError("audio RMS profile unavailable")
    boundaries = sorted({float(cue["startTick"]) / ticks for cue in cues[1:] if isinstance(cue, dict) and isinstance(cue.get("startTick"), int)})
    bin_width = duration / len(rms)
    boundary_values: list[float] = []
    for boundary in boundaries:
        for index, value in enumerate(rms):
            center = (index + 0.5) * bin_width
            if abs(center - boundary) <= window_seconds:
                boundary_values.append(float(value))
    global_mean = _mean([float(value) for value in rms])
    boundary_mean = _mean(boundary_values)
    contrast = (global_mean - boundary_mean) / (statistics.pstdev([float(value) for value in rms]) or 1.0)
    return {
        "boundaryCount": float(len(boundaries)),
        "globalMeanRmsAmplitude": global_mean,
        "boundaryMeanRmsAmplitude": boundary_mean,
        "boundarySilenceContrastZ": contrast,
    }


def crossmodal_profile_coupling(video: dict[str, Any], audio: dict[str, Any]) -> dict[str, float]:
    video_change = video.get("profiles", {}).get("change")
    audio_flux = audio.get("profiles", {}).get("spectralFlux")
    audio_rms = audio.get("profiles", {}).get("rmsAmplitude")
    if not isinstance(video_change, list) or not isinstance(audio_flux, list) or not isinstance(audio_rms, list):
        raise ValueError("crossmodal profiles unavailable")
    bins = min(len(video_change), len(audio_flux), len(audio_rms))
    v = _resample_profile(video_change, bins)
    flux = _resample_profile(audio_flux, bins)
    rms = _resample_profile(audio_rms, bins)
    return {
        "videoChangeAudioFluxCorrelation": _correlation(v, flux),
        "videoChangeAudioRmsCorrelation": _correlation(v, rms),
    }


def _circular_shift_correlation_null(left: Sequence[float], right: Sequence[float]) -> dict[str, float | int]:
    if len(left) != len(right) or len(left) < 4:
        raise ValueError("circular-shift null requires equal profiles with at least four bins")
    values: list[float] = []
    right_values = list(right)
    for shift in range(len(right_values)):
        shifted = right_values[shift:] + right_values[:shift]
        values.append(_correlation(left, shifted))
    baseline = values[0]
    null = values[1:]
    return {
        "baseline": baseline,
        "rankHigh": 1 + sum(value > baseline for value in null),
        "shiftCount": len(null),
        "percentile": sum(value <= baseline for value in values) / len(values),
        "nullMean": statistics.fmean(null),
        "nullSd": statistics.pstdev(null),
        "maxNull": max(null),
        "twoSidedAbsExceedRate": sum(abs(value) >= abs(baseline) for value in null) / len(null),
    }


def crossmodal_circular_shift_null(video: dict[str, Any], audio: dict[str, Any]) -> dict[str, Any]:
    video_change = video.get("profiles", {}).get("change")
    audio_flux = audio.get("profiles", {}).get("spectralFlux")
    audio_rms = audio.get("profiles", {}).get("rmsAmplitude")
    if not isinstance(video_change, list) or not isinstance(audio_flux, list) or not isinstance(audio_rms, list):
        raise ValueError("crossmodal profiles unavailable")
    bins = min(len(video_change), len(audio_flux), len(audio_rms))
    v = _resample_profile(video_change, bins)
    flux = _resample_profile(audio_flux, bins)
    rms = _resample_profile(audio_rms, bins)
    tests = {
        "videoChangeVsAudioFlux": _circular_shift_correlation_null(v, flux),
        "videoChangeVsAudioRms": _circular_shift_correlation_null(v, rms),
    }
    percentiles = [float(item["percentile"]) for item in tests.values()]
    abs_exceed = [float(item["twoSidedAbsExceedRate"]) for item in tests.values()]
    return {
        "bins": bins,
        "tests": tests,
        "disposition": "bounded-positive-alignment-signal" if min(percentiles) >= 0.95 and max(abs_exceed) <= 0.15 else "no-robust-alignment-signal",
        "boundary": "Circular time shifts preserve each modality's marginal profile while perturbing temporal relation. A high baseline percentile is alignment evidence for this artifact, not semantic congruence or aesthetic quality.",
    }


def media_intervention_report(
    *,
    baseline: dict[str, Any],
    controls: Sequence[tuple[str, dict[str, Any]]],
    perturbations: Sequence[tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    control_distances = [{"id": name, "distance": structural_distance(baseline, features)} for name, features in controls]
    perturbation_distances = [{"id": name, "distance": structural_distance(baseline, features)} for name, features in perturbations]
    max_control = max((item["distance"] for item in control_distances), default=0.0)
    min_perturbation = min((item["distance"] for item in perturbation_distances), default=0.0)
    median_perturbation = statistics.median([item["distance"] for item in perturbation_distances]) if perturbation_distances else 0.0
    return {
        "technicalBaseline": technical_fingerprint(baseline),
        "controls": control_distances,
        "perturbations": perturbation_distances,
        "maxControlDistance": max_control,
        "minPerturbationDistance": min_perturbation,
        "medianPerturbationDistance": median_perturbation,
        "strictSeparation": min_perturbation > max_control,
        "separationRatio": min_perturbation / max_control if max_control > 0.0 else None,
        "exactControlMatch": max_control == 0.0,
        "equipmentDecision": "earned-controlled-sensitivity" if min_perturbation > max_control + 0.05 else "insufficient-controlled-sensitivity",
        "boundary": "This measures whether rich perception detects known structural interventions hidden from shallow technical metadata. It does not claim the perturbation is aesthetically better or worse.",
    }


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
