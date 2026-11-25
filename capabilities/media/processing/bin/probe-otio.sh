#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: probe-otio.sh <timeline.otio> <profile.json> <evidence-dir>" >&2
  exit 64
fi
root=$(cd "$(dirname "$0")/../.." && pwd)
# Keep the complete adapter in this digest-bound source. Only the native
# provider uses CPython 3.13; Studio Core's interpreter is unchanged.
export UV_PYTHON=3.13
exec /usr/bin/mise -C "$root" exec -- uv run --no-project --with 'opentimelineio==0.18.1' python - "$@" <<'PY'
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import opentimelineio as otio


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    # Publish each complete file atomically in the exclusively reserved directory.
    staged = path.with_name(path.name + ".tmp")
    with staged.open("xb") as stream:
        stream.write(raw)
    os.replace(staged, path)
    return digest(raw)


def time_value(value):
    return {"value": value.value, "rate": value.rate}


def range_value(value):
    return {"start": time_value(value.start_time), "duration": time_value(value.duration)}


def range_is_valid(value):
    return all(
        math.isfinite(t.value) and math.isfinite(t.rate) and t.rate > 0
        for t in (value.start_time, value.duration)
    ) and value.duration.value >= 0


def inspect_clip(clip):
    url = getattr(clip.media_reference, "target_url", None)
    source = clip.source_range
    available = None
    try:
        available = clip.available_range()
    except otio.exceptions.CannotComputeAvailableRangeError:
        pass
    if source is None and available is not None:
        source = clip.trimmed_range()
    known = (
        source is not None and available is not None
        and range_is_valid(source) and range_is_valid(available)
    )
    if known:
        in_bounds = (
            not source.start_time < available.start_time
            and not available.end_time_inclusive() < source.end_time_inclusive()
        )
    else:
        in_bounds = None
    return {
        "name": clip.name,
        "activeReference": url if isinstance(url, str) else None,
        "sourceRange": range_value(source) if source is not None and range_is_valid(source) else None,
        "availableRange": range_value(available) if available is not None and range_is_valid(available) else None,
        "inBounds": in_bounds,
    }


def inspect(timeline, prefix):
    # Match native otiotool's recursive Track/Clip traversal, not text lines.
    children = list(timeline.find_children())
    tracks = [
        {"name": child.name, "kind": child.kind}
        for child in children if isinstance(child, otio.schema.Track)
    ]
    clips = [inspect_clip(child) for child in children if isinstance(child, otio.schema.Clip)]
    trimmed = timeline.tracks.trimmed_range()
    facts = {
        "timelineName": timeline.name,
        "startTimecode": otio.opentime.to_timecode(trimmed.start_time),
        "endTimecode": otio.opentime.to_timecode(trimmed.end_time_exclusive()),
        "durationTimecode": otio.opentime.to_timecode(trimmed.duration),
        "trackCount": len(tracks),
        "clipCount": len(clips),
        # Retain one observation per active clip, as in the old native CLI.
        "mediaReferenceCount": len(clips),
        "outOfBoundsCount": sum(c["inBounds"] is False for c in clips),
        "unknownRangeCount": sum(c["inBounds"] is None for c in clips),
        "badMediaReferencePrefixCount": sum(
            c["activeReference"] is None or not c["activeReference"].startswith(prefix)
            for c in clips
        ) if prefix is not None else 0,
    }
    return {
        "nativeVersion": otio.__version__,
        "globalStartTime": time_value(timeline.global_start_time) if timeline.global_start_time is not None else None,
        "relativeRange": range_value(trimmed),
        "tracks": tracks,
        "clips": clips,
        "normalizedFacts": facts,
    }


