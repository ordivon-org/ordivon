#!/usr/bin/env bash
set -euo pipefail
target=network-v2-supply-chain.target
svc=network-v2-supply-chain-egress.service
proxy=http://127.0.0.1:19581
wait_local_ready() {
  for _ in $(seq 1 120); do
    if systemctl is-active --quiet "$target" \
      && systemctl is-active --quiet "$svc" \
      && ss -ltn '( sport = :19581 )' | grep -q '127.0.0.1:19581'; then
      return 0
    fi
    sleep 0.25
  done
  echo 'ERROR: Supply-Chain local authority did not converge within 30s' >&2
  systemctl show "$target" "$svc" -p Id -p ActiveState -p SubState -p Result --no-pager >&2 || true
  return 42
}
wait_local_ready
probe() {
  local url=$1 code=000
  for _ in 1 2 3; do
    code=$(curl -4 -x "$proxy" -I -sS --connect-timeout 8 --max-time 20 -o /dev/null -w '%{http_code}' "$url") && {
      test "$code" != 000 && { printf '%s' "$code"; return 0; }
    }
    sleep 1
  done
  return 1
}
registry_code=$(probe https://registry-1.docker.io/v2/)
auth_code=$(probe 'https://auth.docker.io/token?service=registry.docker.io&scope=repository:openpolicyagent/opa:pull')
gcr_code=$(probe https://gcr.io/v2/)
artifact_code=$(probe https://us-central1-docker.pkg.dev/v2/)
elastic_code=$(probe https://docker.elastic.co/v2/)
if curl -4 -x "$proxy" -I -fsS --connect-timeout 4 --max-time 8 https://example.com/ >/dev/null 2>&1; then
  echo 'ERROR: unknown destination escaped Supply-Chain allowlist' >&2
  exit 41
fi
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.supply-chain-readiness","standing":"READY","proxy":"%s","registryHttpStatus":%s,"authHttpStatus":%s,"gcrHttpStatus":%s,"artifactRegistryHttpStatus":%s,"elasticHttpStatus":%s,"unknownDestination":"REJECTED","directFallback":false}
' "$proxy" "$registry_code" "$auth_code" "$gcr_code" "$artifact_code" "$elastic_code"
