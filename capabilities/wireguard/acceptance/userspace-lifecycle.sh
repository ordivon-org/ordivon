#!/usr/bin/env bash
set -euo pipefail

WGGO=${WGGO:-/usr/local/libexec/network-v2/wireguard-go}
A=nv2qa
B=nv2qb
IA=nv2qa0
IB=nv2qb0
CA=/tmp/$IA.conf
CB=/tmp/$IB.conf

cleanup() {
  ip netns exec "$A" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick down "$CA" >/dev/null 2>&1 || true
  ip netns exec "$B" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick down "$CB" >/dev/null 2>&1 || true
  ip netns del "$A" >/dev/null 2>&1 || true
  ip netns del "$B" >/dev/null 2>&1 || true
  rm -f "$CA" "$CB" /tmp/nv2qa.key /tmp/nv2qb.key /tmp/nv2qa.pub /tmp/nv2qb.pub
  rm -f /var/run/wireguard/$IA.sock /var/run/wireguard/$IB.sock
}
trap cleanup EXIT
cleanup

test -x "$WGGO"

umask 077
wg genkey >/tmp/nv2qa.key
wg pubkey </tmp/nv2qa.key >/tmp/nv2qa.pub
wg genkey >/tmp/nv2qb.key
wg pubkey </tmp/nv2qb.key >/tmp/nv2qb.pub
KA=$(cat /tmp/nv2qa.key)
KB=$(cat /tmp/nv2qb.key)
PA=$(cat /tmp/nv2qa.pub)
PB=$(cat /tmp/nv2qb.pub)

ip netns add "$A"
ip netns add "$B"
ip link add nv2qva type veth peer name nv2qvb
ip link set nv2qva netns "$A"
ip link set nv2qvb netns "$B"
ip -n "$A" addr add 192.0.2.1/30 dev nv2qva
ip -n "$A" link set lo up
ip -n "$A" link set nv2qva up
ip -n "$B" addr add 192.0.2.2/30 dev nv2qvb
ip -n "$B" link set lo up
ip -n "$B" link set nv2qvb up

cat >"$CA" <<EOF
[Interface]
Address = 10.211.0.1/30
PrivateKey = $KA
ListenPort = 51920

[Peer]
PublicKey = $PB
AllowedIPs = 10.211.0.2/32
Endpoint = 192.0.2.2:51921
PersistentKeepalive = 1
EOF

cat >"$CB" <<EOF
[Interface]
Address = 10.211.0.2/30
PrivateKey = $KB
ListenPort = 51921

[Peer]
PublicKey = $PA
AllowedIPs = 10.211.0.1/32
Endpoint = 192.0.2.1:51920
PersistentKeepalive = 1
EOF

up() {
  local ns=$1 cfg=$2
  ip netns exec "$ns" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick up "$cfg" >/dev/null
}

down() {
  local ns=$1 cfg=$2
  ip netns exec "$ns" env WG_QUICK_USERSPACE_IMPLEMENTATION="$WGGO" wg-quick down "$cfg" >/dev/null
}

up "$A" "$CA"
up "$B" "$CB"
ip netns exec "$A" ping -c 2 -W 2 10.211.0.2 >/dev/null
echo wgquick-initial=PASS

down "$A" "$CA"
if ip netns exec "$A" ping -c 1 -W 1 10.211.0.2 >/dev/null 2>&1; then
  echo 'failure injection did not fail' >&2
  exit 1
fi
echo wgquick-failure=PASS

up "$A" "$CA"
for _ in $(seq 1 20); do
  if ip netns exec "$A" ping -c 1 -W 1 10.211.0.2 >/dev/null 2>&1; then
    echo wgquick-recovery=PASS
    exit 0
  fi
  sleep 0.2
done

echo 'wg-quick recovery failed' >&2
exit 1
