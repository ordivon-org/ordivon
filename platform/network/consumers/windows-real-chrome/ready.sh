#!/usr/bin/env bash
set -euo pipefail
target=network-v2-windows-real-chrome.target
proxy=network-v2-windows-real-chrome-proxy.service
relay=network-v2-windows-real-chrome-relay.service
provider=/usr/local/libexec/network-v2/browserless-provider-carrier-ready
"$provider" >/dev/null
systemctl is-active --quiet "$target"
systemctl is-active --quiet "$proxy"
systemctl is-active --quiet "$relay"
ss -ltn '( sport = :19781 )' | grep -q '127.0.0.1:19781'
example=$(curl -4 -x http://127.0.0.1:19781 -I -sS --connect-timeout 5 --max-time 15 -o /dev/null -w '%{http_code}' https://example.com/)
chatgpt=$(curl -4 -x http://127.0.0.1:19781 -I -sS --connect-timeout 5 --max-time 15 -o /dev/null -w '%{http_code}' https://chatgpt.com/)
test "$example" != 000
test "$chatgpt" != 000
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.windows-real-chrome-readiness","standing":"READY","exampleHttp":%s,"chatgptHttp":%s,"proxy":"http://127.0.0.1:19781","directFallback":false,"providerEffectAttempted":false}\n' "$example" "$chatgpt"
