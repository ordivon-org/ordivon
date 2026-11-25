#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUNDLE="${1:?Sigstore bundle path required}"
CARRIER="${2:?carrier blob path required}"
PUBLIC_KEY="${3:?cosign public key path required}"
TRUST_POLICY="${4:?trust policy path required}"
SUBJECT_COMMIT="${5:?expected subject Git commit required}"
VERIFIER_ID="${6:?expected verifier id required}"
VERIFIED_LEVEL="${7:?expected verified level required}"
EXPECTED_STATEMENT="${8:-}"

# Capture each shared input once. Both verification layers must consume the
# same bundle and public-key bytes, not reopen caller-controlled paths.
# This is a private local snapshot, not isolation from a same-UID adversary.
umask 077
SNAPSHOT="$(mktemp -d)"
trap 'rm -rf -- "$SNAPSHOT"' EXIT
cp -- "$BUNDLE" "$SNAPSHOT/bundle.json"
cp -- "$PUBLIC_KEY" "$SNAPSHOT/key.pub"
cp -- "$TRUST_POLICY" "$SNAPSHOT/trust.json"
BUNDLE="$SNAPSHOT/bundle.json"
PUBLIC_KEY="$SNAPSHOT/key.pub"
TRUST_POLICY="$SNAPSHOT/trust.json"
if [[ -n "$EXPECTED_STATEMENT" ]]; then
  cp -- "$EXPECTED_STATEMENT" "$SNAPSHOT/expected.json"
  EXPECTED_STATEMENT="$SNAPSHOT/expected.json"
fi

cosign verify-blob-attestation \
  --bundle "$BUNDLE" \
  --key "$PUBLIC_KEY" \
  --type https://slsa.dev/verification_summary/v1 \
  --check-claims=false \
  "$CARRIER"

ARGS=(
  --bundle "$BUNDLE"
  --public-key "$PUBLIC_KEY"
  --trust-policy "$TRUST_POLICY"
  --subject-git-commit "$SUBJECT_COMMIT"
  --verifier-id "$VERIFIER_ID"
  --verified-level "$VERIFIED_LEVEL"
)
if [[ -n "$EXPECTED_STATEMENT" ]]; then
  ARGS+=(--expected-statement "$EXPECTED_STATEMENT")
fi
PYTHONPATH="$ROOT/src" python "$ROOT/scripts/verify_vsa_bundle.py" "${ARGS[@]}"
