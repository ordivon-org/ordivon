#!/usr/bin/env bash
set -euo pipefail

network_root=$(cd "$(dirname "$0")/../../.." && pwd)
candidate_source="$network_root/consumers/browserless/config/provider-carrier-gluetun-candidate.json"

NS=nv2-browserless-prod
HOST_IP=10.252.246.1
HOST_PORT=28224
CANDIDATE_PORT=29680

test -e "/run/netns/$NS"
ip -4 addr show nv2blph | grep -F "$HOST_IP/30" >/dev/null
route=$(ip netns exec "$NS" ip -4 route get "$HOST_IP")
printf '%s\n' "$route" | grep -F 'dev nv2blpn' >/dev/null
printf '%s\n' "$route" | grep -F 'via ' >/dev/null && {
  echo "compatibility hop unexpectedly uses a gateway" >&2
  exit 31
} || true

! ss -ltn | grep -F "$HOST_IP:$HOST_PORT" >/dev/null
! ip netns exec "$NS" ss -ltn | grep -F "10.252.246.2:$CANDIDATE_PORT" >/dev/null

tmp=$(mktemp -d /tmp/network-v2-gluetun-hop.XXXXXX)
cleanup() {
  if [ -n "${candidate_pid:-}" ]; then
    kill "$candidate_pid" >/dev/null 2>&1 || true
    wait "$candidate_pid" >/dev/null 2>&1 || true
  fi
  if [ -n "${upstream_pid:-}" ]; then
    kill "$upstream_pid" >/dev/null 2>&1 || true
    wait "$upstream_pid" >/dev/null 2>&1 || true
  fi
  rm -rf "$tmp"
}
trap cleanup EXIT

cat >"$tmp/upstream.json" <<JSON
{
  "log": {"level": "warn"},
  "inbounds": [
    {"type": "http", "tag": "fixture-upstream", "listen": "$HOST_IP", "listen_port": $HOST_PORT}
  ],
  "outbounds": [
    {"type": "direct", "tag": "fixture-direct"}
  ],
  "route": {"final": "fixture-direct"}
}
JSON

jq --argjson inbound "$CANDIDATE_PORT" --argjson upstream "$HOST_PORT" '
  .inbounds[0].listen_port = $inbound
  | .outbounds[0].server_port = $upstream
' "$candidate_source" >"$tmp/candidate.json"

sing-box check -c "$tmp/upstream.json"
sing-box check -c "$tmp/candidate.json"

sing-box run -c "$tmp/upstream.json" >"$tmp/upstream.log" 2>&1 &
upstream_pid=$!
ip netns exec "$NS" sing-box run -c "$tmp/candidate.json" >"$tmp/candidate.log" 2>&1 &
candidate_pid=$!

for _ in $(seq 1 40); do
  if ss -ltn | grep -F "$HOST_IP:$HOST_PORT" >/dev/null &&
     ip netns exec "$NS" ss -ltn | grep -F "10.252.246.2:$CANDIDATE_PORT" >/dev/null; then
    break
  fi
  sleep 0.1
done

ss -ltn | grep -F "$HOST_IP:$HOST_PORT" >/dev/null
ip netns exec "$NS" ss -ltn | grep -F "10.252.246.2:$CANDIDATE_PORT" >/dev/null

curl --fail --silent --show-error   --proxy "http://10.252.246.2:$CANDIDATE_PORT"   --connect-timeout 3 --max-time 10   -o /dev/null https://example.com/

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.gluetun-compatibility-hop","standing":"PASS","namespace":"%s","hostVeth":"%s","consumerSeamPreserved":true,"providerIdentityUsed":false,"productionNetworkMutation":false}\n' "$NS" "$HOST_IP"
