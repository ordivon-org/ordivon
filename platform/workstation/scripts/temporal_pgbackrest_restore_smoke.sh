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

# This script is an isolated smoke, never an operator for pre-existing PGDATA.
# Admission happens before any trap or destructive operation.
for target in "$RESTORE_ROOT" "$SOCKET_ROOT" "$LOG"; do
  if [[ ! "$target" =~ ^/tmp/[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "restore smoke output must be a direct /tmp scratch path" >&2
    exit 2
  fi
done
if [ "$RESTORE_ROOT" = "$SOCKET_ROOT" ] || [ "$RESTORE_ROOT" = "$LOG" ] || [ "$SOCKET_ROOT" = "$LOG" ]; then
  echo "restore smoke scratch paths must be distinct" >&2
  exit 2
fi
if [[ ! "$WORKFLOW_ID" =~ ^[A-Za-z0-9_./:@-]{1,256}$ ]]; then
  echo "unsafe workflow id" >&2
  exit 2
fi
for target in "$RESTORE_ROOT" "$SOCKET_ROOT" "$LOG"; do
  if [ -e "$target" ] || [ -L "$target" ]; then
    echo "restore smoke scratch path already exists: $target" >&2
    exit 2
  fi
done

owned_restore=false
owned_socket=false
owned_log=false
cleanup() {
  if [ "$owned_restore" = true ]; then
    if [ -f "$RESTORE_ROOT/postmaster.pid" ]; then
      if ! sudo -u postgres "$PG_CTL" -D "$RESTORE_ROOT" -m fast -w stop >/dev/null 2>&1; then
        echo "restore smoke could not confirm isolated PostgreSQL stopped; preserving owned scratch" >&2
        return 1
      fi
      if [ -f "$RESTORE_ROOT/postmaster.pid" ]; then
        echo "restore smoke PostgreSQL pid file remains after stop; preserving owned scratch" >&2
        return 1
      fi
    fi
    rm -rf -- "$RESTORE_ROOT"
  fi
  if [ "$owned_socket" = true ]; then rm -rf -- "$SOCKET_ROOT"; fi
  if [ "$owned_log" = true ]; then rm -f -- "$LOG"; fi
}
trap cleanup EXIT
mkdir -m 0700 -- "$RESTORE_ROOT"
owned_restore=true
mkdir -m 0700 -- "$SOCKET_ROOT"
owned_socket=true
if ! (set -C; : > "$LOG"); then
  echo "restore smoke log path already exists" >&2
  exit 2
fi
owned_log=true
chown postgres:postgres "$RESTORE_ROOT" "$SOCKET_ROOT" "$LOG"

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
ROW=$(sudo -u postgres "$PSQL" -p "$PORT" -h "$SOCKET_ROOT" -d temporal_visibility -Atqc "select workflow_id||'|'||status from executions_visibility where workflow_id='${WORKFLOW_ID//\'/\'\'}' and status=2 order by start_time desc limit 1;")

[ "$CORE_VERSION" = "1.19" ]
[ "$VIS_VERSION" = "1.14" ]
[ "$ROW" = "$WORKFLOW_ID|2" ]

printf '{"backupLabel":"%s","coreSchema":"%s","visibilitySchema":"%s","workflowId":"%s","workflowStatus":2,"standing":"PASS"}\n' \
  "$LABEL" "$CORE_VERSION" "$VIS_VERSION" "$WORKFLOW_ID"
