#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$root/../.." && pwd)"
image="quay.io/keycloak/keycloak:26.7.4"
container="ordivon-web-agent-native-keycloak"
realm_source="$repo/platform/security/labs/agent-admission-rs/keycloak/realm-agent-admission-lab.json"
realm_mount="$(mktemp "${TMPDIR:-/tmp}/ordivon-agent-native-realm.XXXXXX.json")"
issuer="http://127.0.0.1:18080/realms/agent-admission-lab"
audience="http://localhost:8791"

cleanup() {
  /usr/bin/podman rm -f "$container" >/dev/null 2>&1 || true
  rm -f "$realm_mount"
}
trap cleanup EXIT INT TERM

python3 - "$realm_source" "$realm_mount" "$audience" <<'PY'
import json
import sys
source, target, audience = sys.argv[1:]
with open(source, encoding="utf-8") as handle:
    realm = json.load(handle)
found = False
for client in realm.get("clients", []):
    if client.get("clientId") != "agent-research-17":
        continue
    for mapper in client.get("protocolMappers", []):
        if mapper.get("name") == "agent-admission-audience":
            mapper.setdefault("config", {})["included.custom.audience"] = audience
            found = True
if not found:
    raise SystemExit("Keycloak Agent audience mapper not found")
with open(target, "w", encoding="utf-8") as handle:
    json.dump(realm, handle, separators=(",", ":"))
PY
chmod 0644 "$realm_mount"

printf '%s\n' 'stage=image'
if ! /usr/bin/podman image exists "$image"; then
  /usr/bin/timeout 120 /usr/bin/podman pull "$image" >/dev/null || true
fi
/usr/bin/podman image exists "$image"

printf '%s\n' 'stage=keycloak-start'
/usr/bin/podman rm -f "$container" >/dev/null 2>&1 || true
set +e
/usr/bin/timeout 30 /usr/bin/podman run -d   --replace   --rm   --pull=never   --name "$container"   --network host   --mount "type=bind,src=$realm_mount,dst=/opt/keycloak/data/import/realm.json,ro=true"   "$image"   start-dev     --import-realm     --http-enabled=true     --http-host=127.0.0.1     --http-port=18080     --hostname-strict=false >/dev/null
run_rc=$?
set -e
if [[ "$run_rc" -ne 0 ]]; then
  running=$(/usr/bin/podman inspect "$container" --format '{{.State.Running}}' 2>/dev/null || true)
  [[ "$running" == "true" ]]
fi

printf '%s\n' 'stage=keycloak-ready'
for _ in $(seq 1 100); do
  if /usr/bin/curl --fail --silent --show-error --max-time 0.5     "$issuer/.well-known/openid-configuration" >/dev/null 2>&1; then
    break
  fi
  running=$(/usr/bin/podman inspect "$container" --format '{{.State.Running}}' 2>/dev/null || true)
  if [[ "$running" != "true" ]]; then
    /usr/bin/podman logs "$container" 2>&1 || true
    echo "Keycloak exited before readiness" >&2
    exit 1
  fi
  sleep 0.25
done
/usr/bin/curl --fail --silent --show-error --max-time 2   "$issuer/.well-known/openid-configuration" >/dev/null

chromium_executable="$(
  find /root/.cache/ms-playwright     -path '*/chrome-linux64/chrome'     -type f     -perm -0100     2>/dev/null |
    sort -V |
    tail -1
)"
if [[ -z "$chromium_executable" ]]; then
  echo "No installed Playwright Chromium executable found." >&2
  exit 1
fi

printf '%s\n' 'stage=agent-native-e2e'
ORDIVON_WEB_CHROMIUM_EXECUTABLE="$chromium_executable" ORDIVON_WEB_AGENT_ISSUER="$issuer"   mise exec node@26.9.0 -- node "$root/test/agent-native-e2e.ts"

printf '%s\n' 'stage=done'
