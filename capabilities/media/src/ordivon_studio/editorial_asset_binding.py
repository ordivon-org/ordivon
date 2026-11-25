"""Compose native OTIO active references with an explicitly selected Asset manifest.

The two carriers are parsed and hashed from the same bytes. Matching caller
commitments does not authenticate their origin; local byte readback does not
prove renderer consumption, Runtime execution or recipient acceptance.
The existing editorial profile remains an independent gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .assets import hash_file

SCHEMA = Path(__file__).resolve().parents[2] / "schemas/asset.schema.json"
PREFIX = "ordivon-asset://"


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def verify_editorial_assets(
    timeline_path: Path,
    manifest_path: Path,
    *,
    production_id: str,
    expected_timeline_digest: str | None = None,
    expected_manifest_digest: str | None = None,
    materialized: dict[str, Path] | None = None,
) -> dict[str, Any]:
    """Read-only native reference and selected Blob checks, not editorial QC."""
    import opentimelineio as otio
    from jsonschema import Draft202012Validator

    timeline_raw, manifest_raw = timeline_path.read_bytes(), manifest_path.read_bytes()
    timeline_digest, manifest_digest = _digest(timeline_raw), _digest(manifest_raw)
    for label, actual, expected in (
        ("timeline", timeline_digest, expected_timeline_digest),
        ("manifest", manifest_digest, expected_manifest_digest),
    ):
        if expected is not None and actual != expected:
            raise ValueError(f"{label} digest does not match caller commitment")
    manifest = json.loads(manifest_raw)
    Draft202012Validator(json.loads(SCHEMA.read_bytes())).validate(manifest)
    if manifest["productionId"] != production_id:
        raise ValueError("asset manifest productionId does not match selected Production")
    assets = {}
    for asset in manifest["assets"]:
        if asset["id"] in assets:
            raise ValueError(f"duplicate Asset ID: {asset['id']}")
        assets[asset["id"]] = asset

    timeline = otio.adapters.read_from_string(timeline_raw.decode("utf-8"), adapter_name="otio_json")
    if not isinstance(timeline, otio.schema.Timeline):
        raise ValueError("selected OTIO object is not a Timeline")
    references = []
    selected = {}
    for clip in timeline.find_clips():
        ref = clip.media_reference
        if not isinstance(ref, otio.schema.ExternalReference) or not ref.target_url.startswith(PREFIX):
            raise ValueError(f"clip {clip.name!r} has no supported active Asset URI")
        asset_id = ref.target_url.removeprefix(PREFIX)
        asset = assets.get(asset_id)
        if asset is None:
            raise ValueError(f"active Asset URI is undeclared: {ref.target_url}")
        blob = asset.get("selectedBlob")
        if blob is None:
            raise ValueError(f"active Asset has no selected Blob: {asset_id}")
        selected[asset_id] = blob
        references.append({"clip": clip.name, "assetId": asset_id, "uri": ref.target_url})
    if not references:
        raise ValueError("no active clip references to qualify")

    supplied = materialized or {}
    if set(supplied) - set(selected):
        raise ValueError("materialized mapping includes an Asset not selected by the timeline")
    observations = {}
    for asset_id, blob in selected.items():
        path = supplied.get(asset_id)
        standing = "not-observed"
        if path is not None:
            observed = hash_file(path)
            if observed.digest != blob["digest"] or observed.size_bytes != blob["sizeBytes"]:
                raise ValueError(f"materialized bytes do not match selected Blob: {asset_id}")
            standing = "local-bytes-match"
        observations[asset_id] = {"selectedBlob": blob, "materializationStanding": standing}

    def time_value(value: Any) -> dict[str, float] | None:
        return None if value is None else {"value": value.value, "rate": value.rate}

    return {
        "schemaVersion": 1,
        "kind": "ordivon.media.editorial-asset-binding",
        "productionId": production_id,
        "timelineDigest": timeline_digest,
        "manifestDigest": manifest_digest,
        "nativeOTIOVersion": otio.__version__,
        "globalStartTime": time_value(timeline.global_start_time),
        "relativeDuration": time_value(timeline.duration()),
        "activeReferences": references,
        "assets": observations,
        "declaredReferenceStanding": "matched",
        "frozenBindingStanding": (
            "caller-commitments-match"
            if expected_timeline_digest is not None and expected_manifest_digest is not None
            else "not-established"
        ),
        "materializationStanding": (
            "all-local-bytes-match" if len(supplied) == len(selected) else "not-fully-observed"
        ),
        "editorialGate": "not-evaluated",
        "rendererConsumption": "not-observed",
        "recipientStanding": "not-observed",
        "publicationStanding": "not-evaluated",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("timeline", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("production_id")
    parser.add_argument("--expected-timeline-digest")
    parser.add_argument("--expected-manifest-digest")
    parser.add_argument("--materialized", action="append", default=[], metavar="ASSET_ID=PATH")
    args = parser.parse_args()
    paths = {}
    for item in args.materialized:
        asset_id, sep, path = item.partition("=")
        if not sep or not asset_id or not path or asset_id in paths:
            parser.error("materialized mapping must be unique nonempty ASSET_ID=PATH")
        paths[asset_id] = Path(path)
    result = verify_editorial_assets(
        args.timeline, args.manifest, production_id=args.production_id,
        expected_timeline_digest=args.expected_timeline_digest,
        expected_manifest_digest=args.expected_manifest_digest, materialized=paths,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
