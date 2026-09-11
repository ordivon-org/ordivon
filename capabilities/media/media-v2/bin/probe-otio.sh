#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: probe-otio.sh <timeline.otio> <profile.json> <evidence-dir>" >&2
  exit 64
fi

input=$(realpath "$1")
profile=$(realpath "$2")
out=$3
root=$(git rev-parse --show-toplevel)
otiotool="$root/media-v2/bin/otiotool-pinned.sh"

[[ -f "$input" ]] || { echo "timeline not found: $input" >&2; exit 66; }
[[ -f "$profile" ]] || { echo "profile not found: $profile" >&2; exit 66; }
command -v jq >/dev/null
command -v sha256sum >/dev/null

mkdir -p "$out/raw"
inspection="$out/raw/otiotool-inspection.txt"
assertions="$out/assertions.json"
evidence="$out/evidence.json"

"$otiotool" -i "$input" --stats --list-tracks --list-clips --list-media --verify-ranges > "$inspection"

input_sha="sha256:$(sha256sum "$input" | awk '{print $1}')"
input_bytes=$(stat -c '%s' "$input")
profile_sha="sha256:$(sha256sum "$profile" | awk '{print $1}')"
inspection_sha="sha256:$(sha256sum "$inspection" | awk '{print $1}')"

timeline_name=$(sed -n 's/^Name:[[:space:]]*//p' "$inspection" | head -n1)
start_tc=$(sed -n 's/^Start:[[:space:]]*//p' "$inspection" | head -n1)
end_tc=$(sed -n 's/^End:[[:space:]]*//p' "$inspection" | head -n1)
duration_tc=$(sed -n 's/^Duration:[[:space:]]*//p' "$inspection" | head -n1)
track_count=$(grep -c '^TRACK:' "$inspection" || true)
clip_count=$(grep -c '^[[:space:]]*CLIP:' "$inspection" || true)
media_count=$(grep -c '^[[:space:]]*MEDIA:' "$inspection" || true)
out_of_bounds_count=$(grep -c 'OUT OF BOUNDS' "$inspection" || true)
required_prefix=$(jq -r '.requiredMediaPrefix // empty' "$profile")
if [[ -n "$required_prefix" ]]; then
  bad_prefix_count=$(sed -n 's/^[[:space:]]*MEDIA:[[:space:]]*//p' "$inspection" | grep -vc "^${required_prefix}" || true)
else
  bad_prefix_count=0
fi

jq -n \
  --slurpfile p "$profile" \
  --arg timelineName "$timeline_name" \
  --arg startTimecode "$start_tc" \
  --arg endTimecode "$end_tc" \
  --arg durationTimecode "$duration_tc" \
  --argjson trackCount "$track_count" \
  --argjson clipCount "$clip_count" \
  --argjson mediaReferenceCount "$media_count" \
  --argjson outOfBoundsCount "$out_of_bounds_count" \
  --argjson badPrefixCount "$bad_prefix_count" '
  $p[0] as $p |
  [
    {name:"otio.timelineName", expected:$p.timelineName, actual:$timelineName, ok:($timelineName == $p.timelineName)},
    {name:"otio.startTimecode", expected:$p.startTimecode, actual:$startTimecode, ok:($startTimecode == $p.startTimecode)},
    {name:"otio.endTimecode", expected:$p.endTimecode, actual:$endTimecode, ok:($endTimecode == $p.endTimecode)},
    {name:"otio.durationTimecode", expected:$p.durationTimecode, actual:$durationTimecode, ok:($durationTimecode == $p.durationTimecode)},
    {name:"otio.trackCount", expected:$p.trackCount, actual:$trackCount, ok:($trackCount == $p.trackCount)},
    {name:"otio.clipCount", expected:$p.clipCount, actual:$clipCount, ok:($clipCount == $p.clipCount)},
    {name:"otio.mediaReferenceCount", expected:$p.mediaReferenceCount, actual:$mediaReferenceCount, ok:($mediaReferenceCount == $p.mediaReferenceCount)},
    {name:"otio.rangesInBounds", expected:true, actual:($outOfBoundsCount == 0), ok:((($p.requireAllRangesInBounds // true) | not) or $outOfBoundsCount == 0)},
    {name:"otio.mediaReferencePrefix", expected:($p.requiredMediaPrefix // null), actual:{badReferenceCount:$badPrefixCount}, ok:(($p.requiredMediaPrefix // null) == null or $badPrefixCount == 0)}
  ] as $checks |
  {
    schemaVersion:1,
    kind:"ordivon.media.v2.otio-assertions",
    profileId:$p.id,
    normalizedFacts:{timelineName:$timelineName,startTimecode:$startTimecode,endTimecode:$endTimecode,durationTimecode:$durationTimecode,trackCount:$trackCount,clipCount:$clipCount,mediaReferenceCount:$mediaReferenceCount,outOfBoundsCount:$outOfBoundsCount,badMediaReferencePrefixCount:$badPrefixCount},
    ok:($checks|all(.ok)),
    checks:$checks
  }
' > "$assertions"

assertions_sha="sha256:$(sha256sum "$assertions" | awk '{print $1}')"
ok=$(jq -r '.ok' "$assertions")

jq -n \
  --arg input "$input" \
  --arg inputDigest "$input_sha" \
  --argjson inputBytes "$input_bytes" \
  --arg profile "$profile" \
  --arg profileDigest "$profile_sha" \
  --arg inspectionDigest "$inspection_sha" \
  --arg assertionsDigest "$assertions_sha" \
  --slurpfile a "$assertions" \
  --argjson ok "$ok" '
  {
    schemaVersion:1,
    kind:"ordivon.media.v2.external-otio-evidence",
    truthRole:"editorial-structure-and-range-evidence-not-nle-private-state-or-publication-approval",
    input:{path:$input,digest:$inputDigest,sizeBytes:$inputBytes},
    profile:{path:$profile,digest:$profileDigest},
    tools:{opentimelineio:{version:"0.18.1",entrypoint:"otiotool"}},
    evidence:{inspectionDigest:$inspectionDigest,assertionsDigest:$assertionsDigest},
    normalizedFacts:$a[0].normalizedFacts,
    editorialGate:{ok:$ok},
    nlePrivateState:"not-evaluated",
    resolveRoundTrip:"not-evaluated",
    publicationStanding:"not-evaluated"
  }
' > "$evidence"

if [[ "$ok" != "true" ]]; then
  jq -r '.checks[] | select(.ok == false) | "FAIL \(.name): expected=\(.expected|tojson) actual=\(.actual|tojson)"' "$assertions" >&2
  exit 2
fi

cat "$evidence"
