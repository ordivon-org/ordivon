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

# The proxy policy is the network boundary, not proof the already-running
# Windows Codex process consumed ~/.codex/.env (loaded on process startup).
# Require an HTTPS handshake, admitted CONNECT, and origin response for each
# concrete Codex transport dependency.
https_probe() {
  local url=$1 allow_not_found=$2 receipt code tunnel tls extra
  receipt=$(curl -q -4 --noproxy "" -x "$proxy" -I -sS \
    --connect-timeout 5 --max-time 15 -o /dev/null \
    -w '%{http_code} %{http_connect} %{time_appconnect}' "$url") || return 1
  read -r code tunnel tls extra <<< "$receipt" || return 1
  test -z "$extra" || return 1
  test "$tunnel" = 200 || return 1
  [[ "$tls" =~ ^[0-9]+([.][0-9]+)?$ ]] || return 1
  awk -v value="$tls" 'BEGIN { exit !(value > 0) }' || return 1
  if [ "$allow_not_found" = yes ]; then
    [[ "$code" =~ ^(2[0-9][0-9]|3[0-9][0-9]|400|403|404|405)$ ]] || return 1
  else
    [[ "$code" =~ ^(2[0-9][0-9]|3[0-9][0-9])$ ]] || return 1
  fi
  printf '%s\n' "$code"
}

chatgpt_code=$(https_probe https://chatgpt.com/ no) || exit 21
assets_code=$(https_probe https://persistent.oaistatic.com/ yes) || exit 22

# A formerly unknown public HTTPS origin now has to reach a real origin over
# the SAME provider tunnel; CONNECT=200 without TLS is not accepted.
open_code=$(https_probe https://example.com/ no) || exit 23

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.codex-readiness","standing":"READY","chatgptHttp":%s,"cdnHttp":%s,"proxy":"%s","unknownDestination":"ORIGIN_PROVED","openHttp":%s,"applicationProcessEgress":"UNKNOWN","directFallback":false,"providerEffectAttempted":false}\n' \
  "$chatgpt_code" "$assets_code" "$proxy" "$open_code"
