#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo 'must run as root' >&2; exit 2; fi
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MONOREPO_ROOT=$(cd "$ROOT/../.." && pwd)
DIST_INTENT=${DIST_INTENT:-$MONOREPO_ROOT/capabilities/distribution/evidence/r7-artifact-development-publication-intent.json}
SOCKET=/var/lib/postgres/ordivon-data-r5-pg-14550-v4
PORT=55434
WF=ordivon-dist-adapter-smoke-v1
[[ -f "$DIST_INTENT" ]] || { echo "missing Distribution intent: $DIST_INTENT" >&2; exit 3; }
curl -fsS http://127.0.0.1:5678/healthz/readiness >/dev/null
max_id(){ runuser -u postgres -- psql -h "$SOCKET" -p "$PORT" -d n8n -Atqc "select coalesce(max(id),0) from execution_entity where \"workflowId\"='$WF';"; }
exec_data(){ runuser -u postgres -- psql -h "$SOCKET" -p "$PORT" -d n8n -Atqc "select data from execution_data where \"executionId\"=$1;"; }
BEFORE=$(max_id)
"$ROOT/scripts/invoke-n8n-distribution-adapter-smoke.py" --mode blocked --intent "$DIST_INTENT" --id acceptance-blocked-20260912 >/tmp/n8n-dist-blocked.json
BLOCK=$(max_id)
[[ "$BLOCK" -gt "$BEFORE" ]]
BLOCK_DATA=$(exec_data "$BLOCK")
grep -F 'Build Blocked Result' <<<"$BLOCK_DATA" >/dev/null
if grep -F 'GitHub Provider Readback' <<<"$BLOCK_DATA" >/dev/null; then echo 'blocked execution reached provider node' >&2; exit 4; fi
"$ROOT/scripts/invoke-n8n-distribution-adapter-smoke.py" --mode readback --id acceptance-readback-20260912 >/tmp/n8n-dist-readback.json
READ=$(max_id)
[[ "$READ" -gt "$BLOCK" ]]
READ_DATA=$(exec_data "$READ")
grep -F 'GitHub Provider Readback' <<<"$READ_DATA" >/dev/null
grep -F 'Build Provider Readback Result' <<<"$READ_DATA" >/dev/null
python3 - <<'PY'
import json
b=json.load(open('/tmp/n8n-dist-blocked.json'));r=json.load(open('/tmp/n8n-dist-readback.json'))
assert b['data']['providerCalled'] is False and b['data']['externalEffectPerformed'] is False
assert r['data']['providerCalled'] is True and r['data']['externalMethod']=='GET' and r['data']['externalEffectPerformed'] is False
assert r['data']['observedObject']['number']==72
print('PASS blocked branch omitted provider node; readback branch executed GitHub GET only')
PY
printf 'blockedExecutionId=%s readbackExecutionId=%s\n' "$BLOCK" "$READ"
