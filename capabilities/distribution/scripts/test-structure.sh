#!/usr/bin/env bash
set -euo pipefail
for f in external-lock.json adapters/*.json evidence/r7-artifact-development-publication-intent.json; do jq -e . "$f" >/dev/null; done
# Retired executable surfaces must not remain wired into CI or forward scripts.
retired_surfaces=(
  'scripts/temporal_integration_dispatch_smoke.py'
  'scripts/test-temporal-integration-boundary.py'
  'scripts/distribution_preflight.py'
  'scripts/test-distribution-preflight.py'
  'contracts/distribution-preflight.schema.json'
  'profiles/steam-linux-directory-r1.json'
)
for retired in "${retired_surfaces[@]}"; do
  matches="$(grep -R -F -n --exclude='test-structure.sh' -- "$retired" .github scripts 2>/dev/null || true)"
  if [ -n "$matches" ]; then
    echo "FAIL retired Distribution surface remains executable: $retired" >&2
    printf '%s\n' "$matches" >&2
    exit 1
  fi
done
printf 'PASS Distribution source profiles and consumed R7 fixture\n'
