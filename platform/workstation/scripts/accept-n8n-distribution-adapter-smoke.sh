#!/usr/bin/env bash
set -euo pipefail

# The operator supplies the qualified local cluster endpoint (libpq inputs).
# Do not infer another database when this invocation lacks a source binding.
: "${PGHOST:?PGHOST must name the qualified local PostgreSQL Unix socket directory}"
: "${PGPORT:?PGPORT must name the qualified local PostgreSQL port}"
if [[ "$PGHOST" != /* || "$PGHOST" == *,* || ! "$PGPORT" =~ ^[1-9][0-9]{0,4}$ ]] || (( PGPORT > 65535 )); then
  echo "invalid local PostgreSQL endpoint" >&2
  exit 2
fi
# libpq hostaddr/service can override or supplement an explicit socket host.
# This invocation selects its own endpoint; do not inherit those selectors.
unset PGHOSTADDR PGSERVICE PGSERVICEFILE
if [[ ${EUID} -ne 0 ]]; then echo 'must run as root' >&2; exit 2; fi
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MONOREPO_ROOT=$(cd "$ROOT/../.." && pwd)
DIST_INTENT=${DIST_INTENT:-$MONOREPO_ROOT/capabilities/distribution/evidence/r7-artifact-development-publication-intent.json}
WF=ordivon-dist-adapter-smoke-v1
[[ -f "$DIST_INTENT" ]] || { echo "missing Distribution intent: $DIST_INTENT" >&2; exit 3; }
curl -fsS http://127.0.0.1:5678/healthz/readiness >/dev/null
max_id(){ runuser -u postgres -- psql -h "$PGHOST" -p "$PGPORT" -d n8n -Atqc "select coalesce(max(id),0) from execution_entity where \"workflowId\"='$WF';"; }
exec_data(){ runuser -u postgres -- psql -h "$PGHOST" -p "$PGPORT" -d n8n -Atqc "select data from execution_data where \"executionId\"=$1;"; }
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
