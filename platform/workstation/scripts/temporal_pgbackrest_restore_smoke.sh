#!/usr/bin/env bash
set -euo pipefail

LABEL=${1:?backup label required}
WORKFLOW_ID=${2:?workflow id required}
PORT=${3:-55435}
RESTORE_ROOT=${RESTORE_ROOT:-/var/tmp/ordivon-temporal-restore-smoke}
SOCKET_ROOT=${SOCKET_ROOT:-/var/tmp/ordivon-temporal-restore-socket}
LOG=${LOG:-/var/tmp/ordivon-temporal-restore-smoke.log}
PG_CTL=/usr/bin/pg_ctl
PSQL=/usr/bin/psql
PGBACKREST=/usr/bin/pgbackrest

# This script is an isolated smoke, never an operator for pre-existing PGDATA.
# Admission happens before any trap or destructive operation.
for target in "$RESTORE_ROOT" "$SOCKET_ROOT" "$LOG"; do
  if [[ ! "$target" =~ ^/(var/)?tmp/[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "restore smoke output must be a direct /tmp scratch path or /var/tmp scratch path" >&2
    exit 2
  fi
done
if [ "$RESTORE_ROOT" = "$SOCKET_ROOT" ] || [ "$RESTORE_ROOT" = "$LOG" ] || [ "$SOCKET_ROOT" = "$LOG" ]; then
  echo "restore smoke scratch paths must be distinct" >&2
  exit 2
fi
if [[ ! "$PORT" =~ ^[1-9][0-9]{3,4}$ ]] || (( PORT < 1024 || PORT > 65535 )); then
  echo "unsafe restore port" >&2
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
start_attempted=false
restore_identity=
socket_identity=
log_identity=

# A pathname is not an ownership token. Check device/inode and type
# before effects; this observation is not an atomic rename/delete fence.
scratch_identity() {
  local target=$1 kind=$2
  if [ -L "$target" ]; then return 1; fi
  case "$kind" in
    directory) [ -d "$target" ] || return 1 ;;
    file) [ -f "$target" ] || return 1 ;;
    *) return 1 ;;
  esac
  stat -c '%d:%i' -- "$target"
}
same_scratch() {
  local target=$1 kind=$2 expected=$3 actual
  if [ -z "$expected" ] || ! actual=$(scratch_identity "$target" "$kind") || [ "$actual" != "$expected" ]; then
    echo "restore smoke scratch identity changed or unknown: $target; preserving scratch" >&2
    return 1
  fi
}
cleanup() {
  # Check all carriers before the first cleanup effect.
  if [ "$owned_restore" = true ]; then same_scratch "$RESTORE_ROOT" directory "$restore_identity" || return 1; fi
  if [ "$owned_socket" = true ]; then same_scratch "$SOCKET_ROOT" directory "$socket_identity" || return 1; fi
  if [ "$owned_log" = true ]; then same_scratch "$LOG" file "$log_identity" || return 1; fi
  if [ "$owned_restore" = true ]; then
    if [ -f "$RESTORE_ROOT/postmaster.pid" ]; then
      # A PID file from backup bytes or an uncertain pre-start failure is
      # not authority to signal any server. Check our exact PGDATA first.
      if [ "$start_attempted" != true ] || \
         [ "$(sed -n '2p' "$RESTORE_ROOT/postmaster.pid")" != "$RESTORE_ROOT" ]; then
        echo "restore smoke could not confirm isolated PostgreSQL stopped; preserving owned scratch" >&2
        return 1
      fi
      if ! sudo -u postgres "$PG_CTL" -D "$RESTORE_ROOT" -m fast -w stop >/dev/null 2>&1; then
        echo "restore smoke could not confirm isolated PostgreSQL stopped; preserving owned scratch" >&2
        return 1
      fi
      if [ -f "$RESTORE_ROOT/postmaster.pid" ]; then
        echo "restore smoke PostgreSQL pid file remains after stop; preserving owned scratch" >&2
        return 1
      fi
    fi
    same_scratch "$RESTORE_ROOT" directory "$restore_identity" || return 1
    rm -rf -- "$RESTORE_ROOT" || return 1
  fi
  if [ "$owned_socket" = true ]; then
    same_scratch "$SOCKET_ROOT" directory "$socket_identity" || return 1
    rm -rf -- "$SOCKET_ROOT" || return 1
  fi
  if [ "$owned_log" = true ]; then
    same_scratch "$LOG" file "$log_identity" || return 1
    rm -f -- "$LOG" || return 1
  fi
}
on_exit() {
  local rc=$?
  if ! cleanup; then exit 1; fi
  exit "$rc"
}
trap on_exit EXIT
mkdir -m 0700 -- "$RESTORE_ROOT"
owned_restore=true
restore_identity=$(scratch_identity "$RESTORE_ROOT" directory)
mkdir -m 0700 -- "$SOCKET_ROOT"
owned_socket=true
socket_identity=$(scratch_identity "$SOCKET_ROOT" directory)
if ! (set -C; : > "$LOG"); then
  echo "restore smoke log path already exists" >&2
  exit 2
