#!/usr/bin/env bash
# Exact bounded one-session M3B canary. --preflight is no-effect.
# --execute enters a short provider maintenance blackout, tests the candidate,
# ALWAYS tears it down, and restores the legacy realization plus consumers.
set -euo pipefail
if test "$#" -gt 0; then MODE=$1; else MODE=--preflight; fi
case "$MODE" in --preflight|--execute) ;; *) echo "usage: $0 [--preflight|--execute]" >&2; exit 64;; esac

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
REPO=$(git -C "$ROOT" rev-parse --show-toplevel)
SOURCE_HEAD=$(git -C "$REPO" rev-parse HEAD)
git -C "$REPO" diff --quiet
git -C "$REPO" diff --cached --quiet
SCRIPT_SHA=$(sha256sum "$0" | awk '{print $1}')
MAX_SECONDS=150
NS=nv2-browserless-prod
WG=network-v2-browserless-wireguard.service
DNS=network-v2-browserless-dns.service
CARRIER=network-v2-browserless-provider-carrier.service
TARGET=network-v2-browserless.target
PROFILE=/etc/network-v2/browserless/nv2blwg.conf
PROVIDER_ENV=/etc/network-v2/browserless/provider.env
WORKER=ordivon-agent-temporal-worker.service
MCP=ordivon-agent-automation-mcp.service
TEMPORAL=/opt/ordivon/external/temporal-cli/1.8.3/temporal
LOCK="$ROOT/capabilities/gluetun/external/gluetun-image.lock"
CANDIDATE_ENV="$ROOT/capabilities/gluetun/config/serialized-candidate.env"
ADAPTER="$ROOT/consumers/browserless/config/provider-carrier-gluetun-candidate.json"
CONSEQUENCE="$ROOT/capabilities/gluetun/acceptance/candidate-consequence.sh"
LEGACY_READY="$ROOT/consumers/browserless/provider-carrier-ready.sh"
LEGACY_PATH="$ROOT/consumers/browserless/acceptance/production-path.sh"
NET=network-v2-gluetun-private-r1
CTR=network-v2-gluetun-serialized-candidate
HOST_IP=10.252.246.1
HOST_PORT=19682
CANDIDATE_IP=10.253.239.2
NET_CIDR=10.253.239.0/30
GATEWAY=10.253.239.1

digest=$(awk -F= '$1=="amd64Digest"{print $2}' "$LOCK")
test "$digest" = sha256:1baa76576dea1dfbafbd62bb635daf40fd87171f63273c2fdfe630418783011e
image="docker.io/qmcgaw/gluetun@$digest"
for file in "$PROFILE" "$PROVIDER_ENV" "$CANDIDATE_ENV" "$ADAPTER"; do test -f "$file"; done
test -x "$CONSEQUENCE"
podman image exists "$image"
/usr/bin/sing-box check -c "$ADAPTER"
test -e "/run/netns/$NS"
test "$(ip -4 -o addr show nv2blph | awk '{print $4}')" = 10.252.246.1/30
for unit in network-v2-browserless-netns.service network-v2-browserless-forward.service "$WG" "$DNS" "$CARRIER" "$TARGET"; do systemctl is-active --quiet "$unit"; done
if podman container exists "$CTR"; then echo "candidate container already exists" >&2; exit 41; fi
if podman network exists "$NET"; then echo "candidate network already exists" >&2; exit 42; fi
if ss -ltn "( sport = :$HOST_PORT )" | grep -q LISTEN; then echo "candidate host port occupied" >&2; exit 43; fi

running=0
if test -x "$TEMPORAL"; then
  tmp_workflows=$(mktemp)
  "$TEMPORAL" workflow list --address 127.0.0.1:17233 --namespace default --query 'ExecutionStatus="Running" AND TaskQueue="ordivon-agent-automation"' --limit 100 --output json >"$tmp_workflows"
  running=$(jq 'length' "$tmp_workflows")
  rm -f "$tmp_workflows"
fi
test "$running" -eq 0
established=$(ss -H -tn state established | awk '$4 ~ /:19680$/ || $5 ~ /:19680$/ {n++} END{print n+0}')
test "$established" -eq 0

# Reverse dependencies are the canonical network-level blackout surface.
# Any active service in this graph is stopped for the candidate window and
# restored exactly if it had been active. Core carrier is handled separately.
reverse_services=$(systemctl list-dependencies --reverse "$CARRIER" --plain --no-pager   | awk '{$1=$1} /^[^ ]+\.service$/ {print $1}' | sort -u)
active_consumers=()
active_count=0
for unit in $reverse_services; do
  test "$unit" = "$CARRIER" && continue
  if systemctl is-active --quiet "$unit"; then
    active_consumers+=("$unit")
    active_count=$((active_count+1))
  fi
