#!/usr/bin/env bash
set -euo pipefail
# Native Game verification boundary: a missing display/probe tool blocks VERIFIED PREVIEW only.
for required in xvfb-run timeout; do
  if ! command -v "$required" >/dev/null 2>&1; then
    echo "ORBIT_WINDOWED_SMOKE_ENV_BLOCKED missing=$required" >&2
    exit 3
  fi
done
cd "$(dirname -- "${BASH_SOURCE[0]}")/.."
destination="${GAME_EXPORT_DIR:-$PWD/dist/orbit-collector}"
mkdir -p "$destination/linux-x86_64"
install -m 0755 examples/orbit-collector/target/debug/ordivon-orbit-collector "$destination/linux-x86_64/ordivon-orbit-collector"
cp LICENSE "$destination/linux-x86_64/PROJECT_APACHE_2_LICENSE.txt"
cat > "$destination/linux-x86_64/HOW_TO_PLAY.txt" <<'ORBIT_README'
Orbit Collector (Bevy 0.20.1, Rust 1.99.1) - Linux x86-64 native preview
Extract this archive and run ./ordivon-orbit-collector on an X11 graphical desktop.
WASD / arrow keys move. Collect five yellow beacons; avoid the red moving
hazard. Three hits lose. R restarts. This is an unsigned prototype preview.
The game has no third-party art/audio; Bevy dependency licenses are determined
by the pinned Cargo.lock and upstream dependency source.
ORBIT_README
source_commit="$(git rev-parse HEAD)"
rust_version="$(rustc --version)"
binary_digest="$(sha256sum examples/orbit-collector/target/debug/ordivon-orbit-collector | cut -d' ' -f1)"
source_dirty=clean
if [[ -n "$(git status --porcelain -- examples/orbit-collector)" ]]; then
  source_dirty=modified
fi
printf '%s\n' "SOURCE_COMMIT=$source_commit" "ENGINE=Bevy 0.20.1" "RUST=$rust_version" "SOURCE_WORKTREE=$source_dirty" "BINARY_SHA256=$binary_digest" > "$destination/linux-x86_64/BUILD_SOURCE.txt"
set +e
LC_ALL=C timeout --verbose 14s xvfb-run -a -s "-screen 0 1280x720x24" "$destination/linux-x86_64/ordivon-orbit-collector" > "$destination/linux-x86_64/launch.log" 2>&1
rc=$?
set -e
if [ "$rc" -ne 124 ] || ! grep -Fq 'timeout: sending signal TERM to command' "$destination/linux-x86_64/launch.log"; then
  echo "ORBIT_WINDOWED_SMOKE_FAILED exit=$rc no_native_timeout_expiry_witness"
  tail -60 "$destination/linux-x86_64/launch.log"
  exit 1
fi
if grep -Eq 'thread .+ panicked|[[:space:]]ERROR[[:space:]]|FATAL|Failed to create (a |the )?surface' "$destination/linux-x86_64/launch.log"; then
  echo "ORBIT_WINDOWED_SMOKE_FAILED_LOG"
  tail -60 "$destination/linux-x86_64/launch.log"
  exit 1
fi
if ! grep -q 'Creating new window ' "$destination/linux-x86_64/launch.log" || ! grep -q 'AdapterInfo' "$destination/linux-x86_64/launch.log"; then
  echo ORBIT_WINDOWED_SMOKE_MISSING_NATIVE_RENDERER_OR_WINDOW
  tail -60 "$destination/linux-x86_64/launch.log"
  exit 1
fi
echo ORBIT_WINDOWED_SMOKE_PASS_14S_NATIVE_APPLICATION_ALIVE
printf '%s\n' "SMOKE_RESULT=PASS_14S_NATIVE_APP_ALIVE" "TIMEOUT_EXPIRY_WITNESS=GNU_TIMEOUT_VERBOSE_TERM" "WINDOW_WITNESS=Creating new window" "ADAPTER_WITNESS=AdapterInfo" "LOG_SHA256=$(sha256sum "$destination/linux-x86_64/launch.log" | cut -d' ' -f1)" > "$destination/linux-x86_64/SMOKE_EVIDENCE.txt"
tar -czf "$destination/orbit-collector-linux-x86_64.tar.gz" -C "$destination/linux-x86_64" ordivon-orbit-collector PROJECT_APACHE_2_LICENSE.txt HOW_TO_PLAY.txt BUILD_SOURCE.txt launch.log SMOKE_EVIDENCE.txt
test -s "$destination/orbit-collector-linux-x86_64.tar.gz"
sha256sum "$destination/orbit-collector-linux-x86_64.tar.gz"
echo ORBIT_FACTORY_LINUX_PREVIEW_READY
