#!/usr/bin/env bash
set -euo pipefail

egress_target=network-v2-claude.target
proxy=network-v2-claude-proxy.service
relay=network-v2-claude-relay.service
client_target=network-v2-claude-client.target
client_netns=network-v2-claude-client-netns.service
client_bridge=network-v2-claude-client-bridge.service
client_proxy=http://10.252.247.1:19482

for unit in "$egress_target" "$proxy" "$relay" "$client_target" "$client_netns" "$client_bridge"; do
  systemctl is-active --quiet "$unit"
done
ss -ltn '( sport = :19481 )' | grep -q '127.0.0.1:19481'
ip netns exec nv2-browserless-prod ss -ltn '( sport = :19482 )' | grep -q '10.252.247.1:19482'

# The Claude client namespace has only the private inter-namespace link. Any direct
# Internet attempt must fail even if a child process ignores proxy environment variables.
test -z "$(ip netns exec nv2-claude-client ip -4 route show default)"
test -z "$(ip netns exec nv2-claude-client ip -6 route show default)"
if ip netns exec nv2-claude-client curl -4 -I -fsS --connect-timeout 2 --max-time 5 https://api.anthropic.com/ >/dev/null 2>&1; then
  echo 'ERROR: isolated Claude client acquired direct Internet reachability' >&2
  exit 40
fi

proxy_head_code() {
  local url=$1 code=000 attempt
  for attempt in 1 2 3; do
    code=$(ip netns exec nv2-claude-client curl -x "$client_proxy" -I -sS --connect-timeout 8 --max-time 20 -o /dev/null -w '%{http_code}' "$url") && {
      test "$code" != 000 && { printf '%s\n' "$code"; return 0; }
    }
    sleep 1
  done
  return 1
}

api_code=$(proxy_head_code https://api.anthropic.com/)

headers=$(mktemp)
trap 'rm -f "$headers"' EXIT
ok=0
for attempt in 1 2 3; do
  if ip netns exec nv2-claude-client curl -x "$client_proxy" -I -sS --connect-timeout 8 --max-time 20 https://claude.ai/install.sh >"$headers" && grep -Eqi '^location: https://downloads\.claude\.ai/' "$headers"; then
    ok=1
    break
  fi
  sleep 1
done
test "$ok" = 1

# Unknown destinations are refused by the Claude egress policy.
if ip netns exec nv2-claude-client curl -x "$client_proxy" -I -fsS --connect-timeout 3 --max-time 8 https://example.com/ >/dev/null 2>&1; then
  echo 'ERROR: unknown destination escaped Claude allowlist' >&2
  exit 41
fi

# The underlying Surfshark namespace itself also has no IPv6 default route.
test -z "$(ip netns exec nv2-browserless-prod ip -6 route show default)"

printf '{"schemaVersion":1,"kind":"ordivon.network-v2.claude-readiness","standing":"READY","apiHttpStatus":%s,"clientProxy":"%s","directInternet":"BLOCKED","unknownDestination":"REJECTED","ipv6DefaultRoute":false,"directFallback":false}\n' "$api_code" "$client_proxy"
