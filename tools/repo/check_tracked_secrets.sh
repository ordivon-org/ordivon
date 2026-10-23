#!/usr/bin/env bash
# Complements the pre-existing Git history scan. Never substitutes for it.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
head="$(git -C "$root" rev-parse HEAD)"
if [[ -n "${GITHUB_SHA:-}" && "$GITHUB_SHA" != "$head" ]]; then
  echo 'Tracked-source scan checkout SHA mismatch' >&2
  exit 2
fi
snapshot="$(mktemp -d "${RUNNER_TEMP:-/tmp}/ordivon-tracked-source.XXXXXXXX")"
trap 'rm -rf -- "$snapshot"' EXIT
git -C "$root" archive --format=tar "$head" | tar -xf - -C "$snapshot"
echo "Scanning all committed files in exact tree $head; historical Git admission remains separate."
(
  cd "$snapshot"
  gitleaks dir --no-banner --redact=100 --timeout 120 .
)
