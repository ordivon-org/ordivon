#!/usr/bin/env bash
# PostgreSQL 18 baseline; explicit local disposable PostgreSQL 19 qualification.
set -euo pipefail

# The merge-queue and externally supplied DSN remain PG18.
# A new major is a distinct local experiment, not an ambient environment override.
pg_major=18
if (( $# != 0 )); then
  if (( $# == 1 )) && [[ "$1" == "--postgres-major=19" ]]; then
    if [[ "${ORDIVON_HOST_QUEUE_LOCAL_DISPOSABLE:-0}" != "1" ||
          -n "${ORDIVON_HOST_V2_TEST_DSN:-}" ||
          "${GITHUB_ACTIONS:-}" == "true" ]]; then
      echo "HOST_QUEUE_PG19_REQUIRES_LOCAL_DISPOSABLE" >&2
      exit 2
    fi
    pg_major=19
  else
    echo "HOST_QUEUE_INVALID_ARGUMENT" >&2
    exit 2
  fi
fi

container=""
cleanup() {
  if [[ -n "$container" ]]; then
    docker rm -f "$container" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if [[ -z "${ORDIVON_HOST_V2_TEST_DSN:-}" ]]; then
  if [[ "${ORDIVON_HOST_QUEUE_LOCAL_DISPOSABLE:-0}" != "1" &&
      ( "${GITHUB_ACTIONS:-}" != "true" || "${RUNNER_ENVIRONMENT:-}" != "github-hosted" ) ]]; then
    echo "HOST_QUEUE_REQUIRES_TEST_DSN: implicit DB is github-hosted only" >&2
    exit 2
  fi
  for binary in docker openssl psql; do
    if ! command -v "$binary" >/dev/null; then
      echo "HOST_QUEUE_UNAVAILABLE: $binary" >&2
      exit 2
    fi
  done
  # Dynamic identity and loopback-only port: never drop a shared service database.
  identity="ordivon-host-ci-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}-${RANDOM}"
  password="$(openssl rand -hex 24)"
  container="$(docker run --detach --rm --name "$identity" \
    --env POSTGRES_USER=ordivon_ci --env POSTGRES_DB=ordivon_ci \
    --env "POSTGRES_PASSWORD=$password" -p 127.0.0.1::5432 "postgres:$pg_major")"
  image_id="$(docker inspect --format '{{.Image}}' "$container")"
  if [[ ! "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]]; then
    echo "HOST_QUEUE_IMAGE_ID_INVALID" >&2
    exit 4
  fi
  printf 'host_queue_image=%s\n' "$image_id"
  ready=false
  for _ in {1..60}; do
    if docker exec "$container" pg_isready -U ordivon_ci -d ordivon_ci >/dev/null 2>&1; then
      ready=true
      break
    fi
    sleep 1
  done
  if [[ "$ready" != true ]]; then
    echo "HOST_QUEUE_POSTGRES${pg_major}_NOT_READY" >&2
    exit 4
  fi
  binding="$(docker port "$container" 5432/tcp)"
  port="${binding##*:}"
  if [[ ! "$port" =~ ^[0-9]+$ ]]; then
    echo "HOST_QUEUE_POSTGRES${pg_major}_PORT_INVALID" >&2
    exit 4
  fi
  export ORDIVON_HOST_V2_TEST_DSN="postgresql://ordivon_ci:$password@127.0.0.1:$port/ordivon_ci"
fi

# The explicit local disposable-launch opt-in is consumed by this top-level
# launcher only; never pass it to nested queue-governance tests or descendants.
unset ORDIVON_HOST_QUEUE_LOCAL_DISPOSABLE

if ! command -v psql >/dev/null; then
  echo "HOST_QUEUE_REQUIRES_PSQL" >&2
  exit 2
fi
connected=false
pg_version=""
for _ in {1..5}; do
  if pg_version="$(PGCONNECT_TIMEOUT=1 psql -X -Atq "$ORDIVON_HOST_V2_TEST_DSN" -c 'SHOW server_version_num' 2>/dev/null)"; then
    connected=true
    break
  fi
  sleep 1
done
if [[ "$connected" != true ]]; then
  echo "HOST_QUEUE_TEST_DB_CONNECTION_FAILED" >&2
  exit 4
fi
if [[ ! "$pg_version" =~ ^[0-9]+$ ]] || (( pg_version / 10000 != pg_major )); then
  echo "HOST_QUEUE_POSTGRES_MAJOR_INVALID: expected $pg_major" >&2
  exit 4
fi

printf 'host_queue_postgres_major=%s server_version_num=%s\n' "$pg_major" "$pg_version"
# Caller-provisioned complete qualification must have every isolated fixture
# before the first migration. Compare native identity, not textual DSN aliases.
# The owned container path provisions all named databases below.
if [[ -z "$container" ]]; then
  fixture_vars=(
    ORDIVON_HOST_V2_TEST_DSN
    ORDIVON_HOST_V2_BOUNDARY_MESSAGE_DSN
    ORDIVON_HOST_V2_BOUNDARY_CHANGE_DSN
    ORDIVON_HOST_V2_RECEIPT_TEST_DSN
    ORDIVON_HOST_V2_MIGRATION_CLOCK_DSN
    ORDIVON_HOST_V2_MIGRATION_HISTORY_DSN
    ORDIVON_HOST_V2_MIGRATION_ALLOCATOR_DSN
    ORDIVON_HOST_V2_MIGRATION_LOCK_DSN
    ORDIVON_HOST_V2_MIGRATION_STARTUP_DSN
    ORDIVON_HOST_V2_MIGRATION_CJK_DSN
  )
  for fixture in "${fixture_vars[@]}"; do
    if [[ -z "${!fixture:-}" ]]; then
      echo "HOST_QUEUE_FIXTURE_MISSING: $fixture" >&2
      exit 4
    fi
  done
  declare -A observed_db_identities=()
  for fixture in "${fixture_vars[@]}"; do
    if ! identity="$(PGCONNECT_TIMEOUT=5 psql -X -Atq "${!fixture}" -c "
      SELECT current_setting('server_version_num') || ':' ||
        system_identifier::text || ':' ||
        (SELECT oid::text FROM pg_catalog.pg_database WHERE datname=current_database())
      FROM pg_catalog.pg_control_system()
    " 2>/dev/null)" ||
      [[ ! "$identity" =~ ^([0-9]+):([0-9]+):([0-9]+)$ ]]; then
      echo "HOST_QUEUE_FIXTURE_IDENTITY_UNOBSERVABLE: $fixture" >&2
      exit 4
    fi
    if (( ${BASH_REMATCH[1]} / 10000 != pg_version / 10000 )); then
      echo "HOST_QUEUE_FIXTURE_MAJOR_MISMATCH: $fixture" >&2
      exit 4
    fi
    db_key="${BASH_REMATCH[2]}:${BASH_REMATCH[3]}"
    if [[ -v "observed_db_identities[$db_key]" ]]; then
      echo "HOST_QUEUE_FIXTURE_ALIAS: $fixture and ${observed_db_identities[$db_key]}" >&2
      exit 4
    fi
    observed_db_identities[$db_key]="$fixture"
  done
fi

# Alembic owns schema creation; never select unrelated production DSN.
export ORDIVON_HOST_V2_DSN="$ORDIVON_HOST_V2_TEST_DSN"
uv lock --check
uv sync --locked
uv run alembic upgrade head
# Only our fresh disposable container may be filled to coordinate exhaustion.
# Never mutate the capacity of a caller-supplied/shared test database.
if [[ -n "$container" ]]; then
  for domain in message change; do
    database="ordivon_boundary_$domain"
    docker exec "$container" createdb -U ordivon_ci "$database"
    boundary_dsn="postgresql://ordivon_ci:$password@127.0.0.1:$port/$database"
    ORDIVON_HOST_V2_DSN="$boundary_dsn" uv run alembic upgrade head
    if [[ "$domain" == message ]]; then
      export ORDIVON_HOST_V2_BOUNDARY_MESSAGE_DSN="$boundary_dsn"
    else
      export ORDIVON_HOST_V2_BOUNDARY_CHANGE_DSN="$boundary_dsn"
    fi
  done
  # Receipt format activation/rollback tests may change the native fence.
  # Isolate those tests from the ordinary suite and caller-supplied databases.
  database=ordivon_receipt_lifecycle
  docker exec "$container" createdb -U ordivon_ci "$database"
  receipt_dsn="postgresql://ordivon_ci:$password@127.0.0.1:$port/$database"
  ORDIVON_HOST_V2_DSN="$receipt_dsn" uv run alembic upgrade head
  export ORDIVON_HOST_V2_RECEIPT_TEST_DSN="$receipt_dsn"
  # Preserve the original 0014 state in separate destructive negative fixtures.
  for variant in clock history allocator lock startup; do
    database="ordivon_migration_$variant"
    docker exec "$container" createdb -U ordivon_ci "$database"
    migration_dsn="postgresql://ordivon_ci:$password@127.0.0.1:$port/$database"
    # Keep schema-15-specific historical migration fixtures pinned to 0014.
    # The serving negative fixture must exercise the immediately previous schema.
    revision=0014
    if [[ "$variant" == startup ]]; then
      revision=0016
    fi
    ORDIVON_HOST_V2_DSN="$migration_dsn" uv run alembic upgrade "$revision"
    export "ORDIVON_HOST_V2_MIGRATION_${variant^^}_DSN=$migration_dsn"
  done
  # CJK retry tests exercise 0015 -> 0016 even after later schema releases.
  database=ordivon_migration_cjk
  docker exec "$container" createdb -U ordivon_ci "$database"
  cjk_dsn="postgresql://ordivon_ci:$password@127.0.0.1:$port/$database"
  ORDIVON_HOST_V2_DSN="$cjk_dsn" uv run alembic upgrade 0015
  export ORDIVON_HOST_V2_MIGRATION_CJK_DSN="$cjk_dsn"
fi
uv run ruff check .
# Full qualification must not inherit filters or collect-only options.
unset PYTEST_ADDOPTS PYTEST_PLUGINS
# Consume the optional evidence destination at this boundary, not in
# nested queue-governance tests or their child processes.
evidence_dir="${ORDIVON_HOST_QUEUE_EVIDENCE_DIR:-}"
unset ORDIVON_HOST_QUEUE_EVIDENCE_DIR
if [[ -n "$evidence_dir" ]]; then
  uv run python -m pytest --host-require-complete-suite --strict-config --strict-markers \
    -p tools.host_attempt_evidence \
    --host-evidence-dir "$evidence_dir" \
    --junitxml "$evidence_dir/junit.xml"
else
  uv run python -m pytest --host-require-complete-suite --strict-config --strict-markers
fi
