#!/usr/bin/env bash
set -euo pipefail

SHADOW_PORT=${SHADOW_PORT:-19283}
API_PORT=${API_PORT:-19289}
TARGET_URL=${TARGET_URL:-https://openapi.okx.com/api/v5/public/time}
TARGET_JQ=${TARGET_JQ:-'.code == "0" and (.data | type == "array") and (.data | length >= 1)'}
TARGET=network-v2-finance-okx-shadow.target
SHADOW=network-v2-finance-okx-shadow.service
A_WG=network-v2-finance-okx-wireguard@a.service
B_WG=network-v2-finance-okx-wireguard@b.service
A_CARRIER=network-v2-finance-okx-carrier@a.service
B_CARRIER=network-v2-finance-okx-carrier@b.service

recover_shadow() {
  systemctl start "$A_CARRIER" >/dev/null 2>&1 || true
  systemctl start "$B_CARRIER" >/dev/null 2>&1 || true
  systemctl start "$SHADOW" >/dev/null 2>&1 || true
}
trap recover_shadow EXIT

wait_state() {
  local unit=$1 expected=$2 state
  for _ in $(seq 1 60); do
    state=$(systemctl is-active "$unit" 2>/dev/null || true)
    [ "$state" = "$expected" ] && return 0
    sleep 0.2
  done
  echo "unit state mismatch: $unit expected=$expected got=$(systemctl is-active "$unit" 2>/dev/null || true)" >&2
  return 1
}

probe_proxy() {
  local port=$1 out meta
  out=$(mktemp)
  meta=$(curl -4 -sS --proxy "http://127.0.0.1:$port" --connect-timeout 3 --max-time 12 -o "$out" -w '%{http_code} %{time_total}' "$TARGET_URL")
  jq -e "$TARGET_JQ" "$out" >/dev/null
  rm -f "$out"
  test "${meta%% *}" = 200
  printf '%s\n' "${meta#* }"
}

wait_proxy() {
  local port=$1 t
  for _ in $(seq 1 20); do
    if t=$(probe_proxy "$port" 2>/dev/null); then printf '%s\n' "$t"; return 0; fi
    sleep 1
  done
  return 1
}

group_snapshot() {
  sing-box api --url "http://127.0.0.1:$API_PORT" group show finance-okx-shadow-auto
}

wait_group_api() {
  for _ in $(seq 1 60); do
    group_snapshot >/dev/null 2>&1 && return 0
    sleep 0.2
  done
  return 1
}

refresh_group() {
  sing-box api --url "http://127.0.0.1:$API_PORT" group urltest finance-okx-shadow-auto >/dev/null
  sleep 4
  group_snapshot
}

# Persistent shadow topology must be active before destructive checks.
for unit in \
  "$TARGET" "$SHADOW" \
  network-v2-finance-okx-netns@a.service network-v2-finance-okx-netns@b.service \
  "$A_WG" "$B_WG" "$A_CARRIER" "$B_CARRIER"; do
  wait_state "$unit" active
done

# systemd active is only process state. Enter destructive checks only after both
# the application path and sing-box API report functional readiness.
legacy_t=$(wait_proxy 19083)
shadow_t=$(wait_proxy "$SHADOW_PORT")
wait_group_api
initial_group=$(refresh_group)

set +e
curl -4 -sS --proxy "http://127.0.0.1:$SHADOW_PORT" --connect-timeout 2 --max-time 5 https://example.com/ >/dev/null 2>&1
blocked_rc=$?
set -e
test "$blocked_rc" -ne 0

# Remove B's WireGuard unit. BindsTo stops only B's carrier; A must keep shadow usable.
systemctl stop "$B_WG"
wait_state "$B_CARRIER" inactive
b_down_t=$(wait_proxy "$SHADOW_PORT")
b_down_group=$(refresh_group)

# Recovery is expressed by normal systemd dependency activation, not a custom controller.
systemctl start "$B_CARRIER"
wait_state "$B_WG" active
wait_state "$B_CARRIER" active
b_recovered_t=$(wait_proxy "$SHADOW_PORT")
b_recovered_group=$(refresh_group)

# Remove A and prove B independently survives.
systemctl stop "$A_WG"
wait_state "$A_CARRIER" inactive
a_down_t=$(wait_proxy "$SHADOW_PORT")
a_down_group=$(refresh_group)

# Remove B too: no direct/native route is eligible, so the consumer must fail closed.
systemctl stop "$B_WG"
wait_state "$B_CARRIER" inactive
set +e
curl -4 -fsS --proxy "http://127.0.0.1:$SHADOW_PORT" --connect-timeout 2 --max-time 8 "$TARGET_URL" >/dev/null 2>&1
both_down_rc=$?
set -e
test "$both_down_rc" -ne 0
both_down_group=$(refresh_group)

# Recover A from all-down, then recover B so the shadow is left fully healthy.
systemctl start "$A_CARRIER"
wait_state "$A_WG" active
wait_state "$A_CARRIER" active
a_recovered_t=$(wait_proxy "$SHADOW_PORT")
a_recovered_group=$(refresh_group)
systemctl start "$B_CARRIER"
wait_state "$B_WG" active
wait_state "$B_CARRIER" active
final_t=$(wait_proxy "$SHADOW_PORT")

# Restart only the root sing-box service; provider namespaces/tunnels remain owned by systemd.
systemctl restart "$SHADOW"
wait_state "$SHADOW" active
post_restart_t=$(wait_proxy "$SHADOW_PORT")

# The control plane and old production consumer remain independent and untouched.
for u in ordivon-runtime.service ordivon-cloudflare-production-a.service ordivon-cloudflare-production-b.service ordivon-cloudflare-canary.service ordivon-cloudflare-direct-route.service; do
  test "$(systemctl is-active "$u")" = active
done
for p in 19083 19084 19085 8897; do ss -ltn | grep -q "127.0.0.1:$p"; done
for p in 20243 20244 20245; do
  ha=$(curl -fsS --connect-timeout 2 --max-time 4 "http://127.0.0.1:$p/metrics" | awk '$1=="cloudflared_tunnel_ha_connections"{print $2}' | tail -n1)
  test "$ha" = 4
done
legacy_after_t=$(wait_proxy 19083)

printf 'legacy_before_seconds=%s\n' "$legacy_t"
printf 'shadow_initial_seconds=%s\n' "$shadow_t"
printf '%s\n%s\n' '--- shadow group: initial ---' "$initial_group"
printf 'provider_b_down_shadow_seconds=%s\n' "$b_down_t"
printf '%s\n%s\n' '--- shadow group: provider-b down ---' "$b_down_group"
printf 'provider_b_recovered_shadow_seconds=%s\n' "$b_recovered_t"
printf '%s\n%s\n' '--- shadow group: provider-b recovered ---' "$b_recovered_group"
printf 'provider_a_down_shadow_seconds=%s\n' "$a_down_t"
printf '%s\n%s\n' '--- shadow group: provider-a down ---' "$a_down_group"
printf 'both_provider_down_rc=%s\n' "$both_down_rc"
printf '%s\n%s\n' '--- shadow group: both down ---' "$both_down_group"
printf 'provider_a_recovered_shadow_seconds=%s\n' "$a_recovered_t"
printf '%s\n%s\n' '--- shadow group: provider-a recovered ---' "$a_recovered_group"
printf 'shadow_final_seconds=%s\n' "$final_t"
printf 'shadow_post_restart_seconds=%s\n' "$post_restart_t"
printf 'legacy_after_seconds=%s\n' "$legacy_after_t"
printf 'blocked_non_okx_rc=%s\n' "$blocked_rc"
echo finance-okx-shadow-systemd-lifecycle=PASS
echo finance-okx-shadow-dual-provider-failclosed=PASS
echo runtime-cloudflare-legacy-noninterference=PASS
