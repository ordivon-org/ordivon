#!/usr/bin/env bash
set -euo pipefail
root="$(mktemp -d)"
trap 'rm -rf "$root"' EXIT
mkdir -p "$root/source" "$root/destination"
printf 'distribution-v2-rclone-smoke\n' > "$root/source/artifact.txt"
rclone copy "$root/source" "$root/destination"
rclone check "$root/source" "$root/destination" --one-way
src="$(sha256sum "$root/source/artifact.txt" | awk '{print $1}')"
dst="$(sha256sum "$root/destination/artifact.txt" | awk '{print $1}')"
[[ "$src" == "$dst" ]]
printf 'PASS rclone-copy-check sha256:%s\n' "$src"
