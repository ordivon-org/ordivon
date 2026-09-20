#!/usr/bin/env bash
set -euo pipefail
url="${POSTIZ_API_BASE:-https://api.postiz.com/public/v1}/integrations"
body="$(mktemp)"
trap 'rm -f "$body"' EXIT
code="$(curl -sS --connect-timeout 10 --max-time 20 -o "$body" -w '%{http_code}' "$url")"
case "$code" in
  401|403)
    printf 'PASS postiz live API surface requires authorization http=%s\n' "$code"
    ;;
  200)
    echo 'FAIL unauthenticated Postiz integrations unexpectedly returned 200' >&2
    exit 1
    ;;
  *)
    printf 'FAIL unexpected Postiz API status=%s\n' "$code" >&2
    head -c 500 "$body" >&2 || true
    exit 1
    ;;
esac
