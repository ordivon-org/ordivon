#!/usr/bin/env bash
# Opt-in negative test / strict release gate, never production Host.
set -euo pipefail
if [[ -n "$(printenv ORDIVON_HOST_V2_DSN || true)" || -n "$(printenv ORDIVON_HOST_V2_TEST_DSN || true)" || -n "$(printenv HOST_RUST_TEST_DSN || true)" ]]; then
  echo REFUSE_INHERITED_HOST_DSN >&2
  exit 2
fi
for dep in docker psql uv cargo openssl; do command -v "$dep" >/dev/null; done
root="$(git rev-parse --show-toplevel)"
name="host-r10-actor-$(date +%s)-$RANDOM"
password="$(openssl rand -hex 24)"
container=""
cleanup() { if [[ -n "$container" ]]; then docker rm -f "$container" >/dev/null 2>&1 || true; fi; }
trap cleanup EXIT
container="$(docker run -d --rm --name "$name" \
 -e POSTGRES_USER=actor_probe -e POSTGRES_DB=actor_probe \
 -e "POSTGRES_PASSWORD=$password" -p 127.0.0.1::5432 postgres:18)"
port="$(docker port "$container" 5432/tcp | awk -F: 'NR==1 {print $NF}')"
[[ "$port" =~ ^[0-9]+$ ]] || exit 3
export ORDIVON_HOST_V2_DSN="postgresql://actor_probe:$password@127.0.0.1:$port/actor_probe"
export HOST_RUST_TEST_DSN="$ORDIVON_HOST_V2_DSN"
export ORDIVON_TEST_DISPOSABLE_PG18=yes
for _ in {1..80}; do
  if PGCONNECT_TIMEOUT=1 psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c 'SELECT 1' 2>/dev/null | grep -qx 1; then break; fi
  sleep 0.25
done
test "$(psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c 'SHOW server_version_num')" -ge 180000
(cd "$root/services/host" && uv sync --locked --offline --quiet && uv run --offline alembic upgrade head >/dev/null)
test "$(psql -X -Atq "$ORDIVON_HOST_V2_DSN" -c 'SELECT schema_version FROM host_v2_schema WHERE singleton')" = 13
cargo build --manifest-path "$root/services/host/rust/Cargo.toml" --locked --offline --quiet
echo R10_DISPOSABLE_PG18_ACTORREF_PROBE_READY
(cd "$root/services/host" && uv run --offline python \
  rust/tests/actorref_identity_consumer_probe.py \
  "$root/services/host/rust/target/debug/ordivon-host-rust" "$@")
