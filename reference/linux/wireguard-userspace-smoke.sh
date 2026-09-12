#!/usr/bin/env bash
set -euo pipefail

WGGO=${WGGO:-/usr/local/libexec/network-v2/wireguard-go}
A=nv2uwga$$
B=nv2uwgb$$
VA=nv2uva$$
VB=nv2uvb$$
WA=wgua$$
WB=wgub$$
TMP=$(mktemp -d /tmp/network-e2e-userspace-wg.XXXXXX)
PIDA=''
PIDB=''

cleanup() {
  rm -f "/var/run/wireguard/$WA.sock" "/var/run/wireguard/$WB.sock" >/dev/null 2>&1 || true
  [ -z "$PIDA" ] || kill "$PIDA" >/dev/null 2>&1 || true
  [ -z "$PIDB" ] || kill "$PIDB" >/dev/null 2>&1 || true
  [ -z "$PIDA" ] || wait "$PIDA" 2>/dev/null || true
  [ -z "$PIDB" ] || wait "$PIDB" 2>/dev/null || true
  ip netns del "$A" >/dev/null 2>&1 || true
  ip netns del "$B" >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT

[ -x "$WGGO" ]
"$WGGO" --version 2>&1 | grep -F 'wireguard-go v0.0.20250522' >/dev/null

umask 077
wg genkey >"$TMP/a.key"
wg pubkey <"$TMP/a.key" >"$TMP/a.pub"
wg genkey >"$TMP/b.key"
wg pubkey <"$TMP/b.key" >"$TMP/b.pub"

ip netns add "$A"
ip netns add "$B"
ip link add "$VA" type veth peer name "$VB"
ip link set "$VA" netns "$A"
ip link set "$VB" netns "$B"
ip -n "$A" addr add 192.0.2.1/30 dev "$VA"
ip -n "$B" addr add 192.0.2.2/30 dev "$VB"
ip -n "$A" link set lo up
ip -n "$B" link set lo up
ip -n "$A" link set "$VA" up
ip -n "$B" link set "$VB" up

ip netns exec "$A" "$WGGO" -f "$WA" >"$TMP/a.log" 2>&1 &
PIDA=$!
ip netns exec "$B" "$WGGO" -f "$WB" >"$TMP/b.log" 2>&1 &
PIDB=$!

for _ in $(seq 1 50); do
  if ip -n "$A" link show "$WA" >/dev/null 2>&1 && ip -n "$B" link show "$WB" >/dev/null 2>&1 && [ -S "/var/run/wireguard/$WA.sock" ] && [ -S "/var/run/wireguard/$WB.sock" ]; then
    break
  fi
  kill -0 "$PIDA" >/dev/null 2>&1 || { cat "$TMP/a.log" >&2; exit 31; }
  kill -0 "$PIDB" >/dev/null 2>&1 || { cat "$TMP/b.log" >&2; exit 32; }
  sleep .1
done

kill -0 "$PIDA"
kill -0 "$PIDB"
[ -S "/var/run/wireguard/$WA.sock" ]
[ -S "/var/run/wireguard/$WB.sock" ]
ip netns exec "$A" ip -d link show "$WA" | grep -q 'tun type tun'
ip netns exec "$B" ip -d link show "$WB" | grep -q 'tun type tun'
echo userspace-wireguard-implementation=PASS

ip -n "$A" addr add 10.213.0.1/30 dev "$WA"
ip -n "$B" addr add 10.213.0.2/30 dev "$WB"
ip netns exec "$A" wg set "$WA" listen-port 51940 private-key "$TMP/a.key" peer "$(cat "$TMP/b.pub")" allowed-ips 10.213.0.2/32 endpoint 192.0.2.2:51941 persistent-keepalive 1
ip netns exec "$B" wg set "$WB" listen-port 51941 private-key "$TMP/b.key" peer "$(cat "$TMP/a.pub")" allowed-ips 10.213.0.1/32 endpoint 192.0.2.1:51940 persistent-keepalive 1
ip -n "$A" link set "$WA" up
ip -n "$B" link set "$WB" up

ip netns exec "$A" ping -c 2 -W 2 10.213.0.2 >/dev/null
echo userspace-wireguard-initial=PASS

ip -n "$A" link set "$WA" down
if ip netns exec "$A" ping -c 1 -W 1 10.213.0.2 >/dev/null 2>&1; then
  echo 'userspace WireGuard failure injection did not fail' >&2
  exit 33
fi
echo userspace-wireguard-failure=PASS

ip -n "$A" link set "$WA" up
for _ in $(seq 1 20); do
  if ip netns exec "$A" ping -c 1 -W 1 10.213.0.2 >/dev/null 2>&1; then
    echo userspace-wireguard-recovery=PASS
    exit 0
  fi
  sleep .2
done

cat "$TMP/a.log" >&2 || true
cat "$TMP/b.log" >&2 || true
echo 'userspace WireGuard recovery failed' >&2
exit 34