done

ns_inode=$(stat -Lc '%i' "/run/netns/$NS")
profile_sha=$(sha256sum "$PROFILE" | awk '{print $1}')
env_sha=$(sha256sum "$PROVIDER_ENV" | awk '{print $1}')
adapter_sha=$(sha256sum "$ADAPTER" | awk '{print $1}')
candidate_env_sha=$(sha256sum "$CANDIDATE_ENV" | awk '{print $1}')
legacy_endpoint=$(ip netns exec "$NS" wg show nv2blwg endpoints | awk 'NR==1{print $2}')
legacy_handshake=$(ip netns exec "$NS" wg show nv2blwg latest-handshakes | awk 'NR==1{print $2}')
test -n "$legacy_endpoint"
test -n "$legacy_handshake"
test "$legacy_handshake" -gt 0

if test "$MODE" = --preflight; then
  printf '{"schemaVersion":1,"kind":"ordivon.network-v2.m3b-preflight","standing":"READY_FOR_BOUNDED_EFFECT_REVIEW","sourceHead":"%s","canaryScriptSha256":"%s","adapterSha256":"%s","candidateEnvSha256":"%s","imageDigest":"%s","namespaceInode":"%s","legacyEndpoint":"%s","runningAgentWorkflows":0,"establishedCarrierConnections":0,"activeReverseDependencyServices":%s,"profileSha256":"%s","providerEnvSha256":"%s","productionEffect":false}\n'     "$SOURCE_HEAD" "$SCRIPT_SHA" "$adapter_sha" "$candidate_env_sha" "$digest" "$ns_inode" "$legacy_endpoint" "$active_count" "$profile_sha" "$env_sha"
  exit 0
fi

state=$(mktemp -d /run/network-v2-m3b.XXXXXX)
chmod 0700 "$state"
install -m 0600 "$PROFILE" "$state/profile.preimage"
install -m 0600 "$PROVIDER_ENV" "$state/provider.env.preimage"
printf '%s\n' "${active_consumers[@]}" >"$state/active-consumers.txt"

worker_was_active=0
mcp_was_active=0
systemctl is-active --quiet "$WORKER" && worker_was_active=1 || true
systemctl is-active --quiet "$MCP" && mcp_was_active=1 || true
adapter_pid=
watchdog_pid=
network_created=0
restore_failed=0
candidate_pass=0

# Invoked indirectly by EXIT/ERR/INT/TERM traps.
# shellcheck disable=SC2329
restore() {
  rc=$?
  trap - EXIT ERR INT TERM
  set +e
  if test -n "$watchdog_pid"; then kill "$watchdog_pid" >/dev/null 2>&1; wait "$watchdog_pid" >/dev/null 2>&1; fi
  if test -n "$adapter_pid"; then kill "$adapter_pid" >/dev/null 2>&1; wait "$adapter_pid" >/dev/null 2>&1; fi
  podman rm -f "$CTR" >/dev/null 2>&1
  if test "$network_created" = 1; then podman network rm -f "$NET" >/dev/null 2>&1; fi

  current_profile=$(sha256sum "$PROFILE" 2>/dev/null | awk '{print $1}')
  current_env=$(sha256sum "$PROVIDER_ENV" 2>/dev/null | awk '{print $1}')
  if test "$current_profile" != "$profile_sha"; then install -m 0600 "$state/profile.preimage" "$PROFILE"; fi
  if test "$current_env" != "$env_sha"; then install -m 0600 "$state/provider.env.preimage" "$PROVIDER_ENV"; fi

  systemctl start "$WG" || restore_failed=1
  systemctl start "$DNS" || restore_failed=1
  systemctl start "$CARRIER" || restore_failed=1
  systemctl start "$TARGET" || restore_failed=1
  for _ in $(seq 1 120); do
    systemctl is-active --quiet "$WG" && systemctl is-active --quiet "$DNS" && systemctl is-active --quiet "$CARRIER" && break
    sleep 0.25
  done

  if test -f "$state/active-consumers.txt"; then
    while read -r unit; do
      test -z "$unit" && continue
      systemctl start "$unit" || restore_failed=1
    done <"$state/active-consumers.txt"
  fi

  test "$(stat -Lc '%i' "/run/netns/$NS" 2>/dev/null)" = "$ns_inode" || restore_failed=1
  test "$(sha256sum "$PROFILE" 2>/dev/null | awk '{print $1}')" = "$profile_sha" || restore_failed=1
  test "$(sha256sum "$PROVIDER_ENV" 2>/dev/null | awk '{print $1}')" = "$env_sha" || restore_failed=1
  "$LEGACY_READY" >/dev/null 2>&1 || restore_failed=1
  "$LEGACY_PATH" >/dev/null 2>&1 || restore_failed=1
  "$CONSEQUENCE" >/dev/null 2>&1 || restore_failed=1

  test "$worker_was_active" = 1 && systemctl start "$WORKER" >/dev/null 2>&1 || true
  test "$mcp_was_active" = 1 && systemctl start "$MCP" >/dev/null 2>&1 || true
  rm -rf "$state"

  if test "$restore_failed" = 1; then
    echo '{"schemaVersion":1,"kind":"ordivon.network-v2.m3b-canary","standing":"BLOCKED_ROLLBACK"}' >&2
    exit 70
  fi
  if test "$candidate_pass" = 1 && test "$rc" = 0; then
    printf '{"schemaVersion":1,"kind":"ordivon.network-v2.m3b-canary","standing":"CANDIDATE_CONSEQUENCE_PASS_AND_RESTORATION_PASS","sourceHead":"%s","canaryScriptSha256":"%s","imageDigest":"%s","legacyRestored":true,"productionOwnershipTransferred":false}\n' "$SOURCE_HEAD" "$SCRIPT_SHA" "$digest"
    exit 0
  fi
  printf '{"schemaVersion":1,"kind":"ordivon.network-v2.m3b-canary","standing":"CANDIDATE_FAILED_RESTORATION_PASS","legacyRestored":true,"productionOwnershipTransferred":false}\n' >&2
  if test "$rc" -eq 0; then rc=1; fi
  exit "$rc"
}
trap restore EXIT ERR INT TERM
parent_pid=$BASHPID
( sleep "$MAX_SECONDS"; kill -TERM "$parent_pid" >/dev/null 2>&1 || true ) &
watchdog_pid=$!

