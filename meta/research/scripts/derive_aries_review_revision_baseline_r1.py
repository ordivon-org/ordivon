#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

EXPECTED_SNAPSHOT_IDENTITY = "sha256:c044a92034f740802d24a2298cc1569e59bda34c5148e34a6556f356d78b1c77"
EXPECTED_RAW = {
    "review_comments.jsonl": "sha256:0f32ce3b66b12385dd2f9d1bb791a8800e80060b1a58c0deddd87bcded3b2b58",
    "paper_edits.jsonl": "sha256:2ac050dc84ec984db5e9ed166f5411d54e213bfc16a4f596766041f1910e5d3c",
    "edit_labels_test.jsonl": "sha256:e5c827f2572ecbc26e00583ca2ff557b083b8b71a577f4d308aaf00a24c62306",
}


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


def describe(values: Iterable[int]) -> dict[str, float | int]:
    xs = list(values)
    return {
        "n": len(xs),
        "min": min(xs),
        "q1": quantile(xs, 0.25),
        "median": quantile(xs, 0.5),
        "q3": quantile(xs, 0.75),
        "max": max(xs),
        "mean": sum(xs) / len(xs),
    }


def words(value: Any) -> int:
    return len(str(value or "").split())


def derive(root: Path) -> dict[str, Any]:
    raw = root / "raw"
    comments = load_jsonl(raw / "review_comments.jsonl")
    docs = load_jsonl(raw / "paper_edits.jsonl")
    dev = load_jsonl(raw / "edit_labels_dev.jsonl")
    test = load_jsonl(raw / "edit_labels_test.jsonl")
    comment_map = {(str(row["doc_id"]), int(row["comment_id"])): row for row in comments}
    edit_counts = {str(row["doc_id"]): len(row.get("edits", [])) for row in docs}

    manual: list[dict[str, Any]] = []
    for row in test:
        comment = comment_map[(str(row["doc_id"]), int(row["comment_id"]))]
        positive = list(row.get("positive_edits", []))
        negative = list(row.get("negative_edits", []))
        manual.append(
            {
                "doc_id": str(row["doc_id"]),
                "comment_id": int(row["comment_id"]),
                "positive_count": len(positive),
                "negative_count": len(negative),
                "candidate_count": len(positive) + len(negative),
                "comment_words": words(comment.get("comment")),
                "context_words": words(comment.get("comment_context")),
                "document_edit_units": edit_counts[str(row["doc_id"])],
            }
        )
    positive_rows = [row for row in manual if row["positive_count"] > 0]
    zero_rows = [row for row in manual if row["positive_count"] == 0]
    histogram = dict(sorted(Counter(row["positive_count"] for row in manual).items()))

    return {
        "schemaVersion": 1,
        "kind": "ordivon.research.aries-review-revision-baseline",
        "id": "aries-review-revision-baseline-r1",
        "observedAt": "2026-09-23",
        "sourceAsset": "aries-bounded-core-r1",
        "sourceSnapshotIdentity": EXPECTED_SNAPSHOT_IDENTITY,
        "population": "ARIES manually annotated test slice only",
        "counts": {
            "manualTestComments": len(manual),
            "commentsWithPositiveEditAlignment": len(positive_rows),
            "commentsWithoutPositiveEditAlignment": len(zero_rows),
            "positiveEditLinks": sum(row["positive_count"] for row in manual),
            "negativeEditLinks": sum(row["negative_count"] for row in manual),
            "distinctDocumentsInManualTest": len({row["doc_id"] for row in manual}),
        },
        "rates": {
            "commentsWithPositiveEditAlignment": len(positive_rows) / len(manual),
            "commentsWithoutPositiveEditAlignment": len(zero_rows) / len(manual),
            "meanPositiveLinksConditionalOnAnyPositive": sum(
                row["positive_count"] for row in positive_rows
            ) / len(positive_rows),
        },
        "distributions": {
            "positiveLinksPerComment": describe(row["positive_count"] for row in manual),
            "positiveLinksPerPositiveComment": describe(
                row["positive_count"] for row in positive_rows
            ),
            "negativeLinksPerComment": describe(row["negative_count"] for row in manual),
            "candidateLinksPerComment": describe(row["candidate_count"] for row in manual),
            "commentWordsWhitespaceTokenizer": describe(
                row["comment_words"] for row in manual
            ),
            "commentContextWordsWhitespaceTokenizer": describe(
                row["context_words"] for row in manual
            ),
            "documentEditUnitsForManualTestComments": describe(
                row["document_edit_units"] for row in manual
            ),
            "all1720DocumentEditUnits": describe(edit_counts.values()),
        },
        "positiveLinkMultiplicityHistogram": {str(key): value for key, value in histogram.items()},
        "provenance": {
            "devAnnotation": "synthetic",
            "devRowsExcludedFromPrimaryRates": len(dev),
            "testAnnotation": "manual",
            "reviewCommentRawSha256": EXPECTED_RAW["review_comments.jsonl"],
            "paperEditsRawSha256": EXPECTED_RAW["paper_edits.jsonl"],
            "testLabelsRawSha256": EXPECTED_RAW["edit_labels_test.jsonl"],
        },
        "interpretationCeiling": [
            "The 44% positive-alignment fraction is a property of the ARIES manually labeled test slice, not an estimate of how often peer-review comments cause revisions in a scholarly population.",
            "A positive alignment is an annotated correspondence between a comment and one or more edit identities; it does not establish causality or adequacy of the revision.",
            "Negative edit links are candidate negatives supplied by ARIES and are not evidence that an edit is scientifically wrong or irrelevant outside this matching task.",
            "The bounded core omits S2ORC paragraph text, so this baseline analyzes identity/multiplicity and review-comment text, not semantic quality of edit contents.",
        ],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    counts, rates, dist = summary["counts"], summary["rates"], summary["distributions"]
    rate = 100 * rates["commentsWithPositiveEditAlignment"]
    return f"""# ARIES Review-to-Revision Baseline R1

Date: 2026-09-23
Source asset: `aries-bounded-core-r1`
Scope: **manual ARIES test annotations only**

## Result

The manual test slice contains **{counts['manualTestComments']} review comments** across **{counts['distinctDocumentsInManualTest']} documents**. **{counts['commentsWithPositiveEditAlignment']} comments ({rate:.2f}%)** have at least one annotated positive edit correspondence; **{counts['commentsWithoutPositiveEditAlignment']} ({100-rate:.2f}%)** have none. The positive comments carry **{counts['positiveEditLinks']} positive links**, or **{rates['meanPositiveLinksConditionalOnAnyPositive']:.2f} links per positive comment on average**. ARIES supplies **{counts['negativeEditLinks']:,} candidate-negative links** for this slice.

Positive-link multiplicity is concentrated at zero/one: `{summary['positiveLinkMultiplicityHistogram']}`. Candidate-set size per comment has median **{dist['candidateLinksPerComment']['median']:.1f}**, IQR **{dist['candidateLinksPerComment']['q1']:.1f}–{dist['candidateLinksPerComment']['q3']:.1f}**, max **{dist['candidateLinksPerComment']['max']}**.

The associated review comments have median **{dist['commentWordsWhitespaceTokenizer']['median']:.1f} whitespace-token words** (IQR {dist['commentWordsWhitespaceTokenizer']['q1']:.1f}–{dist['commentWordsWhitespaceTokenizer']['q3']:.1f}). The papers represented by those comments expose a median **{dist['documentEditUnitsForManualTestComments']['median']:.1f} edit units** in ARIES. Across all 1,720 ARIES paper-edit documents, the median is **{dist['all1720DocumentEditUnits']['median']:.1f}**, with maximum **{dist['all1720DocumentEditUnits']['max']}**.

## Interpretation ceiling

This is a dataset baseline for **comment↔edit correspondence**, not a peer-review population estimate. Positive alignment does not establish that a reviewer caused an edit or that the edit adequately resolves the concern. Dev labels are synthetic and excluded from the primary rates. The bounded core omits S2ORC paragraph text, so this R1 baseline does not judge edit semantics.

## Why it matters for Ordivon

The useful object is not a scalar reviewer score. ARIES gives us a typed relation:

`Concern/comment -> candidate edit set -> annotated correspondence`

That supports a future `Concern -> ResolutionCandidate -> RevisionEffect` circuit while preserving correspondence, causal, and adequacy boundaries as separate authorities.
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
    args.json_output.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
