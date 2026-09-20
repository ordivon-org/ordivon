#!/usr/bin/env bash
set -euo pipefail
A=nv2kwga$$; B=nv2kwgb$$; VA=nv2kwva$$; VB=nv2kwvb$$; WA=nv2kwga0; WB=nv2kwgb0
TMP=$(mktemp -d /tmp/network-e2e-kernel-wg.XXXXXX)
# shellcheck disable=SC2329
# Invoked indirectly by the EXIT trap below.
cleanup(){ ip netns del "$A" >/dev/null 2>&1 || true; ip netns del "$B" >/dev/null 2>&1 || true; rm -rf "$TMP"; }
trap cleanup EXIT
umask 077
wg genkey >"$TMP/a.key"; wg pubkey <"$TMP/a.key" >"$TMP/a.pub"
wg genkey >"$TMP/b.key"; wg pubkey <"$TMP/b.key" >"$TMP/b.pub"
ip netns add "$A"; ip netns add "$B"
ip link add "$VA" type veth peer name "$VB"; ip link set "$VA" netns "$A"; ip link set "$VB" netns "$B"
ip -n "$A" addr add 192.0.2.1/30 dev "$VA"; ip -n "$B" addr add 192.0.2.2/30 dev "$VB"
ip -n "$A" link set lo up; ip -n "$B" link set lo up; ip -n "$A" link set "$VA" up; ip -n "$B" link set "$VB" up
ip netns exec "$A" ip link add "$WA" type wireguard
ip netns exec "$B" ip link add "$WB" type wireguard
ip -n "$A" addr add 10.212.0.1/30 dev "$WA"; ip -n "$B" addr add 10.212.0.2/30 dev "$WB"
ip netns exec "$A" wg set "$WA" listen-port 51930 private-key "$TMP/a.key" peer "$(cat "$TMP/b.pub")" allowed-ips 10.212.0.2/32 endpoint 192.0.2.2:51931 persistent-keepalive 1
ip netns exec "$B" wg set "$WB" listen-port 51931 private-key "$TMP/b.key" peer "$(cat "$TMP/a.pub")" allowed-ips 10.212.0.1/32 endpoint 192.0.2.1:51930 persistent-keepalive 1
ip -n "$A" link set "$WA" up; ip -n "$B" link set "$WB" up
ip netns exec "$A" ping -c 2 -W 2 10.212.0.2 >/dev/null
echo kernel-wireguard-initial=PASS
ip -n "$A" link set "$WA" down
if ip netns exec "$A" ping -c 1 -W 1 10.212.0.2 >/dev/null 2>&1; then echo 'kernel WG failure injection did not fail' >&2; exit 21; fi
echo kernel-wireguard-failure=PASS
ip -n "$A" link set "$WA" up
for _ in $(seq 1 20); do if ip netns exec "$A" ping -c 1 -W 1 10.212.0.2 >/dev/null 2>&1; then echo kernel-wireguard-recovery=PASS; exit 0; fi; sleep .2; done
echo 'kernel WireGuard recovery failed' >&2; exit 22
