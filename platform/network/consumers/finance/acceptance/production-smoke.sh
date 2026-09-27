#!/usr/bin/env bash
set -euo pipefail
TARGET=network-v2-finance.target
EGRESS=network-v2-finance-egress.service
CARRIER=network-v2-browserless-provider-carrier.service
BROWSERLESS_TARGET=network-v2-browserless.target
SUPPLY_TARGET=network-v2-supply-chain.target
SUPPLY_EGRESS=network-v2-supply-chain-egress.service
CONTROL_UNITS=(ordivon-runtime.service ordivon-cloudflare-production-a.service ordivon-cloudflare-production-b.service ordivon-cloudflare-canary.service ordivon-cloudflare-direct-route.service)
control_state_snapshot(){ local u; for u in "${CONTROL_UNITS[@]}"; do printf '%s=%s\n' "$u" "$(systemctl is-active "$u" 2>/dev/null || true)"; done; }
CONTROL_PLANE_BEFORE=$(control_state_snapshot)
BROWSERLESS_WAS_ACTIVE=$(systemctl is-active "$BROWSERLESS_TARGET" 2>/dev/null || true)
SUPPLY_WAS_ACTIVE=$(systemctl is-active "$SUPPLY_TARGET" 2>/dev/null || true)
wait_state(){ local u=$1 expected=$2 s; for _ in $(seq 1 80); do s=$(systemctl is-active "$u" 2>/dev/null || true); [ "$s" = "$expected" ] && return 0; sleep .25; done; echo "$u expected=$expected got=$s" >&2; return 1; }
probe_okx(){ curl -4 -fsS --proxy http://127.0.0.1:19283 --connect-timeout 3 --max-time 12 https://openapi.okx.com/api/v5/public/time | jq -e '.code=="0" and (.data|length>=1)' >/dev/null; }
probe_binance_spot(){ curl -4 -fsS --proxy http://127.0.0.1:19284 --connect-timeout 3 --max-time 12 https://data-api.binance.vision/api/v3/time | jq -e '(.serverTime|type)=="number"' >/dev/null; }
probe_binance_usdm(){ curl -4 -fsS --proxy http://127.0.0.1:19287 --connect-timeout 3 --max-time 12 https://fapi.binance.com/fapi/v1/time | jq -e '(.serverTime|type)=="number"' >/dev/null; }
probe_wallet(){ curl -4 -fsS --proxy http://127.0.0.1:19290 --connect-timeout 3 --max-time 12 https://api.binance.com/api/v3/time | jq -e '(.serverTime|type)=="number"' >/dev/null; }
probe_treasury(){ curl -4 -fsS --proxy http://127.0.0.1:19291 --connect-timeout 5 --max-time 20 https://home.treasury.gov/robots.txt | grep -qi 'user-agent'; }
probe_fred(){ curl -4 -fsS --proxy http://127.0.0.1:19292 --connect-timeout 5 --max-time 20 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF&cosd=2026-09-22&coed=2026-09-22' | grep -q '^observation_date,DFF'; }
probe_ws(){ local p=$1 u=$2 codes=$3 c; c=$(curl -4 -sS --proxy "http://127.0.0.1:$p" --connect-timeout 3 --max-time 10 -o /dev/null -w '%{http_code}' "$u"); case ",$codes," in *",$c,"*) return 0;; *) return 1;; esac; }
probe_provider_all(){ probe_okx && probe_binance_spot && probe_binance_usdm && probe_wallet && probe_ws 19285 https://data-stream.binance.vision/ '200,400,403,404,426' && probe_ws 19288 https://ws.okx.com:8443/ws/v5/public '200,400,404,426' && probe_ws 19289 https://fstream.binance.com/ '200,400,403,404,426'; }
probe_all(){ probe_provider_all && probe_treasury && probe_fred; }
wait_all(){ for _ in $(seq 1 30); do probe_all >/dev/null 2>&1 && return 0; sleep 1; done; return 1; }
blocked(){ local p=$1 u=$2 rc; set +e; curl -4 -sS --proxy "http://127.0.0.1:$p" --connect-timeout 2 --max-time 5 "$u" >/dev/null 2>&1; rc=$?; set -e; test "$rc" -ne 0; }
cleanup(){
  if [ "$BROWSERLESS_WAS_ACTIVE" = active ]; then
    systemctl start "$BROWSERLESS_TARGET" >/dev/null 2>&1 || true
  else
    systemctl start "$CARRIER" >/dev/null 2>&1 || true
  fi
  systemctl start "$TARGET" >/dev/null 2>&1 || true
  if [ "$SUPPLY_WAS_ACTIVE" = active ]; then systemctl start "$SUPPLY_TARGET" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT
wait_state "$TARGET" active; wait_state "$EGRESS" active; wait_state "$CARRIER" active
# There must be no Finance-owned WireGuard material/session in the current design.
test ! -e /etc/network-v2/finance/provider-endpoints.json
if pgrep -af '/usr/bin/sing-box run -c /etc/network-v2/finance/provider-endpoints.json' >/dev/null; then
  echo 'duplicate Finance WireGuard provider process is still running' >&2
  exit 1
fi
wait_all
# Exact authority fencing remains independent of the shared physical carrier.
blocked 19283 https://fapi.binance.com/fapi/v1/time
blocked 19283 https://home.treasury.gov/
blocked 19284 https://openapi.okx.com/api/v5/public/time
blocked 19287 https://api.binance.com/api/v3/time
blocked 19291 https://openapi.okx.com/api/v5/public/time
blocked 19292 https://home.treasury.gov/
blocked 19283 https://example.com/
# Shared carrier loss must fail provider-bound venue lanes closed while explicit direct macro lanes survive.
systemctl stop "$CARRIER"
wait_state "$CARRIER" inactive
# Physical-carrier loss must not remove semantic authorities. Provider lanes fail inside the proxy; direct lanes remain usable.
wait_state "$TARGET" active
wait_state "$EGRESS" active
if [ "$SUPPLY_WAS_ACTIVE" = active ]; then
  wait_state "$SUPPLY_TARGET" active
  wait_state "$SUPPLY_EGRESS" active
fi
blocked 19283 https://openapi.okx.com/api/v5/public/time
blocked 19284 https://data-api.binance.vision/api/v3/time
blocked 19287 https://fapi.binance.com/fapi/v1/time
blocked 19290 https://api.binance.com/api/v3/time
probe_treasury
probe_fred
if [ "$BROWSERLESS_WAS_ACTIVE" = active ]; then
  systemctl start "$BROWSERLESS_TARGET"
else
  systemctl start "$CARRIER"
fi
wait_state "$CARRIER" active
wait_state "$EGRESS" active
if [ "$SUPPLY_WAS_ACTIVE" = active ]; then
  wait_state "$SUPPLY_EGRESS" active
fi
wait_all
test "$(systemctl is-active ordivon-runtime.service)" = active
CONTROL_PLANE_AFTER=$(control_state_snapshot)
test "$CONTROL_PLANE_AFTER" = "$CONTROL_PLANE_BEFORE"
echo finance-network-v2-nine-authority-fencing=PASS
echo finance-network-v2-shared-carrier-failclosed=PASS
echo finance-network-v2-direct-macro-independence=PASS
