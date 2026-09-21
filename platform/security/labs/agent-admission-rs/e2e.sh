#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
image="quay.io/keycloak/keycloak:26.7.4"
container="ordivon-agent-admission-keycloak"
realm="$root/keycloak/realm-agent-admission-lab.json"
db="$root/.agent-admission-lab.sqlite3"
server_log="${TMPDIR:-/tmp}/ordivon-agent-admission-rs.log"
server_pid=""

cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  /usr/bin/podman rm -f "$container" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

printf '%s\n' 'stage=image'
if ! /usr/bin/podman image exists "$image"; then
  set +e
  /usr/bin/timeout 120 /usr/bin/podman pull "$image" >/dev/null
  pull_rc=$?
  set -e
  if ! /usr/bin/podman image exists "$image"; then
    echo "Keycloak image did not materialize (podman pull rc=$pull_rc)" >&2
    exit "${pull_rc:-1}"
  fi
  if [[ "$pull_rc" -ne 0 ]]; then
    echo "podman pull returned rc=$pull_rc after image materialized; continuing from external image truth" >&2
  fi
fi

printf '%s\n' 'stage=keycloak-start'
/usr/bin/podman rm -f "$container" >/dev/null 2>&1 || true
set +e
/usr/bin/timeout 30 /usr/bin/podman run -d \
  --replace \
  --rm \
  --pull=never \
  --name "$container" \
  --network host \
  --mount "type=bind,src=$realm,dst=/opt/keycloak/data/import/realm.json,ro=true" \
  "$image" \
  start-dev \
    --import-realm \
    --http-enabled=true \
    --http-host=127.0.0.1 \
    --http-port=18080 \
    --hostname-strict=false >/dev/null
run_rc=$?
set -e
if [[ "$run_rc" -ne 0 ]]; then
  running=$(/usr/bin/podman inspect "$container" --format '{{.State.Running}}' 2>/dev/null || true)
  if [[ "$running" != "true" ]]; then
    echo "Keycloak container did not reach running state (podman run rc=$run_rc)" >&2
    exit "$run_rc"
  fi
  echo "podman run returned rc=$run_rc after container reached running state; continuing from external container truth" >&2
fi

issuer="http://127.0.0.1:18080/realms/agent-admission-lab"
printf '%s\n' 'stage=keycloak-ready'
for _ in $(seq 1 160); do
  if /usr/bin/curl --fail --silent --show-error --max-time 1 \
    "$issuer/.well-known/openid-configuration" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done
/usr/bin/curl --fail --silent --show-error --max-time 2 \
  "$issuer/.well-known/openid-configuration" >/dev/null

printf '%s\n' 'stage=grant-bootstrap'
rm -f "$db" "$db-shm" "$db-wal"
AGENT_ADMISSION_DB="$db" \
AGENT_ADMISSION_AUDIENCE="http://127.0.0.1:8788" \
  mise exec node@26.9.0 -- node "$root/src/bootstrap-grant.ts" >/dev/null

printf '%s\n' 'stage=resource-server-start'
AGENT_ADMISSION_DB="$db" \
AGENT_ADMISSION_AUDIENCE="http://127.0.0.1:8788" \
AGENT_ADMISSION_ISSUER="$issuer" \
AGENT_ADMISSION_ALLOW_INSECURE=1 \
  mise exec node@26.9.0 -- node "$root/src/server.ts" >"$server_log" 2>&1 &
server_pid="$!"

printf '%s\n' 'stage=resource-server-ready'
for _ in $(seq 1 100); do
  if /usr/bin/curl --fail --silent --show-error --max-time 1 \
    "http://127.0.0.1:8788/health" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$server_pid" 2>/dev/null; then
    cat "$server_log" >&2
    exit 1
  fi
  sleep 0.1
done
/usr/bin/curl --fail --silent --show-error --max-time 2 \
  "http://127.0.0.1:8788/health" >/dev/null

printf '%s\n' 'stage=e2e-client'
AGENT_ADMISSION_AUDIENCE="http://127.0.0.1:8788" \
AGENT_ADMISSION_ISSUER="$issuer" \
  mise exec node@26.9.0 -- node "$root/src/e2e-client.ts"

printf '%s\n' 'stage=done'
