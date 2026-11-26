#!/usr/bin/env bash
# Isolated, direct-library migration challenger, NOT service admission.
# Requires a prepared Python oracle checkout at the documented exact cut,
# local native PG18 binaries, postgres OS account and root in a test runtime.
set -euo pipefail
rust_root="$(cd "$(dirname "$0")/.." && pwd)"
host_root="$(cd "${1:?supply the independently prepared Python Host root}" && pwd)"
test "$(git -C "$host_root" rev-parse HEAD)" = e518460b99f2464ebe369dc9adf48506ccb768a2
test -z "$(git -C "$host_root" status --porcelain)"
test -x "$host_root/.venv/bin/python"
test "$(id -u)" = 0
case "$(initdb --version)" in *" 18."*) ;; *) echo "requires native PG18" >&2; exit 1;; esac
p=$(mktemp -d /var/tmp/ordivon-r23-verify-pg.XXXXXX)
a=$(mktemp -d /var/tmp/ordivon-r23-verify-results.XXXXXX)
cleanup(){
 runuser -u postgres -- pg_ctl -D "$p/data" -m immediate -w stop >/dev/null 2>&1 || true
 rm -rf -- "$p" "$a"
}
trap cleanup EXIT
chown postgres:postgres "$p"
runuser -u postgres -- initdb -D "$p/data" -A trust --no-locale -E UTF8 -c shared_buffers=16MB -c max_connections=24 >"$p/init.log" 2>&1
# Unique Unix socket directory; no TCP listener. This cluster is disposable.
port=15487
runuser -u postgres -- pg_ctl -D "$p/data" -l "$p/pg.log" -o "-k $p -p $port -c listen_addresses='' -c shared_buffers=16MB -c max_connections=24 -c fsync=off" -w start
export R23_PRIVATE_DSN="host=$p port=$port user=postgres dbname=postgres"
export ORDIVON_HOST_V2_DSN="postgresql://postgres@/postgres?host=$p&port=$port"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$host_root/src"
unset ORDIVON_HOST_V2_SQLALCHEMY_URL ORDIVON_HOST_V2_COMPACT_WORK_RECEIPTS
cd "$rust_root"
export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}" CARGO_PROFILE_DEV_DEBUG=0
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$a/target}"
cargo build --locked --example receipt_cross_language_probe
bin="$CARGO_TARGET_DIR/debug/examples/receipt_cross_language_probe"
cd "$host_root"
.venv/bin/python -m alembic upgrade 0017 >"$p/migrate.log" 2>&1 || { tail -60 "$p/migrate.log"; exit 1; }
.venv/bin/python "$rust_root/tools/python_receipt_cross_language_seed.py" "$a/expected.json"
"$bin" 17 "$a/expected.json" "$a/reverse.json"
.venv/bin/python "$rust_root/tools/python_receipt_cross_language_reverse.py" "$a/reverse.json"
.venv/bin/python -m alembic downgrade 0016 >"$p/downgrade.log" 2>&1 || { tail -60 "$p/downgrade.log"; exit 1; }
"$bin" 16 "$a/expected.json" rollback
test "$(psql -XAtq "$R23_PRIVATE_DSN" -c "SELECT current_revision FROM works WHERE work_ref='work:r23-cross-language'")" = 3
test "$(psql -XAtq "$R23_PRIVATE_DSN" -c "SELECT count(*) FROM command_receipts WHERE client_request_id IN ('r23:legacy','r23:compact','r23:later','r23:rust-legacy')")" = 4
echo 'NATIVE CROSS-LANGUAGE REPLAY AND ROLLBACK QUALIFIED (direct library only)'
