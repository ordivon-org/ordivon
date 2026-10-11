#!/usr/bin/env bash
set -euo pipefail

network_root=$(cd "$(dirname "$0")/../../.." && pwd)
candidate_source="$network_root/consumers/browserless/config/provider-carrier-gluetun-candidate.json"

NS=nv2-browserless-prod
HOST_IP=10.252.246.1
CANDIDATE_PROXY_PORT=19682

test -e "/run/netns/$NS"
ip -4 addr show nv2blph | grep -F "$HOST_IP/30" >/dev/null

route=$(ip netns exec "$NS" ip -4 route get "$HOST_IP")
printf '%s\n' "$route" | grep -F 'dev nv2blpn' >/dev/null
if printf '%s\n' "$route" | grep -F ' via ' >/dev/null; then
  echo "compatibility hop unexpectedly uses a gateway" >&2
  exit 31
fi

if ss -ltn | grep -F "$HOST_IP:$CANDIDATE_PROXY_PORT" >/dev/null; then
  echo "candidate host-veth proxy port is already occupied" >&2
  exit 32
fi

sing-box check -c "$candidate_source"

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.gluetun-compatibility-preflight","standing":"PREFLIGHT_PASS","namespace":"%s","hostVeth":"%s","consumerSeamPreserved":true,"providerIdentityUsed":false,"twoHopExecutionProven":false,"productionNetworkMutation":false}\n' "$NS" "$HOST_IP"
