#!/usr/bin/env bash
set -euo pipefail

target=network-v2-model-provider.target
service=network-v2-model-provider-egress.service
proxy=http://127.0.0.1:19881
# One overall readiness budget across all providers and retry attempts.
# Bash SECONDS is monotonic within this process; do not compound per-target
# request timeouts into multi-minute retry storms under shared carrier failure.
readiness_deadline=$((SECONDS + 90))

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
  local name=$1 url=$2 response="" code=000 tunnel=000 extra="" curl_exit=0 remaining max_time
  for _ in 1 2 3; do
    remaining=$((readiness_deadline - SECONDS))
    ((remaining > 0)) || break
    max_time=$((remaining < 15 ? remaining : 15))
    # Reset each attempt; an earlier HTTP response must not mask a later
    # DNS/connect/TLS failure. Standard libcurl statuses are the transport
    # operator; keep all URL/header/credential content out of diagnostics.
    response="" code=000 tunnel=000 extra=""
    if response=$(curl -q -4 -sS -o /dev/null -w '%{http_code} %{http_connect}' \
      --proxy "$proxy" --noproxy "" \
      --connect-timeout 6 --max-time "$max_time" "$url" 2>/dev/null); then
      curl_exit=0
    else
      curl_exit=$?
    fi
    if [[ -n $response ]]; then
      read -r code tunnel extra <<< "$response"
    fi
    # An origin HTTP 200/401/403 alone does not prove the proxy established
    # a tunnel. Distinguish successful CONNECT from API authentication.
    if [[ $curl_exit == 0 && $tunnel == 200 && -z $extra && $code =~ ^(2[0-9]{2}|401|403)$ ]]; then
      printf '%s=%s\n' "$name" "$code" >&2
      return 0
    fi
    ((SECONDS < readiness_deadline)) || break
    sleep 1
  done
  # Keep the existing fail-closed result, including libcurl's documented exit
  # status so DNS(5/6), connect(7), timeout(28), and TLS(35/60) differ.
  # No request URL, authorization header, or credential is logged.
  printf 'Model Provider %s not ready (last_http=%s CONNECT=%s curl_exit=%s)\n' "$name" "$code" "$tunnel" "$curl_exit" >&2
  return 1
}

probe deepseek https://api.deepseek.com/v1/models
probe google https://generativelanguage.googleapis.com/v1beta/models
probe openrouter https://openrouter.ai/api/v1/models
probe cerebras https://api.cerebras.ai/v1/models
probe nvidia https://integrate.api.nvidia.com/v1/models
probe bigmodel https://open.bigmodel.cn/api/paas/v4/models

set +e
curl -q -4 -sS -o /dev/null --proxy "$proxy" --noproxy "" \
  --connect-timeout 2 --max-time 5 https://example.com/ >/dev/null 2>&1
unknown_rc=$?
set -e
[ "$unknown_rc" -ne 0 ]

printf '%s\n' '{"schemaVersion":1,"kind":"ordivon.network-v2.model-provider-readiness","standing":"READY","proxy":"http://127.0.0.1:19881","unknownDestination":"REJECTED","directFallback":false,"credentialMaterialized":false}'
