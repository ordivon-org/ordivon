#!/usr/bin/env bash
set -euo pipefail

root=$(git rev-parse --show-toplevel)
work="$root/.tmp/media-v2-smoke"
rm -rf "$work"
mkdir -p "$work"
trap 'rm -rf "$work"' EXIT

profile="$root/media-v2/profiles/av-sdr-web-1080p30-noaudio.json"
probe="$root/media-v2/bin/probe-av.sh"

ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i 'testsrc2=size=1920x1080:rate=30:duration=1' \
  -vf 'setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709' \
  -c:v libx264 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -an "$work/good.mp4"

bash "$probe" "$work/good.mp4" "$profile" "$work/good-evidence" >/dev/null
jq -e '.technicalQc.ok == true' "$work/good-evidence/evidence.json" >/dev/null

ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i 'testsrc2=size=1280x720:rate=30:duration=1' \
  -vf 'setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709' \
  -c:v libx264 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -an "$work/bad.mp4"

if bash "$probe" "$work/bad.mp4" "$profile" "$work/bad-evidence" >/dev/null 2>"$work/bad.stderr"; then
  echo "negative fixture unexpectedly passed" >&2
  exit 1
fi
jq -e '.technicalQc.ok == false' "$work/bad-evidence/evidence.json" >/dev/null
grep -q 'FAIL video.width' "$work/bad.stderr"
grep -q 'FAIL video.height' "$work/bad.stderr"

echo 'media-v2 smoke: PASS (positive accepted, wrong-resolution negative rejected)'
