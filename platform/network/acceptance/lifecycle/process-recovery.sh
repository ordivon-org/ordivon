#!/usr/bin/env bash
set -euo pipefail

UNIT=network-v2-singbox.service
PROXY=http://127.0.0.1:28080
TARGET=https://example.com/
BLACKBOX=http://127.0.0.1:29115
PROM=http://127.0.0.1:29090

systemctl is-active --quiet "$UNIT"
curl -fsS --proxy "$PROXY" --connect-timeout 3 --max-time 8 -o /dev/null "$TARGET"

old_pid=$(systemctl show "$UNIT" -p MainPID --value)
baseline_restarts=$(systemctl show "$UNIT" -p NRestarts --value)
[ "$old_pid" -gt 1 ]
started_ms=$(date +%s%3N)

kill -KILL "$old_pid"

failure_observed=no
for _ in $(seq 1 40); do
  if ! curl -fsS --proxy "$PROXY" --connect-timeout 1 --max-time 2 -o /dev/null "$TARGET" 2>/dev/null; then
    failure_observed=yes
    break
  fi
  sleep 0.05
done
[ "$failure_observed" = yes ]

new_pid=''
for _ in $(seq 1 160); do
  pid=$(systemctl show "$UNIT" -p MainPID --value 2>/dev/null || echo 0)
  state=$(systemctl is-active "$UNIT" 2>/dev/null || true)
  if [ "$state" = active ] && [ "$pid" -gt 1 ] && [ "$pid" != "$old_pid" ]; then
    if curl -fsS --proxy "$PROXY" --connect-timeout 2 --max-time 5 -o /dev/null "$TARGET" 2>/dev/null; then
      new_pid=$pid
      break
    fi
  fi
  sleep 0.125
done
[ -n "$new_pid" ]

current_restarts=$(systemctl show "$UNIT" -p NRestarts --value)
[ "$current_restarts" -gt "$baseline_restarts" ]
recovered_ms=$(date +%s%3N)

test "$(curl -fsS "$BLACKBOX/probe?module=tcp_connect&target=127.0.0.1:28080" | awk '/^probe_success / {print $2}')" = "1"

prometheus_ready=no
for _ in $(seq 1 30); do
  if curl -fsS --get --data-urlencode 'query=probe_success{job="blackbox-singbox"}' "$PROM/api/v1/query" | grep -Eq '"value"[^]]*"1"'; then
    prometheus_ready=yes
    break
  fi
  sleep 0.5
done
[ "$prometheus_ready" = yes ]

printf 'old_pid=%s\nnew_pid=%s\nbaseline_restarts=%s\ncurrent_restarts=%s\nrecovery_ms=%s\n' \
  "$old_pid" "$new_pid" "$baseline_restarts" "$current_restarts" "$((recovered_ms-started_ms))"
echo live-recovery=PASS
