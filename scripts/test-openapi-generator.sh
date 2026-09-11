#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${OPENAPI_GENERATOR_IMAGE:-docker.io/openapitools/openapi-generator-cli:v7.24.0}"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT
podman run --rm --network=none --user 0 \
  -v "$ROOT:/work:ro" -v "$out:/out" \
  "$IMAGE" generate -g python -i /work/tests/fixtures/provider-openapi.yaml -o /out/client
test -f "$out/client/README.md"
test -d "$out/client/openapi_client"
grep -R "def get_object" "$out/client/openapi_client/api" >/dev/null
printf 'PASS openapi-generator provider client smoke\n'
