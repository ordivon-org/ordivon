-- Source-bound native PostgreSQL schema for a NEW, empty Runtime epoch.
-- This is not an automatic SQLite migration or proof of installed authority.
-- The operator must select a dedicated, approved private schema and service
-- role, then separately qualify stage-control AFTER verifying the cutover gates.
-- Never run into public, never promote the stale historical staging schema.
BEGIN;
DO $$
BEGIN
  IF current_schema() IS NULL
      OR current_schema() IN ('public', 'information_schema')
      OR current_schema() LIKE 'pg_%'
  THEN
    RAISE EXCEPTION 'Refusing unscoped Runtime PostgreSQL schema creation';
  END IF;
END
$$;
CREATE TABLE jobs(
 job_id text PRIMARY KEY, principal text NOT NULL,
 client_request_id text NOT NULL, request_digest text NOT NULL,
 operation_digest text NOT NULL, workspace_id text NOT NULL,
 workspace_snapshot_json text NOT NULL, execution_plan_json text NOT NULL,
 execution_plan_digest text NOT NULL, created_at_ms bigint NOT NULL,
 desired_state text NOT NULL CHECK(desired_state IN ('run','cancelled')),
 resolution text, current_attempt_id text, row_version bigint NOT NULL DEFAULT 0,
 UNIQUE(principal,client_request_id));
CREATE TABLE attempts(
 attempt_id text PRIMARY KEY, job_id text NOT NULL REFERENCES jobs(job_id),
 attempt_number bigint NOT NULL CHECK(attempt_number >= 1),
 state text NOT NULL, termination_intent text NOT NULL,
 launch_token_digest text NOT NULL, bundle_digest text, bundle_path text NOT NULL,
 unit_name text UNIQUE NOT NULL, created_at_ms bigint NOT NULL,
 boot_id text, invocation_id text, control_group text,
 main_pid bigint CHECK(main_pid BETWEEN 1 AND 4294967295),
 process_start_identity text, runner_start_digest text,
 infrastructure_error_digest text, started_at_ms bigint CHECK(started_at_ms >= 0),
 row_version bigint NOT NULL DEFAULT 0, result_digest text, exit_code integer,
 finished_at_ms bigint, UNIQUE(job_id,attempt_number));
CREATE TABLE idempotency_keys(
 principal text NOT NULL, client_request_id text NOT NULL,
 operation_digest text NOT NULL, job_id text NOT NULL UNIQUE REFERENCES jobs(job_id),
 created_at_ms bigint NOT NULL, PRIMARY KEY(principal,client_request_id));
CREATE TABLE concurrency_reservations(
 reservation_id text PRIMARY KEY,attempt_id text NOT NULL UNIQUE REFERENCES attempts(attempt_id),
 global_limit bigint NOT NULL,state text NOT NULL, acquired_at_ms bigint NOT NULL,
 state_observed_at_ms bigint NOT NULL, released_at_ms bigint, release_reason text);
CREATE TABLE job_events(
 event_id text PRIMARY KEY,job_id text NOT NULL REFERENCES jobs(job_id),
 attempt_id text REFERENCES attempts(attempt_id),
 event_sequence bigint NOT NULL,event_type text NOT NULL,
 origin text NOT NULL,previous_state text,new_state text,reason_code text NOT NULL,
 detail_json text NOT NULL,detail_digest text NOT NULL,
 observed_at_ms bigint NOT NULL,UNIQUE(job_id,event_sequence));
-- Exact Runtime ReleaseEffect ownership, not an unqualified 'pending' flag.
CREATE TABLE job_runtime_release_effects(
  job_id text PRIMARY KEY REFERENCES jobs(job_id) ON DELETE CASCADE,
  effect_id text NOT NULL UNIQUE,
  contract text NOT NULL,
  request_digest text NOT NULL,
  workspace_id text NOT NULL,
  commit_revision text NOT NULL,
  candidate_manifest_digest text NOT NULL,
  expected_tool_count integer NOT NULL CHECK(expected_tool_count >= 0),
  receipt_path text NOT NULL,
  binding_digest text NOT NULL
);
CREATE INDEX idx_runtime_release_effect_request
  ON job_runtime_release_effects(request_digest,job_id);
CREATE TABLE artifacts(
 artifact_id text PRIMARY KEY,job_id text NOT NULL REFERENCES jobs(job_id),
 attempt_id text NOT NULL REFERENCES attempts(attempt_id),
 kind text NOT NULL DEFAULT 'legacy',relative_path text NOT NULL DEFAULT 'legacy',
 digest text NOT NULL DEFAULT 'sha256:legacy',media_type text NOT NULL DEFAULT 'application/octet-stream',
 byte_length bigint NOT NULL DEFAULT 0 CHECK(byte_length>=0),
 truncated boolean NOT NULL DEFAULT false,
 created_at_ms bigint NOT NULL DEFAULT 0 CHECK(created_at_ms>=0),
 UNIQUE(attempt_id,kind,relative_path));
CREATE TABLE _stage_control(
 id text PRIMARY KEY, state text NOT NULL, source_sha256 text NOT NULL,
 promotion_allowed boolean NOT NULL);
COMMIT;
