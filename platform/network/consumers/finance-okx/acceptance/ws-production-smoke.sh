#!/usr/bin/env bash
set -euo pipefail
WS_PORT=${WS_PORT:-19288}
REST_PORT=${REST_PORT:-19283}
API_PORT=${API_PORT:-19289}
TARGET_URL=${TARGET_URL:-https://ws.okx.com:8443/ws/v5/public}
TARGET=network-v2-finance-okx.target
EGRESS=network-v2-finance-okx.service
A_WG=network-v2-finance-okx-wireguard@a.service
B_WG=network-v2-finance-okx-wireguard@b.service
A_CARRIER=network-v2-finance-okx-carrier@a.service
B_CARRIER=network-v2-finance-okx-carrier@b.service
GROUP=finance-okx-ws-auto
recover(){ systemctl start "$A_CARRIER" >/dev/null 2>&1 || true; systemctl start "$B_CARRIER" >/dev/null 2>&1 || true; systemctl start "$EGRESS" >/dev/null 2>&1 || true; }
trap recover EXIT
wait_state(){ local u=$1 e=$2 s; for _ in $(seq 1 60); do s=$(systemctl is-active "$u" 2>/dev/null || true); [ "$s" = "$e" ] && return 0; sleep .2; done; return 1; }
probe_ws(){ local code; code=$(curl -4 -sS --proxy "http://127.0.0.1:$WS_PORT" --connect-timeout 3 --max-time 12 -o /dev/null -w '%{http_code}' "$TARGET_URL"); case "$code" in 200|400|404|426) printf '%s\n' "$code";; *) return 1;; esac; }
wait_ws(){ local c; for _ in $(seq 1 20); do if c=$(probe_ws 2>/dev/null); then printf '%s\n' "$c"; return 0; fi; sleep 1; done; return 1; }
group(){ sing-box api --url "http://127.0.0.1:$API_PORT" group show "$GROUP"; }
refresh(){ sing-box api --url "http://127.0.0.1:$API_PORT" group urltest "$GROUP" >/dev/null; sleep 4; group; }
for u in "$TARGET" "$EGRESS" network-v2-finance-okx-netns@a.service network-v2-finance-okx-netns@b.service "$A_WG" "$B_WG" "$A_CARRIER" "$B_CARRIER"; do wait_state "$u" active; done
initial=$(wait_ws); initial_group=$(refresh)
# Cross-fence and non-OKX destinations must be rejected.
set +e
curl -4 -sS --proxy "http://127.0.0.1:$WS_PORT" --connect-timeout 2 --max-time 5 https://openapi.okx.com/api/v5/public/time >/dev/null 2>&1; ws_to_rest_rc=$?
curl -4 -sS --proxy "http://127.0.0.1:$REST_PORT" --connect-timeout 2 --max-time 5 "$TARGET_URL" >/dev/null 2>&1; rest_to_ws_rc=$?
curl -4 -sS --proxy "http://127.0.0.1:$WS_PORT" --connect-timeout 2 --max-time 5 https://example.com/ >/dev/null 2>&1; non_okx_rc=$?
set -e
test "$ws_to_rest_rc" -ne 0; test "$rest_to_ws_rc" -ne 0; test "$non_okx_rc" -ne 0
systemctl stop "$B_WG"; wait_state "$B_CARRIER" inactive; b_down=$(wait_ws); b_down_group=$(refresh)
systemctl start "$B_CARRIER"; wait_state "$B_WG" active; wait_state "$B_CARRIER" active; b_recovered=$(wait_ws)
systemctl stop "$A_WG"; wait_state "$A_CARRIER" inactive; a_down=$(wait_ws); a_down_group=$(refresh)
systemctl stop "$B_WG"; wait_state "$B_CARRIER" inactive
set +e
curl -4 -sS --proxy "http://127.0.0.1:$WS_PORT" --connect-timeout 2 --max-time 8 -o /dev/null "$TARGET_URL" >/dev/null 2>&1; both_down_rc=$?
set -e
test "$both_down_rc" -ne 0
systemctl start "$A_CARRIER"; wait_state "$A_WG" active; wait_state "$A_CARRIER" active; a_recovered=$(wait_ws)
systemctl start "$B_CARRIER"; wait_state "$B_WG" active; wait_state "$B_CARRIER" active; final=$(wait_ws)
systemctl restart "$EGRESS"; wait_state "$EGRESS" active; post_restart=$(wait_ws)
printf 'ws_initial_http=%s\n' "$initial"
printf '%s\n%s\n' '--- ws group: initial ---' "$initial_group"
printf 'ws_provider_b_down_http=%s\n' "$b_down"
printf '%s\n%s\n' '--- ws group: provider-b down ---' "$b_down_group"
printf 'ws_provider_b_recovered_http=%s\n' "$b_recovered"
printf 'ws_provider_a_down_http=%s\n' "$a_down"
printf '%s\n%s\n' '--- ws group: provider-a down ---' "$a_down_group"
printf 'ws_both_down_rc=%s\n' "$both_down_rc"
printf 'ws_provider_a_recovered_http=%s\n' "$a_recovered"
printf 'ws_final_http=%s\n' "$final"
printf 'ws_post_restart_http=%s\n' "$post_restart"
printf 'ws_to_rest_blocked_rc=%s\nrest_to_ws_blocked_rc=%s\nnon_okx_blocked_rc=%s\n' "$ws_to_rest_rc" "$rest_to_ws_rc" "$non_okx_rc"
echo finance-okx-ws-production-dual-provider-failclosed=PASS
