#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected object: {path}")
    return value


def derive(root: Path, snapshot_identity: str) -> dict[str, Any]:
    census = load(root / "SCHEMA_CENSUS_R1.json")
    analytical = load(root / "ANALYTICAL_BUILD_RECEIPT_R1.json")
    total = census["counts"]["rows"]
    thresholds = analytical["thresholdCounts"]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.research.peersum-meta-review-structure-baseline",
        "id": "peersum-meta-review-structure-baseline-r1",
        "observedAt": "2026-09-23",
        "population": "current exact PeerSum HF carrier only",
        "sourceAsset": "peersum-hf-bounded-core-r1",
        "sourceSnapshotIdentity": snapshot_identity,
        "counts": {
            "papers": total,
            "messages": census["counts"]["reviews"],
            "officialReviewMessages": census["counts"]["official_reviews"],
            "authorMessages": census["counts"]["author_messages"],
            "publicMessages": census["counts"]["public_messages"],
            "nonemptyMetaReviews": census["integrity"]["nonemptyMetaReviews"],
        },
        "splitCountsCurrentCarrier": census["splits"],
        "historicalDocumentationSplitCounts": {"train": 11995, "val": 1499, "test": 1499},
        "splitCountStanding": "CURRENT_CARRIER_DIFFERS_FROM_HISTORICAL_DOCUMENTATION",
        "ratingSpreadProxy": {
            "definition": "max minus min numeric rating among official_reviewer messages within a paper; structural proxy, not semantic conflict annotation",
            "histogram": census["officialRatingSpreadHistogram"],
            "median": census["distributions"]["officialRatingSpreadWhenAtLeastTwoRatings"]["median"],
            "mean": census["distributions"]["officialRatingSpreadWhenAtLeastTwoRatings"]["mean"],
            "thresholdCounts": thresholds,
            "fractions": {key: value / total for key, value in thresholds.items()},
        },
        "discussionStructure": {
            "reviewsPerPaper": census["distributions"]["reviewsPerPaper"],
            "officialReviewsPerPaper": census["distributions"]["officialReviewCountPerPaper"],
            "metaReviewWordsWhitespace": census["distributions"]["metaReviewWordsWhitespace"],
            "ratingSpreadGroups": analytical["ratingSpreadGroups"],
        },
        "interpretationCeiling": [
            "Official-rating spread is a coarse structural disagreement proxy and is not equivalent to semantic contradiction among reviews.",
            "Meta-review is treated as a synthesis artifact supplied by PeerSum, not as reviewer/scientific truth or a correct decision.",
            "paper_acceptance_native is retained only as source metadata and is not used here as a venue-independent quality target.",
            "Current exact carrier split counts differ from historical paper/README counts; analyses bind current bytes rather than silently rewriting them.",
            "Corpus frequencies are PeerSum-specific descriptive statistics, not peer-review population prevalence.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--snapshot-identity", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = derive(args.root, args.snapshot_identity)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
