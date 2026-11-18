"""Project existing Media processing adapters as composable, read-only Agent LEGO.

FFmpeg, FFprobe, OpenTimelineIO and timed-text tools remain the execution and
verification implementations. This module never executes media operations,
installs equipment, duplicates profiles or becomes a second asset registry.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

# Profile kinds retain current wire contracts despite the stable processing directory.
# The native script and its required first argument form one Profile-kind contract.
# OTIO is editorial metadata and TTML is timed text, not video/audio bytes.
_ADAPTERS = {
    "ordivon.media.v2.av-profile": ("probe-av.sh", "videoSource"),
    "ordivon.media.v2.audio-profile": ("probe-audio.sh", "audioSource"),
    "ordivon.media.v2.otio-profile": ("probe-otio.sh", "editorialTimeline"),
    "ordivon.media.v2.timed-text-profile": ("probe-timed-text.sh", "timedTextDocument"),
}


def processing_profiles(root: Path) -> dict[str, Any]:
    """Discover exact source-owned profiles with digest-bound adapter references.

    Physical tool readiness must be observed by the Workstation/Runtime at
    execution time. A present shell adapter does not prove FFmpeg/OTIO availability.
    """
    directory = root / "processing/profiles"
    profiles: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.json")):
        raw = path.read_bytes()
        value = json.loads(raw)
        if (
            not isinstance(value, dict)
            or value.get("schemaVersion") != 1
            or not isinstance(value.get("kind"), str)
            or not isinstance(value.get("id"), str)
            or not value["id"].strip()
        ):
            raise ValueError(f"invalid Media processing profile: {path.name}")
        if value["id"] in seen:
            raise ValueError(f"duplicate Media processing profile id: {value['id']}")
        seen.add(value["id"])
        adapter = _ADAPTERS.get(value["kind"])
        adapter_path = root / "processing/bin" / adapter[0] if adapter else None
        adapter_digest = (
            "sha256:" + hashlib.sha256(adapter_path.read_bytes()).hexdigest()
            if adapter_path is not None and adapter_path.is_file()
            else None
        )
        profiles.append({
            "id": value["id"],
            "profileKind": value["kind"],
            "profilePath": path.relative_to(root).as_posix(),
            "profileDigest": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "adapterPath": adapter_path.relative_to(root).as_posix() if adapter_path else None,
            "adapterPresent": adapter_path.is_file() if adapter_path else False,
            "adapterDigest": adapter_digest,
            "inputRoles": [adapter[1], "profile", "evidenceDirectory"] if adapter else [],
            "externalToolReadiness": "not-observed",
        })
    return {
        "schemaVersion": 1,
        "kind": "ordivon.media.processing-profile-discovery",
        "catalogPresent": directory.is_dir(),
        "profiles": profiles,
        "authority": "source-owned processing profiles; no duplicate registry or selected-asset authority",
        "executionBoundary": "Runtime executes the existing adapter with the chosen exact profile; the adapter emits raw external-tool evidence and a mechanical profile verdict, not publication or aesthetic approval.",
    }


def processing_probe_plan(
    root: Path,
    *,
    profile_id: str,
    expected_profile_digest: str,
    expected_adapter_digest: str,
    input_path: str,
    evidence_directory: str,
    expected_input_digest: str | None = None,
) -> dict[str, Any]:
    """Compile a native Runtime command from exact, already-discovered inputs.

    No process executes here, and no tool state is inferred. The supplied
    profile and adapter digests prevent a caller from silently changing the
    discovered tool implementation between selection and compilation.
    """
    candidates = processing_profiles(root)["profiles"]
    selected = next((item for item in candidates if item["id"] == profile_id), None)
    if selected is None:
        raise ValueError(f"unknown Media processing profile: {profile_id}")
    if selected["profileDigest"] != expected_profile_digest:
        raise ValueError("selected Media processing profile digest changed")
    if selected["adapterDigest"] != expected_adapter_digest:
        raise ValueError("selected Media processing adapter digest changed")
    if not selected["adapterPresent"] or selected["adapterPath"] is None:
        raise ValueError("selected Media processing adapter is unavailable")
    if not input_path.strip() or not evidence_directory.strip():
        raise ValueError("processing input and evidence directory must be non-empty")
    plan = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-native-processing-probe-plan",
        "profileId": profile_id,
        "profileDigest": selected["profileDigest"],
        "adapterDigest": selected["adapterDigest"],
        "execution": {
            "executionTarget": "local_linux",
            "executable": "/usr/bin/bash",
            "args": [
                selected["adapterPath"],
                input_path,
                selected["profilePath"],
                evidence_directory,
            ],
            "cwdRelative": "capabilities/media",
        },
        "expectedReceipt": str(Path(evidence_directory) / "evidence.json"),
        "completionScope": (
            "Native adapter mechanics only: check its exit status, inspect exact "
            "evidence.json and raw tool observations. No rights, taste, semantic "
            "validity or publication verdict follows from profile acceptance."
        ),
        "authorityBoundary": (
            "Studio compiles; Runtime executes. Input/source bytes and native "
            "tool readiness must still be checked at execution; this is not an "
            "effect admission or a source-byte immutability guarantee."
        ),
    }

    # Opt-in execution-time binding: Runtime owns the host path/digest
    # commitments and the witness. Studio does not claim immutable inputs or
    # proof that an opaque Provider consumed the committed bytes.
    if expected_input_digest is not None:
        import re

        if re.fullmatch(r"sha256:[0-9a-f]{64}", expected_input_digest) is None:
            raise ValueError("expected Media input digest must be lowercase sha256:<hex>")
        from .assets import hash_file

        source = Path(input_path)
        if not source.is_absolute():
            source = root / source
        source = source.resolve(strict=True)
        if not source.is_file():
            raise ValueError(f"selected Media input must be a regular file: {source}")
        if hash_file(source).digest != expected_input_digest:
            raise ValueError("selected Media input digest changed")

        # The execution's resolved input path and Runtime's committed input
        # path must be identical. The existing adapters independently report
        # the actual processed file digest for the consuming Production.
        plan["execution"]["args"][1] = str(source)
        dependencies = [
            {"path": str(source), "expectedDigest": expected_input_digest},
            {
                "path": str((root / selected["profilePath"]).resolve(strict=True)),
                "expectedDigest": selected["profileDigest"],
            },
            {
                "path": str((root / selected["adapterPath"]).resolve(strict=True)),
                "expectedDigest": selected["adapterDigest"],
            },
        ]
        plan["execution"]["hostDependencies"] = sorted(
            dependencies, key=lambda item: item["path"]
        )
        plan["inputByteBinding"] = {
            "inputPath": str(source),
            "expectedDigest": expected_input_digest,
            "witnessScope": "runtime_host_namespace_path_witness",
            "status": "proposed-not-executed",
            "consumerObligation": (
                "Read the native adapter evidence artifact/input digest and "
                "compare with this selected digest. Runtime host dependency "
                "witnesses do not prove target-namespace consumption."
            ),
        }
    return plan
