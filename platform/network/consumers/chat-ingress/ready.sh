#!/usr/bin/env bash
set -euo pipefail
target=network-v2-chat-ingress.target
proxy=network-v2-chat-ingress-proxy.service
relay=network-v2-chat-ingress-relay.service
systemctl is-active --quiet "$target"
systemctl is-active --quiet "$proxy"
systemctl is-active --quiet "$relay"
ss -ltn '( sport = :19081 )' | grep -q '127.0.0.1:19081'
code=$(curl -x http://127.0.0.1:19081 -I -sS --max-time 12 -o /dev/null -w '%{http_code}' https://chatgpt.com/)
test "$code" != 000
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.chat-ingress-readiness","standing":"READY","httpStatus":%s,"proxy":"http://127.0.0.1:19081","providerEffectAttempted":false}\n' "$code"
