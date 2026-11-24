#!/usr/bin/env bash
set -euo pipefail
target=network-v2-x-reality.target
egress=network-v2-x-reality-egress.service
proxy=http://127.0.0.1:19681
for _ in $(seq 1 120); do
  if systemctl is-active --quiet "$target" \
    && systemctl is-active --quiet "$egress" \
    && ss -ltn '( sport = :19681 )' | grep -q '127.0.0.1:19681'; then
    break
  fi
  sleep .25
done
systemctl is-active --quiet "$target"
systemctl is-active --quiet "$egress"
ss -ltn '( sport = :19681 )' | grep -q '127.0.0.1:19681'
code=000
connect=000
extra=
for _ in 1 2 3; do
  receipt=$(curl -q -4 --noproxy '' -sS -o /dev/null     -w '%{http_code} %{http_connect}' --proxy "$proxy"     --connect-timeout 5 --max-time 15     https://api.x.com/2/users/me 2>/dev/null) || receipt=
  read -r code connect extra <<< "$receipt"
  [[ "$code" == 401 && "$connect" == 200 && -z "$extra" ]] && break
  sleep 1
done
[[ "$code" == 401 && "$connect" == 200 && -z "$extra" ]]
open_receipt=$(curl -q -4 --noproxy '' -sS -I -o /dev/null   --proxy "$proxy" --connect-timeout 4 --max-time 12   -w '%{http_code} %{http_connect} %{time_appconnect}' https://example.com/)
read -r open_http open_connect open_tls extra <<< "$open_receipt"
[[ "$open_http" =~ ^2[0-9]{2}$ && "$open_connect" == 200 && -z "$extra" ]]
awk -v tls="$open_tls" 'BEGIN{exit !(tls > 0)}'

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.x-reality-readiness","standing":"READY","proxy":"%s","xHttpStatus":%s,"unknownDestination":"ORIGIN_PROVED","directFallback":false,"authenticationAttempted":false,"credentialMaterialized":false,"userContextProven":false}\n' "$proxy" "$code"
