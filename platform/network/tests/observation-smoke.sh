#!/usr/bin/env bash
set -euo pipefail
BB_UNIT=network-v2-r0-blackbox-smoke.service
PROM_UNIT=network-v2-r0-prometheus-smoke.service
DATA=$(mktemp -d /tmp/network-v2-prometheus.XXXXXX)
cleanup(){ systemctl stop "$PROM_UNIT" 2>/dev/null || true; systemctl stop "$BB_UNIT" 2>/dev/null || true; systemctl reset-failed "$PROM_UNIT" "$BB_UNIT" 2>/dev/null || true; rm -rf "$DATA"; }
trap cleanup EXIT
cleanup
bb=$(realpath config/blackbox/blackbox.yml)
prom=$(realpath config/prometheus/prometheus.yml)
systemd-run --quiet --unit="$BB_UNIT" --property=Type=simple --property=Restart=no /usr/bin/prometheus-blackbox-exporter --config.file="$bb" --web.listen-address=127.0.0.1:29115
for _ in $(seq 1 50); do curl -fsS http://127.0.0.1:29115/-/healthy >/dev/null 2>&1 && break; sleep 0.1; done
curl -fsS 'http://127.0.0.1:29115/probe?module=http_2xx&target=https%3A%2F%2Fexample.com%2F' | grep -q '^probe_success 1$'
systemd-run --quiet --unit="$PROM_UNIT" --property=Type=simple --property=Restart=no /usr/bin/prometheus --config.file="$prom" --storage.tsdb.path="$DATA" --storage.tsdb.retention.time=1h --web.listen-address=127.0.0.1:29090
for _ in $(seq 1 60); do curl -fsS http://127.0.0.1:29090/-/ready >/dev/null 2>&1 && break; sleep 0.1; done
ok=0
for _ in $(seq 1 8); do
  if curl -fsS -G --data-urlencode 'query=probe_success' http://127.0.0.1:29090/api/v1/query | jq -e '.data.result[]? | select(.value[1] == "1")' >/dev/null; then ok=1; break; fi
  sleep 2
done
test "$ok" = 1
echo observation-smoke=PASS