def validate_profile(profile):
    if (
        not isinstance(profile, dict)
        or type(profile.get("schemaVersion")) is not int
        or profile["schemaVersion"] != 1
        or profile.get("kind") != "ordivon.media.v2.otio-profile"
    ):
        raise ValueError("invalid OTIO profile kind/version")
    for key in ("id", "timelineName", "startTimecode", "endTimecode", "durationTimecode"):
        if not isinstance(profile.get(key), str) or not profile[key]:
            raise ValueError(f"invalid OTIO profile {key}")
    for key in ("trackCount", "clipCount", "mediaReferenceCount"):
        if type(profile.get(key)) is not int or profile[key] < 0:
            raise ValueError(f"invalid OTIO profile {key}")
    prefix = profile.get("requiredMediaPrefix")
    if prefix is not None and (not isinstance(prefix, str) or not prefix):
        raise ValueError("invalid OTIO profile requiredMediaPrefix")
    if type(profile.get("requireAllRangesInBounds", True)) is not bool:
        raise ValueError("invalid OTIO profile requireAllRangesInBounds")


def main():
    source, profile_path, out = map(Path, sys.argv[1:])
    # A destination belongs to exactly one attempt. Preserve all prior evidence;
    # never overwrite a success or reuse a partially produced directory.
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("OTIO evidence directory must be new: " + str(out), file=sys.stderr)
        return 3
    source, profile_path = source.resolve(strict=True), profile_path.resolve(strict=True)
    raw, profile_raw = source.read_bytes(), profile_path.read_bytes()
    profile = json.loads(profile_raw)
    validate_profile(profile)
    # The current profile is native OTIO JSON. Never parse a different carrier
    # and then hash a later read of the path.
    if source.suffix.lower() != ".otio":
        raise ValueError("native OTIO JSON (.otio) is required")
    timeline = otio.adapters.read_from_string(raw.decode("utf-8"), adapter_name="otio_json")
    if not isinstance(timeline, otio.schema.Timeline):
        raise ValueError("selected OTIO object is not a Timeline")
    prefix = profile.get("requiredMediaPrefix")
    inspection = inspect(timeline, prefix)
    facts = inspection["normalizedFacts"]
    checks = [
        {"name": "otio." + key, "expected": profile[key], "actual": facts[key],
         "ok": profile[key] == facts[key]}
        for key in ("timelineName", "startTimecode", "endTimecode", "durationTimecode",
                    "trackCount", "clipCount", "mediaReferenceCount")
    ]
    ranges = False if facts["outOfBoundsCount"] else None if facts["unknownRangeCount"] else True
    checks.extend([
        {"name": "otio.rangesInBounds", "expected": True, "actual": ranges,
         "ok": not profile.get("requireAllRangesInBounds", True) or ranges is True},
        {"name": "otio.mediaReferencePrefix", "expected": prefix,
         "actual": {"badReferenceCount": facts["badMediaReferencePrefixCount"]},
         "ok": prefix is None or facts["badMediaReferencePrefixCount"] == 0},
    ])
    ok = all(check["ok"] for check in checks)
    (out / "raw").mkdir()
    inspection_path = "raw/otio-inspection.json"
    inspection_digest = write_json(out / inspection_path, inspection)
    assertions_digest = write_json(out / "assertions.json", {
        "schemaVersion": 1, "kind": "ordivon.media.v2.otio-assertions",
        "profileId": profile["id"], "normalizedFacts": facts, "ok": ok, "checks": checks,
    })
    evidence = {
        "schemaVersion": 1, "kind": "ordivon.media.v2.external-otio-evidence",
        "truthRole": "editorial-structure-and-range-evidence-not-nle-private-state-or-publication-approval",
        "evidenceDirectory": str(out.resolve()),
        "input": {"path": str(source), "digest": digest(raw), "sizeBytes": len(raw)},
        "profile": {"path": str(profile_path), "digest": digest(profile_raw)},
        "tools": {"opentimelineio": {"version": otio.__version__, "entrypoint": "python-native-api"}},
        "evidence": {"inspectionPath": inspection_path, "inspectionDigest": inspection_digest,
                     "assertionsDigest": assertions_digest},
        "normalizedFacts": facts, "editorialGate": {"ok": ok},
        "nlePrivateState": "not-evaluated", "resolveRoundTrip": "not-evaluated",
        "publicationStanding": "not-evaluated",
    }
    write_json(out / "evidence.json", evidence)
    if not ok:
        for check in checks:
            if not check["ok"]:
                print(f"FAIL {check['name']}: expected={json.dumps(check['expected'])} actual={json.dumps(check['actual'])}", file=sys.stderr)
        return 2
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
