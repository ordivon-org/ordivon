#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
image="quay.io/keycloak/keycloak:26.7.4"
container="ordivon-agent-admission-keycloak-webauthn"
realm_source="$root/keycloak/realm-agent-admission-lab.json"
realm_mount="$(mktemp "${TMPDIR:-/tmp}/ordivon-agent-admission-realm.XXXXXX.json")"
db="$root/.agent-admission-webauthn.sqlite3"
server_log="${TMPDIR:-/tmp}/ordivon-agent-admission-webauthn-rs.log"
server_pid=""
enrollment_token="lab-enrollment-only"
install -m 0644 "$realm_source" "$realm_mount"

cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  /usr/bin/podman rm -f "$container" >/dev/null 2>&1 || true
  rm -f "$realm_mount"
}
trap cleanup EXIT INT TERM

printf '%s\n' 'stage=image'
if ! /usr/bin/podman image exists "$image"; then
  /usr/bin/timeout 120 /usr/bin/podman pull "$image" >/dev/null || true
fi
/usr/bin/podman image exists "$image"

printf '%s\n' 'stage=keycloak-start'
/usr/bin/podman rm -f "$container" >/dev/null 2>&1 || true
set +e
/usr/bin/timeout 30 /usr/bin/podman run -d \
  --replace \
  --rm \
  --pull=never \
  --name "$container" \
  --network host \
  --mount "type=bind,src=$realm_mount,dst=/opt/keycloak/data/import/realm.json,ro=true" \
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
  [[ "$running" == "true" ]]
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

printf '%s\n' 'stage=resource-server-start'
rm -f "$db" "$db-shm" "$db-wal"
AGENT_ADMISSION_DB="$db" \
AGENT_ADMISSION_AUDIENCE="http://127.0.0.1:8788" \
AGENT_ADMISSION_ISSUER="$issuer" \
AGENT_ADMISSION_ALLOW_INSECURE=1 \
AGENT_ADMISSION_WEBAUTHN_ORIGIN="http://localhost:8788" \
AGENT_ADMISSION_WEBAUTHN_RPID="localhost" \
AGENT_ADMISSION_ENROLLMENT_TOKEN="$enrollment_token" \
AGENT_ADMISSION_WEBAUTHN_STEP_UP=1 \
  mise exec node@26.9.0 -- node "$root/src/server.ts" >"$server_log" 2>&1 &
server_pid="$!"

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
if ! grep -q '"webAuthnStepUpEnabled":true' "$server_log"; then
  cat "$server_log" >&2
  echo "WebAuthn step-up profile did not activate" >&2
  exit 1
fi

printf '%s\n' 'stage=webauthn-e2e'
chromium_executable="$(find /root/.cache/ms-playwright -path '*/chrome-linux64/chrome' -type f -perm -0100 2>/dev/null | sort -V | tail -1)"
if [[ -z "$chromium_executable" ]]; then
  echo "No installed Playwright Chromium executable found" >&2
  exit 1
fi
AGENT_ADMISSION_CHROMIUM_EXECUTABLE="$chromium_executable" \
AGENT_ADMISSION_AUDIENCE="http://127.0.0.1:8788" \
AGENT_ADMISSION_ISSUER="$issuer" \
AGENT_ADMISSION_WEBAUTHN_ORIGIN="http://localhost:8788" \
AGENT_ADMISSION_ENROLLMENT_TOKEN="$enrollment_token" \
AGENT_ADMISSION_WEBAUTHN_STEP_UP=1 \
  mise exec node@26.9.0 -- node "$root/src/webauthn-e2e.ts"

printf '%s\n' 'stage=done'
