#!/usr/bin/env bash
set -euo pipefail

target=network-v2-model-provider.target
service=network-v2-model-provider-egress.service
proxy=http://127.0.0.1:19881

for _ in $(seq 1 120); do
  if systemctl is-active --quiet "$target" \
    && systemctl is-active --quiet "$service" \
    && ss -ltn '( sport = :19881 )' | grep -q '127.0.0.1:19881'; then
    break
  fi
  sleep 0.25
done

systemctl is-active --quiet "$target"
systemctl is-active --quiet "$service"
ss -ltn '( sport = :19881 )' | grep -q '127.0.0.1:19881'

probe() {
  local name=$1 url=$2 code=000
  for _ in 1 2 3; do
    code=$(curl -4 -sS -o /dev/null -w '%{http_code}' \
      --proxy "$proxy" --connect-timeout 6 --max-time 15 "$url" 2>/dev/null || true)
    if [ "$code" != 000 ]; then
      printf '%s=%s\n' "$name" "$code"
      return 0
    fi
    sleep 1
  done
  return 1
}

probe deepseek https://api.deepseek.com/v1/models
probe google https://generativelanguage.googleapis.com/v1beta/models
probe openrouter https://openrouter.ai/api/v1/models
probe cerebras https://api.cerebras.ai/v1/models
probe nvidia https://integrate.api.nvidia.com/v1/models
probe bigmodel https://open.bigmodel.cn/api/paas/v4/models

set +e
curl -4 -sS -o /dev/null --proxy "$proxy" \
  --connect-timeout 2 --max-time 5 https://example.com/ >/dev/null 2>&1
unknown_rc=$?
set -e
[ "$unknown_rc" -ne 0 ]

printf '%s\n' '{"schemaVersion":1,"kind":"ordivon.network-v2.model-provider-readiness","standing":"READY","proxy":"http://127.0.0.1:19881","unknownDestination":"REJECTED","directFallback":false,"credentialMaterialized":false}'
