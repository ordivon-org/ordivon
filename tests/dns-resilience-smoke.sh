#!/usr/bin/env bash
set -euo pipefail
SUFFIX=$$
UP=network-v2-dns-resilience-upstream-$SUFFIX.service
DP=network-v2-dns-resilience-proxy-$SUFFIX.service
cleanup(){
  systemctl stop "$DP" "$UP" >/dev/null 2>&1 || true
  systemctl reset-failed "$DP" "$UP" >/dev/null 2>&1 || true
}
trap cleanup EXIT

pick_port(){
  for p in "$@"; do
    if ! ss -luntH | awk '{print $5}' | grep -Eq "(^|[.:])$p$"; then echo "$p"; return 0; fi
  done
  return 1
}
UP_PORT=$(pick_port 25360 25363 25366 25369)
DEAD_PORT=$(pick_port 25361 25364 25367 25370)
DP_PORT=$(pick_port 25362 25365 25368 25371)
test "$UP_PORT" != "$DEAD_PORT"; test "$UP_PORT" != "$DP_PORT"; test "$DEAD_PORT" != "$DP_PORT"

start_up(){
  systemd-run --quiet --unit="$UP" --property=Type=simple --property=Restart=no \
    /usr/bin/dnsmasq --no-daemon --no-resolv --bind-interfaces --listen-address=127.0.0.1 --port="$UP_PORT" \
    --address=/resilience.test/203.0.113.7 --local-ttl=2
  for _ in $(seq 1 40); do
    if dig +time=1 +tries=1 @127.0.0.1 -p "$UP_PORT" warm.resilience.test A +short 2>/dev/null | grep -qx '203.0.113.7'; then return 0; fi
    sleep 0.1
  done
  return 1
}

start_up
systemd-run --quiet --unit="$DP" --property=Type=simple --property=Restart=no \
  /usr/bin/dnsproxy -l 127.0.0.1 -p "$DP_PORT" -u "127.0.0.1:$UP_PORT" -u "127.0.0.1:$DEAD_PORT" \
  --upstream-mode parallel --cache --cache-size 1024 --pending-requests-enabled --timeout 1s
for _ in $(seq 1 40); do ss -luntH | awk '{print $5}' | grep -Eq "(^|[.:])$DP_PORT$" && break; sleep 0.1; done
ss -luntH | awk '{print $5}' | grep -Eq "(^|[.:])$DP_PORT$"
proxy_pid_before=$(systemctl show -p MainPID --value "$DP")
test "$proxy_pid_before" -gt 0

# One of two parallel upstreams is absent from the beginning.
for proto in udp tcp; do
  extra=; [ "$proto" = tcp ] && extra=+tcp
  ans=$(dig $extra +time=2 +tries=1 @127.0.0.1 -p "$DP_PORT" "partial-$proto.resilience.test" A +short)
  test "$ans" = 203.0.113.7
  echo partial_failure_${proto}=PASS
done

test "$(dig +time=2 +tries=1 @127.0.0.1 -p "$DP_PORT" warm.resilience.test A +short)" = 203.0.113.7

# All upstreams fail while the proxy process and listener remain alive.
systemctl stop "$UP"
test "$(systemctl is-active "$DP")" = active
ss -luntH | awk '{print $5}' | grep -Eq "(^|[.:])$DP_PORT$"
# A valid cached answer is allowed until its TTL expires.
test "$(dig +time=2 +tries=1 @127.0.0.1 -p "$DP_PORT" warm.resilience.test A +short)" = 203.0.113.7
echo cached_answer_during_upstream_outage=PASS
# A never-seen key must not pass merely because the listener is up.
status=$(dig +time=2 +tries=1 @127.0.0.1 -p "$DP_PORT" cold.resilience.test A +comments | awk '/status:/{gsub(/,/,"",$6); print $6; exit}')
test "$status" = SERVFAIL
echo all_upstreams_down_uncached_servfail=PASS
sleep 3
status2=$(dig +time=2 +tries=1 @127.0.0.1 -p "$DP_PORT" warm.resilience.test A +comments | awk '/status:/{gsub(/,/,"",$6); print $6; exit}')
test "$status2" = SERVFAIL
echo cache_expiry_fail_closed=PASS

# Restore one upstream. dnsproxy itself must recover without restart.
start_up
recovered=''
for _ in $(seq 1 20); do
  recovered=$(dig +time=1 +tries=1 @127.0.0.1 -p "$DP_PORT" recovered.resilience.test A +short 2>/dev/null || true)
  [ "$recovered" = 203.0.113.7 ] && break
  sleep 0.25
done
test "$recovered" = 203.0.113.7
proxy_pid_after=$(systemctl show -p MainPID --value "$DP")
test "$proxy_pid_after" = "$proxy_pid_before"
echo dns_upstream_recovery_without_dnsproxy_restart=PASS
printf 'dnsproxy_pid=%s\n' "$proxy_pid_after"
echo dns-resilience-smoke=PASS
