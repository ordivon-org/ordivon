#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: probe-audio.sh <artifact> <profile.json> <evidence-dir>" >&2
  exit 64
fi

artifact=$(realpath "$1")
profile=$(realpath "$2")
out=$3

[[ -f "$artifact" ]] || { echo "artifact not found: $artifact" >&2; exit 66; }
[[ -f "$profile" ]] || { echo "profile not found: $profile" >&2; exit 66; }
command -v ffprobe >/dev/null
command -v ffmpeg >/dev/null
command -v jq >/dev/null
command -v sha256sum >/dev/null

mkdir -p "$out/raw"
probe="$out/raw/ffprobe.json"
loud_stderr="$out/raw/ffmpeg-loudnorm.stderr"
loud_json="$out/raw/ffmpeg-loudnorm.json"
assertions="$out/assertions.json"
evidence="$out/evidence.json"

ffprobe -v error -show_format -show_streams -of json "$artifact" > "$probe"

stream_index=$(jq -r '.audio.streamIndex // 0' "$profile")
ffmpeg -hide_banner -nostats -i "$artifact" -map "0:a:${stream_index}" \
  -af 'loudnorm=I=-23:LRA=7:TP=-1:print_format=json' -f null - 2>"$loud_stderr"

awk '
  /^[[:space:]]*\{[[:space:]]*$/ {capture=1}
  capture {print}
  capture && /^[[:space:]]*\}[[:space:]]*$/ {exit}
' "$loud_stderr" > "$loud_json"

jq -e 'has("input_i") and has("input_tp") and has("input_lra") and has("input_thresh")' "$loud_json" >/dev/null || {
  echo "FFmpeg loudnorm did not produce the expected measurement JSON" >&2
  exit 65
}

artifact_sha="sha256:$(sha256sum "$artifact" | awk '{print $1}')"
artifact_bytes=$(stat -c '%s' "$artifact")
profile_sha="sha256:$(sha256sum "$profile" | awk '{print $1}')"
probe_sha="sha256:$(sha256sum "$probe" | awk '{print $1}')"
loud_stderr_sha="sha256:$(sha256sum "$loud_stderr" | awk '{print $1}')"
loud_json_sha="sha256:$(sha256sum "$loud_json" | awk '{print $1}')"
ffprobe_version=$(ffprobe -version | head -n1)
ffmpeg_version=$(ffmpeg -version | head -n1)

jq -n \
  --slurpfile p "$profile" \
  --slurpfile f "$probe" \
  --slurpfile l "$loud_json" '
  $p[0] as $p |
  $f[0] as $f |
  $l[0] as $l |
  [$f.streams[]? | select(.codec_type == "audio")] as $audios |
  ($audios[$p.audio.streamIndex // 0] // {}) as $a |
  ($l.input_i | tonumber) as $integrated |
  ($l.input_tp | tonumber) as $truePeak |
  ($l.input_lra | tonumber) as $lra |
  ($l.input_thresh | tonumber) as $threshold |
  [
    {name:"audio.streamCount", expected:$p.audio.streamCount, actual:($audios|length), ok:(($audios|length) == $p.audio.streamCount)},
    {name:"audio.codec", expected:$p.audio.codec, actual:$a.codec_name, ok:($a.codec_name == $p.audio.codec)},
    {name:"audio.sampleRate", expected:$p.audio.sampleRate, actual:($a.sample_rate|tonumber? // null), ok:(($a.sample_rate|tonumber? // null) == $p.audio.sampleRate)},
    {name:"audio.channels", expected:$p.audio.channels, actual:$a.channels, ok:($a.channels == $p.audio.channels)},
    {name:"audio.channelLayout", expected:$p.audio.channelLayout, actual:$a.channel_layout, ok:($a.channel_layout == $p.audio.channelLayout)},
    {name:"loudness.integratedLufs", expected:{target:$p.loudness.targetLufs,tolerance:$p.loudness.toleranceLu}, actual:$integrated, ok:((($integrated - $p.loudness.targetLufs)|fabs) <= $p.loudness.toleranceLu)},
    {name:"loudness.truePeakDbtp", expected:{max:$p.loudness.maxTruePeakDbtp}, actual:$truePeak, ok:($truePeak <= $p.loudness.maxTruePeakDbtp)}
  ] as $checks |
  {
    schemaVersion:1,
    kind:"ordivon.media.v2.audio-profile-assertions",
    profileId:$p.id,
    measurement:{integratedLoudnessLufs:$integrated,truePeakDbtp:$truePeak,loudnessRangeLu:$lra,thresholdLufs:$threshold},
    ok:($checks|all(.ok)),
    checks:$checks
  }
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
  --arg ffmpegVersion "$ffmpeg_version" \
  --arg rawProbeDigest "$probe_sha" \
  --arg rawLoudnormStderrDigest "$loud_stderr_sha" \
  --arg rawLoudnormJsonDigest "$loud_json_sha" \
  --arg assertionsDigest "$assertions_sha" \
  --slurpfile a "$assertions" \
  --argjson ok "$ok" '
  {
    schemaVersion:1,
    kind:"ordivon.media.v2.external-audio-qc-evidence",
    truthRole:"mechanical-audio-and-loudness-evidence-not-listening-quality-or-publication-approval",
    artifact:{path:$artifact,digest:$artifactDigest,sizeBytes:$artifactBytes},
    profile:{path:$profile,digest:$profileDigest},
    tools:{ffprobe:{version:$ffprobeVersion},ffmpeg:{version:$ffmpegVersion}},
    evidence:{rawProbeDigest:$rawProbeDigest,rawLoudnormStderrDigest:$rawLoudnormStderrDigest,rawLoudnormJsonDigest:$rawLoudnormJsonDigest,assertionsDigest:$assertionsDigest},
    measurement:$a[0].measurement,
    technicalQc:{ok:$ok},
    listeningQuality:"not-evaluated",
    semanticQuality:"not-evaluated",
    publicationStanding:"not-evaluated"
  }
' > "$evidence"

if [[ "$ok" != "true" ]]; then
  jq -r '.checks[] | select(.ok == false) | "FAIL \(.name): expected=\(.expected|tojson) actual=\(.actual|tojson)"' "$assertions" >&2
  exit 2
fi

cat "$evidence"
