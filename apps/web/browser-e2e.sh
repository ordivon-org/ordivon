#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
chromium_executable="$(
  find /root/.cache/ms-playwright \
    -path '*/chrome-linux64/chrome' \
    -type f \
    -perm -0100 \
    2>/dev/null |
    sort -V |
    tail -1
)"

if [[ -z "$chromium_executable" ]]; then
  echo "No installed Playwright Chromium executable found." >&2
  exit 1
fi

ORDIVON_WEB_CHROMIUM_EXECUTABLE="$chromium_executable" \
  mise exec node@26.9.0 -- node "$root/test/browser-e2e.ts"
