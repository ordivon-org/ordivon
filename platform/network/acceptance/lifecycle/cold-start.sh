#!/usr/bin/env bash
set -euo pipefail
TARGET=network-v2-r0.target
UNITS=(network-v2-dnsproxy.service network-v2-singbox.service network-v2-blackbox.service network-v2-prometheus.service)

recover_r0(){
  systemctl start "$TARGET" >/dev/null 2>&1 || true
}
trap recover_r0 EXIT

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

wait_inactive(){
  local u=$1 state
  for _ in $(seq 1 80); do
    state=$(systemctl is-active "$u" 2>/dev/null || true)
    [ "$state" != active ] && [ "$state" != activating ] && [ "$state" != deactivating ] && return 0
    sleep 0.25
  done
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
wait_inactive "$TARGET"
for u in "${UNITS[@]}"; do wait_inactive "$u"; done
control_plane_guard

systemctl start "$TARGET"
wait_active "$TARGET"
for u in "${UNITS[@]}"; do wait_active "$u"; done
wait_functional

# Cold-start acceptance proves functional external readiness. Large-stream correctness is
# tested deterministically in source acceptance and is not coupled to public-CDN throughput.
external_meta=$(curl --fail --silent --show-error --proxy http://127.0.0.1:28080 --connect-timeout 5 --max-time 15 \
  -o /dev/null -w 'http=%{http_code} httpver=%{http_version} time=%{time_total}' https://example.com/)

control_plane_guard
test "$(systemctl show -p MainPID --value ordivon-runtime.service)" = "$runtime_pid_before"

trap - EXIT
echo "cold_start_external_readiness $external_meta"
echo r0-target-stop=PASS
echo control-plane-independent-while-r0-stopped=PASS
echo r0-target-cold-start=PASS
echo r0-dualstack-functional-readiness=PASS
