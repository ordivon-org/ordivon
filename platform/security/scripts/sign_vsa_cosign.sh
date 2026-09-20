#!/usr/bin/env bash
set -euo pipefail

STATEMENT="${1:?signed in-toto Statement path required}"
CARRIER="${2:?carrier blob path required}"
PRIVATE_KEY="${3:?cosign private key path required}"
BUNDLE="${4:?output Sigstore bundle path required}"

mkdir -p "$(dirname "$BUNDLE")"
cosign attest-blob \
  --statement "$STATEMENT" \
  --key "$PRIVATE_KEY" \
  --bundle "$BUNDLE" \
  --yes \
  "$CARRIER"
