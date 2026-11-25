#!/usr/bin/env bash
# Only the job-owned service container is an eligible target. No DSN input,
# adoption, fallback, DROP, or retry against a partially provisioned database.
set -euo pipefail
service_id="${CI_PAPER_SERVICE_ID-}"
lease="${ORDIVON_CAPITAL_TEST_LEASE-}"
if [[ ! "$service_id" =~ ^[0-9a-f]{64}$ || ! "$lease" =~ ^[0-9a-f]{64}$ ]]; then
    echo "CI Paper PostgreSQL provisioner requires exact service identity and fresh lease" >&2
    exit 2
fi
# The trusted Actions job supplies the service id. The fixed socket is inside
# that container, never an inherited host DSN. Do not print token or SQL errors
# that might contain the token. Failure requires a new disposable job.
if ! {
    cat <<'SQL' &&
DO $guard$
BEGIN
    IF current_setting('server_version_num')::integer / 10000 <> 18
       OR current_database() <> 'postgres' OR current_user <> 'postgres'
       OR pg_is_in_recovery() THEN
        RAISE EXCEPTION 'unexpected CI PostgreSQL bootstrap identity';
    END IF;
END
$guard$;
CREATE DATABASE ordivon_paper TEMPLATE template0;
SQL
    printf "COMMENT ON DATABASE ordivon_paper IS 'ordivon-capital-test:v1:%s:ordivon_paper';\n" "$lease"
} | docker exec -i "$service_id" psql -X -q -v ON_ERROR_STOP=1 \
    --host=/var/run/postgresql --port=5432 --username=postgres --dbname=postgres >/dev/null 2>&1; then
    echo "CI Paper PostgreSQL provisioning failed; fresh job required" >&2
    exit 1
fi
echo "CI_PAPER_POSTGRES_PROVISIONED=1"
