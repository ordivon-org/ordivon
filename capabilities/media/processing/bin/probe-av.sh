#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: probe-av.sh <artifact> <profile.json> <evidence-dir>" >&2
  exit 64
fi

artifact=$(realpath "$1")
profile=$(realpath "$2")
out=$3

[[ -f "$artifact" ]] || { echo "artifact not found: $artifact" >&2; exit 66; }
[[ -f "$profile" ]] || { echo "profile not found: $profile" >&2; exit 66; }
command -v ffprobe >/dev/null
command -v jq >/dev/null
command -v sha256sum >/dev/null

mkdir -p "$out/raw"
probe="$out/raw/ffprobe.json"
assertions="$out/assertions.json"
evidence="$out/evidence.json"

ffprobe -v error -show_format -show_streams -of json "$artifact" > "$probe"

artifact_sha="sha256:$(sha256sum "$artifact" | awk '{print $1}')"
artifact_bytes=$(stat -c '%s' "$artifact")
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
  --arg profile "$profile" \
  --arg profileDigest "$profile_sha" \
  --arg ffprobeVersion "$ffprobe_version" \
  --arg rawProbeDigest "$probe_sha" \
  --arg assertionsDigest "$assertions_sha" \
  --argjson ok "$ok" '
  {
    schemaVersion:1,
    kind:"ordivon.media.v2.external-qc-evidence",
    truthRole:"mechanical-profile-evidence-not-semantic-or-aesthetic-approval",
    artifact:{path:$artifact,digest:$artifactDigest,sizeBytes:$artifactBytes},
    profile:{path:$profile,digest:$profileDigest},
    tools:{ffprobe:{version:$ffprobeVersion}},
    evidence:{rawProbeDigest:$rawProbeDigest,assertionsDigest:$assertionsDigest},
    technicalQc:{ok:$ok},
    semanticQuality:"not-evaluated",
    aestheticQuality:"not-evaluated",
    publicationStanding:"not-evaluated"
  }
' > "$evidence"

if [[ "$ok" != "true" ]]; then
  jq -r '.checks[] | select(.ok == false) | "FAIL \(.name): expected=\(.expected|tojson) actual=\(.actual|tojson)"' "$assertions" >&2
  exit 2
fi

cat "$evidence"
