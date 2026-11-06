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
_ADAPTERS = {
    "ordivon.media.v2.av-profile": "probe-av.sh",
    "ordivon.media.v2.audio-profile": "probe-audio.sh",
    "ordivon.media.v2.otio-profile": "probe-otio.sh",
    "ordivon.media.v2.timed-text-profile": "probe-timed-text.sh",
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
        adapter_path = root / "processing/bin" / adapter if adapter else None
        profiles.append({
            "id": value["id"],
            "profileKind": value["kind"],
            "profilePath": path.relative_to(root).as_posix(),
            "profileDigest": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "adapterPath": adapter_path.relative_to(root).as_posix() if adapter_path else None,
            "adapterPresent": adapter_path.is_file() if adapter_path else False,
            "inputRoles": ["mediaSource", "profile", "evidenceDirectory"],
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
