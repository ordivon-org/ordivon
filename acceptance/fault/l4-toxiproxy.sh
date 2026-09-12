#!/usr/bin/env bash
set -euo pipefail
API=http://127.0.0.1:28474
TOX_UNIT=network-v2-r0-toxiproxy-smoke.service
HTTP_UNIT=network-v2-r0-http-target-smoke.service
cleanup(){ systemctl stop "$TOX_UNIT" 2>/dev/null || true; systemctl stop "$HTTP_UNIT" 2>/dev/null || true; systemctl reset-failed "$TOX_UNIT" "$HTTP_UNIT" 2>/dev/null || true; }
trap cleanup EXIT
cleanup
systemd-run --quiet --unit="$HTTP_UNIT" --property=Type=simple --property=Restart=no /usr/bin/python3 -m http.server 28888 --bind 127.0.0.1
systemd-run --quiet --unit="$TOX_UNIT" --property=Type=simple --property=Restart=no /usr/local/bin/toxiproxy-server -host 127.0.0.1 -port 28474
for _ in $(seq 1 50); do curl -fsS "$API/version" >/dev/null 2>&1 && break; sleep 0.1; done
TOXIPROXY_URL="$API" /usr/local/bin/toxiproxy-cli create --listen 127.0.0.1:28666 --upstream 127.0.0.1:28888 r0-http >/dev/null
curl -fsS --max-time 3 http://127.0.0.1:28666/ >/dev/null
TOXIPROXY_URL="$API" /usr/local/bin/toxiproxy-cli toxic add -t timeout -n cutoff -a timeout=100 r0-http >/dev/null
if curl -fsS --max-time 1 http://127.0.0.1:28666/ >/dev/null 2>&1; then echo 'timeout toxic failed to disrupt request' >&2; exit 1; fi
echo toxiproxy-smoke=PASS
