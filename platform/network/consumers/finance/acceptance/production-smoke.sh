#!/usr/bin/env bash
set -euo pipefail

API_PORT=${API_PORT:-19299}
TARGET=network-v2-finance.target
EGRESS=network-v2-finance-egress.service
ENDPOINTS=/etc/network-v2/finance/provider-endpoints.json
FAULT_TABLE=network_v2_finance_accept
CONTROL_UNITS=(
  ordivon-runtime.service
  ordivon-cloudflare-production-a.service
  ordivon-cloudflare-production-b.service
  ordivon-cloudflare-canary.service
  ordivon-cloudflare-direct-route.service
)

control_state_snapshot() {
  local unit
  for unit in "${CONTROL_UNITS[@]}"; do
    printf '%s=%s\n' "$unit" "$(systemctl is-active "$unit" 2>/dev/null || true)"
  done
}

CONTROL_PLANE_BEFORE=$(control_state_snapshot)
test "$(systemctl is-active ordivon-runtime.service)" = active

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

fault_reset() {
  nft delete table inet "$FAULT_TABLE" >/dev/null 2>&1 || true
}

cleanup() {
  fault_reset
  systemctl restart "$EGRESS" >/dev/null 2>&1 || true
}
trap cleanup EXIT

endpoint_ip() {
  local tag=$1
  jq -er --arg tag "$tag" '.endpoints[] | select(.tag==$tag) | .peers[0].address' "$ENDPOINTS"
}

fault_block() {
  fault_reset
  nft add table inet "$FAULT_TABLE"
  nft "add chain inet $FAULT_TABLE output { type filter hook output priority -50; policy accept; }"
  local tag ip
  for tag in "$@"; do
    ip=$(endpoint_ip "$tag")
    nft add rule inet "$FAULT_TABLE" output ip daddr "$ip" udp dport 51820 drop
  done
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

probe_binance_spot_rest() {
  local out
  out=$(mktemp)
  curl -4 -sS --proxy http://127.0.0.1:19284 --connect-timeout 3 --max-time 12 https://data-api.binance.vision/api/v3/time -o "$out"
  jq -e '(.serverTime|type)=="number"' "$out" >/dev/null
  rm -f "$out"
}

probe_binance_wallet_rest() {
  local out
  out=$(mktemp)
  curl -4 -sS --proxy http://127.0.0.1:19290 --connect-timeout 3 --max-time 12 https://api.binance.com/api/v3/time -o "$out"
  jq -e '(.serverTime|type)=="number"' "$out" >/dev/null
  rm -f "$out"
}

probe_treasury_rest() {
  local out
  out=$(mktemp)
  curl -4 -fsS --proxy http://127.0.0.1:19291 --connect-timeout 3 --max-time 20 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026' -o "$out"
  grep -q '<feed ' "$out"
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
    && probe_binance_spot_rest \
    && probe_binance_rest \
    && probe_treasury_rest \
    && probe_ws_http 19285 https://data-stream.binance.vision/ '200,400,403,404,426' \
    && probe_ws_http 19288 https://ws.okx.com:8443/ws/v5/public '200,400,404,426' \
    && probe_ws_http 19289 https://fstream.binance.com/ '200,400,403,404,426'
}

wait_all() {
  for _ in $(seq 1 30); do
    probe_all >/dev/null 2>&1 && return 0
    sleep 1
  done
  return 1
}

group() { sing-box api --url "http://127.0.0.1:$API_PORT" group show "$1"; }
refresh_groups() {
  sing-box api --url "http://127.0.0.1:$API_PORT" group urltest provider-auto >/dev/null
  sleep 4
  group provider-auto >/dev/null
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

test -r "$ENDPOINTS"
for unit in "$TARGET" "$EGRESS"; do wait_state "$unit" active; done
for legacy in network-v2-finance-netns@a.service network-v2-finance-netns@b.service network-v2-finance-wireguard@a.service network-v2-finance-wireguard@b.service network-v2-finance-carrier@a.service network-v2-finance-carrier@b.service; do
  test "$(systemctl is-active "$legacy" 2>/dev/null || true)" != active
done
if ip netns list | awk '{print $1}' | grep -Eq '^nv2-finance-[ab]$'; then
  echo 'legacy finance namespace is still active' >&2
  exit 1
fi
if ss -lntH | awk '$4 ~ /:28221$/ {found=1} END{exit !found}'; then
  echo 'legacy finance listener :28221 is still active' >&2
  exit 1
fi
wait_all
refresh_groups

# Each inbound is destination-fenced, including against sibling Finance authorities.
blocked 19283 https://fapi.binance.com/fapi/v1/time
blocked 19283 https://data-api.binance.vision/api/v3/time
blocked 19284 https://openapi.okx.com/api/v5/public/time
blocked 19284 https://fapi.binance.com/fapi/v1/time
blocked 19285 https://ws.okx.com:8443/ws/v5/public
blocked 19285 https://fstream.binance.com/
blocked 19287 https://openapi.okx.com/api/v5/public/time
blocked 19287 https://data-api.binance.vision/api/v3/time
blocked 19288 https://fstream.binance.com/
blocked 19288 https://data-stream.binance.vision/
blocked 19289 https://ws.okx.com:8443/ws/v5/public
blocked 19289 https://data-stream.binance.vision/
blocked 19290 https://openapi.okx.com/api/v5/public/time
blocked 19290 https://fapi.binance.com/fapi/v1/time
blocked 19287 https://api.binance.com/api/v3/time
blocked 19291 https://openapi.okx.com/api/v5/public/time
blocked 19291 https://fapi.binance.com/fapi/v1/time
blocked 19283 https://home.treasury.gov/
blocked 19283 https://example.com/

# Mature fault injection: drop only provider B's WireGuard UDP endpoint; A must carry every authority.
fault_block provider-b
refresh_groups || true
wait_all

fault_reset
refresh_groups
wait_all

# Drop only provider A; B must independently carry every authority.
fault_block provider-a
refresh_groups || true
wait_all

# Drop both provider endpoints; provider-bound venue authorities must fail closed while the explicitly direct Treasury authority remains available.
fault_block provider-a provider-b
sleep 4
expect_target_failure 19283 https://openapi.okx.com/api/v5/public/time
expect_target_failure 19284 https://data-api.binance.vision/api/v3/time
expect_target_failure 19285 https://data-stream.binance.vision/
expect_target_failure 19287 https://fapi.binance.com/fapi/v1/time
expect_target_failure 19288 https://ws.okx.com:8443/ws/v5/public
expect_target_failure 19289 https://fstream.binance.com/
expect_target_failure 19290 https://api.binance.com/api/v3/time
probe_treasury_rest

# Restore mature data plane and prove root-process lifecycle recovery.
fault_reset
systemctl restart "$EGRESS"
wait_state "$EGRESS" active
wait_all
refresh_groups

# Finance migration must not perturb Runtime/Cloudflare control-plane state.
test "$(systemctl is-active ordivon-runtime.service)" = active
CONTROL_PLANE_AFTER=$(control_state_snapshot)
if [ "$CONTROL_PLANE_AFTER" != "$CONTROL_PLANE_BEFORE" ]; then
  echo "control-plane state changed during Finance acceptance" >&2
  printf 'before:\n%s\nafter:\n%s\n' "$CONTROL_PLANE_BEFORE" "$CONTROL_PLANE_AFTER" >&2
  exit 1
fi

echo finance-network-v2-eight-authority-fencing=PASS
echo finance-network-v2-singbox-endpoint-failclosed=PASS
echo finance-network-v2-single-process-lifecycle=PASS
