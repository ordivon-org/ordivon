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
oracle="$root/services/host/rust/tests/.r2_python_oracle_runtime.json"
doctor_oracle="$root/services/host/rust/tests/.r5_doctor_oracle_runtime.json"
read_search_oracle="$root/services/host/rust/tests/.r5_mcp_message_observed_runtime.json"
engagement_oracle="$root/services/host/rust/tests/.r7_mcp_engagement_observed_runtime.json"
cleanup() {
  rm -f "$oracle" "$doctor_oracle" "$read_search_oracle" "$engagement_oracle"
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
cargo test --manifest-path "$root/services/host/rust/Cargo.toml" --offline --test status_pg -- --ignored --test-threads=1
cargo test --manifest-path "$root/services/host/rust/Cargo.toml" --offline --test work_pg -- --ignored --test-threads=1
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tests/actor_python_parity.py")
cargo test --manifest-path "$root/services/host/rust/Cargo.toml" --offline --test social_attention_pg -- --ignored --test-threads=1
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tests/social_native_python_replay.py")
echo "R2_WORK_SOCIAL_ATTENTION_PG18_PASS"
cargo test --manifest-path "$root/services/host/rust/Cargo.toml" --locked --offline --test work_engagement_pg -- --ignored --test-threads=1
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tests/work_engagement_python_readback.py")
echo "R7_WORK_ENGAGEMENT_DOMAIN_AND_ORIGINAL_PYTHON_PASS"
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tests/python_oracle.py" seed "$oracle")
export HOST_RUST_PYTHON_ORACLE_PATH="$oracle"
cargo test --manifest-path "$root/services/host/rust/Cargo.toml" --offline --test work_python_parity -- --ignored --test-threads=1
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tests/python_oracle.py" verify)
echo "R2_PYTHON_RUST_BIDIRECTIONAL_PASS"
cargo build --manifest-path "$root/services/host/rust/Cargo.toml" --offline --quiet
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tests/attention_mcp_cross_language.py" "$root/services/host/rust/target/debug/ordivon-host-rust")
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/sync_python_output_contracts.py" --check)
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/audit_mcp_surface.py" \
  --rust-bin "$root/services/host/rust/target/debug/ordivon-host-rust" \
  --source-manifest "$root/services/host/mcp-surface.json" \
  --extension work.engagement.advance --extension work.engagement.list \
  --report "$root/services/host/rust/planning/mcp_source_rust_r7.json")
echo "R7_MCP_SOURCE_VS_NATIVE_EXTENSIONS_TYPED_PARITY_PASS"
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/python_work_oracle.py" seed)
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/python_social_oracle.py" seed)
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/python_status_doctor_oracle.py" seed "$doctor_oracle")
export HOST_RUST_DOCTOR_ORACLE_PATH="$doctor_oracle"
export HOST_RUST_READ_SEARCH_ORACLE_PATH="$read_search_oracle"
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/mcp_stdio_smoke.py" "$root/services/host/rust/target/debug/ordivon-host-rust")
export HOST_RUST_ENGAGEMENT_OBSERVED_PATH="$engagement_oracle"
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/mcp_engagement_stdio_smoke.py" "$root/services/host/rust/target/debug/ordivon-host-rust")
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/python_native_collaboration_oracle.py")
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/python_social_oracle.py" verify)
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/python_work_oracle.py" verify)
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/python_status_doctor_oracle.py" verify)
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/mcp_http_smoke.py" "$root/services/host/rust/target/debug/ordivon-host-rust")
# Gateway's real MCP SDK transport + actual Rust HTTP owner + real disposable PG,
# after Rust's own MCP integration has seeded and checked all direct results.
(cd "$root/services/gateway" && uv sync --locked --offline --quiet && uv run --offline python "$root/services/host/rust/tools/gateway_rust_owner_consumer_smoke.py" "$root/services/host/rust/target/debug/ordivon-host-rust")
(cd "$root/services/host" && uv run --offline python "$root/services/host/rust/tools/python_mcp_engagement_oracle.py")
echo "R7_NATIVE_MCP_STDIO_HTTP_ENGAGEMENT_PYTHON_CONSUMER_PASS"
echo "R2_MCP_STDIO_HTTP_PASS"
echo "R2_DISPOSABLE_INTEGRATION_ALL_PASS"
