#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--snapshot-identity", required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    census = json.loads((a.root / "SCHEMA_CENSUS_R1.json").read_text())
    forks = load_jsonl(a.root / "derived/jsonl/lifecycle_forks.jsonl")
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.aries-lifecycle-fork-baseline",
        "id": "aries-lifecycle-fork-baseline-r1",
        "observedAt": "2026-09-23",
        "population": "ARIES 196 manual test concerns with exact source-review identity",
        "sourceParentAsset": "aries-bounded-core-r1",
        "sourceReplyAsset": "aries-review-response-core-r1",
        "sourceSnapshotIdentity": a.snapshot_identity,
        "counts": census["counts"],
        "responseCountPerConcern": dict(Counter(x["response_count"] for x in forks)),
        "positiveRevisionCountPerConcern": dict(
            Counter(x["positive_revision_count"] for x in forks)
        ),
        "interpretationCeiling": [
            "Exact review identity plus reply topology establishes review-level response context, not concern-specific semantic resolution.",
            "Annotated concern-edit correspondence remains separate from author reply topology; no Response->Revision causal or semantic edge is asserted.",
            "The lifecycle fork is same-authority identity evidence, not proof of reviewer correctness, response adequacy, or revision quality.",
        ],
    }
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
