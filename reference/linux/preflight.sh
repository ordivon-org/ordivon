#!/usr/bin/env bash
set -euo pipefail
if [ "$(uname -s)" != Linux ]; then echo 'requires Linux' >&2; exit 2; fi
if grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then echo 'reference runner must not be WSL' >&2; exit 3; fi
for x in ip tc wg docker containerlab; do command -v "$x" >/dev/null || { echo "missing: $x" >&2; exit 4; }; done
docker info >/dev/null

NS=nv2-ref-preflight-$$
V0=nv2rpf0$$
V1=nv2rpf1$$
WG=nv2rpwg$$
cleanup(){ ip netns del "$NS" >/dev/null 2>&1 || true; ip link del "$V0" >/dev/null 2>&1 || true; ip link del "$WG" >/dev/null 2>&1 || true; }
trap cleanup EXIT
ip netns add "$NS"
ip link add "$V0" type veth peer name "$V1"
ip link set "$V1" netns "$NS"
tc qdisc add dev "$V0" root netem delay 1ms
TC=$(tc qdisc show dev "$V0")
grep -q 'netem' <<<"$TC"
ip link add "$WG" type wireguard
ip link show "$WG" >/dev/null
echo reference-linux-preflight=PASS