# Freeze primary orchestration and every currently active canonical carrier
# dependent service before the sole production WireGuard session is stopped.
systemctl stop "$MCP"
systemctl stop "$WORKER"
for unit in "${active_consumers[@]}"; do systemctl stop "$unit"; done

if test -x "$TEMPORAL"; then
  tmp_workflows=$(mktemp)
  "$TEMPORAL" workflow list --address 127.0.0.1:17233 --namespace default --query 'ExecutionStatus="Running" AND TaskQueue="ordivon-agent-automation"' --limit 100 --output json >"$tmp_workflows"
  test "$(jq 'length' "$tmp_workflows")" -eq 0
  rm -f "$tmp_workflows"
fi
test "$(ss -H -tn state established | awk '$4 ~ /:19680$/ || $5 ~ /:19680$/ {n++} END{print n+0}')" -eq 0

systemctl stop "$CARRIER"
systemctl stop "$DNS"
systemctl stop "$WG"
systemctl is-active --quiet "$WG" && false || true
if ip netns exec "$NS" ip link show nv2blwg >/dev/null 2>&1; then echo "legacy WireGuard interface still present" >&2; false; fi

podman network create --driver bridge --subnet "$NET_CIDR" --gateway "$GATEWAY" --opt isolate=strict "$NET" >/dev/null
network_created=1
podman run -d --name "$CTR" --network "$NET" --ip "$CANDIDATE_IP" --cap-add NET_ADMIN --cap-add NET_RAW --device /dev/net/tun -p "$HOST_IP:$HOST_PORT:8888/tcp" --env-file "$CANDIDATE_ENV" -v "$PROFILE:/gluetun/wireguard/wg0.conf:ro" "$image" >/dev/null

for _ in $(seq 1 120); do
  test "$(podman inspect -f '{{.State.Status}}' "$CTR" 2>/dev/null || true)" = running || false
  ss -ltn "( sport = :$HOST_PORT )" | grep -q "$HOST_IP:$HOST_PORT" && break
  sleep 0.25
done
ss -ltn "( sport = :$HOST_PORT )" | grep -q "$HOST_IP:$HOST_PORT"

ip netns exec "$NS" /usr/bin/sing-box run -c "$ADAPTER" >"$state/adapter.stdout" 2>"$state/adapter.stderr" &
adapter_pid=$!
for _ in $(seq 1 100); do
  kill -0 "$adapter_pid" >/dev/null 2>&1 || false
  ip netns exec "$NS" ss -ltn '( sport = :19680 )' | grep -q '10.252.246.2:19680' && break
  sleep 0.2
done
ip netns exec "$NS" ss -ltn '( sport = :19680 )' | grep -q '10.252.246.2:19680'
"$CONSEQUENCE"
candidate_pass=1
exit 0
