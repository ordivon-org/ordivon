#!/usr/bin/env bash
set -euo pipefail
out="${1:-web-v3/assets/audio}"
mkdir -p "$out"
# Short, low-fatigue synthetic cues. No external samples.
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "aevalsrc=0.050*sin(2*PI*660*t)+0.025*sin(2*PI*990*t):s=48000:d=0.22" -af "afade=t=in:st=0:d=0.015,afade=t=out:st=0.14:d=0.08" -c:a libvorbis -q:a 4 "$out/plan-ready.ogg"
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "aevalsrc=0.060*sin(2*PI*185*t)+0.030*sin(2*PI*277.5*t):s=48000:d=0.20" -af "afade=t=in:st=0:d=0.01,afade=t=out:st=0.11:d=0.09" -c:a libvorbis -q:a 4 "$out/commit.ogg"
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "aevalsrc=0.040*sin(2*PI*420*t)+0.025*sin(2*PI*630*t)+0.015*sin(2*PI*840*t):s=48000:d=0.30" -af "afade=t=in:st=0:d=0.02,afade=t=out:st=0.18:d=0.12" -c:a libvorbis -q:a 4 "$out/aftermath.ogg"
