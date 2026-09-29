#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

STUDY = Path(__file__).resolve().parents[1]
SCHEMA = STUDY / "schemas/aries-response-revision-annotation-v1.schema.json"
SUBSTRATE = Path(
    "/root/projects/ordivon-corpora/scholarly-data/aries/"
    "aries-response-revision-annotation-r1-20260924"
)
LABELS = [
    "DIRECT_REALIZATION",
    "PARTIAL_REALIZATION",
    "RELATED_NOT_REALIZATION",
    "NO_RELATION",
    "INSUFFICIENT_CONTEXT",
]
LINKED = {"DIRECT_REALIZATION", "PARTIAL_REALIZATION"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate_cut(path: Path, expected_prefix: str) -> dict[str, dict[str, Any]]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    units = read_jsonl(path)
    canonical = read_jsonl(SUBSTRATE / "canonical/annotation_units.jsonl")
    membership = {
        unit["unitId"]: {c["candidatePairId"] for c in unit["candidates"]}
        for unit in canonical
    }
    if {row["unitId"] for row in units} != set(membership):
        raise SystemExit(f"{expected_prefix} cut does not cover exact unit set")
    by_pair: dict[str, dict[str, Any]] = {}
    for row in units:
        errors = list(validator.iter_errors(row))
        if errors:
            raise SystemExit(
                f"invalid annotation row {row['unitId']}: {errors[0].message}"
            )
        if not str(row["coderId"]).startswith(expected_prefix):
            raise SystemExit(f"unexpected coder identity {row['coderId']}")
        observed = {j["candidatePairId"] for j in row["judgments"]}
        if observed != membership[row["unitId"]]:
            raise SystemExit(f"candidate membership drift in {row['unitId']}")
        for judgment in row["judgments"]:
            pair_id = judgment["candidatePairId"]
            if pair_id in by_pair:
                raise SystemExit(f"duplicate candidate judgment: {pair_id}")
            by_pair[pair_id] = {
                **judgment,
                "unitId": row["unitId"],
                "coderId": row["coderId"],
            }
    if len(by_pair) != 248:
        raise SystemExit(f"expected 248 judgments, got {len(by_pair)}")
    return by_pair


def nominal_alpha(a: list[str], b: list[str]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("paired labels required")
    do = sum(x != y for x, y in zip(a, b)) / len(a)
    counts = Counter(a + b)
    n = sum(counts.values())
    if n <= 1:
        return 1.0
    de = 1.0 - sum(v * (v - 1) for v in counts.values()) / (n * (n - 1))
    return 1.0 if de == 0 and do == 0 else (float("nan") if de == 0 else 1.0 - do / de)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cut-a", type=Path, required=True)
    parser.add_argument("--cut-b", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    a = validate_cut(args.cut_a, "ARIES_A_")
    b = validate_cut(args.cut_b, "ARIES_B_")
    if set(a) != set(b):
        raise SystemExit("A/B candidate sets differ")
    ids = sorted(a)
    la = [a[x]["relationLabel"] for x in ids]
    lb = [b[x]["relationLabel"] for x in ids]
    raw = sum(x == y for x, y in zip(la, lb)) / len(ids)
    alpha = nominal_alpha(la, lb)
    disagreements = []
    by_unit_a: dict[str, set[str]] = defaultdict(set)
    by_unit_b: dict[str, set[str]] = defaultdict(set)
    for pair_id in ids:
        if a[pair_id]["relationLabel"] in LINKED:
            by_unit_a[a[pair_id]["unitId"]].add(pair_id)
        if b[pair_id]["relationLabel"] in LINKED:
            by_unit_b[b[pair_id]["unitId"]].add(pair_id)
        if a[pair_id]["relationLabel"] != b[pair_id]["relationLabel"]:
            disagreements.append(
                {
                    "candidatePairId": pair_id,
                    "unitId": a[pair_id]["unitId"],
                    "labelA": a[pair_id]["relationLabel"],
                    "labelB": b[pair_id]["relationLabel"],
                    "adjudicatedLabel": "REPLACE_ME",
                    "rationale": "",
                    "adequacyStanding": "NOT_ANNOTATED_R1",
                    "causalStanding": "NOT_INFERRED",
                }
            )
    units = sorted(set(by_unit_a) | set(by_unit_b) | {a[x]["unitId"] for x in ids})
    exact = 0
    jaccards = []
    for unit in units:
        sa, sb = by_unit_a[unit], by_unit_b[unit]
        exact += sa == sb
        union = sa | sb
        jaccards.append(1.0 if not union else len(sa & sb) / len(union))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    adjudication = args.output_dir / "adjudication-template.jsonl"
    with adjudication.open("w", encoding="utf-8", newline="\n") as fh:
        for row in disagreements:
            fh.write(
                json.dumps(
                    row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
                + "\n"
            )
    result = {
        "schemaVersion": 1,
        "kind": "aries-response-revision-independent-agreement-r1",
        "cutA": {"path": str(args.cut_a), "sha256": digest(args.cut_a)},
        "cutB": {"path": str(args.cut_b), "sha256": digest(args.cut_b)},
        "counts": {
            "candidatePairs": 248,
            "units": 87,
            "disagreements": len(disagreements),
        },
        "pairAgreement": {"rawAgreement": raw, "krippendorffAlphaNominal": alpha},
        "groupLinkedSetAgreement": {
            "exactSetAgreement": exact / len(units),
            "meanJaccard": sum(jaccards) / len(jaccards),
        },
        "goldAdmission": "READY_FOR_ADJUDICATION"
        if disagreements
        else "READY_WITHOUT_ADJUDICATION",
        "truthBoundary": "Agreement measures coder consistency only. It does not establish causal effect, adequacy, or scientific correctness.",
    }
    (args.output_dir / "agreement.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
