#!/usr/bin/env bash
set -euo pipefail
DNS_UNIT=network-v2-r0-dnsproxy-smoke.service
SB_UNIT=network-v2-r0-singbox-smoke.service
cleanup(){ systemctl stop "$SB_UNIT" 2>/dev/null || true; systemctl stop "$DNS_UNIT" 2>/dev/null || true; systemctl reset-failed "$SB_UNIT" "$DNS_UNIT" 2>/dev/null || true; }
trap cleanup EXIT
cleanup
systemd-run --quiet --unit="$DNS_UNIT" --property=Type=simple --property=Restart=no /usr/bin/dnsproxy -l 127.0.0.1 -p 25353 -u 1.1.1.1:53 -u 8.8.8.8:53 --upstream-mode parallel --cache --ipv6-disabled --refuse-any --pending-requests-enabled --timeout 5s
for _ in $(seq 1 40); do systemctl is-active --quiet "$DNS_UNIT" && break; sleep 0.1; done
/usr/bin/dig @127.0.0.1 -p 25353 example.com A +time=2 +tries=1 +short | grep -Eq '^[0-9]+\.'
cfg=$(realpath config/sing-box/direct.json)
systemd-run --quiet --unit="$SB_UNIT" --property=Type=simple --property=Restart=no /usr/bin/sing-box run -c "$cfg"
for _ in $(seq 1 40); do ss -ltn | grep -q '127.0.0.1:28080' && break; sleep 0.1; done
curl --fail --silent --show-error --proxy http://127.0.0.1:28080 --connect-timeout 5 --max-time 15 -o /dev/null https://example.com/
echo direct-chain-smoke=PASS
