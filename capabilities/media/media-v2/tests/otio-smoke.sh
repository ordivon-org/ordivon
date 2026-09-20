#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
work="$root/.tmp/media-v2-otio-smoke"
rm -rf "$work"
mkdir -p "$work"
trap 'rm -rf "$work"' EXIT

probe="$root/media-v2/bin/probe-otio.sh"

/usr/bin/uv run --with 'opentimelineio==0.18.1' python - "$work/good.otio" "$work/bad-range.otio" <<'PY'
import sys
import opentimelineio as otio

def write(path, source_start, source_duration, available_duration):
    available = otio.opentime.TimeRange(otio.opentime.RationalTime(0, 30), otio.opentime.RationalTime(available_duration, 30))
    source = otio.opentime.TimeRange(otio.opentime.RationalTime(source_start, 30), otio.opentime.RationalTime(source_duration, 30))
    clip = otio.schema.Clip(name='clip', media_reference=otio.schema.ExternalReference(target_url='ordivon-asset://fixture', available_range=available), source_range=source)
    track = otio.schema.Track(name='V1', kind=otio.schema.TrackKind.Video)
    track.append(clip)
    timeline = otio.schema.Timeline(name='OTIO Smoke')
    timeline.tracks.append(track)
    otio.adapters.write_to_file(timeline, path)

write(sys.argv[1], 0, 30, 30)
write(sys.argv[2], 25, 20, 30)
PY

cat > "$work/profile.json" <<'EOF'
{
  "schemaVersion":1,
  "kind":"ordivon.media.v2.otio-profile",
  "id":"otio-smoke",
  "timelineName":"OTIO Smoke",
  "startTimecode":"00:00:00:00",
  "endTimecode":"00:00:01:00",
  "durationTimecode":"00:00:01:00",
  "trackCount":1,
  "clipCount":1,
  "mediaReferenceCount":1,
  "requiredMediaPrefix":"ordivon-asset://",
  "requireAllRangesInBounds":true
}
EOF

bash "$probe" "$work/good.otio" "$work/profile.json" "$work/good-evidence" >/dev/null
jq -e '.editorialGate.ok == true and .normalizedFacts.trackCount == 1 and .normalizedFacts.clipCount == 1' "$work/good-evidence/evidence.json" >/dev/null

if bash "$probe" "$work/bad-range.otio" "$work/profile.json" "$work/bad-range-evidence" >/dev/null 2>"$work/bad-range.stderr"; then
  echo "out-of-bounds OTIO unexpectedly passed" >&2
  exit 1
fi
grep -q 'FAIL otio.rangesInBounds' "$work/bad-range.stderr"

jq '.id="otio-smoke-wrong-count" | .clipCount=2' "$work/profile.json" > "$work/wrong-count-profile.json"
if bash "$probe" "$work/good.otio" "$work/wrong-count-profile.json" "$work/wrong-count-evidence" >/dev/null 2>"$work/wrong-count.stderr"; then
  echo "wrong-count OTIO profile unexpectedly passed" >&2
  exit 1
fi
grep -q 'FAIL otio.clipCount' "$work/wrong-count.stderr"

printf '%s\n' '{not valid otio' > "$work/malformed.otio"
if bash "$probe" "$work/malformed.otio" "$work/profile.json" "$work/malformed-evidence" >/dev/null 2>/dev/null; then
  echo "malformed OTIO unexpectedly passed" >&2
  exit 1
fi

echo 'media-v2 OTIO smoke: PASS (official OTIO inspection accepted good timeline; range/count/malformed negatives rejected)'
