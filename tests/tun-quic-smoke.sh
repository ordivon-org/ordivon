#!/usr/bin/env bash
set -euo pipefail
NS=${NS:-nv2-tun-quic-smoke}
UNIT=${UNIT:-network-v2-tun-quic-smoke.service}
CFG=$(mktemp /tmp/network-v2-tun-quic.XXXXXX.json)
TMP=$(mktemp -d /tmp/network-v2-tun-quic.XXXXXX)
cleanup(){
  systemctl stop "$UNIT" >/dev/null 2>&1 || true
  systemctl reset-failed "$UNIT" >/dev/null 2>&1 || true
  ip netns del "$NS" >/dev/null 2>&1 || true
  rm -f "$CFG"
  rm -rf "$TMP"
}
trap cleanup EXIT
cleanup
mkdir -p "$TMP"

test -c /dev/net/tun
ip netns add "$NS"
ip -n "$NS" link set lo up
cat >"$CFG" <<JSON
{
  "log":{"level":"info","timestamp":true},
  "inbounds":[{
    "type":"tun",
    "tag":"isolated-tun",
    "netns":"$NS",
    "interface_name":"nv2tun0",
    "address":["172.31.251.1/30","fdfe:dcba:9877::1/126"],
    "mtu":1400,
    "auto_route":true,
    "auto_redirect":false,
    "strict_route":true,
    "dns_mode":"disabled"
  }],
  "outbounds":[{"type":"direct","tag":"direct"}],
  "route":{"auto_detect_interface":true,"final":"direct"}
}
JSON
sing-box check -c "$CFG"
systemd-run --quiet --unit="$UNIT" --property=Type=simple --property=Restart=no /usr/bin/sing-box run -c "$CFG"

ready=0
for _ in $(seq 1 80); do
  if systemctl is-active --quiet "$UNIT" && \
     ip -n "$NS" link show nv2tun0 2>/dev/null | grep -q 'UP' && \
     ip -n "$NS" route show table 2022 2>/dev/null | grep -q '^default ' && \
     ip -n "$NS" -6 route show table 2022 2>/dev/null | grep -q '^default '; then
    ready=1; break
  fi
  sleep 0.2
done
test "$ready" = 1

# Process/unit state is not functional readiness. Require a real TCP request through
# the isolated TUN before the destructive UDP/QUIC proof.
tcp_ip=$(dig +short example.com A | head -n1)
test -n "$tcp_ip"
tcp=''
for _ in $(seq 1 20); do
  if tcp=$(ip netns exec "$NS" curl --resolve "example.com:443:$tcp_ip" \
      --fail --silent --show-error --connect-timeout 3 --max-time 10 -o "$TMP/tcp" \
      -w 'rc=%{exitcode} http=%{http_code} httpver=%{http_version} bytes=%{size_download} time=%{time_total}' \
      https://example.com/ 2>/dev/null) && grep -qi 'Example Domain' "$TMP/tcp"; then
    break
  fi
  tcp=''
  sleep 0.5
done
test -n "$tcp"

# Cloudflare publishes multiple anycast addresses. A single endpoint can transiently
# reject QUIC, so the acceptance is bounded across the authoritative A set and still
# requires an actual HTTP/3 success through this TUN.
quic=''
quic_ip=''
while IFS= read -r candidate; do
  test -n "$candidate" || continue
  for _ in 1 2 3; do
    if attempt=$(ip netns exec "$NS" curl --http3-only --resolve "cloudflare-quic.com:443:$candidate" \
        --fail --silent --show-error --connect-timeout 4 --max-time 15 -o "$TMP/quic" \
        -w 'rc=%{exitcode} http=%{http_code} httpver=%{http_version} bytes=%{size_download} time=%{time_total}' \
        https://cloudflare-quic.com/ 2>/dev/null); then
      version=$(awk '{for(i=1;i<=NF;i++) if($i ~ /^httpver=/){sub(/^httpver=/,"",$i); print $i}}' <<<"$attempt")
      if [ "$version" = 3 ]; then quic=$attempt; quic_ip=$candidate; break 2; fi
    fi
    sleep 0.5
  done
done < <(dig +short cloudflare-quic.com A)
test -n "$quic"
printf 'quic_endpoint=%s\n' "$quic_ip"

rx=$(ip -s -n "$NS" link show nv2tun0 | awk '/RX:/{getline; print $2}')
tx=$(ip -s -n "$NS" link show nv2tun0 | awk '/TX:/{getline; print $2}')
test "$rx" -gt 0; test "$tx" -gt 0
printf 'quic_over_isolated_tun %s\n' "$quic"
printf 'tcp_over_isolated_tun %s\n' "$tcp"
printf 'tun_rx_packets=%s tun_tx_packets=%s\n' "$rx" "$tx"
echo isolated-tun-udp-quic=PASS
