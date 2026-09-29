#!/usr/bin/env python3
"""Dimensioned Social Fabric flux projection over two owner-counter cuts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
INPUT_KIND = "ordivon.social-fabric-counter-cut-pair"
OUTPUT_KIND = "ordivon.social-flux-projection"


class SocialFluxError(ValueError):
    pass


def digest(v: Any) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            json.dumps(
                v, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
    )


def _instant(v: Any, label: str) -> datetime:
    if not isinstance(v, str) or not v:
        raise SocialFluxError(f"{label} must be a non-empty ISO timestamp")
    try:
        d = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError as e:
        raise SocialFluxError(f"{label} invalid timestamp") from e
    if d.tzinfo is None:
        raise SocialFluxError(f"{label} must include timezone")
    return d


def _cut(v: Any, label: str) -> dict[str, Any]:
    if not isinstance(v, dict):
        raise SocialFluxError(f"{label} must be an object")
    _instant(v.get("observedAt"), f"{label}.observedAt")
    refs = v.get("sourceRefs")
    if (
        not isinstance(refs, list)
        or not refs
        or not all(isinstance(x, str) and x for x in refs)
    ):
        raise SocialFluxError(f"{label}.sourceRefs must be non-empty strings")
    cs = v.get("counters")
    if not isinstance(cs, dict) or not cs:
        raise SocialFluxError(f"{label}.counters must be non-empty")
    for k, x in cs.items():
        if not isinstance(k, str) or not k or not isinstance(x, dict):
            raise SocialFluxError(f"{label}.counter invalid")
        if not isinstance(x.get("value"), int) or x["value"] < 0:
            raise SocialFluxError(f"{label}.{k}.value invalid")
        for f in ("owner", "unit"):
            if not isinstance(x.get(f), str) or not x[f]:
                raise SocialFluxError(f"{label}.{k}.{f} invalid")
        if x.get("counterSemantics") != "monotonic":
            raise SocialFluxError(f"{label}.{k}.counterSemantics must be monotonic")
    return v


def compile_flux(pair: dict[str, Any]) -> dict[str, Any]:
    if pair.get("schemaVersion") != 1 or pair.get("kind") != INPUT_KIND:
        raise SocialFluxError("unsupported counter-cut-pair kind/schema")
    a = _cut(pair.get("start"), "start")
    b = _cut(pair.get("end"), "end")
    window = (
        _instant(b["observedAt"], "end.observedAt")
        - _instant(a["observedAt"], "start.observedAt")
    ).total_seconds()
    if window <= 0:
        raise SocialFluxError("end must be after start")
    ak = set(a["counters"])
    bk = set(b["counters"])
    if ak != bk:
        raise SocialFluxError(
            f"counter key mismatch: startOnly={sorted(ak - bk)} endOnly={sorted(bk - ak)}"
        )
    coverage = pair.get("coverage")
    if (
        not isinstance(coverage, dict)
        or not isinstance(coverage.get("standing"), str)
        or not coverage["standing"]
    ):
        raise SocialFluxError("coverage.standing must be non-empty")
    rows = []
    for k in sorted(ak):
        x = a["counters"][k]
        y = b["counters"][k]
        if (x["owner"], x["unit"], x["counterSemantics"]) != (
            y["owner"],
            y["unit"],
            y["counterSemantics"],
        ):
            raise SocialFluxError(f"counter contract drift: {k}")
        delta = y["value"] - x["value"]
        if delta < 0:
            raise SocialFluxError(f"monotonic counter regressed: {k}")
        rows.append(
            {
                "metric": k,
                "owner": x["owner"],
                "startValue": x["value"],
                "endValue": y["value"],
                "delta": delta,
                "windowSeconds": window,
                "rate": {
                    "perSecond": delta / window,
                    "perHour": delta / window * 3600.0,
                    "dimensions": {
                        "perSecond": f"{x['unit']}/second",
                        "perHour": f"{x['unit']}/hour",
                    },
                },
                "sourceRefs": sorted(set(a["sourceRefs"] + b["sourceRefs"])),
                "coverageStanding": coverage["standing"],
                "standing": "UNCHANGED" if delta == 0 else "INCREASED",
            }
        )
    out = {
        "schemaVersion": 1,
        "kind": OUTPUT_KIND,
        "truthRole": "rebuildable-dimensional-rate-projection",
        "startObservedAt": a["observedAt"],
        "endObservedAt": b["observedAt"],
        "windowSeconds": window,
        "sourceCutDigest": digest(pair),
        "coverage": coverage,
        "metrics": rows,
        "nonClaims": [
            "A rate is an observation, not priority or scheduling authority.",
            "Bounded counter coverage does not imply global completeness.",
            "No dimensionless pressure score is derived.",
            "Natural owners retain counter truth and EffectAuthority.",
        ],
    }
    out["projectionDigest"] = digest(out)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pair", type=Path, required=True)
    ns = p.parse_args()
    raw = json.loads(ns.pair.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SocialFluxError("pair must be JSON object")
    print(json.dumps(compile_flux(raw), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
