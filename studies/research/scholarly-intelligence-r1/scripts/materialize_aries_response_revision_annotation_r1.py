#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

SOURCE_ROOT = Path(
    "/root/projects/ordivon-corpora/scholarly-data/aries/aries-semantic-content-core-r1-20260924"
)
SOURCE_IDENTITY = (
    "sha256:aee4b640155c01f8c0e1f677494356f87944671e4a5c7079de8c86ee11fb0848"
)
OUT_ROOT = Path(
    "/root/projects/ordivon-corpora/scholarly-data/aries/aries-response-revision-annotation-r1-20260924"
)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")
STOP = {
    "the",
    "and",
    "that",
    "this",
    "with",
    "from",
    "for",
    "are",
    "was",
    "were",
    "have",
    "has",
    "had",
    "will",
    "would",
    "can",
    "could",
    "our",
    "we",
    "their",
    "they",
    "its",
    "into",
    "than",
    "then",
    "also",
    "which",
    "these",
    "those",
    "been",
}


def db(x: bytes) -> str:
    return "sha256:" + hashlib.sha256(x).hexdigest()


def dt(x: str) -> str:
    return db(x.encode())


def readj(p: Path):
    with p.open(encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def toks(s: str):
    return [t for t in TOKEN_RE.findall((s or "").lower()) if t not in STOP]


def delta(a: str, b: str) -> str:
    aa = (a or "").split()
    bb = (b or "").split()
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        a=aa, b=bb, autojunk=False
    ).get_opcodes():
        if tag in {"insert", "replace"} and j1 != j2:
            out.append(" ".join(bb[j1:j2]))
        if tag in {"delete", "replace"} and i1 != i2:
            out.append(" ".join(aa[i1:i2]))
    return " ".join(out)


def vec(ts, idf):
    c = Counter(ts)
    return {k: (1 + math.log(v)) * idf.get(k, 0.0) for k, v in c.items()}


def cos(a, b):
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def shuf(xs, seed):
    r = random.Random(int(hashlib.sha256(seed.encode()).hexdigest(), 16))
    o = list(xs)
    r.shuffle(o)
    return o


