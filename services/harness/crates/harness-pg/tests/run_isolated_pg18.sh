#!/usr/bin/env bash
# Test-only isolated PostgreSQL18: Python legacy writer -> Rust read-only reader.
# Never opens configured Harness production PG DSN.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
for tool in initdb pg_ctl psql runuser cargo uv python3; do
  command -v "$tool" >/dev/null || { echo "missing $tool" >&2; exit 2; }
done
if [[ "$(id -u)" -ne 0 ]]; then
  echo "isolated PG18 test requires root to run private postgres UID" >&2
  exit 2
fi
ROOT="$(mktemp -d /tmp/ordivon-harness-pg18-rust-a-XXXXXXXX)"
chmod 700 "$ROOT"
chown postgres:postgres "$ROOT"
started=0
cleanup() {
  if [[ "$started" == 1 ]]; then
    runuser -u postgres -- pg_ctl -D "$ROOT/data" -m immediate -w stop >/dev/null || true
  fi
  rm -rf -- "$ROOT"
}
trap cleanup EXIT
runuser -u postgres -- initdb -D "$ROOT/data" -U postgres -A trust --no-instructions > "$ROOT/initdb.log"
runuser -u postgres -- pg_ctl -D "$ROOT/data" -o "-k $ROOT -p 59433 -h ''" -l "$ROOT/server.log" -w start
started=1
writer_dsn="host=$ROOT port=59433 dbname=postgres user=postgres connect_timeout=5"
psql "$writer_dsn" -v ON_ERROR_STOP=1 -c 'CREATE ROLE rust_readonly LOGIN'
export HARNESS_RUST_TEST_PG_DSN="$writer_dsn"
export HARNESS_RUST_TEST_SCHEMA="hpg_rust_isolated_a_$(date +%s)"
export HARNESS_RUST_TEST_FIXTURE_PATH="$ROOT/fixture.json"
uv run --project services/harness --offline --locked python services/harness/crates/harness-pg/tests/fixture_python_store.py
psql "$writer_dsn" -v ON_ERROR_STOP=1 -c "GRANT USAGE ON SCHEMA $HARNESS_RUST_TEST_SCHEMA TO rust_readonly; GRANT SELECT ON ALL TABLES IN SCHEMA $HARNESS_RUST_TEST_SCHEMA TO rust_readonly;"
for item in 'valid:HARNESS_RUST_TEST_RUN_ID' 'corrupt:HARNESS_RUST_TEST_CORRUPT_RUN_ID' 'bad_revision:HARNESS_RUST_TEST_BAD_REVISION_RUN_ID' 'bad_edge:HARNESS_RUST_TEST_BAD_EDGE_RUN_ID' 'deep:HARNESS_RUST_TEST_DEEP_RUN_ID'; do
  IFS=: read -r key variable <<< "$item"
  value="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$ROOT/fixture.json" "$key")"
  printf -v "$variable" '%s' "$value"
  export "$variable"
done
export HARNESS_RUST_TEST_PG_DSN="host=$ROOT port=59433 dbname=postgres user=rust_readonly connect_timeout=5"
cargo test --manifest-path services/harness/Cargo.toml --locked --offline \
  -p ordivon-harness-pg --test pg_live -- --nocapture
psql "$HARNESS_RUST_TEST_PG_DSN" -Atc "SELECT has_table_privilege(current_user,'$HARNESS_RUST_TEST_SCHEMA.run_events','INSERT'),has_table_privilege(current_user,'$HARNESS_RUST_TEST_SCHEMA.runs','UPDATE')" \
  | grep -Fx 'f|f'
echo 'PG18_PYTHON_WRITE_RUST_READ_ALL_FAIL_CLOSED_PASS'
if [[ "${HARNESS_CONSUMER_FALSIFY_CONTRACT:-}" == 1 ]]; then
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" uv run --project services/harness --offline --locked python \
    services/harness/rust-migration/consumer-acceptance/make_invalid_contract_fixture.py
  export HARNESS_RUST_TEST_INVALID_CONTRACT_RUN_ID="$(python3 -c \
    'import json,sys;print(json.load(open(sys.argv[1]))["invalid_contract"])' "$ROOT/fixture.json")"
  cargo test --manifest-path services/harness/Cargo.toml --locked --offline \
    -p ordivon-harness-pg --test contract_semantic_falsifier -- --ignored --nocapture
fi
