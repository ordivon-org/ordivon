#!/usr/bin/env bash
# One native preview bundle lifecycle; product-specific suppliers retain their
# existing native acceptance and export paths.
set -euo pipefail
product="${1:-}"
case "$product" in
  room-encounter)
    target="$PWD/dist/room-encounter"
    completion=ROOM
    ;;
  beacon-relay)
    target="${GAME_EXPORT_DIR:-$PWD/dist/beacon-relay}"
    completion=BEACON
    ;;
  *)
    echo "usage: package_godot_preview.sh {room-encounter|beacon-relay}" >&2
    exit 2
    ;;
esac
mkdir -p "$target"
head_before="$(git rev-parse HEAD)"
tree_before="$(git rev-parse 'HEAD^{tree}')"
if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
  echo "GAME_FACTORY_DIRTY_SOURCE_NOT_RELEASABLE" >&2
  exit 42
fi
stage="$(mktemp -d "$target/.factory-package.XXXXXXXX")"
trap 'rm -rf -- "$stage"' EXIT
python3 scripts/native_export_identity.py "examples/$product" > "$stage/export-inputs.before"
case "$product" in
  room-encounter)
    mise run factory:validate:godot
    GAME_EXPORT_DIR="$stage/linux-x86_64" mise run export:room-linux
    GAME_EXPORT_DIR="$stage/windows-x86_64" mise run export:room-windows
    test -s "$stage/room-encounter-linux-x86_64.tar.gz"
    test -s "$stage/room-encounter-windows-x86_64.zip"
    mkdir -p "$stage/ready"
    mv -- "$stage/room-encounter-linux-x86_64.tar.gz" "$stage/ready/"
    mv -- "$stage/room-encounter-windows-x86_64.zip" "$stage/ready/"
    ;;
  beacon-relay)
    mise run test:beacon
    mkdir -p "$stage/linux-x86_64" "$stage/windows-x86_64"
    python3 scripts/native_process.py -- godot --headless --path examples/beacon-relay --export-release "Linux x86_64" "$stage/linux-x86_64/beacon-relay.x86_64"
    python3 scripts/native_process.py -- godot --headless --path examples/beacon-relay --export-release "Windows x86_64" "$stage/windows-x86_64/beacon-relay.exe"
    test -s "$stage/linux-x86_64/beacon-relay.x86_64"
    test -s "$stage/windows-x86_64/beacon-relay.exe"
    chmod +x "$stage/linux-x86_64/beacon-relay.x86_64"
    cp examples/beacon-relay/LICENSE "$stage/linux-x86_64/UPSTREAM_MIT_LICENSE.txt"
    cp examples/beacon-relay/fonts/LICENSE.txt "$stage/linux-x86_64/FONT_OFL_LICENSE.txt"
    cp examples/beacon-relay/CREDITS.txt "$stage/linux-x86_64/CREDITS.txt"
    cp "$stage/linux-x86_64/"*.txt "$stage/windows-x86_64/"
    python3 scripts/native_process.py -- "$stage/linux-x86_64/beacon-relay.x86_64" --headless --quit-after 4
    mkdir -p "$stage/ready"
    tar -czf "$stage/ready/beacon-relay-linux-x86_64.tar.gz" -C "$stage/linux-x86_64" beacon-relay.x86_64 UPSTREAM_MIT_LICENSE.txt FONT_OFL_LICENSE.txt CREDITS.txt
    (cd "$stage/windows-x86_64" && python3 -m zipfile -c "$stage/ready/beacon-relay-windows-x86_64.zip" beacon-relay.exe UPSTREAM_MIT_LICENSE.txt FONT_OFL_LICENSE.txt CREDITS.txt)
    test -s "$stage/ready/beacon-relay-linux-x86_64.tar.gz"
    test -s "$stage/ready/beacon-relay-windows-x86_64.zip"
    ;;
esac
{
  echo "BUILD_SCHEMA=1"
  echo "PRODUCT=$product"
  echo "SOURCE_COMMIT=$head_before"
  echo "SOURCE_TREE=$tree_before"
  echo "SOURCE_WORKTREE=clean"
  cat "$stage/export-inputs.before"
  echo "QUALIFICATION=native_headless_preview"
  echo "LINUX_SCOPE=native_headless_smoke"
  echo "WINDOWS_SCOPE=export_only"
  echo "RELEASE_PUBLISHED=false"
} > "$stage/ready/BUILD_SOURCE.txt"
(
  cd "$stage/ready"
  sha256sum "$product-linux-x86_64.tar.gz" "$product-windows-x86_64.zip" BUILD_SOURCE.txt > SHA256SUMS
  sha256sum -c SHA256SUMS
)
if [[ "$(git rev-parse HEAD)" != "$head_before" || "$(git rev-parse 'HEAD^{tree}')" != "$tree_before" || -n "$(git status --porcelain --untracked-files=normal)" ]]; then
  echo "GAME_FACTORY_SOURCE_CHANGED_DURING_BUILD" >&2
  exit 43
fi
python3 scripts/native_export_identity.py "examples/$product" > "$stage/export-inputs.after"
if ! cmp -s "$stage/export-inputs.before" "$stage/export-inputs.after"; then
  echo "GAME_FACTORY_EXPORT_INPUT_CHANGED_DURING_BUILD" >&2
  exit 44
fi
printf 'COMPLETE_SOURCE_COMMIT=%s\n' "$head_before" > "$stage/ready/READY"
bundle="$target/bundle-${head_before:0:12}-${stage##*.}"
test ! -e "$bundle"
mv -T -- "$stage/ready" "$bundle"
echo "GAME_FACTORY_BUNDLE_PATH=$bundle"
echo "GAME_FACTORY_${completion}_PACKAGES_READY_NATIVE_PREVIEW_NOT_STORE_RELEASE"
