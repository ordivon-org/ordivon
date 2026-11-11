#!/usr/bin/env bash
# Isolated Host Rust R2 Work+Social+Attention+MCP integration qualification.
set -euo pipefail
if [[ -n "${ORDIVON_HOST_V2_DSN:-}" || -n "${ORDIVON_HOST_V2_TEST_DSN:-}" || -n "${HOST_RUST_TEST_DSN:-}" ]]; then
  echo "REFUSE_INHERITED_PG_DSN" >&2
  exit 2
fi
for executable in docker openssl psql uv cargo python3; do command -v "$executable" >/dev/null || exit 3; done
root="$(git rev-parse --show-toplevel)"
name="host-rust-r2-$(date +%s)-$RANDOM"
container=""
oracle="$root/services/host-rust/tests/.r2_python_oracle_runtime.json"
cleanup() {
  rm -f "$oracle"
  if [[ -n "$container" ]]; then docker rm -f "$container" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT
password="$(openssl rand -hex 24)"
container="$(docker run --detach --rm --name "$name"   --env POSTGRES_USER=host_rust_r2 --env POSTGRES_DB=host_rust_r2   --env "POSTGRES_PASSWORD=$password" -p 127.0.0.1::5432 postgres:18)"
port="$(docker port "$container" 5432/tcp | awk -F: 'NR==1 {print $NF}')"
[[ "$port" =~ ^[0-9]+$ ]] || exit 5
export ORDIVON_HOST_V2_DSN="postgresql://host_rust_r2:$password@127.0.0.1:$port/host_rust_r2"
export HOST_RUST_TEST_DSN="$ORDIVON_HOST_V2_DSN"
connected=0
for _ in {1..90}; do
  if PGCONNECT_TIMEOUT=1 psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c "SELECT 1" 2>/dev/null | grep -qx 1; then connected=1; break; fi
  sleep 0.3
done
[[ "$connected" == 1 ]] || { echo PG_TCP_NOT_READY; exit 6; }
major="$(psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c 'SHOW server_version_num')"
(( major / 10000 == 18 )) || exit 7
echo "PG18_DISPOSABLE_CONNECTION_PASS"
(cd "$root/services/host" && uv sync --locked --offline --quiet && uv run --offline alembic upgrade head >/dev/null)
[[ "$(psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c 'SELECT schema_version FROM host_v2_schema WHERE singleton')" == 13 ]] || exit 8
echo "ALEMBIC_SCHEMA13_PASS"
cargo test --manifest-path "$root/services/host-rust/Cargo.toml" --offline --test status_pg -- --ignored --test-threads=1
cargo test --manifest-path "$root/services/host-rust/Cargo.toml" --offline --test work_pg -- --ignored --test-threads=1
cargo test --manifest-path "$root/services/host-rust/Cargo.toml" --offline --test social_attention_pg -- --ignored --test-threads=1
echo "R2_WORK_SOCIAL_ATTENTION_PG18_PASS"
(cd "$root/services/host" && uv run --offline python "$root/services/host-rust/tests/python_oracle.py" seed "$oracle")
export HOST_RUST_PYTHON_ORACLE_PATH="$oracle"
cargo test --manifest-path "$root/services/host-rust/Cargo.toml" --offline --test work_python_parity -- --ignored --test-threads=1
(cd "$root/services/host" && uv run --offline python "$root/services/host-rust/tests/python_oracle.py" verify)
echo "R2_PYTHON_RUST_BIDIRECTIONAL_PASS"
cargo build --manifest-path "$root/services/host-rust/Cargo.toml" --offline --quiet
(cd "$root/services/host" && uv run --offline python "$root/services/host-rust/tools/python_work_oracle.py" seed)
python3 "$root/services/host-rust/tools/mcp_stdio_smoke.py" "$root/services/host-rust/target/debug/ordivon-host-rust"
(cd "$root/services/host" && uv run --offline python "$root/services/host-rust/tools/python_work_oracle.py" verify)
python3 "$root/services/host-rust/tools/mcp_http_smoke.py" "$root/services/host-rust/target/debug/ordivon-host-rust"
echo "R2_MCP_STDIO_HTTP_PASS"
echo "R2_DISPOSABLE_INTEGRATION_ALL_PASS"
