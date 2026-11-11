#!/usr/bin/env bash
# Repository-level E2E seam: Host owns PG fixtures, Gateway owns its MCP consumer.
# Neither domain imports or references the other's source as a runtime dependency.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
(cd "$root/services/gateway" && \
  uv sync --locked --offline --quiet && \
  uv run --offline python \
    "$root/services/gateway/tests/native_rust_host_consumer_smoke.py" \
    "$root/services/host/rust/target/debug/ordivon-host-rust")
