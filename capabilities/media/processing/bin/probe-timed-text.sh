#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: probe-timed-text.sh <timed-text> <profile.json> <evidence-dir>" >&2
  exit 64
fi

input=$(realpath "$1")
profile=$(realpath "$2")
out=$3

# Reserve exactly one execution destination without overwriting prior evidence.
mkdir -p -- "$(dirname -- "$out")"
if ! mkdir -- "$out"; then
  echo "evidence directory must be new: $out" >&2
  exit 3
fi
out=$(realpath -- "$out")
root=$(cd "$(dirname "$0")/../.." && pwd)
ttconv="$root/processing/bin/ttconv-pinned.sh"

[[ -f "$input" ]] || { echo "timed text not found: $input" >&2; exit 66; }
[[ -f "$profile" ]] || { echo "profile not found: $profile" >&2; exit 66; }
command -v ffprobe >/dev/null
command -v jq >/dev/null
command -v sha256sum >/dev/null
command -v python3 >/dev/null

# Retain the single admitted profile byte stream. Native validation,
# execution policy and receipt digest all consume this attempt-owned copy.
profile_source=$profile
profile="$out/profile.json"
python3 -I "$root/src/ordivon_studio/strict_json.py" "$profile_source" "$profile"


# jq's alternative operator treats false as absent. Validate explicit
# optional boolean controls before invoking native conversion.
jq -e '
  type == "object" and .schemaVersion == 1 and
  .kind == "ordivon.media.v2.timed-text-profile" and
  (.format | . == "ttml" or . == "vtt") and
  (.expectedCueCount | type == "number" and isfinite and floor == . and . >= 0) and
  (.maxEndSeconds | type == "number" and isfinite and . >= 0) and
  (if has("expectedLanguage") then (.expectedLanguage | . == null or (type == "string" and length > 0)) else true end) and
  (if has("requirePositiveDurations") then (.requirePositiveDurations | type) == "boolean" else true end) and
  (if has("requireNonemptyPackets") then (.requireNonemptyPackets | type) == "boolean" else true end)
' "$profile" >/dev/null || { echo "invalid timed-text profile" >&2; exit 65; }

# shellcheck source=processing/bin/native-input.sh
source "$root/processing/bin/native-input.sh"
input_custody_start "$input" "$out"

mkdir -p "$out/raw"
normalized="$out/raw/normalized.vtt"
packets="$out/raw/ffprobe-subtitle-packets.json"
assertions="$out/assertions.json"
evidence="$out/evidence.json"
format=$(jq -r '.format' "$profile")
actual_language=""

case "$format" in
  ttml)
    command -v xmllint >/dev/null
    xmllint --noout "$input_snapshot"
    actual_language=$(xmllint --xpath 'string(/*/@xml:lang)' "$input_snapshot")
    "$ttconv" convert -i "$input_snapshot" -o "$normalized" --otype VTT \
      --config '{"general":{"progress_bar":false,"log_level":"WARN"},"vtt_writer":{"cue_id":true}}'
    ;;
  vtt)
    cp "$input_snapshot" "$normalized"
    ;;
  *)
    echo "unsupported timed-text profile format: $format" >&2
    exit 65
    ;;
esac

ffprobe -v error -show_packets -select_streams s -of json "$normalized" > "$packets"

input_custody_finish
input_sha=$input_digest
input_bytes=$input_size
profile_sha="sha256:$(sha256sum "$profile" | awk '{print $1}')"
normalized_sha="sha256:$(sha256sum "$normalized" | awk '{print $1}')"
packets_sha="sha256:$(sha256sum "$packets" | awk '{print $1}')"
ffprobe_version=$(ffprobe -version | head -n1)

