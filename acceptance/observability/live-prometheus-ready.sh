#!/usr/bin/env bash
set -euo pipefail

PROM=http://127.0.0.1:29090
for _ in $(seq 1 30); do
  if curl -fsS --get --data-urlencode 'query=probe_success{job="blackbox-singbox"}' "$PROM/api/v1/query" | grep -Eq '"value"[^]]*"1"'; then
    echo prometheus-singbox-ready=PASS
    exit 0
  fi
  sleep 0.5
done

echo 'Prometheus did not expose probe_success=1 for blackbox-singbox within the readiness budget' >&2
exit 1
