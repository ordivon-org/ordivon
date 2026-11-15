#!/usr/bin/env bash
# Work lifecycle proposal against unmodified Host PostgreSQL Schema 13.
set -euo pipefail
if [[ -n "$(printenv ORDIVON_HOST_V2_DSN || true)" || -n "$(printenv ORDIVON_HOST_V2_TEST_DSN || true)" || -n "$(printenv HOST_RUST_TEST_DSN || true)" ]]; then
  echo "REFUSE_INHERITED_OR_PRODUCTION_HOST_DSN" >&2
  exit 2
fi
for dep in docker psql openssl uv cargo; do command -v "$dep" >/dev/null; done
root="$(git rev-parse --show-toplevel)"
name="host-engagement-r7-$(date +%s)-$RANDOM"
password="$(openssl rand -hex 24)"
container=""
cleanup() { if [[ -n "$container" ]]; then docker rm -f "$container" >/dev/null 2>&1 || true; fi; }
trap cleanup EXIT
container="$(docker run -d --rm --name "$name" \
    -e POSTGRES_USER=engagement -e POSTGRES_DB=engagement \
    -e "POSTGRES_PASSWORD=$password" -p 127.0.0.1::5432 postgres:18)"
port="$(docker port "$container" 5432/tcp | awk -F: 'NR==1 {print $NF}')"
[[ "$port" =~ ^[0-9]+$ ]] || exit 3
export ORDIVON_HOST_V2_DSN="postgresql://engagement:$password@127.0.0.1:$port/engagement"
export HOST_RUST_TEST_DSN="$ORDIVON_HOST_V2_DSN"
for _ in {1..100}; do
  if PGCONNECT_TIMEOUT=1 psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c 'SELECT 1' 2>/dev/null | grep -qx 1; then break; fi
  sleep 0.25
done
test "$(psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c 'SHOW server_version_num')" -ge 180000
(cd "$root/services/host" && uv sync --locked --offline --quiet && uv run --offline alembic upgrade head >/dev/null)
test "$(psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c 'SELECT schema_version FROM host_v2_schema WHERE singleton')" = 13
echo "R7_UNMODIFIED_SCHEMA13_ADMITTED"
cargo test --manifest-path "$root/services/host/rust/Cargo.toml" --locked --offline --test work_engagement_pg -- --ignored --test-threads=1
(cd "$root/services/host" && uv run --offline python rust/tests/work_engagement_python_readback.py)
echo "R7_WORK_OFFER_CLAIM_SUBMIT_REVIEW_ACCEPT_REAL_PG18_GREEN"
