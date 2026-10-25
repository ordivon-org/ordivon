#!/usr/bin/env bash
set -euo pipefail
target=network-v2-supply-chain.target
svc=network-v2-supply-chain-egress.service
proxy=http://127.0.0.1:19581
readiness_deadline=$((SECONDS + 90))
wait_local_ready() {
  for _ in $(seq 1 120); do
    ((SECONDS < readiness_deadline)) || break
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
  local url=$1 allowed=$2 code=000 tunnel=000 response="" extra="" remaining max_time
  for _ in 1 2 3; do
    remaining=$((readiness_deadline - SECONDS))
    ((remaining > 0)) || break
    max_time=$((remaining < 20 ? remaining : 20))
    # A permitted origin HTTP status does not prove the proxy established
    # its HTTPS CONNECT tunnel. Consume curl's standard two-stage result.
    # Explicit --noproxy "" prevents inherited NO_PROXY from bypassing policy.
    # Use GET: auth.docker.io and Artifact Registry legitimately reject HEAD.
    response=$(curl -q -4 --noproxy "" -x "$proxy" -sS --connect-timeout 8 --max-time "$max_time" -o /dev/null -w '%{http_code} %{http_connect}' "$url") || response=""
    code=000 tunnel=000 extra=""
    read -r code tunnel extra <<< "$response"
    if [[ "$code" =~ ^($allowed)$ && "$tunnel" == 200 && -z "$extra" ]]; then
      printf '%s' "$code"
      return 0
    fi
    ((SECONDS < readiness_deadline)) || break
    sleep 1
  done
  echo "Supply-Chain required provider endpoint rejected response: $url (http=$code CONNECT=$tunnel)" >&2
  return 1
}
registry_code=$(probe https://registry-1.docker.io/v2/ '200|401')
auth_code=$(probe 'https://auth.docker.io/token?service=registry.docker.io&scope=repository:openpolicyagent/opa:pull' '200')
gcr_code=$(probe https://gcr.io/v2/ '200|401')
artifact_code=$(probe https://us-central1-docker.pkg.dev/v2/ '200|401')
elastic_code=$(probe https://docker.elastic.co/v2/ '200|401')
remaining=$((readiness_deadline - SECONDS))
((remaining > 0)) || { echo 'Supply-Chain readiness total deadline expired' >&2; exit 1; }
max_time=$((remaining < 8 ? remaining : 8))
# A failed curl transport is not proof that the Network allowlist rejected
# this destination. Demand the HTTP proxy's explicit CONNECT=403 policy denial;
# CONNECT=000 (DNS/TLS/proxy outage), 407 (proxy auth), and CONNECT=200
# (origin reachable, even with an application 403) are all insufficient.
# Do not apply curl --fail: the denial must be parsed from the same attempt.
deny_receipt=$(curl -q -4 --noproxy "" -x "$proxy" -I -sS \
  --connect-timeout 4 --max-time "$max_time" -o /dev/null \
  -w '%{http_code} %{http_connect}' https://example.com/ 2>/dev/null) || deny_receipt="${deny_receipt:-}"
read -r deny_code deny_connect deny_extra <<< "$deny_receipt"
if [[ "$deny_connect" != 403 || -n "$deny_extra" ]]; then
  echo "ERROR: unknown Supply-Chain destination lacks explicit CONNECT denial (http=${deny_code:-000} CONNECT=${deny_connect:-000})" >&2
  exit 41
fi
((SECONDS < readiness_deadline)) || { echo 'Supply-Chain readiness total deadline expired' >&2; exit 1; }
printf '{"schemaVersion":1,"kind":"ordivon.network-v2.supply-chain-readiness","standing":"READY","proxy":"%s","registryHttpStatus":%s,"authHttpStatus":%s,"gcrHttpStatus":%s,"artifactRegistryHttpStatus":%s,"elasticHttpStatus":%s,"unknownDestination":"REJECTED","directFallback":false}
' "$proxy" "$registry_code" "$auth_code" "$gcr_code" "$artifact_code" "$elastic_code"
