#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo 'must run as root: PostgreSQL metadata inspection and rootless n8n handoff are required' >&2
  exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SOURCE="$ROOT/n8n/workflows/ordivon-discord-research-v0.json"
WORKFLOW_ID=ordivon-discord-research-v0
CREDENTIAL_NAME="${ORDIVON_DISCORD_N8N_CREDENTIAL_NAME:-ordivon-discord-research-v0}"
SOCKET=/var/lib/postgres/ordivon-data-r5-pg-14550-v4
PORT=55434
STATE=/var/lib/n8n/.n8n
RUNTIME=/run/user/934

if [[ ! "$CREDENTIAL_NAME" =~ ^[A-Za-z0-9._:-]{1,128}$ ]]; then
  echo 'ORDIVON_DISCORD_N8N_CREDENTIAL_NAME contains unsupported characters' >&2
  exit 3
fi

run_n8n() {
  (
    cd /var/lib/n8n
    runuser -u n8n -- env -i \
      HOME=/var/lib/n8n USER=n8n LOGNAME=n8n PATH=/usr/bin:/bin \
      XDG_RUNTIME_DIR="$RUNTIME" \
      DBUS_SESSION_BUS_ADDRESS="unix:path=$RUNTIME/bus" \
      "$@"
  )
}

[[ -f "$SOURCE" ]] || { echo "missing workflow source: $SOURCE" >&2; exit 4; }
python3 -m json.tool "$SOURCE" >/dev/null

mapfile -t credential_rows < <(
  runuser -u postgres -- psql -h "$SOCKET" -p "$PORT" -d n8n -AtF '|' -c \
    "select id,name,type from credentials_entity where name='$CREDENTIAL_NAME' and type='discordBotApi' order by id;"
)
if [[ ${#credential_rows[@]} -ne 1 ]]; then
  echo "expected exactly one n8n discordBotApi credential named '$CREDENTIAL_NAME', found ${#credential_rows[@]}" >&2
  exit 5
fi
IFS='|' read -r credential_id credential_name credential_type <<<"${credential_rows[0]}"
[[ -n "$credential_id" && "$credential_name" == "$CREDENTIAL_NAME" && "$credential_type" == "discordBotApi" ]] || {
  echo 'Discord credential metadata identity mismatch' >&2
  exit 6
}

mapfile -t projects < <(
  runuser -u postgres -- psql -h "$SOCKET" -p "$PORT" -d n8n -Atqc \
    "select id from project where type='personal' order by \"createdAt\";"
)
if [[ ${#projects[@]} -ne 1 ]]; then
  echo "expected exactly one personal n8n project for local deployment, found ${#projects[@]}" >&2
  exit 7
fi
project="${projects[0]}"

materialized=$(mktemp)
current=$(mktemp)
import_path="$STATE/ordivon-discord-research-v0.import.json"
cleanup() {
  rm -f "$materialized" "$current"
  rm -f "$import_path"
}
trap cleanup EXIT

python3 - "$SOURCE" "$materialized" "$credential_id" "$credential_name" <<'PY'
import json
import sys

source_path, output_path, credential_id, credential_name = sys.argv[1:]
workflow = json.load(open(source_path, encoding="utf-8"))
matches = [node for node in workflow["nodes"] if node.get("name") == "Discord Search Guild Messages"]
if len(matches) != 1:
    raise SystemExit(f"expected exactly one Discord HTTP node, found {len(matches)}")
http = matches[0]
if http.get("parameters", {}).get("authentication") != "predefinedCredentialType":
    raise SystemExit("Discord HTTP node must use predefinedCredentialType")
if http.get("parameters", {}).get("nodeCredentialType") != "discordBotApi":
    raise SystemExit("Discord HTTP node must use discordBotApi")
http["credentials"] = {
    "discordBotApi": {
        "id": credential_id,
        "name": credential_name,
    }
}
workflow["active"] = True
with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(workflow, handle, sort_keys=True, separators=(",", ":"))
    handle.write("\n")
PY

runuser -u postgres -- psql -h "$SOCKET" -p "$PORT" -d n8n -Atqc \
  "select json_build_object('id',id,'name',name,'active',active,'nodes',nodes,'connections',connections,'settings',settings)::text from workflow_entity where id='$WORKFLOW_ID';" \
  > "$current"

if [[ -s "$current" ]] && python3 - "$materialized" "$current" <<'PY'
import json
import sys
desired = json.load(open(sys.argv[1], encoding="utf-8"))
current = json.load(open(sys.argv[2], encoding="utf-8"))
keys = ("id", "name", "active", "nodes", "connections", "settings")
def pick(value):
    return {key: value.get(key) for key in keys}
if pick(desired) != pick(current):
    raise SystemExit(1)
PY
then
  echo "n8n Discord research workflow already converged: $WORKFLOW_ID"
  exit 0
fi

install -o n8n -g n8n -m 0600 "$materialized" "$import_path"
run_n8n podman exec ordivon-n8n n8n import:workflow \
  --input=/home/node/.n8n/ordivon-discord-research-v0.import.json \
  --projectId="$project"
run_n8n podman exec ordivon-n8n n8n publish:workflow --id="$WORKFLOW_ID"
rm -f "$import_path"
run_n8n systemctl --user restart ordivon-n8n-pod.service

for _ in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:5678/healthz/readiness >/dev/null 2>&1; then
    echo "n8n Discord research workflow converged and published: $WORKFLOW_ID"
    exit 0
  fi
  sleep 1
done

echo 'n8n failed to regain readiness after Discord research workflow convergence' >&2
exit 8
