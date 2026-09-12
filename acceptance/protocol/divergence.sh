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

identity=''
for i in $(seq 1 5); do
  ip=$(curl --fail --silent --show-error --proxy "$PROXY" --connect-timeout 4 --max-time 12 https://ifconfig.co/ip | tr -d '\r\n')
  test -n "$ip"
  if [ -z "$identity" ]; then identity=$ip; else test "$ip" = "$identity"; fi
done
printf 'stable_egress_identity=%s\n' "$identity"

for i in 1 2 3; do
  meta=$(curl --fail --silent --show-error --proxy "$PROXY" --connect-timeout 5 --max-time 45 \
    -o "$TMP/5m.$i" -w 'rc=%{exitcode} http=%{http_code} bytes=%{size_download} speed=%{speed_download} time=%{time_total}' \
    'https://speed.cloudflare.com/__down?bytes=5000000')
  test "$(stat -c %s "$TMP/5m.$i")" -eq 5000000
  printf 'longflow_%s %s\n' "$i" "$meta"
done

echo protocol-divergence-smoke=PASS
