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
    c = load(root / "SCHEMA_CENSUS_R1.json")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.research.context24-claim-evidence-baseline",
        "id": "context24-claim-evidence-baseline-r1",
        "observedAt": "2026-09-23",
        "population": "exact Context24 bounded identity core at repo commit 457d3b5c only",
        "sourceAsset": "context24-identity-core-r1",
        "sourceSnapshotIdentity": snapshot_identity,
        "counts": c["counts"],
        "nativeIdCollisionClasses": c["nativeIdCollisionClasses"],
        "evidenceKinds": c["evidenceKindCounts"],
        "evidenceMultiplicityPerTask1TrainRow": c[
            "evidenceMultiplicityPerTask1TrainRow"
        ],
        "methodContextMultiplicityPerTask2TrainRow": c[
            "methodContextMultiplicityPerTask2TrainRow"
        ],
        "goldAvailability": c["goldAvailability"],
        "identityPolicy": c["identityPolicy"],
        "interpretationCeiling": [
            "Task 1 findings are annotated evidence identities, not proof that a claim is scientifically true or causally established.",
            "Task 2 context snippets are annotated methodological context, not proof that the method is adequate or the claim valid.",
            "Native claim id is not unique in the current Task 1 training carrier; source-coordinate claim_instance_id is the bounded-core identity authority.",
            "Challenge test gold is withheld and is never fabricated or inferred in this asset.",
            "R1 does not bind figure/table pixels, captions, full text, or the 17k silver corpus; evidence identities remain identity_only.",
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--snapshot-identity", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = derive(a.root, a.snapshot_identity)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
