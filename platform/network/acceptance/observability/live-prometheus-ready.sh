#!/usr/bin/env bash
set -euo pipefail

PROM=http://127.0.0.1:29090
WITNESS="$(dirname -- "$0")/prometheus-singbox-sample.sh"
for _ in $(seq 1 30); do
  # Prometheus's instant-vector lookback can report stale samples. Require a
  # recent, correctly identified observation, not arbitrary JSON text.
  minimum_ms="$(($(date +%s%3N) - 20000))"
  if curl -fsS --get --data-urlencode 'query=probe_success{job="blackbox-singbox"}' "$PROM/api/v1/query" |
    "$WITNESS" "$minimum_ms"; then
    echo prometheus-singbox-ready=PASS
    exit 0
  fi
  sleep 0.5
done

echo 'Prometheus did not expose probe_success=1 for blackbox-singbox within the readiness budget' >&2
exit 1
