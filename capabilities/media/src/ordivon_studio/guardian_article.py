"""Guardian article structure, matched controls, and provider retrieval experiment."""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Any

from .observatory import TITLE_FEATURES, build_matched_pairs, collect_guardian, title_features
from .perception_profiles import _cv, _mean, _resample_profile, profile_signature

RICH_ARTICLE_KIND = "ordivon.studio-rich-article-experiment"
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
_WORD = re.compile(r"[^\W_]+(?:[’'-][^\W_]+)*|\d+", re.UNICODE)
_SENTENCE_BREAK = re.compile(r"(?<=[.!?。！？])(?:[\"'”’)]*)\s+")


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