jq -n \
  --slurpfile p "$profile" \
  --slurpfile f "$packets" \
  --arg actualLanguage "$actual_language" '
  $p[0] as $p |
  ($f[0].packets // []) as $packets |
  ($p | if has("requirePositiveDurations") then .requirePositiveDurations else true end) as $requirePositive |
  ($p | if has("requireNonemptyPackets") then .requireNonemptyPackets else true end) as $requireNonempty |
  ([$packets[]? | (.duration_time | tonumber)] | all(. > 0)) as $positive |
  ([$packets[]? | (.size | tonumber)] | all(. > 0)) as $nonempty |
  ($packets | length) as $count |
  ([$packets[]? | (.pts_time | tonumber)] | if length == 0 then 0 else min end) as $minStart |
  ([$packets[]? | ((.pts_time | tonumber) + (.duration_time | tonumber))] | if length == 0 then 0 else max end) as $maxEnd |
  [
    {name:"timedText.cueCount", expected:$p.expectedCueCount, actual:$count, ok:($count == $p.expectedCueCount)},
    {name:"timedText.nonnegativeStart", expected:">=0", actual:$minStart, ok:($minStart >= 0)},
    {name:"timedText.positiveDurations", required:$requirePositive, expected:(if $requirePositive then true else null end), actual:$positive, ok:(($requirePositive | not) or $positive)},
    {name:"timedText.nonemptyPackets", required:$requireNonempty, expected:(if $requireNonempty then true else null end), actual:$nonempty, ok:(($requireNonempty | not) or $nonempty)},
    {name:"timedText.maxEndSeconds", expected:{max:$p.maxEndSeconds}, actual:$maxEnd, ok:($maxEnd <= $p.maxEndSeconds)},
    {name:"timedText.language", expected:($p.expectedLanguage // null), actual:(if $actualLanguage == "" then null else $actualLanguage end), ok:(($p.expectedLanguage // null) == null or $actualLanguage == $p.expectedLanguage)}
  ] as $checks |
  {
    schemaVersion:1,
    kind:"ordivon.media.v2.timed-text-assertions",
    profileId:$p.id,
    normalizedFacts:{cueCount:$count,minStartSeconds:$minStart,maxEndSeconds:$maxEnd,language:(if $actualLanguage == "" then null else $actualLanguage end)},
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
  --arg evidenceDirectory "$out" \
  --arg profile "$profile_source" \
  --arg profileDigest "$profile_sha" \
  --arg normalizedDigest "$normalized_sha" \
  --arg packetEvidenceDigest "$packets_sha" \
  --arg assertionsDigest "$assertions_sha" \
  --arg ffprobeVersion "$ffprobe_version" \
  --slurpfile a "$assertions" \
  --argjson ok "$ok" '
  {
    schemaVersion:1,
    evidenceDirectory:$evidenceDirectory,
    kind:"ordivon.media.v2.external-timed-text-evidence",
    truthRole:"mechanical-timed-text-delivery-evidence-not-semantic-caption-completeness-or-imsc-conformance",
    input:{path:$input,digest:$inputDigest,sizeBytes:$inputBytes,observationMode:"attempt-private-copy-retired"},
    profile:{path:$profile,digest:$profileDigest,snapshotPath:"profile.json"},
    tools:{ttconv:{version:"1.2.3",role:"format-conversion"},ffprobe:{version:$ffprobeVersion,role:"subtitle-packet-timing"},xmllint:{role:"xml-well-formedness-and-language-when-ttml"}},
    evidence:{normalizedVttDigest:$normalizedDigest,packetEvidenceDigest:$packetEvidenceDigest,assertionsDigest:$assertionsDigest},
    normalizedFacts:$a[0].normalizedFacts,
    mechanicalDelivery:{ok:$ok},
    semanticCaptionCompleteness:"not-evaluated",
    audioDescriptionNeed:"not-evaluated",
    imscConformance:"not-claimed",
    publicationStanding:"not-evaluated"
  }
' > "$evidence.tmp"
mv -T -- "$evidence.tmp" "$evidence"

if [[ "$ok" != "true" ]]; then
  jq -r '.checks[] | select(.ok == false) | "FAIL \(.name): expected=\(.expected|tojson) actual=\(.actual|tojson)"' "$assertions" >&2
  exit 2
fi

cat "$evidence"
