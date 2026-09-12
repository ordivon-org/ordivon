#!/usr/bin/env bash
set -euo pipefail
TMP=$(mktemp -d /tmp/network-v2-family-fallback.XXXXXX)
SUFFIX=$$
U4=network-v2-family-http4-$SUFFIX.service
U6=network-v2-family-http6-$SUFFIX.service
S4=network-v2-family-pref4-$SUFFIX.service
S6=network-v2-family-pref6-$SUFFIX.service
cleanup(){
  systemctl stop "$S4" "$S6" "$U4" "$U6" >/dev/null 2>&1 || true
  systemctl reset-failed "$S4" "$S6" "$U4" "$U6" >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT
mkdir -p "$TMP/www"
printf 'fallback-ok\n' >"$TMP/www/index.html"

# Prefer IPv6, but only IPv4 is healthy.
systemd-run --quiet --unit="$U4" --property=Type=simple --property=Restart=no \
  /usr/bin/python3 -m http.server 38080 --bind 127.0.0.1 --directory "$TMP/www"
for _ in $(seq 1 40); do curl -fsS http://127.0.0.1:38080/ >/dev/null 2>&1 && break; sleep 0.1; done
curl -fsS http://127.0.0.1:38080/ >/dev/null
! ss -ltn6 | grep -q ':38080 '
cat >"$TMP/pref6.json" <<'JSON'
{"log":{"level":"info","timestamp":true},"dns":{"servers":[{"type":"hosts","tag":"hosts","predefined":{"fallback.test":["127.0.0.1","::1"]}}],"final":"hosts","strategy":"prefer_ipv6"},"inbounds":[{"type":"mixed","tag":"mixed","listen":"127.0.0.1","listen_port":28084}],"outbounds":[{"type":"direct","tag":"direct"}],"route":{"rules":[{"action":"resolve","server":"hosts","strategy":"prefer_ipv6"}],"final":"direct"}}
JSON
sing-box check -c "$TMP/pref6.json"
systemd-run --quiet --unit="$S6" --property=Type=simple --property=Restart=no /usr/bin/sing-box run -c "$TMP/pref6.json"
for _ in $(seq 1 50); do ss -ltn | grep -q '127.0.0.1:28084' && break; sleep 0.1; done
m6=$(curl --fail --silent --show-error --proxy http://127.0.0.1:28084 --connect-timeout 3 --max-time 10 \
  -o "$TMP/out6" -w 'rc=%{exitcode} http=%{http_code} time=%{time_total}' http://fallback.test:38080/)
grep -qx fallback-ok "$TMP/out6"
printf 'prefer_ipv6_ipv6_failed_ipv4_healthy %s\n' "$m6"
systemctl stop "$S6" "$U4"

# Prefer IPv4, but only IPv6 is healthy.
systemd-run --quiet --unit="$U6" --property=Type=simple --property=Restart=no \
  /usr/bin/python3 -m http.server 38081 --bind ::1 --directory "$TMP/www"
for _ in $(seq 1 40); do curl -g -fsS 'http://[::1]:38081/' >/dev/null 2>&1 && break; sleep 0.1; done
curl -g -fsS 'http://[::1]:38081/' >/dev/null
! ss -ltn4 | grep -q ':38081 '
cat >"$TMP/pref4.json" <<'JSON'
{"log":{"level":"info","timestamp":true},"dns":{"servers":[{"type":"hosts","tag":"hosts","predefined":{"fallback.test":["127.0.0.1","::1"]}}],"final":"hosts","strategy":"prefer_ipv4"},"inbounds":[{"type":"mixed","tag":"mixed","listen":"127.0.0.1","listen_port":28085}],"outbounds":[{"type":"direct","tag":"direct"}],"route":{"rules":[{"action":"resolve","server":"hosts","strategy":"prefer_ipv4"}],"final":"direct"}}
JSON
sing-box check -c "$TMP/pref4.json"
systemd-run --quiet --unit="$S4" --property=Type=simple --property=Restart=no /usr/bin/sing-box run -c "$TMP/pref4.json"
for _ in $(seq 1 50); do ss -ltn | grep -q '127.0.0.1:28085' && break; sleep 0.1; done
m4=$(curl --fail --silent --show-error --proxy http://127.0.0.1:28085 --connect-timeout 3 --max-time 10 \
  -o "$TMP/out4" -w 'rc=%{exitcode} http=%{http_code} time=%{time_total}' http://fallback.test:38081/)
grep -qx fallback-ok "$TMP/out4"
printf 'prefer_ipv4_ipv4_failed_ipv6_healthy %s\n' "$m4"

echo family-fallback-smoke=PASS
