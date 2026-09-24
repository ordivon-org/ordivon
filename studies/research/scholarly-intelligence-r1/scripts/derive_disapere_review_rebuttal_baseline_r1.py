#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

EXPECTED_SNAPSHOT_IDENTITY = "sha256:bb2ca8ce6324bdf93d1523c2de09ceebe16445835d765664d348e1e49edf6470"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def quantile(values: list[int], p: float) -> float:
    xs = sorted(values)
    pos = (len(xs) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return float(xs[lo])
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def describe(values: list[int]) -> dict[str, float | int]:
    return {
        "n": len(values),
        "min": min(values),
        "q1": quantile(values, 0.25),
        "median": quantile(values, 0.5),
        "q3": quantile(values, 0.75),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def derive(root: Path) -> dict[str, Any]:
    derived = root / "derived/jsonl"
    reviews = load_jsonl(derived / "review_sentences.jsonl")
    rebuttals = load_jsonl(derived / "rebuttal_sentences.jsonl")
    links = load_jsonl(derived / "local_alignment_links.jsonl")
    review_by = {
        (row["pair_id"], int(row["sentence_index"])): row for row in reviews
    }
    rebuttal_by = {
        (row["pair_id"], int(row["sentence_index"])): row for row in rebuttals
    }
    targeted = Counter(
        (row["pair_id"], int(row["review_sentence_index"])) for row in links
    )
    source_mult = Counter(
        (row["pair_id"], int(row["rebuttal_sentence_index"])) for row in links
    )

    def coverage(predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
        rows = [row for row in reviews if predicate(row)]
        hit = sum(
            (row["pair_id"], int(row["sentence_index"])) in targeted for row in rows
        )
        return {"targeted": hit, "total": len(rows), "fraction": hit / len(rows)}

    request_sources: set[tuple[str, int]] = set()
    for link in links:
        review = review_by[(link["pair_id"], int(link["review_sentence_index"]))]
        if review["review_action"] == "arg_request":
            request_sources.add(
                (link["pair_id"], int(link["rebuttal_sentence_index"]))
            )
    request_rebuttals = [rebuttal_by[key] for key in request_sources]

    return {
        "schemaVersion": 1,
        "kind": "ordivon.research.disapere-review-rebuttal-baseline",
        "id": "disapere-review-rebuttal-baseline-r1",
        "observedAt": "2026-09-23",
        "sourceAsset": "disapere-bounded-core-r1",
        "sourceSnapshotIdentity": EXPECTED_SNAPSHOT_IDENTITY,
        "population": "DISAPERE 506-pair annotated corpus only",
        "counts": {
            "pairs": 506,
            "reviewSentences": len(reviews),
            "rebuttalSentences": len(rebuttals),
            "localAlignmentLinks": len(links),
            "locallyAlignedRebuttalSentences": len(source_mult),
            "locallyTargetedReviewSentences": len(targeted),
            "requestLinkedRebuttalSentences": len(request_rebuttals),
        },
        "explicitLocalAlignmentCoverage": {
            "allReviewSentences": coverage(lambda row: True),
            "requestReviewSentences": coverage(
                lambda row: row["review_action"] == "arg_request"
            ),
            "negativePolarityReviewSentences": coverage(
                lambda row: row["polarity"] == "pol_negative"
            ),
            "clarityReviewSentences": coverage(
                lambda row: row["aspect"] == "asp_clarity"
            ),
            "soundnessCorrectnessReviewSentences": coverage(
                lambda row: row["aspect"] == "asp_soundness-correctness"
            ),
            "replicabilityReviewSentences": coverage(
                lambda row: row["aspect"] == "asp_replicability"
            ),
        },
        "distributions": {
            "reviewAction": dict(Counter(row["review_action"] for row in reviews)),
            "reviewPolarity": dict(Counter(row["polarity"] for row in reviews)),
            "rebuttalStance": dict(
                Counter(row["rebuttal_stance"] for row in rebuttals)
            ),
            "rebuttalAction": dict(
                Counter(row["rebuttal_action"] for row in rebuttals)
            ),
            "alignmentKind": dict(
                Counter(row["alignment_kind"] for row in rebuttals)
            ),
            "localReviewLinksPerLocallyAlignedRebuttal": describe(
                list(source_mult.values())
            ),
            "requestLinkedRebuttalStance": dict(
                Counter(row["rebuttal_stance"] for row in request_rebuttals)
            ),
            "requestLinkedRebuttalAction": dict(
                Counter(row["rebuttal_action"] for row in request_rebuttals)
            ),
        },
        "interpretationCeiling": [
            "Explicit local-alignment coverage is not a response-rate estimate: DISAPERE also contains global, in-rebuttal, none, unknown, and error alignment states.",
            "A concur/dispute label describes annotated stance, not whether the author or reviewer is scientifically correct.",
            "Multiple links are many-to-many discourse correspondences and are not independent observations.",
            "Corpus frequencies are DISAPERE-specific descriptive statistics, not peer-review population prevalence.",
            "This asset is licensed CC BY-NC 4.0 and is admitted only for current non-commercial research.",
        ],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    coverage = summary["explicitLocalAlignmentCoverage"]
    distributions = summary["distributions"]

    def pct(row: dict[str, Any]) -> float:
        return 100 * float(row["fraction"])

    return f"""# DISAPERE Review–Rebuttal Discourse Baseline R1

Date: 2026-09-23
Source asset: `disapere-bounded-core-r1`
Scope: **DISAPERE 506-pair annotated corpus only**

## Corpus

The bounded corpus contains **506 review–rebuttal pairs**, **{counts['reviewSentences']:,} review sentences**, **{counts['rebuttalSentences']:,} rebuttal sentences**, and **{counts['localAlignmentLinks']:,} explicit local review-sentence links**. The normalized analytical layer contains no reviewer or annotator identity fields.

## Explicit local alignment coverage

- all review sentences: **{coverage['allReviewSentences']['targeted']:,}/{coverage['allReviewSentences']['total']:,} ({pct(coverage['allReviewSentences']):.2f}%)**;
- request sentences: **{coverage['requestReviewSentences']['targeted']:,}/{coverage['requestReviewSentences']['total']:,} ({pct(coverage['requestReviewSentences']):.2f}%)**;
- negative-polarity sentences: **{coverage['negativePolarityReviewSentences']['targeted']:,}/{coverage['negativePolarityReviewSentences']['total']:,} ({pct(coverage['negativePolarityReviewSentences']):.2f}%)**;
- clarity sentences: **{coverage['clarityReviewSentences']['targeted']:,}/{coverage['clarityReviewSentences']['total']:,} ({pct(coverage['clarityReviewSentences']):.2f}%)**;
- soundness/correctness sentences: **{coverage['soundnessCorrectnessReviewSentences']['targeted']:,}/{coverage['soundnessCorrectnessReviewSentences']['total']:,} ({pct(coverage['soundnessCorrectnessReviewSentences']):.2f}%)**;
- replicability sentences: **{coverage['replicabilityReviewSentences']['targeted']:,}/{coverage['replicabilityReviewSentences']['total']:,} ({pct(coverage['replicabilityReviewSentences']):.2f}%)**.

This is **explicit local sentence alignment**, not a response-rate estimator. DISAPERE separately represents global and in-rebuttal context.

## Rebuttal structure

Across all rebuttal sentences, stance counts are `{distributions['rebuttalStance']}`. Alignment kinds are `{distributions['alignmentKind']}`. For the **{counts['locallyAlignedRebuttalSentences']:,}** locally aligned rebuttal sentences, the number of linked review sentences has median **{distributions['localReviewLinksPerLocallyAlignedRebuttal']['median']:.1f}**, IQR **{distributions['localReviewLinksPerLocallyAlignedRebuttal']['q1']:.1f}–{distributions['localReviewLinksPerLocallyAlignedRebuttal']['q3']:.1f}**, and maximum **{distributions['localReviewLinksPerLocallyAlignedRebuttal']['max']}**.

Among **{counts['requestLinkedRebuttalSentences']:,}** rebuttal sentences explicitly linked to at least one review request, stance counts are `{distributions['requestLinkedRebuttalStance']}`. The dominant response action is `rebuttal_answer` (**{distributions['requestLinkedRebuttalAction'].get('rebuttal_answer', 0):,}**), followed by structuring, done, summary, and several reject/concede/mitigate actions.

## Ordivon implication

The data supports a typed circuit rather than a scalar reviewer score:

`ConcernType -> ExplicitContext -> ResponseStance -> ResponseAction -> ResolutionCandidate -> RevisionEffect`

`ExplicitContext` must allow local-sentence, global, in-rebuttal, none, unknown, and error states. Stance and action remain descriptive annotations; they do not authorize scientific or submission decisions.

## Rights boundary

The canonical repository applies **CC BY-NC 4.0**. This snapshot is admitted for current non-commercial research only. It is **not** authorized for future commercial product/service use without another rights basis.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    summary = derive(args.root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
