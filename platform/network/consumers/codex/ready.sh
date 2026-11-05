#!/usr/bin/env bash
set -euo pipefail

target=network-v2-codex.target
proxy_service=network-v2-codex-proxy.service
relay_service=network-v2-codex-relay.service
proxy=http://127.0.0.1:19982

systemctl is-active --quiet "$target"
systemctl is-active --quiet "$proxy_service"
systemctl is-active --quiet "$relay_service"
ss -ltn '( sport = :19982 )' | grep -q '127.0.0.1:19982'

code=$(curl -4 --noproxy "" -x "$proxy" -I -sS   --connect-timeout 5 --max-time 15 -o /dev/null -w '%{http_code}' https://chatgpt.com/)
test "$code" != 000

set +e
curl -4 --noproxy "" -x "$proxy" -I -sS   --connect-timeout 2 --max-time 5 https://example.com/ >/dev/null 2>&1
unknown_rc=$?
set -e
test "$unknown_rc" -ne 0

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.codex-readiness","standing":"READY","chatgptHttp":%s,"proxy":"%s","unknownDestination":"REJECTED","directFallback":false,"providerEffectAttempted":false}\n' "$code" "$proxy"
