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
# Network readiness verifies only the scoped HTTPS tunnel and origin response.
# Do not let inherited ~/.curlrc, HTTPS_PROXY or NO_PROXY change this path.
probe() {
  local url=$1 response="" code=000 tunnel=000 extra=""
  response=$(curl -q -4 --noproxy "" -x http://127.0.0.1:19781 -I -sS     --connect-timeout 5 --max-time 15 -o /dev/null     -w '%{http_code} %{http_connect}' "$url")
  read -r code tunnel extra <<< "$response"
  # An origin 200/403 without a completed proxy CONNECT is not READY.
  if [[ $tunnel != 200 || -n $extra || ! $code =~ ^(2[0-9]{2}|4[0-9]{2})$     || $code == 407 || $code == 408 || $code == 429 ]]; then
    return 1
  fi
  printf '%s' "$code"
}
example=$(probe https://example.com/)
chatgpt=$(probe https://chatgpt.com/)
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.windows-real-chrome-readiness","standing":"READY","exampleHttp":%s,"chatgptHttp":%s,"proxy":"http://127.0.0.1:19781","directFallback":false,"providerEffectAttempted":false}\n' "$example" "$chatgpt"
