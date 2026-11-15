-- One-time, explicitly operator-selected Harness PG schema extension.
-- Run ONLY with search_path set to the approved Harness schema (never public).
-- Operator separately GRANTs EXECUTE on the one aggregate function to the
-- qualified Runtime PG role AFTER reviewing schema, source cut and role.
-- This creates no independent Job Registry, no Runner and no credential.
BEGIN;
DO $migration$
DECLARE selected_schema text := current_schema();
BEGIN
 IF selected_schema IS NULL
    OR selected_schema IN ('public','information_schema')
    OR selected_schema LIKE 'pg_%'
    OR selected_schema !~ '^[a-z][a-z0-9_]{0,62}$'
 THEN
   RAISE EXCEPTION 'explicit private Harness schema required';
 END IF;
 EXECUTE format(
    'CREATE TABLE IF NOT EXISTS %I.run_workspace_claims (
       harness_run_id text PRIMARY KEY REFERENCES %I.runs(harness_run_id) ON DELETE RESTRICT,
       workspace_id text NOT NULL,
       claim_state text NOT NULL CHECK(claim_state IN (''held'',''released'')),
       registered_at_ms bigint NOT NULL CHECK(registered_at_ms >= 0),
       released_at_ms bigint,
       CHECK ((claim_state=''held'' AND released_at_ms IS NULL)
         OR (claim_state=''released'' AND released_at_ms >= registered_at_ms)))',
    selected_schema, selected_schema
 );
 EXECUTE format(
    'CREATE INDEX IF NOT EXISTS idx_run_workspace_claims_held
       ON %I.run_workspace_claims(workspace_id) WHERE claim_state=''held''',
    selected_schema
 );
 EXECUTE format(
    'CREATE OR REPLACE FUNCTION %I.harness_workspace_unreleased_count(p_workspace_id text)
       RETURNS bigint LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $claim$
       SELECT CASE WHEN EXISTS (
           SELECT 1 FROM %I.runs r
           WHERE r.status NOT IN (''completed'',''stopped'',''failed'')
             AND NOT EXISTS (
                SELECT 1 FROM %I.run_workspace_claims c
                WHERE c.harness_run_id=r.harness_run_id)
         ) THEN (-1)::bigint
         ELSE (SELECT count(*) FROM %I.run_workspace_claims
               WHERE workspace_id=p_workspace_id AND claim_state=''held'')
       END
       $claim$',
    selected_schema, selected_schema, selected_schema, selected_schema
 );
 EXECUTE format(
    'REVOKE ALL ON FUNCTION %I.harness_workspace_unreleased_count(text) FROM PUBLIC',
    selected_schema
 );
END;
$migration$;
COMMIT;
