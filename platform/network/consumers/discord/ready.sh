#!/usr/bin/env bash
set -euo pipefail

target=network-v2-discord.target
service=network-v2-discord-egress.service
proxy=http://127.0.0.1:19981

for _ in $(seq 1 120); do
  if systemctl is-active --quiet "$target" \
    && systemctl is-active --quiet "$service" \
    && ss -ltn '( sport = :19981 )' | grep -q '127.0.0.1:19981'; then
    break
  fi
  sleep 0.25
done

systemctl is-active --quiet "$target"
systemctl is-active --quiet "$service"
ss -ltn '( sport = :19981 )' | grep -q '127.0.0.1:19981'

gateway=$(curl -q --noproxy '' -4 -sS --proxy "$proxy" \
  --connect-timeout 6 --max-time 15 \
  https://discord.com/api/v10/gateway)
gateway_url=$(printf '%s' "$gateway" | jq -r '.url // empty')
test "$gateway_url" = "wss://gateway.discord.gg"

# Reuse libcurl's native WSS/HTTP CONNECT/TLS implementation. Discovery alone
# does not prove a usable Gateway; opcode 10 Hello is required by Discord.
# A healthy *open* WebSocket normally reaches curl's bounded timeout (28).
ws_receipt_dir=$(mktemp -d -t network-v2-discord-wss-XXXXXX)
trap 'rm -rf -- "$ws_receipt_dir"' EXIT
set +e
ws_status=$(curl -q --noproxy '' -4 --http1.1 --proxy "$proxy" \
  --connect-timeout 4 --max-time 8 --max-filesize 4096 \
  --silent --show-error -D "$ws_receipt_dir/headers" \
  -o "$ws_receipt_dir/hello.json" \
  -w '%{http_code} %{http_connect}' \
  'wss://gateway.discord.gg/?v=10&encoding=json' 2>/dev/null)
ws_exit=$?
set -e
# 28 means a correctly upgraded persistent Gateway remains open until the
# bounded deadline. No other exit statuses are accepted as readiness.
test "$ws_exit" -eq 0 || test "$ws_exit" -eq 28
test "$ws_status" = '101 200'
jq -e '(.op == 10) and (.d.heartbeat_interval | type == "number" and . > 0)' \
  "$ws_receipt_dir/hello.json" >/dev/null

set +e
curl -q --noproxy '' -4 -sS -o /dev/null --proxy "$proxy" \
  --connect-timeout 2 --max-time 5 https://example.com/ >/dev/null 2>&1
unknown_rc=$?
set -e
test "$unknown_rc" -ne 0

printf '%s\n' '{"schemaVersion":1,"kind":"ordivon.network-v2.discord-readiness","standing":"READY","proxy":"http://127.0.0.1:19981","gatewayDiscovery":"PASS","gatewayHost":"gateway.discord.gg","gatewayHello":"PASS","unknownDestination":"REJECTED","directFallback":false,"credentialMaterialized":false}'
