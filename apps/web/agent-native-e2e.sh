#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$root/../.." && pwd)"
image="quay.io/keycloak/keycloak:26.7.4"
realm_source="$repo/platform/security/labs/agent-admission-rs/keycloak/realm-agent-admission-lab.json"
fixture="$(mktemp -d "${TMPDIR:-/tmp}/ordivon-web-agent-native.XXXXXX")"
container="ordivon-web-agent-native-$(basename "$fixture" | cut -d. -f2)"
cidfile="$fixture/container.id"
realm_mount="$fixture/realm.json"

# Never remove a container based on a shared name, or replace an existing
# fixture. On incomplete cleanup preserve the coordinates for the caller.
cleanup() {
  local rc=$? cid actual status
  trap - EXIT
  set +e
  if [[ -s "$cidfile" ]]; then
    cid="$(cat "$cidfile")"
    if [[ ! "$cid" =~ ^[0-9a-f]{64}$ ]]; then
      echo "Invalid owned fixture CID; preserve $fixture" >&2
      exit 1
    fi
    /usr/bin/podman container exists "$cid"; status=$?
    if [[ "$status" == 0 ]]; then
      actual="$(/usr/bin/podman inspect "$cid" --format '{{.Id}} {{.Name}}')"
      if [[ "$actual" != "$cid $container" ]]; then
        echo "Fixture identity mismatch; preserve $fixture" >&2
        exit 1
      fi
      /usr/bin/podman rm -f "$cid"
      /usr/bin/podman container exists "$cid"; status=$?
    fi
    if [[ "$status" != 1 ]]; then
      echo "Owned fixture cleanup not confirmed; preserve $fixture" >&2
      exit 1
    fi
  fi
  # A failed start without a CID never authorizes deletion by name.
  /usr/bin/podman container exists "$container"; status=$?
  if [[ "$status" != 1 ]]; then
    echo "Fixture name still present or unobservable; preserve $fixture" >&2
    exit 1
  fi
  rm -rf -- "$fixture"
  echo "ownedFixtureRemoved=true"
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Choose distinct local ports without claiming a reservation. A concurrent
# bind must fail the native start; never evict another listener.
read -r issuer_port web_port < <(python3 - <<'PY'
import socket
with socket.socket() as a, socket.socket() as b:
    a.bind(("127.0.0.1", 0))
    b.bind(("127.0.0.1", 0))
    print(a.getsockname()[1], b.getsockname()[1])
PY
)
issuer="http://127.0.0.1:$issuer_port/realms/agent-admission-lab"
audience="http://localhost:$web_port"

python3 - "$realm_source" "$realm_mount" "$audience" <<'PY'
import json
import sys
source, target, audience = sys.argv[1:]
with open(source, encoding="utf-8") as handle:
    realm = json.load(handle)
found = 0
for client in realm.get("clients", []):
    if client.get("clientId") != "agent-research-17":
        continue
    for mapper in client.get("protocolMappers", []):
        if mapper.get("name") == "agent-admission-audience":
            mapper.setdefault("config", {})["included.custom.audience"] = audience
            found += 1
if found != 1:
    raise SystemExit("Expected exactly one Keycloak Agent audience mapper")
with open(target, "w", encoding="utf-8") as handle:
    json.dump(realm, handle, separators=(",", ":"))
PY
chmod 0644 "$realm_mount"

printf '%s\n' 'stage=image'
if ! /usr/bin/podman image exists "$image"; then
  /usr/bin/timeout 120 /usr/bin/podman pull "$image"
fi
# Resolve the native image once, then launch that immutable local ID.
image_id="$(/usr/bin/podman image inspect "$image" --format '{{.Id}}')"
[[ "$image_id" =~ ^[0-9a-f]{64}$ ]]
/usr/bin/podman image inspect "$image" --format 'fixtureImage={{.Id}} tagDigest={{.Digest}}'

printf 'stage=keycloak-start fixture=%s issuerPort=%s webPort=%s\n' "$container" "$issuer_port" "$web_port"
# Native host-loopback is the qualified carrier. The bridge port publication
# path was unreachable on this host. Bind only to loopback, never 0.0.0.0.
/usr/bin/timeout 35 /usr/bin/podman run -d --pull=never \
  --cidfile "$cidfile" --name "$container" --network host \
  --memory 1200m --cpus 2 \
  --mount "type=bind,src=$realm_mount,dst=/opt/keycloak/data/import/realm.json,ro=true" \
  "$image_id" start-dev --import-realm --http-enabled=true \
  --http-host=127.0.0.1 --http-port="$issuer_port" --hostname-strict=false >/dev/null
cid="$(cat "$cidfile")"
[[ "$cid" =~ ^[0-9a-f]{64}$ ]]
[[ "$(/usr/bin/podman inspect "$cid" --format '{{.Id}} {{.Name}}')" = "$cid $container" ]]

printf '%s\n' 'stage=keycloak-ready'
deadline=$((SECONDS + 55))
ready=false
while (( SECONDS < deadline )); do
  if /usr/bin/curl --fail --silent --max-time 1 \
      "$issuer/.well-known/openid-configuration" > "$fixture/discovery.json"; then
    ready=true
    break
  fi
  [[ "$(/usr/bin/podman inspect "$cid" --format '{{.State.Running}}')" = true ]] || break
  sleep 0.3
done
if [[ "$ready" != true ]]; then
  echo "Owned Keycloak fixture not ready; no other listener will be evicted" >&2
  exit 1
fi
python3 - "$fixture/discovery.json" "$issuer" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    if json.load(handle).get("issuer") != sys.argv[2]:
        raise SystemExit("Keycloak discovery issuer did not match owned fixture")
PY

chromium_executable="$(
  find /root/.cache/ms-playwright -path '*/chrome-linux64/chrome' -type f -perm -0100 \
    2>/dev/null | sort -V | tail -1
)"
if [[ -z "$chromium_executable" ]]; then
  echo "No installed Playwright Chromium executable found." >&2
  exit 1
fi

printf '%s\n' 'stage=agent-native-e2e'
ORDIVON_WEB_CHROMIUM_EXECUTABLE="$chromium_executable" \
ORDIVON_WEB_AGENT_ISSUER="$issuer" \
ORDIVON_WEB_AGENT_E2E_PORT="$web_port" \
  /usr/bin/timeout 60 mise exec node@26.12.1 -- node "$root/test/agent-native-e2e.ts"

printf '%s\n' 'stage=done'
