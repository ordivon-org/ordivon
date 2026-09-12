#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo 'must run as root: PostgreSQL inspection and rootless n8n user handoff are required' >&2
  exit 2
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SOURCE="$ROOT/n8n/workflows/ordivon-integration-smoke-v1.json"
WORKFLOW_ID=ordivon-smoke-v1
SOCKET=/var/lib/postgres/ordivon-data-r5-pg-14550-v4
PORT=55434
STATE=/var/lib/n8n/.n8n
RUNTIME=/run/user/934

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

[[ -f "$SOURCE" ]] || { echo "missing workflow source: $SOURCE" >&2; exit 3; }
python3 -m json.tool "$SOURCE" >/dev/null

current=$(mktemp)
trap 'rm -f "$current" "$STATE/ordivon-integration-smoke-v1.import.json"' EXIT
runuser -u postgres -- psql -h "$SOCKET" -p "$PORT" -d n8n -Atqc \
  "select json_build_object('id',id,'name',name,'active',active,'nodes',nodes,'connections',connections,'settings',settings)::text from workflow_entity where id='$WORKFLOW_ID';" \
  > "$current"

if [[ -s "$current" ]] && python3 - "$SOURCE" "$current" <<'PY'
import json, sys
source=json.load(open(sys.argv[1]))
current=json.load(open(sys.argv[2]))
keys=('id','name','active','nodes','connections','settings')
def pick(x): return {k:x.get(k) for k in keys}
if pick(source) != pick(current):
    raise SystemExit(1)
PY
then
  echo "n8n smoke workflow already converged: $WORKFLOW_ID"
  exit 0
fi

mapfile -t projects < <(runuser -u postgres -- psql -h "$SOCKET" -p "$PORT" -d n8n -Atqc \
  "select id from project where type='personal' order by \"createdAt\";")
if [[ ${#projects[@]} -ne 1 ]]; then
  echo "expected exactly one personal n8n project for local acceptance, found ${#projects[@]}" >&2
  exit 4
fi
project=${projects[0]}

install -o n8n -g n8n -m 0600 "$SOURCE" "$STATE/ordivon-integration-smoke-v1.import.json"
run_n8n podman exec ordivon-n8n n8n import:workflow \
  --input=/home/node/.n8n/ordivon-integration-smoke-v1.import.json \
  --projectId="$project"
run_n8n podman exec ordivon-n8n n8n publish:workflow --id="$WORKFLOW_ID"
rm -f "$STATE/ordivon-integration-smoke-v1.import.json"
run_n8n systemctl --user restart ordivon-n8n-pod.service

for _ in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:5678/healthz/readiness >/dev/null 2>&1; then
    echo "n8n smoke workflow converged and published: $WORKFLOW_ID"
    exit 0
  fi
  sleep 1
done

echo 'n8n failed to regain readiness after workflow convergence' >&2
exit 5
