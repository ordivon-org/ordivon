#!/usr/bin/env bash
set -euo pipefail

mode=${1:-all}
timeout_seconds=${2:-30}
target=network-v2-finance.target
egress=network-v2-finance-egress.service

case "$mode" in
  all|public|okx|binance-usdm|binance-spot|binance-wallet|treasury|fred) ;;
  *) echo "usage: $0 [all|public|okx|binance-usdm|binance-spot|binance-wallet|treasury|fred] [timeout_seconds]" >&2; exit 2 ;;
esac
case "$timeout_seconds" in
  ''|*[!0-9]*) echo "timeout_seconds must be a non-negative integer" >&2; exit 2 ;;
esac

unit_active() { systemctl is-active --quiet "$1"; }
probe_okx() {
  curl -4 -fsS --proxy http://127.0.0.1:19283 --connect-timeout 3 --max-time 8 https://openapi.okx.com/api/v5/public/time |
    jq -e '.code=="0" and (.data|type)=="array" and (.data|length>=1)' >/dev/null
}
probe_binance_usdm() {
  curl -4 -fsS --proxy http://127.0.0.1:19287 --connect-timeout 3 --max-time 8 https://fapi.binance.com/fapi/v1/time |
    jq -e '(.serverTime|type)=="number"' >/dev/null
}
probe_binance_spot() {
  curl -4 -fsS --proxy http://127.0.0.1:19284 --connect-timeout 3 --max-time 8 https://data-api.binance.vision/api/v3/time |
    jq -e '(.serverTime|type)=="number"' >/dev/null
}
probe_binance_wallet() {
  curl -4 -fsS --proxy http://127.0.0.1:19290 --connect-timeout 3 --max-time 8 https://api.binance.com/api/v3/time |
    jq -e '(.serverTime|type)=="number"' >/dev/null
}
probe_treasury() {
  local out
  out=$(curl -4 -fsS --proxy http://127.0.0.1:19291 --connect-timeout 5 --max-time 20 'https://home.treasury.gov/robots.txt')
  printf '%s' "$out" | grep -qi 'user-agent'
}
probe_fred() {
  local out
  out=$(curl -4 -fsS --proxy http://127.0.0.1:19292 --connect-timeout 5 --max-time 20 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF&cosd=2026-09-22&coed=2026-09-22')
  printf '%s' "$out" | grep -q '^observation_date,DFF'
}
probe_selected() {
  unit_active "$target" && unit_active "$egress" || return 1
  case "$mode" in
    okx) probe_okx ;;
    binance-usdm) probe_binance_usdm ;;
    binance-spot) probe_binance_spot ;;
    binance-wallet) probe_binance_wallet ;;
    treasury) probe_treasury ;;
    fred) probe_fred ;;
    public) probe_okx && probe_binance_usdm && probe_binance_spot && probe_treasury && probe_fred ;;
    all) probe_okx && probe_binance_usdm && probe_binance_spot && probe_treasury && probe_fred && probe_binance_wallet ;;
  esac
}

started=$SECONDS
while :; do
  if probe_selected >/dev/null 2>&1; then
    elapsed=$((SECONDS-started))
    printf '{"schemaVersion":1,"kind":"ordivon.network-v2.finance-readiness","mode":"%s","standing":"READY","elapsedSeconds":%d,"targetActive":true,"egressActive":true,"directFallback":false}\n' "$mode" "$elapsed"
    exit 0
  fi
  elapsed=$((SECONDS-started))
  if [ "$elapsed" -ge "$timeout_seconds" ]; then
    break
  fi
  sleep 1
done

target_state=$(systemctl is-active "$target" 2>/dev/null || true)
egress_state=$(systemctl is-active "$egress" 2>/dev/null || true)
printf 'finance readiness failed: mode=%s timeout=%ss target=%s egress=%s\n' "$mode" "$timeout_seconds" "$target_state" "$egress_state" >&2
exit 4
