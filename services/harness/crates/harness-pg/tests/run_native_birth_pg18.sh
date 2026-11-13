#!/usr/bin/env bash
# Rust-native Harness Run PG18 smoke. Disposable local cluster; never production.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
for command in initdb pg_ctl psql runuser cargo; do
  command -v "$command" >/dev/null
done
test "$(id -u)" = 0
ROOT="$(mktemp -d /var/tmp/ordivon-harness-native-pg18-XXXXXXXX)"
chmod 700 "$ROOT"
chown postgres:postgres "$ROOT"
started=0
cleanup() {
  if [[ "$started" == 1 ]]; then
    runuser -u postgres -- pg_ctl -D "$ROOT/data" -m immediate -w stop >/dev/null 2>&1 || true
  fi
  rm -rf -- "$ROOT"
}
trap cleanup EXIT
port=$((31000 + $$ % 23000))
runuser -u postgres -- initdb -D "$ROOT/data" -U postgres -A trust --no-instructions > "$ROOT/init.log"
runuser -u postgres -- pg_ctl -D "$ROOT/data" -o "-k $ROOT -p $port -h ''" -l "$ROOT/server.log" -w start >/dev/null
started=1
dsn="host=$ROOT port=$port dbname=postgres user=postgres connect_timeout=5"
psql "$dsn" -v ON_ERROR_STOP=1 > "$ROOT/setup.log" <<'SQL'
CREATE SCHEMA harness_native;
SET search_path TO harness_native;
CREATE TABLE schema_info(key text PRIMARY KEY,value text NOT NULL);
INSERT INTO schema_info VALUES('schema_version','1');
CREATE TABLE objects(
  digest text PRIMARY KEY,kind text NOT NULL,byte_length bigint NOT NULL CHECK(byte_length>=0),
  content bytea NOT NULL,first_seen_at_ms bigint NOT NULL CHECK(first_seen_at_ms>=0)
);
CREATE TABLE runs(
  harness_run_id text PRIMARY KEY,contract_digest text NOT NULL UNIQUE,
  contract_object_digest text NOT NULL REFERENCES objects(digest),
  caller_id text NOT NULL,caller_run_ref text NOT NULL,status text NOT NULL,
  revision bigint NOT NULL CHECK(revision>=1),created_at_ms bigint NOT NULL CHECK(created_at_ms>=0),
  updated_at_ms bigint NOT NULL CHECK(updated_at_ms>=created_at_ms),
  terminal_event_id text,UNIQUE(caller_id,caller_run_ref)
);
CREATE TABLE run_events(
  sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id text NOT NULL UNIQUE,
  harness_run_id text NOT NULL REFERENCES runs(harness_run_id) ON DELETE CASCADE,
  run_revision bigint NOT NULL CHECK(run_revision>=1),event_kind text NOT NULL,
  payload_digest text NOT NULL REFERENCES objects(digest),
  caused_by_event_id text REFERENCES run_events(event_id),
  recorded_at_ms bigint NOT NULL CHECK(recorded_at_ms>=0),UNIQUE(harness_run_id,run_revision)
);
CREATE TABLE run_object_refs(
  harness_run_id text NOT NULL REFERENCES runs(harness_run_id) ON DELETE CASCADE,
  event_id text NOT NULL REFERENCES run_events(event_id) ON DELETE CASCADE,
  digest text NOT NULL REFERENCES objects(digest),
  role text NOT NULL CHECK(role IN ('payload','reference')),PRIMARY KEY(event_id,digest)
);
CREATE UNIQUE INDEX run_object_refs_one_payload ON run_object_refs(event_id) WHERE role='payload';
CREATE TABLE run_leases(
  harness_run_id text PRIMARY KEY REFERENCES runs(harness_run_id) ON DELETE CASCADE,
  owner_id text NOT NULL,lease_revision bigint NOT NULL CHECK(lease_revision>=1),
  run_revision bigint NOT NULL CHECK(run_revision>=1),expires_at_ms bigint NOT NULL CHECK(expires_at_ms>=0)
);
SQL
export HARNESS_RUST_NATIVE_PG_DSN="$dsn" HARNESS_RUST_NATIVE_PG_SCHEMA=harness_native
cargo fmt --manifest-path services/harness/Cargo.toml --all -- --check
cargo test --manifest-path services/harness/Cargo.toml --locked --offline \
  -p ordivon-harness-pg --test native_birth_pg18 -- --ignored --nocapture
printf 'RUST_ONLY_DISPOSABLE_PG18_RUN_BIRTH_GREEN\n'

# Exercise actual installed-shape Rust binary create/status/inspect in the
# SAME disposable PG18 authority: no Python, no SQLite, no compatibility CLI.
cargo build --manifest-path services/harness/Cargo.toml --locked --offline \
  -p ordivon-harness-cli --bin ordivon-harness
zero="$(printf '%064d' 0)"
cat > "$ROOT/contract-native.json" <<JSON
{
 "schemaVersion":2,"kind":"ordivon.harness-run-contract",
 "harnessRunId":"harness-run:native-cli-smoke",
 "harnessImplementationId":"rust-cli","callerId":"caller:rust-cli",
 "callerRunRef":"native-cli-one",
 "objectiveRef":{"ref":"objective:one","kind":"objective","digest":"sha256:$zero"},
 "contextRefs":[{"ref":"context:one","kind":"context","digest":"sha256:$zero"}],
 "providerId":"provider:script","adapterId":"adapter:rust","requestedModelId":"model",
 "toolCatalogDigest":"sha256:$zero","toolGrantDigest":"sha256:$zero",
 "budget":{"maxTurns":2},"completionContract":{"mode":"plain-text"},
 "systemManifestRef":{"ref":"manifest:one","kind":"system-manifest","digest":"sha256:$zero"},
 "createdAtMs":2000,"sourceRefs":[],"priorArtifactRefs":[],
 "privacy":{"contentPolicy":"metadata-only","allowModelContent":false,"allowToolContent":false},
 "deadlineMs":null
}
JSON
export HARNESS_PG_DSN="$dsn" HARNESS_PG_SCHEMA=harness_native
target_dir="$(cargo metadata --manifest-path services/harness/Cargo.toml --no-deps --locked --offline --format-version 1 | python3 -c 'import json,sys;print(json.load(sys.stdin)["target_directory"])')"
binary="$target_dir/debug/ordivon-harness"
test -x "$binary"
"$binary" create "$ROOT/contract-native.json" | grep -F '"admission":"created"'
"$binary" create "$ROOT/contract-native.json" | grep -F '"admission":"existing"'
"$binary" status harness-run:native-cli-smoke | grep -F '"status":"created"'
"$binary" inspect harness-run:native-cli-smoke | grep -F '"eventCount":1'
sed 's/native-cli-one/native-cli-forged/' "$ROOT/contract-native.json" > "$ROOT/forged.json"
if "$binary" create "$ROOT/forged.json" > "$ROOT/forged-out" 2>&1; then
  echo "changed native Run Contract wrongly admitted" >&2
  exit 1
fi
"$binary" inspect harness-run:native-cli-smoke | grep -F '"eventCount":1'
printf 'RUST_ONLY_NATIVE_CLI_PHYSICAL_PG18_PASS\n'
