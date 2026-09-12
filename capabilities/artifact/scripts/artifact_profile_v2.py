#!/usr/bin/env python3
"""Shadow mapper/validator for Artifact Profile v2.

R1 proves classification separation and semantic preservation without cutting
production over from profile-v1 or promoting a universal Artifact AST.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "artifact-delivery/profile-v2.shadow.schema.json"

FAMILY_MAP = {
    "document": ("text-document", "office-package"),
    "presentation": ("presentation", "office-package"),
    "spreadsheet": ("spreadsheet", "office-package"),
    "web": ("web", "html-css-js-runtime"),
    "fixed-view": ("fixed-document", "fixed-layout"),
    "accessible": ("fixed-document", "fixed-layout"),
    "archive": ("fixed-document", "fixed-layout"),
}

MEDIA_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
    "pdf-a-4": "application/pdf",
    "pdf-ua-2": "application/pdf",
    "html": "text/html",
    "PNG": "image/png",
    "Apache Parquet": "application/vnd.apache.parquet",
}

GATE_CLAIMS = {
    "profileSchema": "profile schema validation",
    "structural": "artifact structural validity",
    "dependency": "declared build/render dependencies are satisfied",
    "semantic": "profile-specific semantic checks",
    "visual": "visual evidence satisfies the profile",
    "target": "required target authority acceptance",
    "accessibility": "accessibility evidence satisfies the profile",
    "conformance": "selected external conformance profile is satisfied",
    "companionPdf": "required companion PDF exists and is accepted",
    "deliveryReadback": "delivered bytes are read back and identity-checked",
    "releaseProvenance": "release provenance evidence is present and accepted",
}


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA.read_text())


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def fmt(name: str, media_type: str | None = None) -> dict[str, Any]:
    out = {"name": name}
    media = media_type or MEDIA_TYPES.get(name)
    if media:
        out["mediaType"] = media
    return out


def validate(profile: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    validator = jsonschema.Draft202012Validator(load_schema())
    for error in sorted(validator.iter_errors(profile), key=lambda x: list(x.path)):
        failures.append(error.message)
    if failures:
        return failures
    primary = [o for o in profile["outputs"] if o["role"] == "primary"]
    if len(primary) != 1:
        failures.append(f"exactly one primary output is required; found {len(primary)}")
    elif primary[0]["format"] != profile["classification"]["format"]:
        failures.append("classification.format must equal the primary output format")
    contract = profile.get("objectContract")
    if contract and contract.get("required") and not contract.get("schemaReference"):
        failures.append("required objectContract must declare schemaReference")
    for authority in profile.get("targetAuthorities", []):
        if authority["authorityClass"] == "independent-implementation-matrix" and "minimumIndependentImplementations" not in authority:
            failures.append("independent-implementation-matrix requires minimumIndependentImplementations")
    return failures


def v1_conformance(source: dict[str, Any]) -> str | None:
    c = source.get("artifactClass")
    f = source.get("primaryOutput", {}).get("format")
    if c == "accessible" or f == "pdf-ua-2":
        return "PDF/UA-2"
    if c == "archive" or f == "pdf-a-4":
        return "PDF/A-4"
    return None


def map_v1(source: dict[str, Any]) -> dict[str, Any]:
    family, representation = FAMILY_MAP[source["artifactClass"]]
    primary = source["primaryOutput"]
    purposes = [primary["purpose"]]
    if source["artifactClass"] == "accessible" and "accessibility" not in purposes:
        purposes.append("accessibility")
    if source["artifactClass"] == "archive" and "preservation" not in purposes:
        purposes.append("preservation")
    classification: dict[str, Any] = {
        "family": family,
        "representation": representation,
        "format": fmt(primary["format"]),
        "purposes": purposes,
    }
    conformance = v1_conformance(source)
    if conformance:
        classification["conformanceProfile"] = conformance
    outputs = [{
        "role": "primary", "format": fmt(primary["format"]), "purpose": primary["purpose"],
        "required": primary["required"], **({"editable": primary["editable"]} if "editable" in primary else {})
    }]
    for companion in source.get("companions", []):
        outputs.append({
            "role": "companion", "format": fmt(companion["format"]), "purpose": companion["purpose"],
            "required": companion["required"], **({"editable": companion["editable"]} if "editable" in companion else {})
        })
    targets: list[dict[str, Any]] = []
    if source.get("targetRenderer"):
        r = source["targetRenderer"]
        targets.append({"authorityClass": "native-consumer", "name": r["name"], "platform": r["platform"], "required": r["required"]})
    for r in source.get("secondaryRenderers", []):
        targets.append({"authorityClass": "native-consumer", "name": r["name"], "platform": r["platform"], "required": r["required"]})
    evidence = {k: {"required": bool(v), "claim": GATE_CLAIMS.get(k, f"legacy v1 gate: {k}")} for k, v in source["gates"].items()}
    policy: dict[str, Any] = {}
    presentation = {k: source[k] for k in ("aspectRatio", "fontPolicy", "fonts", "semanticPolicy", "renderEvidence") if k in source}
    if presentation:
        policy["presentation"] = presentation
    if "conformancePolicy" in source:
        policy["conformance"] = source["conformancePolicy"]
    if source.get("unsupportedRenderers"):
        policy["unsupportedTargets"] = source["unsupportedRenderers"]
    out: dict[str, Any] = {
        "profileVersion": 2,
        "id": source["id"],
        "classification": classification,
        "construction": {"authorityMode": source["authorityMode"], "locale": source["locale"]},
        "outputs": outputs,
        "targetAuthorities": targets,
        "requiredEvidence": evidence,
        "deliveryDefaults": {"targets": source["deliveryTargets"]},
        "nonClaims": [],
        "notes": source.get("notes", ""),
    }
    if policy:
        out["profilePolicy"] = policy
    return out


def shadow_target(source: dict[str, Any]) -> list[dict[str, Any]]:
    authority = source["classification"].get("targetAuthority")
    if not authority:
        return []
    minimum = 2
    for value in source.get("requiredEvidence", {}).values():
        for key in ("minimumIndependentReaders", "minimumIndependentDecoders", "minimumIndependentImplementations"):
            if key in value:
                minimum = max(minimum, int(value[key]))
    if "matrix" in authority:
        return [{"authorityClass": "independent-implementation-matrix", "name": authority, "required": True, "minimumIndependentImplementations": minimum}]
    return [{"authorityClass": "native-consumer", "name": authority, "required": True}]


def map_shadow(source: dict[str, Any]) -> dict[str, Any]:
    c = source["classification"]
    classification: dict[str, Any] = {
        "family": c["family"],
        "representation": c["representation"],
        "format": fmt(c["format"], c.get("mediaType")),
        "purposes": list(c["purpose"]),
    }
    if c.get("conformanceProfile"):
        classification["conformanceProfile"] = c["conformanceProfile"]
    evidence: dict[str, Any] = {}
    for name, value in source["requiredEvidence"].items():
        claim = value.get("claim") or value.get("acceptance") or value.get("policy") or f"required evidence: {name}"
        item = {"required": bool(value["required"]), "claim": claim}
        params = {k: v for k, v in value.items() if k not in {"required", "claim"}}
        if params:
            item["parameters"] = params
        evidence[name] = item
    out: dict[str, Any] = {
        "profileVersion": 2,
        "id": source["id"],
        "classification": classification,
        "outputs": [{"role": "primary", "format": classification["format"], "purpose": c["purpose"][0], "required": True}],
        "targetAuthorities": shadow_target(source),
        "requiredEvidence": evidence,
        "profilePolicy": {"formatPolicy": source["formatPolicy"]},
        "nonClaims": list(source.get("nonClaims", [])),
        "notes": "Mapped from standards-first shadow profile; remains non-production until profile-v2 graduation.",
    }
    if c["family"] == "dataset":
        out["objectContract"] = {
            "required": True,
            "kind": "dataset-contract-v1",
            "schemaReference": "shadow-contracts/dataset-contract-v1.schema.json",
            "binding": "request-digest",
        }
    return out


def map_profile(source: dict[str, Any]) -> dict[str, Any]:
    if source.get("profileVersion") == 1 and "artifactClass" in source:
        return map_v1(source)
    if source.get("shadowProfileVersion") == 1 and "classification" in source:
        return map_shadow(source)
    raise ValueError("unsupported source profile shape")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    source = json.loads(args.source.read_text())
    mapped = map_profile(source)
    failures = validate(mapped)
    result = {"status": "PASS" if not failures else "FAIL", "source": str(args.source), "sourceDigest": digest(source), "mappedDigest": digest(mapped), "failures": failures, "profile": mapped}
    text = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
