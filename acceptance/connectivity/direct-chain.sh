#!/usr/bin/env bash
set -euo pipefail
DNS_UNIT=network-v2-r0-dnsproxy-smoke.service
SB_UNIT=network-v2-r0-singbox-smoke.service
SB4_UNIT=network-v2-r0-singbox-v4-smoke.service
SB6_UNIT=network-v2-r0-singbox-v6-smoke.service
TMP=$(mktemp -d /tmp/network-v2-direct-smoke.XXXXXX)
cleanup(){
  systemctl stop "$SB6_UNIT" "$SB4_UNIT" "$SB_UNIT" "$DNS_UNIT" 2>/dev/null || true
  systemctl reset-failed "$SB6_UNIT" "$SB4_UNIT" "$SB_UNIT" "$DNS_UNIT" 2>/dev/null || true
  rm -rf "$TMP"
}
trap cleanup EXIT
cleanup
mkdir -p "$TMP"

systemd-run --quiet --unit="$DNS_UNIT" --property=Type=simple --property=Restart=no \
  /usr/bin/dnsproxy -l 127.0.0.1 -p 25354 -u 1.1.1.1:53 -u 8.8.8.8:53 \
  --upstream-mode parallel --cache --refuse-any --pending-requests-enabled --timeout 5s
for _ in $(seq 1 50); do
  if /usr/bin/dig @127.0.0.1 -p 25354 example.com A +time=1 +tries=1 +short 2>/dev/null | grep -Eq '^[0-9]+\.' && \
     /usr/bin/dig @127.0.0.1 -p 25354 example.com AAAA +time=1 +tries=1 +short 2>/dev/null | grep -q ':'; then break; fi
  sleep 0.1
done
/usr/bin/dig @127.0.0.1 -p 25354 example.com A +time=2 +tries=1 +short | grep -Eq '^[0-9]+\.'
/usr/bin/dig @127.0.0.1 -p 25354 example.com AAAA +time=2 +tries=1 +short | grep -q ':'

make_cfg(){
  strategy=$1; port=$2; out=$3
  jq --arg strategy "$strategy" --argjson port "$port" \
    '.dns.servers[0].server_port=25354 | .dns.strategy=$strategy | .inbounds[0].listen_port=$port' \
    config/sing-box/direct.json >"$out"
  /usr/bin/sing-box check -c "$out"
}
make_cfg prefer_ipv6 28081 "$TMP/dual.json"
make_cfg ipv4_only 28082 "$TMP/v4.json"
make_cfg ipv6_only 28083 "$TMP/v6.json"

start_sb(){
  unit=$1; cfg=$2; port=$3
  systemd-run --quiet --unit="$unit" --property=Type=simple --property=Restart=no /usr/bin/sing-box run -c "$cfg"
  for _ in $(seq 1 50); do ss -ltn | grep -q "127.0.0.1:$port" && break; sleep 0.1; done
  ss -ltn | grep -q "127.0.0.1:$port"
}
probe_example(){
  port=$1
  curl --fail --silent --show-error --proxy "http://127.0.0.1:$port" --connect-timeout 5 --max-time 20 \
    https://example.com/ | grep -qi 'Example Domain'
}

start_sb "$SB_UNIT" "$TMP/dual.json" 28081
probe_example 28081

# Large-body path: catches small-request false greens and PMTU/stream stalls.
meta=$(curl --fail --silent --show-error --proxy http://127.0.0.1:28081 --connect-timeout 5 --max-time 45 \
  -o "$TMP/5m.bin" -w 'http=%{http_code} bytes=%{size_download} speed=%{speed_download} time=%{time_total}' \
  'https://speed.cloudflare.com/__down?bytes=5000000')
test "$(stat -c %s "$TMP/5m.bin")" -eq 5000000
printf 'dualstack-longflow %s\n' "$meta"

# Concurrent connection admission: no request may silently fall out of the proxy.
for i in 1 2 3 4; do
  (curl --fail --silent --show-error --proxy http://127.0.0.1:28081 --connect-timeout 5 --max-time 20 \
     -o "$TMP/c.$i" https://example.com/ && grep -qi 'Example Domain' "$TMP/c.$i") &
done
wait

start_sb "$SB4_UNIT" "$TMP/v4.json" 28082
probe_example 28082
start_sb "$SB6_UNIT" "$TMP/v6.json" 28083
probe_example 28083

echo dns-a-aaaa=PASS
echo ipv4-forced=PASS
echo ipv6-forced=PASS
echo dualstack-prefer-ipv6=PASS
echo concurrent-admission=PASS
echo direct-chain-smoke=PASS
