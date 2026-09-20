#!/usr/bin/env bash
set -euo pipefail

LABEL=${1:?backup label required}
WORKFLOW_ID=${2:?workflow id required}
PORT=${3:-55435}
RESTORE_ROOT=${RESTORE_ROOT:-/tmp/ordivon-temporal-restore-smoke}
SOCKET_ROOT=${SOCKET_ROOT:-/tmp/ordivon-temporal-restore-socket}
LOG=${LOG:-/tmp/ordivon-temporal-restore-smoke.log}
PG_CTL=/usr/bin/pg_ctl
PSQL=/usr/bin/psql
PGBACKREST=/usr/bin/pgbackrest

cleanup() {
  if [ -f "$RESTORE_ROOT/postmaster.pid" ]; then
    sudo -u postgres "$PG_CTL" -D "$RESTORE_ROOT" -m fast -w stop >/dev/null 2>&1 || true
  fi
  rm -rf "$RESTORE_ROOT" "$SOCKET_ROOT" "$LOG"
}
trap cleanup EXIT
cleanup
install -d -o postgres -g postgres -m 0700 "$RESTORE_ROOT" "$SOCKET_ROOT"

sudo -u postgres "$PGBACKREST" \
  --stanza=ordivon \
  --pg1-path="$RESTORE_ROOT" \
  --set="$LABEL" \
  --type=immediate \
  --target-action=promote \
  restore

sudo -u postgres "$PG_CTL" -D "$RESTORE_ROOT" -l "$LOG" \
  -o "-p $PORT -k $SOCKET_ROOT -c listen_addresses=127.0.0.1 -c archive_mode=off -c archive_command=/bin/true" \
  -w start

CORE_VERSION=$(sudo -u postgres "$PSQL" -p "$PORT" -h "$SOCKET_ROOT" -d temporal -Atqc 'select curr_version from schema_version;')
VIS_VERSION=$(sudo -u postgres "$PSQL" -p "$PORT" -h "$SOCKET_ROOT" -d temporal_visibility -Atqc 'select curr_version from schema_version;')
ROW=$(sudo -u postgres "$PSQL" -p "$PORT" -h "$SOCKET_ROOT" -d temporal_visibility -Atqc "select workflow_id||'|'||status from executions_visibility where workflow_id='${WORKFLOW_ID//\'/\'\'}';")

[ "$CORE_VERSION" = "1.19" ]
[ "$VIS_VERSION" = "1.14" ]
[ "$ROW" = "$WORKFLOW_ID|2" ]

printf '{"backupLabel":"%s","coreSchema":"%s","visibilitySchema":"%s","workflowId":"%s","workflowStatus":2,"standing":"PASS"}\n' \
  "$LABEL" "$CORE_VERSION" "$VIS_VERSION" "$WORKFLOW_ID"
