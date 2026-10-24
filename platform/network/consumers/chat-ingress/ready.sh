#!/usr/bin/env bash
set -euo pipefail
target=network-v2-chat-ingress.target
proxy=network-v2-chat-ingress-proxy.service
relay=network-v2-chat-ingress-relay.service
systemctl is-active --quiet "$target"
systemctl is-active --quiet "$proxy"
systemctl is-active --quiet "$relay"
ss -ltn '( sport = :19081 )' | grep -q '127.0.0.1:19081'
# One typed observation for this actual HTTPS consumer. HTTP status alone
# cannot prove that the declared proxy established a CONNECT tunnel; inherited
# curlrc/NO_PROXY must not create a silently different network path.
receipt=$(curl -q -4 --noproxy '' --proxy http://127.0.0.1:19081 \
  -I -sS --connect-timeout 5 --max-time 12 -o /dev/null \
  -w '%{http_code} %{http_connect}' https://chatgpt.com/)
read -r code connect extra <<< "$receipt"
# Anonymous access challenges prove only transport, never credentials/session.
[[ "$connect" == 200 && -z "$extra" ]] || { echo 'chat-ingress CONNECT proof failed' >&2; exit 1; }
[[ "$code" =~ ^(2[0-9]{2}|3[0-9]{2}|400|401|403|404|405)$ ]] || {
  echo 'chat-ingress origin response invalid' >&2
  exit 1
}
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.chat-ingress-readiness","standing":"READY","httpStatus":%s,"connectStatus":%s,"proxy":"http://127.0.0.1:19081","providerEffectAttempted":false}\n' "$code" "$connect"
