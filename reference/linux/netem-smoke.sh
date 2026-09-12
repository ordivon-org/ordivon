#!/usr/bin/env bash
set -euo pipefail
A=nv2-netem-a-$$; B=nv2-netem-b-$$; VA=nv2nema$$; VB=nv2nemb$$
cleanup(){ ip netns del "$A" >/dev/null 2>&1 || true; ip netns del "$B" >/dev/null 2>&1 || true; ip link del "$VA" >/dev/null 2>&1 || true; }
trap cleanup EXIT
ip netns add "$A"; ip netns add "$B"
ip link add "$VA" type veth peer name "$VB"
ip link set "$VA" netns "$A"; ip link set "$VB" netns "$B"
ip -n "$A" addr add 10.253.10.1/30 dev "$VA"; ip -n "$B" addr add 10.253.10.2/30 dev "$VB"
ip -n "$A" link set lo up; ip -n "$B" link set lo up; ip -n "$A" link set "$VA" up; ip -n "$B" link set "$VB" up
ip netns exec "$A" ping -c 1 -W 1 10.253.10.2 >/dev/null
ip netns exec "$A" tc qdisc add dev "$VA" root netem loss 100%
if ip netns exec "$A" ping -c 1 -W 1 10.253.10.2 >/dev/null 2>&1; then echo 'netem loss did not drop packet' >&2; exit 11; fi
ip netns exec "$A" tc qdisc replace dev "$VA" root netem delay 50ms reorder 100% gap 2
q=$(ip netns exec "$A" tc qdisc show dev "$VA")
grep -q 'netem' <<<"$q"; grep -q 'delay 50ms' <<<"$q"; grep -q 'reorder 100%' <<<"$q"
ip netns exec "$A" ping -c 2 -W 2 10.253.10.2 >/dev/null
echo reference-netem=PASS
