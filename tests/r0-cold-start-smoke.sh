#!/usr/bin/env bash
set -euo pipefail
TARGET=network-v2-r0.target
UNITS=(network-v2-dnsproxy.service network-v2-singbox.service network-v2-blackbox.service network-v2-prometheus.service)

control_plane_guard(){
  for u in ordivon-runtime.service ordivon-cloudflare-production-a.service ordivon-cloudflare-production-b.service ordivon-cloudflare-canary.service ordivon-cloudflare-direct-route.service; do
    test "$(systemctl is-active "$u")" = active
  done
  ss -ltn | grep -q '127.0.0.1:8897'
  for p in 20243 20244 20245; do
    ha=$(curl -fsS --connect-timeout 2 --max-time 4 "http://127.0.0.1:$p/metrics" | awk '$1=="cloudflared_tunnel_ha_connections"{v=$2}END{print v}')
    test "$ha" = 4
  done
}

wait_active(){
  local u=$1
  for _ in $(seq 1 80); do systemctl is-active --quiet "$u" && return 0; sleep 0.25; done
  systemctl status "$u" --no-pager >&2 || true
  return 1
}

wait_functional(){
  local ok=0
  for _ in $(seq 1 40); do
    if [ -n "$(dig +time=1 +tries=1 @127.0.0.1 -p 25353 example.com A +short 2>/dev/null)" ] && \
       [ -n "$(dig +time=1 +tries=1 @127.0.0.1 -p 25353 example.com AAAA +short 2>/dev/null)" ] && \
       curl --fail --silent --show-error --proxy http://127.0.0.1:28080 --connect-timeout 3 --max-time 8 -o /dev/null https://example.com/ 2>/dev/null && \
       [ "$(curl -fsS --connect-timeout 2 --max-time 5 'http://127.0.0.1:29115/probe?module=http_2xx_ipv4&target=https://example.com/' 2>/dev/null | awk '/^probe_success /{print $2}')" = 1 ] && \
       [ "$(curl -fsS --connect-timeout 2 --max-time 5 'http://127.0.0.1:29115/probe?module=http_2xx_ipv6&target=https://example.com/' 2>/dev/null | awk '/^probe_success /{print $2}')" = 1 ]; then
      ok=1; break
    fi
    sleep 1
  done
  test "$ok" = 1
}

control_plane_guard
runtime_pid_before=$(systemctl show -p MainPID --value ordivon-runtime.service)

systemctl stop "$TARGET"
test "$(systemctl is-active "$TARGET" 2>/dev/null || true)" != active
for u in "${UNITS[@]}"; do test "$(systemctl is-active "$u" 2>/dev/null || true)" != active; done
control_plane_guard

systemctl start "$TARGET"
wait_active "$TARGET"
for u in "${UNITS[@]}"; do wait_active "$u"; done
wait_functional

# Long-flow proof after a cold start catches readiness that only works for tiny requests.
meta=$(curl --fail --silent --show-error --proxy http://127.0.0.1:28080 --connect-timeout 5 --max-time 30 \
  -o /tmp/network-v2-r0-cold-1m.bin -w 'http=%{http_code} bytes=%{size_download} speed=%{speed_download} time=%{time_total}' \
  'https://speed.cloudflare.com/__down?bytes=1000000')
test "$(stat -c %s /tmp/network-v2-r0-cold-1m.bin)" -eq 1000000
rm -f /tmp/network-v2-r0-cold-1m.bin

control_plane_guard
test "$(systemctl show -p MainPID --value ordivon-runtime.service)" = "$runtime_pid_before"

echo "cold_start_longflow $meta"
echo r0-target-stop=PASS
echo control-plane-independent-while-r0-stopped=PASS
echo r0-target-cold-start=PASS
echo r0-dualstack-functional-readiness=PASS
