#!/usr/bin/env bash
set -euo pipefail

ENGINE=${1:-podman}
IMAGE=ghcr.io/ossf/scorecard:v5.5.0
TARGET=github.com/ossf/scorecard
ROOT=${SCORECARD_ACCEPTANCE_ROOT:-/tmp/ordivon-security-v2-scorecard-r1}
REPO=$(cd "$(dirname "$0")/.." && pwd)

command -v "$ENGINE" >/dev/null
mkdir -p "$ROOT"
"$ENGINE" pull "$IMAGE" >/dev/null
TOKEN=''
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then TOKEN=$(gh auth token); fi
run=("$ENGINE" run --rm --network=host)
if [[ -n "$TOKEN" ]]; then run+=( -e "GITHUB_AUTH_TOKEN=$TOKEN" ); fi
"${run[@]}" "$IMAGE" --repo="$TARGET" --format=json > "$ROOT/scorecard.json"
commit=$(jq -er '.repo.commit' "$ROOT/scorecard.json")
PY=$(uv python find 3.12)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$REPO/src" "$PY" "$REPO/scripts/validate_scorecard_result.py" \
  "$ROOT/scorecard.json" --repo "$TARGET" --commit "$commit" \
  --require-check Branch-Protection \
  --require-check Token-Permissions \
  --require-check Vulnerabilities
