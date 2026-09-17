from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from artifact_core.contracts import file_fact, sha256_file


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_file_fact(fact: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    path_value = fact.get("path")
    path = Path(path_value) if isinstance(path_value, str) and path_value else None
    if path is None or not path.is_file():
        failures.append("referenced file is absent")
        return {"status": "FAIL", "path": path_value, "failures": failures}
    actual = file_fact(path)
    if fact.get("name") != actual.get("name"):
        failures.append("file name mismatch")
    if fact.get("size") != actual.get("size"):
        failures.append("file size mismatch")
    if fact.get("digest", {}).get("sha256") != actual.get("digest", {}).get("sha256"):
        failures.append("file SHA-256 mismatch")
    return {"status": "PASS" if not failures else "FAIL", "path": str(path), "actual": actual, "failures": failures}


def verify_render_evidence(render_dir: Path, expected_slides: int) -> dict[str, Any]:
    pngs = sorted(p for p in render_dir.iterdir() if p.is_file() and p.suffix.casefold() == ".png") if render_dir.is_dir() else []
    bad = [str(p) for p in pngs if p.stat().st_size <= 0]
    ok = len(pngs) == expected_slides and not bad and expected_slides > 0
    return {
        "status": "PASS" if ok else "FAIL",
        "renderDirectory": str(render_dir.resolve()),
        "expectedSlideCount": expected_slides,
        "observedPngCount": len(pngs),
        "emptyFiles": bad,
        "digests": [{"name": p.name, "sha256": sha256_file(p)} for p in pngs],
        "note": "Presence/count/digest evidence does not replace visual defect review.",
    }


def verify_target_evidence(evidence_path: Path, pptx: Path, pdf: Path | None, expected_slides: int, render_result: dict[str, Any] | None = None) -> dict[str, Any]:
    value = load_json(evidence_path)
    failures: list[str] = []
    if value.get("artifact", {}).get("sha256") != sha256_file(pptx):
        failures.append("target evidence PPTX digest does not match the inspected artifact")
    renderer = value.get("renderer", {})
    if renderer.get("name") != "Microsoft PowerPoint Desktop":
        failures.append("target evidence renderer is not Microsoft PowerPoint Desktop")
    if int(value.get("result", {}).get("slideCount", -1)) != expected_slides:
        failures.append("target evidence slide count mismatch")
    if pdf is not None and value.get("result", {}).get("pdfSha256") != sha256_file(pdf):
        failures.append("target evidence PDF digest mismatch")
    if not renderer.get("version"):
        failures.append("target evidence omitted PowerPoint version")
    if render_result is not None and render_result.get("status") == "PASS":
        expected_render_map = {item["name"]: item["sha256"] for item in render_result.get("digests", [])}
        target_pngs = value.get("result", {}).get("pngs")
        if not isinstance(target_pngs, list):
            failures.append("target evidence omitted PNG digest list")
        else:
            observed_render_map = {str(item.get("name")): str(item.get("sha256")) for item in target_pngs if isinstance(item, dict)}
            if observed_render_map != expected_render_map:
                failures.append("target evidence PNG digests do not match rendered evidence")
        if int(value.get("result", {}).get("pngCount", -1)) != expected_slides:
            failures.append("target evidence PNG count mismatch")
    return {"status": "PASS" if not failures else "FAIL", "evidencePath": str(evidence_path.resolve()), "renderer": renderer, "failures": failures}


def verify_visual_review(evidence_path: Path, pptx: Path, render_result: dict[str, Any]) -> dict[str, Any]:
    value = load_json(evidence_path)
    failures: list[str] = []
    if value.get("artifactSha256") != sha256_file(pptx):
        failures.append("visual review artifact digest mismatch")
    if value.get("verdict") != "PASS":
        failures.append("visual review verdict is not PASS")
    blocking = value.get("blockingDefects")
    if not isinstance(blocking, list) or blocking:
        failures.append("visual review must provide an empty blockingDefects list")
    expected_renders = {item["name"]: item["sha256"] for item in render_result.get("digests", [])}
    observed_renders = value.get("renderDigests")
    if not isinstance(observed_renders, dict) or observed_renders != expected_renders:
        failures.append("visual review render digests do not bind the exact rendered evidence")
    methods = value.get("methods")
    if not isinstance(methods, list) or not methods or not all(isinstance(item, str) and item for item in methods):
        failures.append("visual review must name at least one review method")
    return {
        "status": "PASS" if not failures else "FAIL",
        "evidencePath": str(evidence_path.resolve()),
        "methods": methods if isinstance(methods, list) else [],
        "blockingDefects": blocking if isinstance(blocking, list) else None,
        "failures": failures,
        "boundary": "Visual-review evidence is bound to exact PPTX and render digests; structural/target/delivery validators remain independent gates.",
    }


def verify_readback(source: Path, readback: Path, destination: str | None = None, destination_reference: str | None = None, artifact_role: str | None = None) -> dict[str, Any]:
    source_fact = file_fact(source)
    read_fact = file_fact(readback)
    matched = source_fact["digest"]["sha256"] == read_fact["digest"]["sha256"]
    return {
        "status": "PASS" if matched else "FAIL",
        "destination": destination,
        "destinationReference": destination_reference,
        "artifactRole": artifact_role,
        "source": source_fact,
        "readback": read_fact,
        "digestMatched": matched,
    }


def verify_delivery_evidence(evidence_paths: Iterable[Path], profile: dict[str, Any], pptx: Path, pdf: Path | None) -> dict[str, Any]:
    expected_artifacts: dict[str, str] = {"primary": sha256_file(pptx)}
    required_companions = [item for item in profile.get("companions", []) if item.get("required") is True]
    if required_companions:
        if pdf is None:
            return {"status": "FAIL", "failures": ["required companion delivery cannot be verified without a companion PDF"], "evidence": []}
        expected_artifacts["companion"] = sha256_file(pdf)
    expected_pairs = {(str(destination), role) for destination in profile.get("deliveryTargets", []) for role in expected_artifacts}
    seen: set[tuple[str, str]] = set()
    failures: list[str] = []
    evidence: list[dict[str, Any]] = []
    for path in evidence_paths:
        value = load_json(path)
        destination = value.get("destination")
        role = value.get("artifactRole")
        pair = (str(destination), str(role))
        item_failures: list[str] = []
        if pair not in expected_pairs:
            item_failures.append(f"unexpected destination/artifactRole pair: {pair}")
        elif pair in seen:
            item_failures.append(f"duplicate destination/artifactRole evidence: {pair}")
        else:
            seen.add(pair)
        if value.get("status") != "PASS" or value.get("digestMatched") is not True:
            item_failures.append("read-back evidence did not PASS exact digest comparison")
        expected_digest = expected_artifacts.get(str(role))
        if expected_digest is not None and value.get("source", {}).get("digest", {}).get("sha256") != expected_digest:
            item_failures.append("read-back evidence source digest does not match the current build artifact")
        if not value.get("destinationReference"):
            item_failures.append("read-back evidence omitted destinationReference")
        failures.extend(f"{path}: {item}" for item in item_failures)
        evidence.append({"path": str(path.resolve()), "destination": destination, "artifactRole": role, "failures": item_failures})
    missing = sorted(expected_pairs - seen)
    if missing:
        failures.append("missing required destination/artifactRole read-back evidence: " + repr(missing))
    return {
        "status": "PASS" if not failures else "FAIL",
        "expected": sorted(expected_pairs),
        "evidence": evidence,
        "failures": failures,
        "boundary": "The delivery adapter owns the external write/read operation; this gate verifies exact returned bytes plus destination reference without inventing a transport protocol.",
    }
