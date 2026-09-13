#!/usr/bin/env python3
"""Thin verification-service adapter for already-existing Artifact bytes.

R1 intentionally does not define artifact content semantics, transport, workflow, or
publication state. It validates an exact request envelope, exact byte/profile/contract
bindings, requires an already LOCAL_LIVE_PROVEN capability binding, and delegates the
actual claim to the existing family-specific verifier.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifact-delivery"
REQUEST_SCHEMA = ART / "verification/request-v1.schema.json"
PROFILE_ROOT = ART / "shadow-v2/examples"
BINDING_ROOT = ART / "shadow-bindings"

# Explicit R1 service surface. A profile is not callable merely because a file exists.
# Every entry must also have a LOCAL_LIVE_PROVEN capability binding at execution time.
ROUTES: dict[str, tuple[str, str, bool]] = {
    "still-image-png-srgb-r1": ("scripts/artifact_still_image.py", "verify_png_srgb", False),
    "still-image-svg-static-r1": ("scripts/artifact_svg.py", "verify_svg", False),
    "dataset-parquet-flat-r1": ("scripts/artifact_dataset.py", "verify_parquet", True),
    "audio-flac-pcm16-r1": ("scripts/artifact_audio.py", "verify_flac", True),
    "audio-wave-pcm16-r1": ("scripts/artifact_wave.py", "verify_wave", True),
    "audio-ogg-vorbis-r1": ("scripts/artifact_ogg_vorbis.py", "verify_ogg_vorbis", True),
    "geospatial-geopackage-point-r1": ("scripts/artifact_geospatial.py", "verify_geopackage", True),
    "moving-image-matroska-ffv1-v3-r1": ("scripts/artifact_moving_image.py", "verify_moving_image", True),
    "design-2d-tiled-tmj-object-map-r1": ("scripts/artifact_tiled.py", "verify_tiled_tmj", True),
    "design-2d-aseprite-horizontal-sheet-r1": ("scripts/artifact_aseprite.py", "verify_aseprite", True),
    "design-3d-glb-static-mesh-r1": ("scripts/artifact_design3d.py", "verify_glb", True),
    "design-3d-glb-material-scene-r1": ("scripts/artifact_design3d.py", "verify_glb", True),
    "design-3d-glb-skinned-animation-r1": ("scripts/artifact_design3d.py", "verify_glb", True),
    "web-archive-warc-response-r1": ("scripts/artifact_web_archive.py", "verify_warc", True),
    "message-internet-text-r1": ("scripts/artifact_message.py", "verify_message", True),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def request_fail(request_id: str | None, failures: list[str], *, request_digest: str | None = None) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "artifact-verification-result",
        "requestId": request_id,
        "requestDigest": request_digest,
        "status": "FAIL",
        "failures": failures,
        "boundary": "Request admission failure; no family-specific Artifact verification PASS is claimed."
    }


def validate_request(value: Any) -> list[str]:
    schema = load_json(REQUEST_SCHEMA)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    return [e.message for e in sorted(validator.iter_errors(value), key=lambda e: list(e.path))]


def resolve_request_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path)
    return path.resolve()


def binding_for(profile_id: str) -> tuple[Path, dict[str, Any]] | None:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(BINDING_ROOT.glob("*.json")):
        value = load_json(path)
        if value.get("profileId") == profile_id:
            matches.append((path, value))
    if len(matches) != 1:
        return None
    return matches[0]


def load_function(relative: str, name: str) -> tuple[Callable[..., dict[str, Any]], str]:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location("artifact_verify_delegate_" + path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load verifier module: {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, name, None)
    if not callable(fn):
        raise RuntimeError(f"verifier function missing: {relative}:{name}")
    return fn, sha256_file(path)


def verify_request(request_path: Path) -> dict[str, Any]:
    try:
        request = load_json(request_path)
    except Exception as error:
        return request_fail(None, [f"request JSON unreadable: {error}"])
    request_id = request.get("requestId") if isinstance(request, dict) else None
    failures = validate_request(request)
    request_digest = canonical_sha256(request) if isinstance(request, dict) else None
    if failures:
        return request_fail(request_id, [f"request schema invalid: {x}" for x in failures], request_digest=request_digest)

    profile_ref = request["profile"]
    profile_id = profile_ref["id"]
    route = ROUTES.get(profile_id)
    if route is None:
        return request_fail(request_id, [f"profile is not on the Artifact verification R1 service surface: {profile_id}"], request_digest=request_digest)

    profile_path = resolve_request_path(profile_ref["path"])
    expected_profile_root = PROFILE_ROOT.resolve()
    if expected_profile_root not in profile_path.parents:
        return request_fail(request_id, ["profile path is outside the normalized Artifact profile authority"], request_digest=request_digest)
    if not profile_path.is_file():
        return request_fail(request_id, ["profile file is unavailable"], request_digest=request_digest)
    if sha256_file(profile_path) != profile_ref["sha256"]:
        return request_fail(request_id, ["profile bytes differ from request digest"], request_digest=request_digest)
    profile = load_json(profile_path)
    if profile.get("profileVersion") != 2 or profile.get("id") != profile_id:
        return request_fail(request_id, ["profile identity/version differs from request"], request_digest=request_digest)

    bound = binding_for(profile_id)
    if bound is None:
        return request_fail(request_id, ["exactly one capability binding is required for the profile"], request_digest=request_digest)
    binding_path, binding = bound
    if binding.get("status") != "LOCAL_LIVE_PROVEN":
        return request_fail(request_id, ["profile capability binding is not LOCAL_LIVE_PROVEN"], request_digest=request_digest)

    subject_path = resolve_request_path(request["subject"]["path"])
    if not subject_path.is_file():
        return request_fail(request_id, ["subject is not a regular file"], request_digest=request_digest)
    subject_sha = sha256_file(subject_path)
    if subject_sha != request["subject"]["sha256"]:
        return request_fail(request_id, ["subject bytes differ from request digest"], request_digest=request_digest)

    verifier_relative, verifier_name, contract_required = route
    contract_path: Path | None = None
    contract_fact: dict[str, Any] | None = None
    if request.get("objectContract"):
        contract_path = resolve_request_path(request["objectContract"]["path"])
        if not contract_path.is_file():
            return request_fail(request_id, ["object contract is not a regular file"], request_digest=request_digest)
        contract_sha = sha256_file(contract_path)
        if contract_sha != request["objectContract"]["sha256"]:
            return request_fail(request_id, ["object contract bytes differ from request digest"], request_digest=request_digest)
        contract_fact = {"path": str(contract_path), "sha256": contract_sha}
    elif contract_required:
        return request_fail(request_id, [f"profile requires an object contract: {profile_id}"], request_digest=request_digest)

    evidence_dir = resolve_request_path(request["evidenceDirectory"])
    evidence_dir.mkdir(parents=True, exist_ok=True)
    verifier, verifier_sha = load_function(verifier_relative, verifier_name)
    if contract_required:
        assert contract_path is not None
        delegated = verifier(subject_path, contract_path, evidence_dir)
    else:
        delegated = verifier(subject_path, evidence_dir)

    delegated_status = delegated.get("status")
    result = {
        "schemaVersion": 1,
        "kind": "artifact-verification-result",
        "requestId": request_id,
        "requestDigest": request_digest,
        "status": "PASS" if delegated_status == "PASS" else "FAIL",
        "profile": {"id": profile_id, "path": str(profile_path), "sha256": profile_ref["sha256"], "standing": "SHADOW_PROFILE_LIVE_VERIFIER"},
        "subject": {"path": str(subject_path), "sha256": subject_sha, "size": subject_path.stat().st_size},
        "objectContract": contract_fact,
        "capabilityBinding": {"path": str(binding_path.resolve()), "sha256": sha256_file(binding_path), "standing": binding["status"]},
        "verifier": {"path": verifier_relative, "sha256": verifier_sha, "function": verifier_name},
        "consumer": request.get("consumer"),
        "verification": delegated,
        "failures": list(delegated.get("failures") or []),
        "boundary": "PASS means the exact requested bytes passed the selected Artifact profile through its existing live-proven family verifier. It does not promote a shadow profile to production, prove caller-domain suitability, define transport/workflow semantics, or upgrade the verifier's declared nonClaims."
    }
    (evidence_dir / "service-result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("request", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = verify_request(args.request.resolve())
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
