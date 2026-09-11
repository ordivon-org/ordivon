#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: probe-timed-text.sh <timed-text> <profile.json> <evidence-dir>" >&2
  exit 64
fi

input=$(realpath "$1")
profile=$(realpath "$2")
out=$3
root=$(git rev-parse --show-toplevel)
ttconv="$root/media-v2/bin/ttconv-pinned.sh"

[[ -f "$input" ]] || { echo "timed text not found: $input" >&2; exit 66; }
[[ -f "$profile" ]] || { echo "profile not found: $profile" >&2; exit 66; }
command -v ffprobe >/dev/null
command -v jq >/dev/null
command -v sha256sum >/dev/null

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
    xmllint --noout "$input"
    actual_language=$(xmllint --xpath 'string(/*/@xml:lang)' "$input")
    "$ttconv" convert -i "$input" -o "$normalized" --otype VTT \
      --config '{"general":{"progress_bar":false,"log_level":"WARN"},"vtt_writer":{"cue_id":true}}'
    ;;
  vtt)
    cp "$input" "$normalized"
    ;;
  *)
    echo "unsupported timed-text profile format: $format" >&2
    exit 65
    ;;
esac

ffprobe -v error -show_packets -select_streams s -of json "$normalized" > "$packets"

input_sha="sha256:$(sha256sum "$input" | awk '{print $1}')"
input_bytes=$(stat -c '%s' "$input")
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
  ($packets | length) as $count |
  ([$packets[]? | (.pts_time | tonumber)] | if length == 0 then 0 else min end) as $minStart |
  ([$packets[]? | ((.pts_time | tonumber) + (.duration_time | tonumber))] | if length == 0 then 0 else max end) as $maxEnd |
  [
    {name:"timedText.cueCount", expected:$p.expectedCueCount, actual:$count, ok:($count == $p.expectedCueCount)},
    {name:"timedText.nonnegativeStart", expected:">=0", actual:$minStart, ok:($minStart >= 0)},
    {name:"timedText.positiveDurations", expected:true, actual:([$packets[]? | (.duration_time | tonumber)] | all(. > 0)), ok:((($p.requirePositiveDurations // true) | not) or ([$packets[]? | (.duration_time | tonumber)] | all(. > 0)))},
    {name:"timedText.nonemptyPackets", expected:true, actual:([$packets[]? | (.size | tonumber)] | all(. > 0)), ok:((($p.requireNonemptyPackets // true) | not) or ([$packets[]? | (.size | tonumber)] | all(. > 0)))},
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
  --arg profile "$profile" \
  --arg profileDigest "$profile_sha" \
  --arg normalizedDigest "$normalized_sha" \
  --arg packetEvidenceDigest "$packets_sha" \
  --arg assertionsDigest "$assertions_sha" \
  --arg ffprobeVersion "$ffprobe_version" \
  --slurpfile a "$assertions" \
  --argjson ok "$ok" '
  {
    schemaVersion:1,
    kind:"ordivon.media.v2.external-timed-text-evidence",
    truthRole:"mechanical-timed-text-delivery-evidence-not-semantic-caption-completeness-or-imsc-conformance",
    input:{path:$input,digest:$inputDigest,sizeBytes:$inputBytes},
    profile:{path:$profile,digest:$profileDigest},
    tools:{ttconv:{version:"1.2.3",role:"format-conversion"},ffprobe:{version:$ffprobeVersion,role:"subtitle-packet-timing"},xmllint:{role:"xml-well-formedness-and-language-when-ttml"}},
    evidence:{normalizedVttDigest:$normalizedDigest,packetEvidenceDigest:$packetEvidenceDigest,assertionsDigest:$assertionsDigest},
    normalizedFacts:$a[0].normalizedFacts,
    mechanicalDelivery:{ok:$ok},
    semanticCaptionCompleteness:"not-evaluated",
    audioDescriptionNeed:"not-evaluated",
    imscConformance:"not-claimed",
    publicationStanding:"not-evaluated"
  }
' > "$evidence"

if [[ "$ok" != "true" ]]; then
  jq -r '.checks[] | select(.ok == false) | "FAIL \(.name): expected=\(.expected|tojson) actual=\(.actual|tojson)"' "$assertions" >&2
  exit 2
fi

cat "$evidence"
