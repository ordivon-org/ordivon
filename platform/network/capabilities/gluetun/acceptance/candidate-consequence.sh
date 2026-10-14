#!/usr/bin/env bash
set -euo pipefail
if test "$#" -gt 0; then PROXY=$1; else PROXY=http://10.252.246.2:19680; fi

head_code() {
  local url=$1 code
  code=$(curl -4 -x "$PROXY" -I -sS --connect-timeout 6 --max-time 15 -o /dev/null -w '%{http_code}' "$url")
  test "$code" != 000
  printf '%s' "$code"
}
openai=$(head_code https://api.openai.com/v1/models)
anthropic=$(head_code https://api.anthropic.com/)
registry=$(head_code https://registry-1.docker.io/v2/)
deepseek=$(head_code https://api.deepseek.com/)
xapi=$(head_code https://api.x.com/)
okx_file=$(mktemp)
binance_file=$(mktemp)
trap 'rm -f "$okx_file" "$binance_file"' EXIT
curl -4 -fsS -x "$PROXY" --connect-timeout 6 --max-time 15 https://openapi.okx.com/api/v5/public/time -o "$okx_file"
jq -e '.code=="0" and (.data|type)=="array" and (.data|length>=1)' "$okx_file" >/dev/null
curl -4 -fsS -x "$PROXY" --connect-timeout 6 --max-time 15 https://data-api.binance.vision/api/v3/time -o "$binance_file"
jq -e '(.serverTime|type)=="number"' "$binance_file" >/dev/null
set +e
curl -4 -x "$PROXY" -fsS --connect-timeout 2 --max-time 5 http://127.0.0.1:9/ >/dev/null 2>&1
private_rc=$?
set -e
test "$private_rc" -ne 0
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.provider-carrier-candidate-consequence","standing":"PASS","proxy":"%s","openaiHttp":%s,"anthropicHttp":%s,"registryHttp":%s,"deepseekHttp":%s,"xHttp":%s,"okx":"PASS","binance":"PASS","privateDestination":"REJECTED","mechanismNeutral":true}\n' "$PROXY" "$openai" "$anthropic" "$registry" "$deepseek" "$xapi"