def writej(p, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(
                json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n"
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", type=Path, default=OUT_ROOT)
    args = ap.parse_args()
    out = args.output_root
    src = SOURCE_ROOT / "derived/jsonl"
    cands = readj(src / "response_revision_candidates.jsonl")
    edits = readj(src / "positive_edit_texts.jsonl")
    cmap = {(r["doc_id"], int(r["comment_id"]), int(r["edit_id"])): r for r in edits}
    bound = []
    gc = defaultdict(set)
    docs = []
    for r in cands:
        k = (r["doc_id"], int(r["comment_id"]), int(r["edit_id"]))
        if k not in cmap:
            raise SystemExit(f"missing concern binding {k}")
        c = cmap[k]
        g = (r["doc_id"], int(r["comment_id"]))
        gc[g].add(c["concern_text"])
        d = delta(r.get("source_text", ""), r.get("target_text", ""))
        x = dict(r)
        x.update(
            concern_text=c["concern_text"],
            concern_context=c.get("concern_context", ""),
            delta_text=d,
        )
        bound.append(x)
        docs += [
            toks(c["concern_text"]),
            toks(r["response_text"]),
            toks(d),
            toks(r.get("target_text", "")),
        ]
    if len(bound) != 248 or len(gc) != 87 or any(len(v) != 1 for v in gc.values()):
        raise SystemExit("binding cardinality/inconsistency")
    df = Counter()
    [df.update(set(d)) for d in docs]
    idf = {t: math.log((1 + len(docs)) / (1 + n)) + 1 for t, n in df.items()}
    features = []
    for r in bound:
        cv, rv, dv, tv = (
            vec(toks(r["concern_text"]), idf),
            vec(toks(r["response_text"]), idf),
            vec(toks(r["delta_text"]), idf),
            vec(toks(r.get("target_text", "")), idf),
        )
        features.append(
            {
                "candidatePairId": r["candidate_pair_id"],
                "responseDeltaTfidfCosine": cos(rv, dv),
                "concernDeltaTfidfCosine": cos(cv, dv),
                "responseTargetTfidfCosine": cos(rv, tv),
                "editKind": r["edit_kind"],
                "directToReview": r["direct_to_review"],
                "threadOrder": r["thread_order"],
            }
        )
    fb = {r["candidatePairId"]: r for r in features}
    groups = defaultdict(list)
    for r in bound:
        groups[(r["doc_id"], int(r["comment_id"]))].append(r)
    units = []
    for (doc, comment), rows in sorted(groups.items()):
        uid = dt(f"{SOURCE_IDENTITY}|{doc}|{comment}")
        cs = []
        for r in sorted(rows, key=lambda x: x["candidate_pair_id"]):
            cs.append(
                {
                    "candidatePairId": r["candidate_pair_id"],
                    "response": {
                        "text": r["response_text"],
                        "directToReview": r["direct_to_review"],
                        "threadOrder": r["thread_order"],
                    },
                    "revision": {
                        "editKind": r["edit_kind"],
                        "sourceText": r.get("source_text", ""),
                        "targetText": r.get("target_text", ""),
                    },
                }
            )
        units.append(
            {
                "schemaVersion": 1,
                "unitId": uid,
                "concern": {
                    "text": rows[0]["concern_text"],
                    "context": rows[0]["concern_context"],
                },
                "candidates": cs,
            }
        )
    writej(out / "canonical/annotation_units.jsonl", units)
    writej(out / "diagnostics/ranking_features.jsonl", features)
    for coder, seed in [("A", "aries-r1-coder-A"), ("B", "aries-r1-coder-B")]:
        packed = []
        templates = []
        for unit in shuf(units, seed):
            x = json.loads(json.dumps(unit))
            x["candidates"] = shuf(x["candidates"], seed + x["unitId"])
            packed.append(x)
            templates.append(
                {
                    "schemaVersion": 1,
                    "unitId": x["unitId"],
                    "coderId": f"CODER_{coder}_REPLACE_ME",
                    "judgments": [
                        {
                            "candidatePairId": c["candidatePairId"],
                            "relationLabel": "REPLACE_ME",
                            "evidenceBasis": [],
                            "confidence": "REPLACE_ME",
                            "adequacyStanding": "NOT_ANNOTATED_R1",
                            "causalStanding": "NOT_INFERRED",
                            "note": "",
                        }
                        for c in x["candidates"]
                    ],
                    "groupNote": "",
                }
            )
        writej(out / f"coder-packs/coder-{coder.lower()}-units.jsonl", packed)
        writej(out / f"coder-packs/coder-{coder.lower()}-template.jsonl", templates)
    ranks = []
    for u in units:
        rr = sorted(
            u["candidates"],
            key=lambda c: (
                -fb[c["candidatePairId"]]["responseDeltaTfidfCosine"],
                -fb[c["candidatePairId"]]["concernDeltaTfidfCosine"],
                c["candidatePairId"],
            ),
        )
        ranks.append(
            {
                "unitId": u["unitId"],
                "rankedCandidatePairIds": [c["candidatePairId"] for c in rr],
            }
        )
    writej(out / "diagnostics/baseline_ranking.jsonl", ranks)
    files = [
        {
            "path": str(p.relative_to(out)),
            "bytes": p.stat().st_size,
            "sha256": db(p.read_bytes()),
        }
        for p in sorted(out.rglob("*.jsonl"))
    ]
    m = {
        "schemaVersion": 1,
        "kind": "aries-response-revision-annotation-substrate-r1",
        "sourceSnapshotIdentity": SOURCE_IDENTITY,
        "counts": {
            "units": 87,
            "candidatePairs": 248,
            "coderPacks": 2,
            "missingConcernBindings": 0,
            "inconsistentConcernGroups": 0,
        },
        "blindness": {
            "rankingFeaturesExcludedFromCoderPacks": True,
            "independentShuffle": True,
            "automaticRankIsGoldAuthority": False,
        },
        "relationStanding": "ANNOTATION_SUBSTRATE_ONLY_NO_GOLD_YET",
        "rightsBoundary": {
            "internalAnnotationOnly": True,
            "externalPaperTextRedistribution": "NOT_AUTHORIZED_BY_CATALOG",
            "commercialPaperTextReuse": "NOT_AUTHORIZED_BY_CATALOG",
        },
        "files": files,
    }
    (out / "ANNOTATION_SUBSTRATE_MANIFEST_R1.json").write_text(
        json.dumps(m, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )
    print(json.dumps(m, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
