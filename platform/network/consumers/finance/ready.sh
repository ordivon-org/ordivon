#!/usr/bin/env bash
set -euo pipefail

mode=${1:-all}
timeout_seconds=${2:-30}
target=network-v2-finance.target
egress=network-v2-finance-egress.service

case "$mode" in
  all|public|okx|binance-usdm|binance-spot|binance-wallet|treasury) ;;
  *) echo "usage: $0 [all|public|okx|binance-usdm|binance-spot|binance-wallet|treasury] [timeout_seconds]" >&2; exit 2 ;;
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
  out=$(curl -4 -fsS --proxy http://127.0.0.1:19291 --connect-timeout 5 --max-time 35 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026')
  printf '%s' "$out" | grep -q '<feed '
}
probe_selected() {
  unit_active "$target" && unit_active "$egress" || return 1
  case "$mode" in
    okx) probe_okx ;;
    binance-usdm) probe_binance_usdm ;;
    binance-spot) probe_binance_spot ;;
    binance-wallet) probe_binance_wallet ;;
    treasury) probe_treasury ;;
    public) probe_okx && probe_binance_usdm && probe_binance_spot && probe_treasury ;;
    all) probe_okx && probe_binance_usdm && probe_binance_spot && probe_treasury && probe_binance_wallet ;;
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
