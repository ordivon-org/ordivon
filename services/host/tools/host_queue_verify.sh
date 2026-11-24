#!/usr/bin/env bash
# PostgreSQL 18 qualification for Host merge-queue tests.
set -euo pipefail

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
    --env "POSTGRES_PASSWORD=$password" -p 127.0.0.1::5432 postgres:18)"
  ready=false
  for _ in {1..60}; do
    if docker exec "$container" pg_isready -U ordivon_ci -d ordivon_ci >/dev/null 2>&1; then
      ready=true
      break
    fi
    sleep 1
  done
  if [[ "$ready" != true ]]; then
    echo "HOST_QUEUE_POSTGRES18_NOT_READY" >&2
    exit 4
  fi
  binding="$(docker port "$container" 5432/tcp)"
  port="${binding##*:}"
  if [[ ! "$port" =~ ^[0-9]+$ ]]; then
    echo "HOST_QUEUE_POSTGRES18_PORT_INVALID" >&2
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
if [[ ! "$pg_version" =~ ^[0-9]+$ ]] || (( pg_version / 10000 != 18 )); then
  echo "HOST_QUEUE_POSTGRES_MAJOR_INVALID: expected 18" >&2
  exit 4
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
  # Preserve the original 0014 state in separate destructive negative fixtures.
  for variant in clock history allocator lock; do
    database="ordivon_migration_$variant"
    docker exec "$container" createdb -U ordivon_ci "$database"
    migration_dsn="postgresql://ordivon_ci:$password@127.0.0.1:$port/$database"
    ORDIVON_HOST_V2_DSN="$migration_dsn" uv run alembic upgrade 0014
    export "ORDIVON_HOST_V2_MIGRATION_${variant^^}_DSN=$migration_dsn"
  done
fi
uv run ruff check .
uv run python -m pytest
