#!/usr/bin/env bash
set -euo pipefail
NS=nv2-browserless-prod
PROXY=http://10.252.246.2:19680
TARGET=network-v2-browserless.target
LEGACY_WG=network-v2-browserless-wireguard.service
LEGACY_CARRIER=network-v2-browserless-provider-carrier.service
OWNED=network-v2-gluetun-owned.service
OWNED_ADAPTER=network-v2-gluetun-owned-adapter.service

systemctl is-active --quiet "$TARGET"
test -e "/run/netns/$NS"
ip netns exec "$NS" ss -ltn | grep -q '10.252.246.2:19680'

if systemctl is-active --quiet "$OWNED" && systemctl is-active --quiet "$OWNED_ADAPTER"; then
  mechanism=gluetun
elif systemctl is-active --quiet "$LEGACY_WG" && systemctl is-active --quiet "$LEGACY_CARRIER"; then
  mechanism=legacy-wireguard
else
  echo "shared provider carrier has no recognized physical realization" >&2
  exit 41
fi

probe_code() {
  local url=$1 allowed=$2 code=000
  for _ in 1 2 3; do
    code=$(curl -4 --noproxy "" -x "$PROXY" -I -sS --connect-timeout 6 --max-time 15 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || true)
    if [[ "$code" =~ ^($allowed)$ ]]; then printf '%s' "$code"; return 0; fi
    sleep 1
  done
  echo "unexpected provider consequence $code for $url" >&2
  return 1
}
openai=$(probe_code https://api.openai.com/v1/models '401|403')
registry=$(probe_code https://registry-1.docker.io/v2/ '200|401')
anthropic=$(probe_code https://api.anthropic.com/ '401|403|404|405')
okx_json=$(mktemp)
trap 'rm -f "$okx_json"' EXIT
for _ in 1 2 3; do
  curl -4 --noproxy "" -fsS -x "$PROXY" --connect-timeout 6 --max-time 15 https://openapi.okx.com/api/v5/public/time -o "$okx_json" 2>/dev/null || true
  jq -e '.code=="0" and (.data|type)=="array" and (.data|length>=1)' "$okx_json" >/dev/null 2>&1 && break
  sleep 1
done
jq -e '.code=="0" and (.data|type)=="array" and (.data|length>=1)' "$okx_json" >/dev/null
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.shared-provider-readiness","standing":"READY","mechanism":"%s","openaiHttp":%s,"registryHttp":%s,"anthropicHttp":%s,"okx":"PASS","proxy":"%s"}\n' "$mechanism" "$openai" "$registry" "$anthropic" "$PROXY"
