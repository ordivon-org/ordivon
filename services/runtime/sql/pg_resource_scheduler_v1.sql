-- Operator migration inside the selected Runtime schema, never public.
-- Apply with schema-owner authority; independently qualify the migrated source and physical writer epoch.
BEGIN;
DO $$ BEGIN IF current_schema() IS NULL OR current_schema() IN ('public','information_schema') OR current_schema() LIKE 'pg_%' THEN RAISE EXCEPTION 'explicit Runtime schema required'; END IF; END $$;
CREATE TABLE job_allocations(
 attempt_id text PRIMARY KEY REFERENCES attempts(attempt_id),
 resources_json text NOT NULL,workspace_access_json text NOT NULL,owner text NOT NULL,
 state text NOT NULL CHECK(state IN ('active','released')),
 acquired_at_ms bigint NOT NULL,released_at_ms bigint);
CREATE INDEX idx_job_allocations_active ON job_allocations(state,attempt_id);
COMMIT;
