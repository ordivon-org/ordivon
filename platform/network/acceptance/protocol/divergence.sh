#!/usr/bin/env bash
set -euo pipefail
PROXY=${PROXY:-http://127.0.0.1:28080}
DNS_HOST=${DNS_HOST:-127.0.0.1}
DNS_PORT=${DNS_PORT:-25353}
TMP=$(mktemp -d /tmp/network-v2-protocol.XXXXXX)
trap 'rm -rf "$TMP"' EXIT

probe_http(){
  mode=$1; expected=$2
  meta=$(curl "$mode" --fail --silent --show-error --proxy "$PROXY" --connect-timeout 5 --max-time 20 \
    -o "$TMP/http.$expected" -w 'rc=%{exitcode} http=%{http_code} httpver=%{http_version} bytes=%{size_download} time=%{time_total}' https://example.com/)
  grep -qi 'Example Domain' "$TMP/http.$expected"
  actual=$(awk '{for(i=1;i<=NF;i++) if($i ~ /^httpver=/){sub(/^httpver=/,"",$i); print $i}}' <<<"$meta")
  test "$actual" = "$expected"
  printf 'http%s %s\n' "$expected" "$meta"
}
probe_http --http1.1 1.1
probe_http --http2 2

for proto in udp tcp; do
  if [ "$proto" = tcp ]; then extra=+tcp; else extra=; fi
  for q in A AAAA; do
    ans=$(dig $extra +time=3 +tries=1 @"$DNS_HOST" -p "$DNS_PORT" example.com "$q" +short)
    test -n "$ans"
    if [ "$q" = A ]; then grep -Eq '^[0-9]+\.' <<<"$ans"; else grep -q ':' <<<"$ans"; fi
    printf 'dns_%s_%s=PASS\n' "$proto" "${q,,}"
  done
done

# Generic Network only requires an observable valid external egress. Stability of a
# specific public IP is a provider/consumer policy, not a universal direct-network invariant.
ip=$(curl --fail --silent --show-error --proxy "$PROXY" --connect-timeout 4 --max-time 12 https://ifconfig.co/ip | tr -d '\r\n')
test -n "$ip"
python3 - "$ip" <<'PY'
import ipaddress, sys
ipaddress.ip_address(sys.argv[1])
PY
printf 'external_egress_observed=%s\n' "$ip"

echo protocol-divergence-smoke=PASS
