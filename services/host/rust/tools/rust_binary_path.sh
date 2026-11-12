#!/usr/bin/env bash
# Resolve the actual Cargo binary location instead of assuming in-tree target/.
# Runtime may supply CARGO_TARGET_DIR as a /proc/self/fd/N path; realpath
# canonicalizes it before subprocess launch, which closes inherited FDs.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
manifest="$root/services/host/rust/Cargo.toml"
target="$(
  cargo metadata --offline --locked --no-deps --format-version 1 --manifest-path "$manifest" |
    python3 -c 'import json,sys; print(json.load(sys.stdin)["target_directory"])'
)"
realpath -e "$target/debug/ordivon-host-rust"
