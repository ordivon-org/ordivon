#!/usr/bin/env bash
set -euo pipefail
A=nv2-client
R=nv2-router
T=nv2-target
cleanup(){ ip netns del "$A" 2>/dev/null || true; ip netns del "$R" 2>/dev/null || true; ip netns del "$T" 2>/dev/null || true; }
trap cleanup EXIT
cleanup
ip netns add "$A"; ip netns add "$R"; ip netns add "$T"
ip link add nv2-a type veth peer name nv2-r1
ip link add nv2-r2 type veth peer name nv2-t
ip link set nv2-a netns "$A"; ip link set nv2-r1 netns "$R"; ip link set nv2-r2 netns "$R"; ip link set nv2-t netns "$T"
ip -n "$A" addr add 10.241.1.2/24 dev nv2-a; ip -n "$R" addr add 10.241.1.1/24 dev nv2-r1
ip -n "$R" addr add 10.241.2.1/24 dev nv2-r2; ip -n "$T" addr add 10.241.2.2/24 dev nv2-t
for ns in "$A" "$R" "$T"; do ip -n "$ns" link set lo up; done
ip -n "$A" link set nv2-a up; ip -n "$R" link set nv2-r1 up; ip -n "$R" link set nv2-r2 up; ip -n "$T" link set nv2-t up
ip -n "$A" route add 10.241.2.0/24 via 10.241.1.1
ip -n "$T" route add 10.241.1.0/24 via 10.241.2.1
ip netns exec "$R" sysctl -q -w net.ipv4.ip_forward=1
ip netns exec "$A" ping -c 2 -W 1 10.241.2.2 >/dev/null
ip netns exec "$T" iperf3 -s -1 -D
sleep 0.2
ip netns exec "$A" iperf3 -c 10.241.2.2 -t 1 -J | jq -e '.end.sum_received.bits_per_second > 0' >/dev/null
echo netns-smoke=PASS
