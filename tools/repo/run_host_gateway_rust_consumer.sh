#!/usr/bin/env bash
# Repository-level E2E seam: Host owns PG fixtures, Gateway owns its MCP consumer.
# Neither domain imports or references the other's source as a runtime dependency.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
rust_binary="${HOST_RUST_BINARY:-}"
if [[ -z "$rust_binary" ]]; then
  rust_binary="$(bash "$root/services/host/rust/tools/rust_binary_path.sh")"
fi
test -x "$rust_binary"

# Reuse Security Owner's pinned native OPA provider for *real*, isolated
# AuthZEN/OPA principal→Actor policy decisions in the Gateway→Rust test.
# Never read installed Security credentials, grants or production policy data.
mise -C "$root/platform/security" install opa >/dev/null
export ORDIVON_HOST_RUST_TEST_OPA
ORDIVON_HOST_RUST_TEST_OPA="$(mise -C "$root/platform/security" which opa)"
test -x "$ORDIVON_HOST_RUST_TEST_OPA"

# Cold GitHub runners have no pinned wheel cache (including protobuf).
# Provision the Gateway's locked env first; the actual consumer stays offline.
# Never solve missing wheels by dropping a test or altering the locked versions.
(cd "$root/services/gateway" && \
  uv sync --locked --quiet && \
  uv run --offline python \
    "$root/services/gateway/tests/native_rust_host_consumer_smoke.py" \
    "$rust_binary")
