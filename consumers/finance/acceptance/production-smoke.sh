#!/usr/bin/env bash
set -euo pipefail

API_PORT=${API_PORT:-19299}
TARGET=network-v2-finance.target
EGRESS=network-v2-finance-egress.service
A_WG=network-v2-finance-wireguard@a.service
B_WG=network-v2-finance-wireguard@b.service
A_CARRIER=network-v2-finance-carrier@a.service
B_CARRIER=network-v2-finance-carrier@b.service

recover() {
  systemctl start "$A_CARRIER" >/dev/null 2>&1 || true
  systemctl start "$B_CARRIER" >/dev/null 2>&1 || true
  systemctl start "$EGRESS" >/dev/null 2>&1 || true
}
trap recover EXIT

wait_state() {
  local unit=$1 expected=$2 state=unknown
  for _ in $(seq 1 80); do
    state=$(systemctl is-active "$unit" 2>/dev/null || true)
    [ "$state" = "$expected" ] && return 0
    sleep 0.25
  done
  echo "unit state mismatch: $unit expected=$expected got=$state" >&2
  return 1
}

probe_okx_rest() {
  local out
  out=$(mktemp)
  curl -4 -sS --proxy http://127.0.0.1:19283 --connect-timeout 3 --max-time 12 https://openapi.okx.com/api/v5/public/time -o "$out"
  jq -e '.code=="0" and (.data|type)=="array" and (.data|length>=1)' "$out" >/dev/null
  rm -f "$out"
}

probe_binance_rest() {
  local out
  out=$(mktemp)
  curl -4 -sS --proxy http://127.0.0.1:19287 --connect-timeout 3 --max-time 12 https://fapi.binance.com/fapi/v1/time -o "$out"
  jq -e '(.serverTime|type)=="number"' "$out" >/dev/null
  rm -f "$out"
}

probe_ws_http() {
  local port=$1 url=$2 codes=$3 code
  code=$(curl -4 -sS --proxy "http://127.0.0.1:$port" --connect-timeout 3 --max-time 10 -o /dev/null -w '%{http_code}' "$url")
  case ",$codes," in
    *",$code,"*) return 0 ;;
    *) echo "unexpected WS HTTP consequence: $url => $code" >&2; return 1 ;;
  esac
}

probe_all() {
  probe_okx_rest \
    && probe_binance_rest \
    && probe_ws_http 19288 https://ws.okx.com:8443/ws/v5/public '200,400,404,426' \
    && probe_ws_http 19289 https://fstream.binance.com/ '200,400,403,404,426'
}

wait_all() {
  for _ in $(seq 1 25); do
    probe_all >/dev/null 2>&1 && return 0
    sleep 1
  done
  return 1
}

group() { sing-box api --url "http://127.0.0.1:$API_PORT" group show "$1"; }
refresh_groups() {
  local g
  for g in finance-okx-auto finance-okx-ws-auto finance-binance-usdm-auto finance-binance-usdm-ws-auto; do
    sing-box api --url "http://127.0.0.1:$API_PORT" group urltest "$g" >/dev/null
  done
  sleep 4
  for g in finance-okx-auto finance-okx-ws-auto finance-binance-usdm-auto finance-binance-usdm-ws-auto; do group "$g" >/dev/null; done
}

blocked() {
  local port=$1 url=$2 rc
  set +e
  curl -4 -sS --proxy "http://127.0.0.1:$port" --connect-timeout 2 --max-time 5 "$url" >/dev/null 2>&1
  rc=$?
  set -e
  test "$rc" -ne 0
}

expect_target_failure() {
  local port=$1 url=$2 rc
  set +e
  curl -4 -sS --proxy "http://127.0.0.1:$port" --connect-timeout 2 --max-time 6 "$url" >/dev/null 2>&1
  rc=$?
  set -e
  test "$rc" -ne 0
}

for unit in "$TARGET" "$EGRESS" network-v2-finance-netns@a.service network-v2-finance-netns@b.service "$A_WG" "$B_WG" "$A_CARRIER" "$B_CARRIER"; do
  wait_state "$unit" active
done
wait_all
refresh_groups

# Each inbound is destination-fenced, including against sibling Finance authorities.
blocked 19283 https://fapi.binance.com/fapi/v1/time
blocked 19287 https://openapi.okx.com/api/v5/public/time
blocked 19288 https://fstream.binance.com/
blocked 19289 https://ws.okx.com:8443/ws/v5/public
blocked 19283 https://example.com/

# Provider B down: A must carry all four authorities.
systemctl stop "$B_WG"
wait_state "$B_CARRIER" inactive
wait_all

# Normal systemd dependency activation restores B; no custom recovery controller.
systemctl start "$B_CARRIER"
wait_state "$B_WG" active
wait_state "$B_CARRIER" active
wait_all

# Provider A down: B must independently carry all four authorities.
systemctl stop "$A_WG"
wait_state "$A_CARRIER" inactive
wait_all

# Both down: every admitted authority must fail closed against its own real target.
systemctl stop "$B_WG"
wait_state "$B_CARRIER" inactive
expect_target_failure 19283 https://openapi.okx.com/api/v5/public/time
expect_target_failure 19287 https://fapi.binance.com/fapi/v1/time
expect_target_failure 19288 https://ws.okx.com:8443/ws/v5/public
expect_target_failure 19289 https://fstream.binance.com/

# Recover both providers and then restart only the root consumer process.
systemctl start "$A_CARRIER"
wait_state "$A_WG" active
wait_state "$A_CARRIER" active
systemctl start "$B_CARRIER"
wait_state "$B_WG" active
wait_state "$B_CARRIER" active
wait_all
systemctl restart "$EGRESS"
wait_state "$EGRESS" active
wait_all
refresh_groups

# Finance migration must not perturb Runtime/Cloudflare control plane.
for unit in ordivon-runtime.service ordivon-cloudflare-production-a.service ordivon-cloudflare-production-b.service ordivon-cloudflare-canary.service ordivon-cloudflare-direct-route.service; do
  test "$(systemctl is-active "$unit")" = active
done

echo finance-network-v2-four-authority-fencing=PASS
echo finance-network-v2-dual-provider-failclosed=PASS
echo finance-network-v2-systemd-lifecycle=PASS
