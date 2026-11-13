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
  export HARNESS_RUST_TEST_INVALID_CONTRACT_CASES="$(python3 -c \
    'import json,sys;cases=json.load(open(sys.argv[1]))["invalid_contract_cases"];print(chr(10).join(k+"|"+v for k,v in sorted(cases.items())))' "$ROOT/fixture.json")"
  export HARNESS_RUST_TEST_VALID_CONTRACT_CASES="$(python3 -c \
    'import json,sys;cases=json.load(open(sys.argv[1]))["positive_contract_cases"];print(chr(10).join(k+"|"+v for k,v in sorted(cases.items())))' "$ROOT/fixture.json")"
  cargo test --manifest-path services/harness/Cargo.toml --locked --offline \
    -p ordivon-harness-pg --test contract_semantic_falsifier -- --ignored --nocapture
fi

# Test-only contribution to the existing A-owned PG v1 Store/Lease port.
# This uses the SAME disposable PostgreSQL18 cluster and Python Store schema.
if [[ "${HARNESS_PG_NATIVE_LEASE:-}" == 1 ]]; then
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" uv run --project services/harness --offline --locked python \
    services/harness/crates/harness-pg/tests/lease_python_store.py prepare
  export HARNESS_RUST_TEST_PG_READONLY_DSN="$HARNESS_RUST_TEST_PG_DSN"
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" cargo test \
    --manifest-path services/harness/Cargo.toml --locked --offline \
    -p ordivon-harness-pg --test pg_lease_live native_run_lease_owner_race_revision_expiry_cross_language -- --ignored --nocapture
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" uv run --project services/harness --offline --locked python \
    services/harness/crates/harness-pg/tests/lease_python_store.py verify
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" cargo test \
    --manifest-path services/harness/Cargo.toml --locked --offline \
    -p ordivon-harness-pg --test pg_lease_live python_journal_consumed_rust_native_lease_then_rust_replay -- --ignored --nocapture
  echo 'PG18_RUST_LEASE_PYTHON_JOURNAL_CROSS_CONSUMER_PASS'
fi

# Optional real PG18 source->Rust native Event Writer->Python legacy reader.
if [[ "$(printenv HARNESS_PG_NATIVE_WRITER || true)" == 1 ]]; then
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" uv run --project services/harness --offline --locked python     services/harness/crates/harness-pg/tests/journal_writer_python_store.py prepare
  export HARNESS_RUST_TEST_PG_READONLY_DSN="$HARNESS_RUST_TEST_PG_DSN"
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" cargo test     --manifest-path services/harness/Cargo.toml --locked --offline     -p ordivon-harness-pg --test pg_writer_live -- --ignored --nocapture --test-threads=1
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" uv run --project services/harness --offline --locked python     services/harness/crates/harness-pg/tests/journal_writer_python_store.py verify
  echo PG18_NATIVE_RUST_WRITER_PYTHON_STORE_INTEROP_PASS
fi
# B consumer extension: reuse this SAME disposable A-owned PG instance.
# Opt-in only: no second PG bootstrap, Schema owner, writer, or Tool effect.
if [[ "${HARNESS_B_BOUND_PG_DOMAIN:-}" == 1 ]]; then
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" uv run --project services/harness --offline --locked python \
    services/harness/crates/harness-loop/tests/pg_domain_python_store.py
  cargo test --manifest-path services/harness/Cargo.toml --locked --offline \
    -p ordivon-harness-loop --test pg_domain_readback -- --ignored --nocapture
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" uv run --project services/harness --offline --locked python \
    services/harness/crates/harness-loop/tests/pg_provider_v4_python_store.py
  # The native Writer test uses the same PG source fixtures but requires
  # a separate test-authorized writer DSN; all Provider reads still use
  # rust_readonly. No physical Provider/Runtime requests are sent.
  HARNESS_RUST_TEST_PG_WRITER_DSN="$writer_dsn" \
    cargo test --manifest-path services/harness/Cargo.toml --locked --offline \
      -p ordivon-harness-loop --test pg_provider_head -- --ignored --nocapture
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" uv run --project services/harness --offline --locked python \
    services/harness/crates/harness-loop/tests/pg_provider_v4_python_store.py verify-native
fi

# Independent optional Writer semantic gate falsification, not production.
if [[ "$(printenv HARNESS_WRITER_CONTRACT_FALSIFY || true)" == 1 ]]; then
  if [[ "$(printenv HARNESS_CONSUMER_FALSIFY_CONTRACT || true)" != 1 ]]; then
    echo "Writer Contract falsifier requires Python-invalid Contract corpus" >&2
    exit 2
  fi
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" cargo test \
    --manifest-path services/harness/Cargo.toml --locked --offline \
    -p ordivon-harness-pg --test pg_writer_contract_gate \
    -- --ignored --nocapture
fi


# B typed Tool consumer reuses A's ONE disposable PG18, Python Source producer,
# and SELECT-only Rust role. Cannot grant any Runtime execution.
if [[ "$(printenv HARNESS_B_TYPED_TOOL_HEAD || true)" == 1 ]]; then
  if [[ "$(printenv HARNESS_B_BOUND_PG_DOMAIN || true)" != 1 ]]; then
    echo "Typed Tool consumer requires B's existing PG source fixture" >&2
    exit 2
  fi
  HARNESS_RUST_TEST_PG_DSN="$writer_dsn" uv run     --project services/harness --offline --locked python     services/harness/crates/harness-loop/tests/pg_tool_head_python_store.py
  cargo test --manifest-path services/harness/Cargo.toml --locked --offline     -p ordivon-harness-loop --test pg_tool_head     -- --ignored --nocapture
fi

# Provider-only path: real Python PG18 NoTool Contract -> Rust HTTP -> native Loop.
# Uses the same disposable PostgreSQL cluster; no production DSN.
if [[ "${HARNESS_B_BOUND_PG_DOMAIN:-}" == 1 ]]; then
  cargo test --manifest-path services/harness/Cargo.toml --locked --offline \
    -p ordivon-harness-loop --test native_pg_no_tool_http -- --ignored --nocapture
fi
