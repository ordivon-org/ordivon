#!/usr/bin/env bash
# Disposable PG18 migration + Rust Host summary MCP end-to-end.
# Does not reuse production credentials or an existing DB.
set -euo pipefail
if [[ -n "${ORDIVON_HOST_V2_DSN:-}" || -n "${ORDIVON_HOST_V2_TEST_DSN:-}" ]]; then
  echo "REFUSE_INHERITED_HOST_DSN" >&2
  exit 2
fi
for binary in docker openssl psql uv cargo python3; do
  command -v "$binary" >/dev/null || { echo "MISSING:$binary" >&2; exit 2; }
done
root="$(git rev-parse --show-toplevel)"
container=""
cleanup() {
  if [[ -n "$container" ]]; then
    docker rm -f "$container" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT
password="$(openssl rand -hex 24)"
identity="ordivon-host-rust-c-$(date +%s)-$RANDOM"
container="$(docker run --detach --rm --name "$identity" \
  --env POSTGRES_USER=host_rust_c --env POSTGRES_DB=host_rust_c \
  --env "POSTGRES_PASSWORD=$password" -p 127.0.0.1::5432 postgres:18)"
ready=0
for _ in {1..60}; do
  if docker exec "$container" pg_isready -U host_rust_c -d host_rust_c >/dev/null 2>&1; then
    ready=1;break
  fi
  sleep 1
done
[[ "$ready" == 1 ]] || { echo "PG18_CONTAINER_NOT_READY" >&2;exit 4; }
binding="$(docker port "$container" 5432/tcp)"
port="${binding##*:}"
[[ "$port" =~ ^[0-9]+$ ]] || exit 5
export ORDIVON_HOST_V2_DSN="postgresql://host_rust_c:$password@127.0.0.1:$port/host_rust_c"
export HOST_RUST_TEST_DSN="$ORDIVON_HOST_V2_DSN"
connected=0
for _ in {1..60}; do
  if PGCONNECT_TIMEOUT=1 psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c "SELECT 1" >/dev/null 2>&1; then
    connected=1;break
  fi
  sleep 1
done
[[ "$connected" == 1 ]] || { echo "PG18_TCP_NOT_READY" >&2; exit 4; }
major="$(psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c 'SHOW server_version_num')"
[[ "$major" =~ ^[0-9]+$ ]] && (( major / 10000 == 18 )) || { echo "PG_NOT_18" >&2;exit 4; }
echo "PG18_READY isolated_dynamic_port"
(
  cd "$root/services/host"
  uv sync --locked --offline --quiet
  uv run --offline alembic upgrade head >/dev/null
)
version="$(psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c 'SELECT schema_version FROM host_v2_schema WHERE singleton')"
[[ "$version" == 13 ]] || { echo "SCHEMA_NOT_13:$version" >&2;exit 5; }
echo "ALEMBIC_0001_TO_0013_PASS"
cargo build --manifest-path "$root/services/host/rust/Cargo.toml" --offline --quiet
host_rust_binary="$(bash "$root/services/host/rust/tools/rust_binary_path.sh")"
test -x "$host_rust_binary"

cargo test --manifest-path "$root/services/host/rust/Cargo.toml" --offline --test status_pg -- --ignored
cargo test --manifest-path "$root/services/host/rust/Cargo.toml" --offline --test work_pg -- --ignored
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/python_work_oracle.py" seed)
python3 "$root/services/host/rust/tools/mcp_stdio_smoke.py" \
    "$host_rust_binary"
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/python_work_oracle.py" verify)
python3 "$root/services/host/rust/tools/mcp_http_smoke.py"     "$host_rust_binary"
echo "PG18_RUST_MCP_VERIFIED"
