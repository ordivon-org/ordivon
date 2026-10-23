#!/usr/bin/env bash
set -euo pipefail
NS=nv2-browserless-prod
PROXY=http://10.252.246.2:19680
ENV_FILE=/etc/network-v2/browserless/provider.env
MANIFEST=/etc/network-v2/providers/catalog-profiles/MANIFEST.tsv
for u in network-v2-browserless.target network-v2-browserless-wireguard.service network-v2-browserless-dns.service network-v2-browserless-provider-carrier.service; do
  systemctl is-active --quiet "$u"
done
ip netns exec "$NS" ss -ltn | grep -q '10.252.246.2:19680'
site=$(awk -F= '$1=="PROVIDER_SITE"{print $2}' "$ENV_FILE")
endpoint=$(awk -F= '$1=="ENDPOINT"{print $2}' "$ENV_FILE")
test "$site" = th-bkk
expected=$(awk -F '\t' -v site="$site" '$1==site{print $2; exit}' "$MANIFEST")
test -n "$expected"
test "$endpoint" = "$expected"
probe_code() {
  local url=$1 code=000
  for _ in 1 2 3; do
    code=$(curl -4 -x "$PROXY" -I -sS --connect-timeout 6 --max-time 15 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || true)
    test "$code" != 000 && { printf '%s' "$code"; return 0; }
    sleep 1
  done
  return 1
}
openai=$(probe_code https://api.openai.com/v1/models)
registry=$(probe_code https://registry-1.docker.io/v2/)
anthropic=$(probe_code https://api.anthropic.com/)
okx_json=$(mktemp)
trap 'rm -f "$okx_json"' EXIT
for _ in 1 2 3; do
  curl -4 -fsS -x "$PROXY" --connect-timeout 6 --max-time 15 https://openapi.okx.com/api/v5/public/time -o "$okx_json" 2>/dev/null || true
  jq -e '.code=="0" and (.data|type)=="array" and (.data|length>=1)' "$okx_json" >/dev/null 2>&1 && break
  sleep 1
done
jq -e '.code=="0" and (.data|type)=="array" and (.data|length>=1)' "$okx_json" >/dev/null
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.shared-provider-readiness","standing":"READY","providerSite":"%s","endpoint":"%s","openaiHttp":%s,"registryHttp":%s,"anthropicHttp":%s,"okx":"PASS"}\n' "$site" "$endpoint" "$openai" "$registry" "$anthropic"
