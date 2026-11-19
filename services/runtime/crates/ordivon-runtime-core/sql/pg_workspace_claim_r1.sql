-- Operator-approved additive Runtime PG schema upgrade for source-qualified
-- Release only. Must run in the SAME Runtime database/schema as jobs.
-- Grant DML privileges to the independently qualified Runtime app role before
-- deploying a binary that expects this table. Never apply to Harness DB.
BEGIN;
DO $$ BEGIN
 IF current_schema() IS NULL OR current_schema() IN ('public','information_schema')
    OR current_schema() LIKE 'pg_%' THEN
   RAISE EXCEPTION 'Refusing unscoped Runtime Workspace Claim schema upgrade';
 END IF;
END $$;
CREATE TABLE workspace_consumer_claims(
 claim_id text PRIMARY KEY, principal text NOT NULL,
 client_request_id text NOT NULL, store_root text NOT NULL, workspace_id text NOT NULL,
 run_ref text NOT NULL, source_repo text NOT NULL, source_revision text NOT NULL,
 source_state_digest text NOT NULL,
 state text NOT NULL CHECK(state IN ('held','released')),
 created_at_ms bigint NOT NULL, updated_at_ms bigint NOT NULL,
 UNIQUE(principal,client_request_id));
CREATE INDEX idx_workspace_consumer_claims_held
 ON workspace_consumer_claims(store_root,workspace_id) WHERE state='held';
COMMIT;
