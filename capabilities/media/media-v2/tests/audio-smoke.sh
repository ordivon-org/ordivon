#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
work="$root/.tmp/media-v2-audio-smoke"
rm -rf "$work"
mkdir -p "$work"
trap 'rm -rf "$work"' EXIT

profile="$root/media-v2/profiles/audio-program-48k-mono-lufs23.json"
probe="$root/media-v2/bin/probe-audio.sh"

# FFmpeg's sine source is about -21 LUFS here. Reduce by 2 dB for a bounded -23 LUFS fixture.
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i 'sine=frequency=1000:sample_rate=48000:duration=3' \
  -af 'volume=-2dB' -c:a pcm_s24le "$work/good.wav"

bash "$probe" "$work/good.wav" "$profile" "$work/good-evidence" >/dev/null
jq -e '.technicalQc.ok == true' "$work/good-evidence/evidence.json" >/dev/null
jq -e '.measurement.integratedLoudnessLufs >= -24 and .measurement.integratedLoudnessLufs <= -22' "$work/good-evidence/evidence.json" >/dev/null

# Loudness negative: same technical stream shape, deliberately too loud for the profile.
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i 'sine=frequency=1000:sample_rate=48000:duration=3' \
  -af 'volume=+6dB' -c:a pcm_s24le "$work/bad-loud.wav"

if bash "$probe" "$work/bad-loud.wav" "$profile" "$work/bad-loud-evidence" >/dev/null 2>"$work/bad-loud.stderr"; then
  echo "over-loud negative fixture unexpectedly passed" >&2
  exit 1
fi
grep -q 'FAIL loudness.integratedLufs' "$work/bad-loud.stderr"

# True-peak negative: keep the same known-good artifact but tighten only peak authority.
jq '.id="audio-program-48k-mono-lufs23-peak-negative" | .loudness.maxTruePeakDbtp=-25.0' "$profile" > "$work/peak-negative-profile.json"
if bash "$probe" "$work/good.wav" "$work/peak-negative-profile.json" "$work/bad-peak-evidence" >/dev/null 2>"$work/bad-peak.stderr"; then
  echo "true-peak negative fixture unexpectedly passed" >&2
  exit 1
fi
grep -q 'FAIL loudness.truePeakDbtp' "$work/bad-peak.stderr"

# Codec negative: exact same bytes under a deliberately false codec expectation.
jq '.id="audio-program-48k-mono-lufs23-codec-negative" | .audio.codec="aac"' "$profile" > "$work/codec-negative-profile.json"
if bash "$probe" "$work/good.wav" "$work/codec-negative-profile.json" "$work/bad-codec-evidence" >/dev/null 2>"$work/bad-codec.stderr"; then
  echo "codec negative fixture unexpectedly passed" >&2
  exit 1
fi
grep -q 'FAIL audio.codec' "$work/bad-codec.stderr"

echo 'media-v2 audio smoke: PASS (target accepted; loudness, peak, and codec negatives rejected)'
