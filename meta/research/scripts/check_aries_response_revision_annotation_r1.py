#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

META = Path(__file__).resolve().parents[2]
SCHEMA = META / "research/schemas/aries-response-revision-annotation-v1.schema.json"
RECEIPT = (
    META / "research/evidence/aries-response-revision-annotation-substrate-r1.json"
)
ROOT = Path(
    "/root/projects/ordivon-corpora/scholarly-data/aries/aries-response-revision-annotation-r1-20260924"
)
SID = "sha256:aee4b640155c01f8c0e1f677494356f87944671e4a5c7079de8c86ee11fb0848"


def fail(x):
    raise SystemExit(x)


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def readj(p):
    return [
        json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()
    ]


def sha(p):
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    Draft202012Validator.check_schema(load(SCHEMA))
    m = load(ROOT / "ANNOTATION_SUBSTRATE_MANIFEST_R1.json")
    expc = {
        "units": 87,
        "candidatePairs": 248,
        "coderPacks": 2,
        "missingConcernBindings": 0,
        "inconsistentConcernGroups": 0,
    }
    expr = {
        "internalAnnotationOnly": True,
        "externalPaperTextRedistribution": "NOT_AUTHORIZED_BY_CATALOG",
        "commercialPaperTextReuse": "NOT_AUTHORIZED_BY_CATALOG",
    }
    expb = {
        "rankingFeaturesExcludedFromCoderPacks": True,
        "independentShuffle": True,
        "automaticRankIsGoldAuthority": False,
    }
    if (
        m["sourceSnapshotIdentity"] != SID
        or m["counts"] != expc
        or m["rightsBoundary"] != expr
        or m["blindness"] != expb
        or m["relationStanding"] != "ANNOTATION_SUBSTRATE_ONLY_NO_GOLD_YET"
    ):
        fail("manifest contract drift")
    for r in m["files"]:
        p = ROOT / r["path"]
        if not p.is_file() or p.stat().st_size != r["bytes"] or sha(p) != r["sha256"]:
            fail(f"file drift {r['path']}")
    can = readj(ROOT / "canonical/annotation_units.jsonl")
    a = readj(ROOT / "coder-packs/coder-a-units.jsonl")
    b = readj(ROOT / "coder-packs/coder-b-units.jsonl")
    f = readj(ROOT / "diagnostics/ranking_features.jsonl")
    r = readj(ROOT / "diagnostics/baseline_ranking.jsonl")
    if not (len(can) == len(a) == len(b) == len(r) == 87 and len(f) == 248):
        fail("cardinality drift")

    def mem(rows):
        return {
            x["unitId"]: {c["candidatePairId"] for c in x["candidates"]} for x in rows
        }

    cm, am, bm = mem(can), mem(a), mem(b)
    if cm != am or cm != bm:
        fail("pack membership drift")
    if [x["unitId"] for x in a] == [x["unitId"] for x in b] or [
        x["unitId"] for x in a
    ] == [x["unitId"] for x in can]:
        fail("blind shuffle failed")
    if {x["candidatePairId"] for x in f} != set().union(*cm.values()):
        fail("feature membership drift")
    ser = json.dumps(a + b, sort_keys=True)
    for k in [
        "responseDeltaTfidfCosine",
        "concernDeltaTfidfCosine",
        "responseTargetTfidfCosine",
        "rank",
        "score",
    ]:
        if f'"{k}"' in ser:
            fail("diagnostic feature leaked into coder pack")
    compact = {
        "schemaVersion": 1,
        "kind": "ordivon.research.aries-response-revision-annotation-substrate-acceptance",
        "standing": "PASS_ARIES_RESPONSE_REVISION_ANNOTATION_SUBSTRATE_R1",
        "sourceSnapshotIdentity": SID,
        "counts": expc,
        "relationStanding": "ANNOTATION_SUBSTRATE_ONLY_NO_GOLD_YET",
        "rightsBoundary": expr,
        "goldAdmission": "BLOCKED_PENDING_TWO_INDEPENDENT_FROZEN_CODER_CUTS_AND_ADJUDICATION",
        "modelTrainingStanding": "BLOCKED_PENDING_GOLD_ADMISSION",
        "truthBoundary": "Acceptance proves complete blinded annotation substrate construction only. It does not establish response-to-revision semantic gold, adequacy, or causality.",
    }
    if load(RECEIPT) != compact:
        fail("Git receipt drift")
    print(json.dumps(compact, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
