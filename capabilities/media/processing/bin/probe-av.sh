#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: probe-av.sh <artifact> <profile.json> <evidence-dir>" >&2
  exit 64
fi

artifact=$(realpath "$1")
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

[[ -f "$artifact" ]] || { echo "artifact not found: $artifact" >&2; exit 66; }
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


# Validate the declared policy before native observation; invalid is not optional.
jq -es '
  def text: type == "string" and (length > 0);
  def integer: type == "number" and isfinite and (floor == .);
  def positive_integer: integer and . > 0;
  length == 1 and (.[0] |
    type == "object" and .schemaVersion == 1 and
    (.id | text) and
    .kind == "ordivon.media.v2.av-profile" and
    (.video | type == "object") and (.audio | type == "object") and
    (.video | (.streamCount | positive_integer) and
      (.width | positive_integer) and (.height | positive_integer) and
      (.frameRate | type == "string" and test("^[1-9][0-9]*/[1-9][0-9]*$")) and
      ([.codec,.pixelFormat,.colorPrimaries,.colorTransfer,.colorSpace,.colorRange]
       | all(.[]; text))) and
    (.audio.presence | . == "forbidden" or . == "required" or . == "optional"))
' "$profile" >/dev/null || { echo "invalid av profile" >&2; exit 65; }

# shellcheck source=processing/bin/native-input.sh
source "$root/processing/bin/native-input.sh"
input_custody_start "$artifact" "$out"

mkdir -p "$out/raw"
probe="$out/raw/ffprobe.json"
assertions="$out/assertions.json"
evidence="$out/evidence.json"

ffprobe -v error -show_format -show_streams -of json "$input_snapshot" > "$probe"

input_custody_finish
artifact_sha=$input_digest
artifact_bytes=$input_size
profile_sha="sha256:$(sha256sum "$profile" | awk '{print $1}')"
probe_sha="sha256:$(sha256sum "$probe" | awk '{print $1}')"
ffprobe_version=$(ffprobe -version | head -n1)

jq -n \
  --slurpfile p "$profile" \
  --slurpfile f "$probe" '
  $p[0] as $p |
  $f[0] as $f |
  [$f.streams[]? | select(.codec_type == "video")] as $videos |
  [$f.streams[]? | select(.codec_type == "audio")] as $audios |
  ($videos[0] // {}) as $v |
  [
    {name:"video.streamCount", expected:$p.video.streamCount, actual:($videos|length), ok:(($videos|length) == $p.video.streamCount)},
    {name:"video.codec", expected:$p.video.codec, actual:$v.codec_name, ok:($v.codec_name == $p.video.codec)},
    {name:"video.width", expected:$p.video.width, actual:$v.width, ok:($v.width == $p.video.width)},
    {name:"video.height", expected:$p.video.height, actual:$v.height, ok:($v.height == $p.video.height)},
    {name:"video.frameRate", expected:$p.video.frameRate, actual:($v.avg_frame_rate // $v.r_frame_rate), ok:(($v.avg_frame_rate // $v.r_frame_rate) == $p.video.frameRate)},
    {name:"video.pixelFormat", expected:$p.video.pixelFormat, actual:$v.pix_fmt, ok:($v.pix_fmt == $p.video.pixelFormat)},
    {name:"video.colorPrimaries", expected:$p.video.colorPrimaries, actual:$v.color_primaries, ok:($v.color_primaries == $p.video.colorPrimaries)},
    {name:"video.colorTransfer", expected:$p.video.colorTransfer, actual:$v.color_transfer, ok:($v.color_transfer == $p.video.colorTransfer)},
    {name:"video.colorSpace", expected:$p.video.colorSpace, actual:$v.color_space, ok:($v.color_space == $p.video.colorSpace)},
    {name:"video.colorRange", expected:$p.video.colorRange, actual:$v.color_range, ok:($v.color_range == $p.video.colorRange)},
    {name:"audio.presence", expected:$p.audio.presence, actual:(if ($audios|length) == 0 then "absent" else "present" end), ok:(if $p.audio.presence == "forbidden" then (($audios|length) == 0) elif $p.audio.presence == "required" then (($audios|length) > 0) else true end)}
  ] as $checks |
  {schemaVersion:1, kind:"ordivon.media.v2.profile-assertions", profileId:$p.id, ok:($checks|all(.ok)), checks:$checks}
' > "$assertions"

assertions_sha="sha256:$(sha256sum "$assertions" | awk '{print $1}')"
ok=$(jq -r '.ok' "$assertions")

jq -n \
  --arg artifact "$artifact" \
  --arg artifactDigest "$artifact_sha" \
  --argjson artifactBytes "$artifact_bytes" \
  --arg evidenceDirectory "$out" \
  --arg profile "$profile_source" \
  --arg profileDigest "$profile_sha" \
  --arg ffprobeVersion "$ffprobe_version" \
  --arg rawProbeDigest "$probe_sha" \
  --arg assertionsDigest "$assertions_sha" \
  --argjson ok "$ok" '
  {
    schemaVersion:1,
    evidenceDirectory:$evidenceDirectory,
    kind:"ordivon.media.v2.external-qc-evidence",
    truthRole:"mechanical-profile-evidence-not-semantic-or-aesthetic-approval",
    artifact:{path:$artifact,digest:$artifactDigest,sizeBytes:$artifactBytes,observationMode:"attempt-private-copy-retired"},
    profile:{path:$profile,digest:$profileDigest,snapshotPath:"profile.json"},
    tools:{ffprobe:{version:$ffprobeVersion}},
    evidence:{rawProbeDigest:$rawProbeDigest,assertionsDigest:$assertionsDigest},
    technicalQc:{ok:$ok},
    semanticQuality:"not-evaluated",
    aestheticQuality:"not-evaluated",
    publicationStanding:"not-evaluated"
  }
' > "$evidence.tmp"
mv -T -- "$evidence.tmp" "$evidence"

if [[ "$ok" != "true" ]]; then
  jq -r '.checks[] | select(.ok == false) | "FAIL \(.name): expected=\(.expected|tojson) actual=\(.actual|tojson)"' "$assertions" >&2
  exit 2
fi

cat "$evidence"
