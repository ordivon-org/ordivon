#!/usr/bin/env bash
# Real disposable PG18, source-only H2 cross-Run + Runtime close fence checks.
# Never use ORDIVON_PG_DSN, production schema, or installed Runtime service.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
for program in initdb pg_ctl psql runuser uv cargo; do
  command -v "$program" >/dev/null || { echo "missing $program" >&2; exit 2; }
done
test "$(id -u)" -eq 0 || { echo "requires test-only postgres UID switch" >&2; exit 2; }
scratch="$(mktemp -d /tmp/ordivon-h2-consumer-pg18-XXXXXXXX)"
chmod 700 "$scratch"
chown postgres:postgres "$scratch"
started=0
cleanup() {
  if [[ "$started" == 1 ]]; then
    runuser -u postgres -- pg_ctl -D "$scratch/data" -m immediate -w stop >/dev/null || :
  fi
  rm -rf -- "$scratch"
}
trap cleanup EXIT
runuser -u postgres -- initdb -D "$scratch/data" -U postgres -A trust --no-instructions >"$scratch/initdb.log"
# Official PostgreSQL mmap avoids competing POSIX shared-memory resource pressure.
runuser -u postgres -- pg_ctl -D "$scratch/data"   -o "-k $scratch -p 59457 -h '' -c dynamic_shared_memory_type=mmap"   -l "$scratch/server.log" -w start
started=1
dsn="host=$scratch port=59457 dbname=postgres user=postgres connect_timeout=5"
export HARNESS_PG_TEST_DSN="$dsn"
export ORDIVON_PG_TEST_DSN="$dsn"
# First falsify accidental migration into PUBLIC; transaction must roll back.
if psql "$dsn" -v ON_ERROR_STOP=1   -f services/harness/sql/runtime_workspace_consumer_claim_r1.sql   >"$scratch/negative-public.log" 2>&1; then
  echo "unsafe PUBLIC migration unexpectedly succeeded" >&2
  exit 6
fi
grep -q 'explicit private Harness schema required' "$scratch/negative-public.log"
# Exercise the actual one-time SQL migration against a preexisting Harness-
# style Run table (no new production database, no second registry).
psql "$dsn" -v ON_ERROR_STOP=1 -c   'CREATE SCHEMA h2_upgrade; CREATE TABLE h2_upgrade.runs(harness_run_id text PRIMARY KEY,status text NOT NULL);'   >/dev/null
psql "$dsn" -v ON_ERROR_STOP=1 -c 'SET search_path TO h2_upgrade;'   -f services/harness/sql/runtime_workspace_consumer_claim_r1.sql   >"$scratch/migration.log"
# Re-execution is a no-op for existing claims; it cannot erase a held consumer.
psql "$dsn" -v ON_ERROR_STOP=1 -c 'SET search_path TO h2_upgrade;'   -f services/harness/sql/runtime_workspace_consumer_claim_r1.sql   >>"$scratch/migration.log"
psql "$dsn" -v ON_ERROR_STOP=1 -c "INSERT INTO h2_upgrade.runs VALUES ('runA','active');" >/dev/null
psql "$dsn" -v ON_ERROR_STOP=1 -c   "INSERT INTO h2_upgrade.run_workspace_claims VALUES ('runA','ws-shared','held',1,NULL);" >/dev/null
psql "$dsn" -v ON_ERROR_STOP=1 -c 'CREATE ROLE h2_readonly LOGIN;' >/dev/null
psql "$dsn" -v ON_ERROR_STOP=1 -c 'GRANT USAGE ON SCHEMA h2_upgrade TO h2_readonly;' >/dev/null
reader="host=$scratch port=59457 dbname=postgres user=h2_readonly connect_timeout=5"
if psql "$reader" -v ON_ERROR_STOP=1 -Atc   "SELECT h2_upgrade.harness_workspace_unreleased_count('ws-shared')"   >"$scratch/denied.log" 2>&1; then
  echo "Runtime-like reader used ungranted Harness function" >&2
  exit 7
fi
psql "$dsn" -v ON_ERROR_STOP=1 -c   'GRANT EXECUTE ON FUNCTION h2_upgrade.harness_workspace_unreleased_count(text) TO h2_readonly;'   >/dev/null
test "$(psql "$reader" -v ON_ERROR_STOP=1 -Atc   "SELECT h2_upgrade.harness_workspace_unreleased_count('ws-shared')")" = 1
if psql "$reader" -v ON_ERROR_STOP=1 -Atc   'SELECT * FROM h2_upgrade.run_workspace_claims' >"$scratch/forbidden-table.log" 2>&1; then
  echo "Runtime-like reader obtained private Harness table access" >&2
  exit 8
fi
psql "$dsn" -v ON_ERROR_STOP=1 -c   "UPDATE h2_upgrade.run_workspace_claims SET claim_state='released',released_at_ms=2 WHERE harness_run_id='runA';"   >/dev/null
test "$(psql "$reader" -v ON_ERROR_STOP=1 -Atc   "SELECT h2_upgrade.harness_workspace_unreleased_count('ws-shared')")" = 0
# Preserve another independent active Harness Run claim for the original
# Rust consumer. Its service query must see one unrelinquished owner.
psql "$dsn" -v ON_ERROR_STOP=1 -c "INSERT INTO h2_upgrade.runs VALUES ('runB','active');" >/dev/null
psql "$dsn" -v ON_ERROR_STOP=1 -c   "INSERT INTO h2_upgrade.run_workspace_claims VALUES ('runB','ws-shared','held',3,NULL);" >/dev/null
export ORDIVON_H2_TEST_SCHEMA=h2_upgrade
# Unknown historical nonterminal Run with no explicit Workspace classification
# must not produce a deceptive zero. A completed unclassified history is okay.
psql "$dsn" -v ON_ERROR_STOP=1 -c "INSERT INTO h2_upgrade.runs VALUES ('runLegacy','active');" >/dev/null
test "$(psql "$reader" -v ON_ERROR_STOP=1 -Atc   "SELECT h2_upgrade.harness_workspace_unreleased_count('ws-unused')")" = -1
psql "$dsn" -v ON_ERROR_STOP=1 -c   "UPDATE h2_upgrade.runs SET status='completed' WHERE harness_run_id='runLegacy';" >/dev/null
test "$(psql "$reader" -v ON_ERROR_STOP=1 -Atc   "SELECT h2_upgrade.harness_workspace_unreleased_count('ws-unused')")" = 0
echo H2_OPERATOR_MIGRATION_AND_SQL_ROLE_NEGATIVE_PASS
( cd services/harness && uv run --project . --offline --locked python -m pytest -q tests/test_plugin_gateway_effect.py )
CARGO_BUILD_JOBS=2 cargo test --manifest-path services/runtime/Cargo.toml   --locked --offline --features postgres-registry-admission   -p ordivon-runtime-core harness_workspace_close_fence_tests   -- --ignored --nocapture 2>&1 | tee "$scratch/runtime-h2-native-pg.log"
grep -q 'test result: ok. 2 passed' "$scratch/runtime-h2-native-pg.log" || {
  echo "filtered-out Rust test is NOT a physical PASS" >&2
  exit 5
}
echo H2_REAL_DISPOSABLE_PG18_CONSUMER_FENCE_PASS
