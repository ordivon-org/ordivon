#!/usr/bin/env bash
set -euo pipefail

UNIT=network-v2-provider-carrier-smoke.service
PORT=28181
CFG=$(mktemp /tmp/network-v2-provider-carrier.XXXXXX.json)

cleanup() {
  systemctl stop "$UNIT" >/dev/null 2>&1 || true
  systemctl reset-failed "$UNIT" >/dev/null 2>&1 || true
  rm -f "$CFG"
}
trap cleanup EXIT
cleanup

namespace=''
default_dev=''
ingress_ip=''

# Treat provider namespaces as external substrate. Discovery is based only on
# standard Linux namespace/routing state plus WireGuard's own control tool.
for candidate in $(ip netns list | awk '{print $1}'); do
  dev=$(ip netns exec "$candidate" sh -c \
    "ip -4 route show default | awk 'NR==1{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}'" \
    2>/dev/null || true)
  [ -n "$dev" ] || continue
  ip netns exec "$candidate" wg show "$dev" >/dev/null 2>&1 || continue
  side_ip=$(ip netns exec "$candidate" sh -c \
    "ip -4 -o addr show scope global | awk -v d='$dev' '\$2!=d {split(\$4,a,\"/\"); print a[1]; exit}'" \
    2>/dev/null || true)
  [ -n "$side_ip" ] || continue
  root_route=$(ip -4 route get "$side_ip" 2>/dev/null | head -n 1 || true)
  [ -n "$root_route" ] || continue
  printf '%s\n' "$root_route" | grep -q ' dev ' || continue
  if printf '%s\n' "$root_route" | grep -q ' via '; then
    continue
  fi
  namespace=$candidate
  default_dev=$dev
  ingress_ip=$side_ip
  break
done

[ -n "$namespace" ] || { echo 'no externally managed WireGuard provider namespace is observable' >&2; exit 2; }

# DNS egress must be relation-relative: the chosen resolver addresses must route
# through the provider default device inside the same namespace.
for resolver in 1.1.1.1 8.8.8.8; do
  route=$(ip netns exec "$namespace" ip -4 route get "$resolver")
  printf '%s\n' "$route" | grep -q " dev $default_dev "
done
ip netns exec "$namespace" dig @1.1.1.1 example.com A +time=3 +tries=1 +short | grep -Eq '^[0-9]+\.'

cat >"$CFG" <<'EOF'
{
  "log": {"level": "warn", "timestamp": true},
  "dns": {
    "servers": [{"type": "udp", "tag": "provider-dns", "server": "1.1.1.1", "server_port": 53}],
    "final": "provider-dns",
    "strategy": "ipv4_only"
  },
  "inbounds": [{"type": "mixed", "tag": "provider-in", "listen": "0.0.0.0", "listen_port": 28181}],
  "outbounds": [{"type": "direct", "tag": "direct"}],
  "route": {
    "rules": [
      {"ip_is_private": true, "action": "reject"},
      {"ip_version": 6, "action": "reject"}
    ],
    "final": "direct"
  }
}
EOF

sing-box check -c "$CFG"
systemd-run --quiet --unit="$UNIT" --property=Type=simple --property=Restart=no \
  /usr/bin/ip netns exec "$namespace" /usr/bin/sing-box run -c "$CFG"
for _ in $(seq 1 50); do
  ip netns exec "$namespace" ss -ltn 2>/dev/null | grep -q ":$PORT " && break
  sleep 0.1
done
ip netns exec "$namespace" ss -ltn | grep -q ":$PORT "

direct_ip=''
provider_ip=''
probe_url=''
for candidate_url in \
  https://ifconfig.me/ip \
  https://api.ipify.org \
  https://icanhazip.com \
  https://checkip.amazonaws.com; do
  direct=$(curl -4 -fsS --connect-timeout 3 --max-time 8 "$candidate_url" 2>/dev/null | tr -d '[:space:]' || true)
  provider=$(curl -4 -fsS --proxy "http://$ingress_ip:$PORT" --connect-timeout 3 --max-time 8 "$candidate_url" 2>/dev/null | tr -d '[:space:]' || true)
  if [ -n "$direct" ] && [ -n "$provider" ] && [ "$direct" != "$provider" ]; then
    direct_ip=$direct
    provider_ip=$provider
    probe_url=$candidate_url
    break
  fi
done

[ -n "$probe_url" ] || { echo 'no bounded public identity probe proved distinct direct/provider egress' >&2; exit 3; }
curl -fsS --proxy "http://$ingress_ip:$PORT" --connect-timeout 5 --max-time 15 -o /dev/null https://example.com/

printf 'namespace=%s\ndefault_dev=%s\nprobe_url=%s\ndirect_egress=%s\nprovider_egress=%s\n' \
  "$namespace" "$default_dev" "$probe_url" "$direct_ip" "$provider_ip"
echo provider-singbox-carrier-smoke=PASS