fi
owned_log=true
log_identity=$(scratch_identity "$LOG" file)
chown postgres:postgres "$RESTORE_ROOT" "$SOCKET_ROOT" "$LOG"

# pgBackRest owns physical restoration. Never follow backup-origin links to
# the original server's storage. Remap tablespaces into our scratch carrier
# (the current smoke qualifies only clusters without external tablespaces).
mkdir -m 0700 -- "$SOCKET_ROOT/tablespaces"
chown postgres:postgres "$SOCKET_ROOT/tablespaces"
sudo -u postgres "$PGBACKREST" \
  --stanza=ordivon \
  --pg1-path="$RESTORE_ROOT" \
  --set="$LABEL" \
  --type=immediate \
  --target-action=promote \
  --archive-mode=off \
  --no-link-all \
  --reset-link-map \
  --reset-tablespace-map \
  --tablespace-map-all="$SOCKET_ROOT/tablespaces" \
  restore

same_scratch "$RESTORE_ROOT" directory "$restore_identity"
same_scratch "$SOCKET_ROOT" directory "$socket_identity"
same_scratch "$LOG" file "$log_identity"

# Recovered configuration is data, not executable operator intent. This
# isolated smoke intentionally does not reuse production include files,
# preload libraries, archive-push commands or replication connection settings.
links=$(find "$RESTORE_ROOT" -type l -print -quit)
if [ -n "$links" ] || [ -e "$RESTORE_ROOT/standby.signal" ] || \
   [ ! -f "$RESTORE_ROOT/recovery.signal" ] || [ -e "$RESTORE_ROOT/postmaster.pid" ]; then
  echo "unsupported restored topology or recovery signal; refusing startup" >&2
  exit 2
fi
# Only files in this newly created, link-free scratch PGDATA are changed.
: > "$RESTORE_ROOT/postgresql.auto.conf"
cat > "$RESTORE_ROOT/ordivon-smoke.conf" <<EOF
data_directory = '$RESTORE_ROOT'
hba_file = '$RESTORE_ROOT/ordivon-smoke-hba.conf'
ident_file = '$RESTORE_ROOT/ordivon-smoke-ident.conf'
port = $PORT
listen_addresses = ''
unix_socket_directories = '$SOCKET_ROOT'
unix_socket_permissions = 0700
shared_buffers = '64MB'
hot_standby = off
archive_mode = off
archive_command = ''
restore_command = '/usr/bin/pgbackrest --stanza=ordivon --pg1-path=$RESTORE_ROOT --no-archive-async --log-path=$SOCKET_ROOT archive-get %f "%p"'
recovery_target = 'immediate'
recovery_target_action = 'promote'
recovery_target_timeline = 'current'
EOF
printf 'local all postgres peer\n' > "$RESTORE_ROOT/ordivon-smoke-hba.conf"
: > "$RESTORE_ROOT/ordivon-smoke-ident.conf"
chown postgres:postgres "$RESTORE_ROOT/postgresql.auto.conf" "$RESTORE_ROOT"/ordivon-smoke*.conf
start_attempted=true
sudo -u postgres "$PG_CTL" -D "$RESTORE_ROOT" -l "$LOG" \
  -o "-c config_file=$RESTORE_ROOT/ordivon-smoke.conf" \
  -t 120 -w start

# pg_ctl readiness alone can precede completion of WAL replay.
promoted=false
for ((i=0; i<60; i++)); do
  if [ "$(sudo -u postgres "$PSQL" -X -v ON_ERROR_STOP=1 -p "$PORT" -h "$SOCKET_ROOT" -d postgres -Atqc 'select not pg_is_in_recovery();' 2>/dev/null)" = t ]; then
    promoted=true
    break
  fi
  sleep 1
done
if [ "$promoted" != true ]; then
  echo "isolated recovery did not reach a promoted state" >&2
  exit 1
fi

CORE_VERSION=$(sudo -u postgres "$PSQL" -X -v ON_ERROR_STOP=1 -p "$PORT" -h "$SOCKET_ROOT" -d temporal -Atqc 'select curr_version from schema_version;')
VIS_VERSION=$(sudo -u postgres "$PSQL" -X -v ON_ERROR_STOP=1 -p "$PORT" -h "$SOCKET_ROOT" -d temporal_visibility -Atqc 'select curr_version from schema_version;')
ROW=$(sudo -u postgres "$PSQL" -X -v ON_ERROR_STOP=1 -p "$PORT" -h "$SOCKET_ROOT" -d temporal_visibility -Atqc "select workflow_id||'|'||status from executions_visibility where workflow_id='${WORKFLOW_ID//\'/\'\'}' and status=2 order by start_time desc limit 1;")

[ "$CORE_VERSION" = "1.19" ]
[ "$VIS_VERSION" = "1.14" ]
[ "$ROW" = "$WORKFLOW_ID|2" ]

# Do not emit PASS if the isolated postmaster could not be stopped.
trap - EXIT
cleanup

printf '{"backupLabel":"%s","coreSchema":"%s","visibilitySchema":"%s","workflowId":"%s","workflowStatus":2,"standing":"PASS"}\n' \
  "$LABEL" "$CORE_VERSION" "$VIS_VERSION" "$WORKFLOW_ID"
