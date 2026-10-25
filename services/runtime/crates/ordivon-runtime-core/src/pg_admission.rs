//! Native PostgreSQL Runtime admission contract, NOT production authority.
//! Explicitly opt-in until the full lifecycle/refinement/consumer proof exists.
use postgres::{Client, IsolationLevel, NoTls};
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use uuid::Uuid;

#[derive(Debug)]
pub enum PgAdmissionError {
    InvalidInput,
    Unqualified,
    Capacity,
    IdempotencyConflict,
    PendingEffect,
    Blocked,
    UnknownCommit,
    Database(postgres::Error),
}
impl From<postgres::Error> for PgAdmissionError {
    fn from(error: postgres::Error) -> Self {
        Self::Database(error)
    }
}

#[derive(Clone)]
pub struct PgAdmissionInput {
    pub job_id: String,
    pub attempt_id: String,
    pub reservation_id: String,
    pub principal: String,
    pub client_request_id: String,
    pub request_digest: String,
    pub operation_digest: String,
    pub workspace_id: String,
    pub workspace_snapshot_json: String,
    pub execution_plan_json: String,
    pub execution_plan_digest: String,
    pub launch_token_digest: String,
    pub bundle_path: String,
    pub unit_name: String,
    pub global_limit: i32,
    pub created_at_ms: i64,
    pub expected_source_sha256: String,
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgAdmissionOutcome {
    Created(String),
    Existing(String),
}

fn exact_schema(s: &str) -> bool {
    !matches!(s, "public" | "information_schema")
        && !s.starts_with("pg_")
        && !s.is_empty()
        && s.len() <= 63
        && s.as_bytes()[0].is_ascii_alphabetic()
        && s.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'_')
}
impl PgAdmissionInput {
    fn validate(&self) -> Result<(), PgAdmissionError> {
        let strings = [
            &self.job_id,
            &self.attempt_id,
            &self.reservation_id,
            &self.principal,
            &self.client_request_id,
            &self.request_digest,
            &self.operation_digest,
            &self.workspace_id,
            &self.workspace_snapshot_json,
            &self.execution_plan_json,
            &self.execution_plan_digest,
            &self.launch_token_digest,
            &self.bundle_path,
            &self.unit_name,
        ];
        if strings.iter().any(|s| s.is_empty())
            || self.created_at_ms < 0
            || self.global_limit < 1
            || self.expected_source_sha256.len() != 64
            || !self
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
            || serde_json::from_str::<serde_json::Value>(&self.workspace_snapshot_json).is_err()
            || serde_json::from_str::<serde_json::Value>(&self.execution_plan_json).is_err()
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        Ok(())
    }
}

/// Required keys and references for the durable PG authority, not merely
/// a row-correct historical import. The native stage intentionally does not
/// assert all of these, and must not be promoted as an active write schema.
fn qualified_schema_constraints(client: &mut Client, schema: &str) -> Result<(), PgAdmissionError> {
    let rows = client.query(
        "SELECT r.relname::text,c.contype::text,ARRAY_AGG(a.attname::text ORDER BY k.ordinality) \
         FROM pg_catalog.pg_constraint c \
         JOIN pg_catalog.pg_class r ON r.oid=c.conrelid \
         JOIN pg_catalog.pg_namespace n ON n.oid=r.relnamespace \
         JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum,ordinality) ON TRUE \
         JOIN pg_catalog.pg_attribute a ON a.attrelid=r.oid AND a.attnum=k.attnum \
         WHERE n.nspname=$1 AND c.contype IN ('p','u','f') \
         GROUP BY r.relname,c.oid,c.contype",
        &[&schema],
    )?;
    let actual: HashSet<(String, String, Vec<String>)> = rows
        .iter()
        .map(|row| (row.get(0), row.get(1), row.get(2)))
        .collect();
    let required: &[(&str, &str, &[&str])] = &[
        ("jobs", "p", &["job_id"]),
        ("jobs", "u", &["principal", "client_request_id"]),
        ("attempts", "p", &["attempt_id"]),
        ("attempts", "u", &["job_id", "attempt_number"]),
        ("attempts", "f", &["job_id"]),
        ("idempotency_keys", "p", &["principal", "client_request_id"]),
        ("idempotency_keys", "u", &["job_id"]),
        ("idempotency_keys", "f", &["job_id"]),
        ("concurrency_reservations", "p", &["reservation_id"]),
        ("concurrency_reservations", "u", &["attempt_id"]),
        ("concurrency_reservations", "f", &["attempt_id"]),
        ("job_events", "p", &["event_id"]),
        ("job_events", "u", &["job_id", "event_sequence"]),
        ("job_events", "f", &["job_id"]),
        ("job_events", "f", &["attempt_id"]),
        ("artifacts", "p", &["artifact_id"]),
        ("artifacts", "f", &["job_id"]),
        ("artifacts", "f", &["attempt_id"]),
        ("_stage_control", "p", &["id"]),
    ];
    if required.iter().any(|(table, kind, columns)| {
        !actual.contains(&(
            (*table).to_owned(),
            (*kind).to_owned(),
            columns.iter().map(|name| (*name).to_owned()).collect(),
        ))
    }) {
        return Err(PgAdmissionError::Unqualified);
    }
    Ok(())
}

pub struct PgAdmissionStore {
    client: Client,
}
impl PgAdmissionStore {
    pub fn connect(dsn: &str, schema: &str) -> Result<Self, PgAdmissionError> {
        if !exact_schema(schema) {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut client = Client::connect(dsn, NoTls)?;
        client.query_one(
            "SELECT set_config('search_path',$1,false)",
            &[&format!("\"{schema}\"")],
        )?;
        let actual: Option<String> = client.query_one("SELECT current_schema()", &[])?.get(0);
        if actual.as_deref() != Some(schema) {
            return Err(PgAdmissionError::Unqualified);
        }
        qualified_schema_constraints(&mut client, schema)?;
        Ok(Self { client })
    }

    /// One atomic admission. No dispatch/terminal/repair effect is authorized.
    pub fn admit(&mut self, i: &PgAdmissionInput) -> Result<PgAdmissionOutcome, PgAdmissionError> {
        i.validate()?;
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        // Serialize the global+per-Workspace capacity predicates and replay.
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE", &[]
        )?;
        let Some(authority) = authority else {
            return Err(PgAdmissionError::Unqualified);
        };
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        let pending:bool=tx.query_one(
            "SELECT EXISTS(SELECT 1 FROM job_runtime_release_effects r JOIN jobs j ON j.job_id=r.job_id WHERE j.resolution IS NULL OR EXISTS(SELECT 1 FROM attempts a JOIN concurrency_reservations c ON c.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND c.state IN ('active','held_orphaned')))",&[])?.get(0);
        if pending {
            return Err(PgAdmissionError::PendingEffect);
        }
        if let Some(row)=tx.query_opt(
            "SELECT job_id,operation_digest FROM idempotency_keys WHERE principal=$1 AND client_request_id=$2",
            &[&i.principal,&i.client_request_id])? {
            let job_id:String=row.get(0);
            let digest:String=row.get(1);
            if digest!=i.operation_digest {return Err(PgAdmissionError::IdempotencyConflict);}
            tx.commit().map_err(|_|PgAdmissionError::UnknownCommit)?;
            return Ok(PgAdmissionOutcome::Existing(job_id));
        }
        let workspace_count:i64=tx.query_one(
            "SELECT count(*) FROM concurrency_reservations r JOIN attempts a ON a.attempt_id=r.attempt_id JOIN jobs j ON j.job_id=a.job_id WHERE r.state IN ('active','held_orphaned') AND j.workspace_id=$1",
            &[&i.workspace_id])?.get(0);
        let global_count:i64=tx.query_one(
            "SELECT count(*) FROM concurrency_reservations WHERE state IN ('active','held_orphaned')",&[])?.get(0);
        if workspace_count >= 1 || global_count >= i64::from(i.global_limit) {
            return Err(PgAdmissionError::Capacity);
        }
        tx.execute(
            "INSERT INTO jobs(job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'run',NULL,NULL,0)",
            &[&i.job_id,&i.principal,&i.client_request_id,&i.request_digest,&i.operation_digest,
              &i.workspace_id,&i.workspace_snapshot_json,&i.execution_plan_json,
              &i.execution_plan_digest,&i.created_at_ms])?;
        tx.execute(
            "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,row_version) VALUES($1,$2,1,'accepted','natural',$3,$4,$5,$6,0)",
            &[&i.attempt_id,&i.job_id,&i.launch_token_digest,&i.bundle_path,&i.unit_name,&i.created_at_ms])?;
        tx.execute(
            "UPDATE jobs SET current_attempt_id=$1 WHERE job_id=$2",
            &[&i.attempt_id, &i.job_id],
        )?;
        tx.execute(
            "INSERT INTO idempotency_keys(principal,client_request_id,operation_digest,job_id,created_at_ms) VALUES($1,$2,$3,$4,$5)",
            &[&i.principal,&i.client_request_id,&i.operation_digest,&i.job_id,&i.created_at_ms])?;
        tx.execute(
            "INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,state_observed_at_ms) VALUES($1,$2,$3,'active',$4,$4)",
            &[&i.reservation_id,&i.attempt_id,&i64::from(i.global_limit),&i.created_at_ms])?;
        let events = [
            (
                "REQUEST_RECEIVED",
                "REQUEST_ACCEPTED",
                None,
                serde_json::json!({"requestDigest":i.request_digest}),
            ),
            (
                "JOB_RECORD_CREATED",
                "JOB_CREATED",
                None,
                serde_json::json!({"operationDigest":i.operation_digest}),
            ),
            (
                "ATTEMPT_CREATED",
                "ATTEMPT_ACCEPTED",
                Some("accepted"),
                serde_json::json!({"attemptNumber":1}),
            ),
        ];
        for (idx, (event_type, reason, next_state, detail)) in events.iter().enumerate() {
            let encoded = detail.to_string();
            let digest = format!("sha256:{}", hex::encode(Sha256::digest(encoded.as_bytes())));
            tx.execute(
                "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES($1,$2,$3,$4,$5,'SYSTEM_DERIVED',NULL,$6,$7,$8,$9,$10)",
                &[&format!("event-{}",Uuid::now_v7()),&i.job_id,&i.attempt_id,
                  &((idx+1) as i64),event_type,next_state,reason,&encoded,&digest,&i.created_at_ms])?;
        }
        // A failed COMMIT is UNKNOWN, not a retryable assertion of no effect.
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgAdmissionOutcome::Created(i.job_id.clone()))
    }
}

#[derive(Clone)]
pub struct PgTerminalNoArtifacts {
    pub attempt_id: String,
    pub expected_row_version: i64,
    pub terminal_state: String,
    pub result_digest: String,
    pub reason_code: String,
    pub exit_code: Option<i32>,
    pub finished_at_ms: i64,
    pub expected_source_sha256: String,
}
#[derive(Debug, PartialEq, Eq)]
pub enum PgTerminalOutcome {
    Committed(String),
    Existing(String),
}
fn terminal_transition(from: &str, to: &str) -> bool {
    match from {
        "accepted" => matches!(to, "cancelled" | "failed" | "lost" | "orphaned"),
        "starting" | "running" | "stopping" | "recovering" => matches!(
            to,
            "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
        ),
        _ => false,
    }
}
impl PgAdmissionStore {
    /// Exact no-Artifact terminal/Job/reservation/event atomicity, no runner or
    /// external output effect. Arbitrary Artifact-bearing terminal commits are
    /// deliberately unsupported until a complete consumer-owned transaction.
    pub fn commit_terminal_no_artifacts(
        &mut self,
        i: &PgTerminalNoArtifacts,
    ) -> Result<PgTerminalOutcome, PgAdmissionError> {
        if i.attempt_id.is_empty()
            || i.result_digest.is_empty()
            || i.reason_code.is_empty()
            || i.finished_at_ms < 0
            || i.expected_row_version < 0
            || i.expected_source_sha256.len() != 64
            || !i
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
            || !matches!(
                i.terminal_state.as_str(),
                "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
            )
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let auth=tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE",&[])?;
        let Some(auth) = auth else {
            return Err(PgAdmissionError::Unqualified);
        };
        let status: String = auth.get(0);
        let seal: String = auth.get(1);
        let permitted: bool = auth.get(2);
        if status != "QUALIFIED_WRITER" || !permitted || seal != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        let current=tx.query_opt(
            "SELECT job_id,state,result_digest,row_version FROM attempts WHERE attempt_id=$1 FOR UPDATE",
            &[&i.attempt_id])?.ok_or(PgAdmissionError::InvalidInput)?;
        let job_id: String = current.get(0);
        let previous: String = current.get(1);
        let digest: Option<String> = current.get(2);
        let version: i64 = current.get(3);
        let job = tx.query_one(
            "SELECT resolution FROM jobs WHERE job_id=$1 FOR UPDATE",
            &[&job_id],
        )?;
        let job_resolution: Option<String> = job.get(0);
        // This is strictly the no-Artifact terminal responsibility. Never
        // silently complete a Job with registered Artifact consumers here.
        let has_artifacts: bool = tx
            .query_one(
                "SELECT EXISTS(SELECT 1 FROM artifacts WHERE attempt_id=$1)",
                &[&i.attempt_id],
            )?
            .get(0);
        if has_artifacts {
            return Err(PgAdmissionError::Blocked);
        }
        if matches!(
            previous.as_str(),
            "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
        ) {
            if previous == i.terminal_state
                && digest.as_deref() == Some(&i.result_digest)
                && job_resolution.as_deref() == Some(&i.terminal_state)
            {
                tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
                return Ok(PgTerminalOutcome::Existing(job_id));
            }
            return Err(PgAdmissionError::IdempotencyConflict);
        }
        if version != i.expected_row_version
            || !terminal_transition(&previous, &i.terminal_state)
            || job_resolution.is_some()
        {
            return Err(PgAdmissionError::Blocked);
        }
        let changed=tx.execute(
            "UPDATE attempts SET state=$1,result_digest=$2,exit_code=$3,finished_at_ms=$4,row_version=row_version+1 WHERE attempt_id=$5 AND row_version=$6 AND state=$7",
            &[&i.terminal_state,&i.result_digest,&i.exit_code,&i.finished_at_ms,
              &i.attempt_id,&i.expected_row_version,&previous])?;
        if changed != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        if i.terminal_state == "orphaned" {
            let count=tx.execute(
                "UPDATE concurrency_reservations SET state='held_orphaned',release_reason=$1,state_observed_at_ms=$2 WHERE attempt_id=$3 AND state IN ('active','held_orphaned')",
                &[&i.reason_code,&i.finished_at_ms,&i.attempt_id])?;
            if count != 1 {
                return Err(PgAdmissionError::Blocked);
            }
        } else {
            let count=tx.execute(
                "UPDATE concurrency_reservations SET state='released',released_at_ms=$1,release_reason=$2,state_observed_at_ms=$1 WHERE attempt_id=$3 AND state IN ('active','held_orphaned')",
                &[&i.finished_at_ms,&i.reason_code,&i.attempt_id])?;
            if count != 1 {
                return Err(PgAdmissionError::Blocked);
            }
        }
        let changed=tx.execute(
            "UPDATE jobs SET resolution=$1,current_attempt_id=NULL,row_version=row_version+1 WHERE job_id=$2 AND resolution IS NULL",
            &[&i.terminal_state,&job_id])?;
        if changed != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        let start: i64 = tx
            .query_one(
                "SELECT COALESCE(MAX(event_sequence),0)+1 FROM job_events WHERE job_id=$1",
                &[&job_id],
            )?
            .get(0);
        let items = [
            (
                "PROCESS_EXITED",
                "SYSTEM_OBSERVED",
                serde_json::json!({"resultDigest":i.result_digest,"exitCode":i.exit_code}),
            ),
            (
                "JOB_TERMINAL",
                "SYSTEM_DERIVED",
                serde_json::json!({"resolution":i.terminal_state}),
            ),
        ];
        for (n, (event_type, origin, detail)) in items.iter().enumerate() {
            let encoded = detail.to_string();
            let digest = format!("sha256:{}", hex::encode(Sha256::digest(encoded.as_bytes())));
            tx.execute(
                "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)",
                &[&format!("event-{}",Uuid::now_v7()),&job_id,&i.attempt_id,
                  &(start+n as i64),event_type,origin,&previous,&i.terminal_state,
                  &i.reason_code,&encoded,&digest,&i.finished_at_ms])?;
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgTerminalOutcome::Committed(job_id))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn schema_boundary_fails_closed() {
        for name in ["", "public", "pg_catalog", "_secret", "x;DROP SCHEMA"] {
            assert!(!exact_schema(name), "unsafe {name}");
        }
        assert!(exact_schema("runtime_pg_qualified_r1"));
    }
    #[test]
    fn source_identity_must_be_present() {
        let i = PgAdmissionInput {
            job_id: "j".into(),
            attempt_id: "a".into(),
            reservation_id: "r".into(),
            principal: "p".into(),
            client_request_id: "c".into(),
            request_digest: "sha256:r".into(),
            operation_digest: "sha256:o".into(),
            workspace_id: "ws".into(),
            workspace_snapshot_json: "{}".into(),
            execution_plan_json: "{}".into(),
            execution_plan_digest: "sha256:plan".into(),
            launch_token_digest: "sha256:l".into(),
            bundle_path: "/tmp/test".into(),
            unit_name: "unit".into(),
            global_limit: 1,
            created_at_ms: 1,
            expected_source_sha256: String::new(),
        };
        assert!(matches!(i.validate(), Err(PgAdmissionError::InvalidInput)));
    }
}

#[cfg(all(test, feature = "postgres-registry-admission"))]
mod live_pg_tests {
    use super::*;
    use std::sync::{Arc, Barrier};
    use std::thread;

    // An operator supplies an isolated PostgreSQL DSN for physical tests.
    // No environment value means the ordinary CI suite never mutates PG.
    const SCHEMA: &str = r#"
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
 launch_token_digest text NOT NULL, bundle_path text NOT NULL,
 unit_name text UNIQUE NOT NULL, created_at_ms bigint NOT NULL,
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
CREATE TABLE job_runtime_release_effects(job_id text NOT NULL);
CREATE TABLE artifacts(
 artifact_id text PRIMARY KEY,job_id text NOT NULL REFERENCES jobs(job_id),
 attempt_id text NOT NULL REFERENCES attempts(attempt_id));
CREATE TABLE _stage_control(
 id text PRIMARY KEY, state text NOT NULL, source_sha256 text NOT NULL,
 promotion_allowed boolean NOT NULL);
"#;

    struct Scratch {
        admin: Client,
        name: String,
    }
    impl Scratch {
        fn new(dsn: &str) -> Self {
            let name = format!("test_admit_{}", Uuid::now_v7().simple());
            let mut admin = Client::connect(dsn, NoTls).expect("test PG18 connection");
            admin
                .batch_execute(&format!("CREATE SCHEMA \"{name}\""))
                .expect("private test schema");
            admin
                .query_one(
                    "SELECT set_config('search_path',$1,false)",
                    &[&format!("\"{name}\"")],
                )
                .expect("test-only search path");
            admin
                .batch_execute(SCHEMA)
                .expect("native PG fixture constraints");
            admin
                .execute(
                    "INSERT INTO _stage_control VALUES('source','VERIFIED_NON_AUTHORITY',$1,false)",
                    &[&"a".repeat(64)],
                )
                .expect("non-authority fixture");
            Self { admin, name }
        }
        fn qualify(&mut self) {
            self.admin.execute(
                "UPDATE _stage_control SET state='QUALIFIED_WRITER',promotion_allowed=true WHERE id='source'",
                &[]
            ).expect("test-only synthetic qualifier");
        }
        fn count(&mut self, table: &str) -> i64 {
            self.admin
                .query_one(&format!("SELECT count(*) FROM {table}"), &[])
                .unwrap()
                .get(0)
        }
    }
    impl Drop for Scratch {
        fn drop(&mut self) {
            // A dedicated scratch namespace, never an installed Runtime
            // schema; do not retain test effects across test runs.
            let _ = self.admin.batch_execute(&format!(
                "SET search_path TO public; DROP SCHEMA IF EXISTS \"{}\" CASCADE",
                self.name
            ));
        }
    }
    fn payload(client_key: &str, job: &str, workspace: &str, cap: i32) -> PgAdmissionInput {
        PgAdmissionInput {
            job_id: job.to_string(),
            attempt_id: format!("attempt-{job}"),
            reservation_id: format!("reservation-{job}"),
            principal: "pg-native-test".into(),
            client_request_id: client_key.to_string(),
            request_digest: format!("sha256:request-{client_key}"),
            operation_digest: format!("sha256:operation-{client_key}"),
            workspace_id: workspace.into(),
            workspace_snapshot_json: "{}".into(),
            execution_plan_json: "{}".into(),
            execution_plan_digest: "sha256:test-plan".into(),
            launch_token_digest: "sha256:launch".into(),
            bundle_path: "/nonproduction/pg-test".into(),
            unit_name: format!("{job}.service"),
            global_limit: cap,
            created_at_ms: 1234567,
            expected_source_sha256: "a".repeat(64),
        }
    }

    #[test]
    fn pg18_rejects_synthetic_writer_without_event_sequence_uniqueness() {
        let Ok(dsn) = std::env::var("ORDIVON_PG_TEST_DSN") else {
            return;
        };
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        assert!(PgAdmissionStore::connect(&dsn, &scratch.name).is_ok());
        scratch
            .admin
            .batch_execute(
                "ALTER TABLE job_events DROP CONSTRAINT job_events_job_id_event_sequence_key",
            )
            .expect("test-only weakened catalog");
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, &scratch.name),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(scratch.count("jobs"), 0);
    }

    #[test]
    fn pg18_native_atomic_admission_replay_fence_and_rollback() {
        let Ok(dsn) = std::env::var("ORDIVON_PG_TEST_DSN") else {
            return;
        };
        let mut scratch = Scratch::new(&dsn);
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let a = payload("request-A", "job-A", "workspace-A", 2);
        assert!(matches!(
            store.admit(&a),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(scratch.count("jobs"), 0, "no write before PG qualification");
        scratch.qualify();
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Created("job-A".into())
        );
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Existing("job-A".into())
        );
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
        assert_eq!(scratch.count("idempotency_keys"), 1);
        assert_eq!(scratch.count("job_events"), 3);
        let mut conflict = a.clone();
        conflict.operation_digest = "sha256:different-effect".into();
        assert!(matches!(
            store.admit(&conflict),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        assert!(matches!(
            store.admit(&payload("request-B", "job-B", "workspace-A", 2)),
            Err(PgAdmissionError::Capacity)
        ));
        assert!(matches!(
            store.admit(&payload("request-B", "job-B", "workspace-B", 1)),
            Err(PgAdmissionError::Capacity)
        ));

        // A row uniqueness error after inserting Job must rollback every
        // consumer-visible part of this admission.
        let mut duplicate_attempt = payload("request-C", "job-C", "workspace-B", 2);
        duplicate_attempt.attempt_id = a.attempt_id.clone();
        assert!(matches!(
            store.admit(&duplicate_attempt),
            Err(PgAdmissionError::Database(_))
        ));
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("idempotency_keys"), 1);
        assert_eq!(scratch.count("job_events"), 3);
        assert_eq!(
            store
                .admit(&payload("request-D", "job-D", "workspace-B", 2))
                .unwrap(),
            PgAdmissionOutcome::Created("job-D".into())
        );
        assert_eq!(scratch.count("jobs"), 2);
        assert_eq!(scratch.count("job_events"), 6);
    }

    #[test]
    fn pg18_terminal_cas_replay_orphan_hold_and_atomic_rollback() {
        let Ok(dsn) = std::env::var("ORDIVON_PG_TEST_DSN") else {
            return;
        };
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("terminal-one", "job-terminal", "workspace-term", 2);
        store.admit(&input).unwrap();
        let terminal = PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:result".into(),
            reason_code: "NATIVE_PG_TEST".into(),
            exit_code: Some(3),
            finished_at_ms: 1234578,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        let mut stale = terminal.clone();
        stale.expected_row_version = 1;
        assert!(matches!(
            store.commit_terminal_no_artifacts(&stale),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 3);
        assert_eq!(
            store.commit_terminal_no_artifacts(&terminal).unwrap(),
            PgTerminalOutcome::Committed(input.job_id.clone())
        );
        assert_eq!(
            store.commit_terminal_no_artifacts(&terminal).unwrap(),
            PgTerminalOutcome::Existing(input.job_id.clone())
        );
        assert_eq!(scratch.count("job_events"), 5);
        let state: String = scratch
            .admin
            .query_one(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(state, "released");
        let mut conflicting = terminal.clone();
        conflicting.result_digest = "sha256:other".into();
        assert!(matches!(
            store.commit_terminal_no_artifacts(&conflicting),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        assert_eq!(scratch.count("job_events"), 5);

        let orphan = payload("orphan", "job-orphan", "workspace-term", 2);
        store.admit(&orphan).unwrap();
        let hold = PgTerminalNoArtifacts {
            attempt_id: orphan.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "orphaned".into(),
            result_digest: "sha256:orphan".into(),
            reason_code: "ORPHAN".into(),
            exit_code: None,
            finished_at_ms: 1234580,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        store.commit_terminal_no_artifacts(&hold).unwrap();
        let held: String = scratch
            .admin
            .query_one(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
                &[&orphan.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(held, "held_orphaned");
        assert!(matches!(
            store.admit(&payload("after-orphan", "job-after", "workspace-term", 2)),
            Err(PgAdmissionError::Capacity)
        ));
        assert_eq!(scratch.count("jobs"), 2);
    }

    #[test]
    fn pg18_artifact_bearing_terminal_is_denied_until_full_owner_exists() {
        let Ok(dsn) = std::env::var("ORDIVON_PG_TEST_DSN") else {
            return;
        };
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("has-artifact", "job-artifact", "workspace-artifact", 1);
        store.admit(&input).unwrap();
        scratch
            .admin
            .execute(
                "INSERT INTO artifacts VALUES('artifact-test',$1,$2)",
                &[&input.job_id, &input.attempt_id],
            )
            .unwrap();
        let terminal = PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:result".into(),
            reason_code: "ARTIFACT_STOP".into(),
            exit_code: Some(1),
            finished_at_ms: 1234599,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.commit_terminal_no_artifacts(&terminal),
            Err(PgAdmissionError::Blocked)
        ));
        let standing: String = scratch
            .admin
            .query_one(
                "SELECT state FROM attempts WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(standing, "accepted");
        assert_eq!(scratch.count("job_events"), 3);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
    }

    #[test]
    fn historical_pg_stage_is_not_an_admission_authority() {
        let Ok(dsn) = std::env::var("ORDIVON_PG_STAGE_TEST_DSN") else {
            return;
        };
        let mut inspector = Client::connect(&dsn, NoTls).unwrap();
        let before: i64 = inspector
            .query_one("SELECT count(*) FROM rw12_stage_cutover_r1.jobs", &[])
            .unwrap()
            .get(0);
        let row=inspector.query_one(
            "SELECT state,source_sha256,promotion_allowed FROM rw12_stage_cutover_r1._stage_control WHERE id='source'",
            &[]).unwrap();
        let state: String = row.get(0);
        let source: String = row.get(1);
        let permitted: bool = row.get(2);
        assert_eq!(state, "VERIFIED_NON_AUTHORITY");
        assert!(!permitted);
        assert_eq!(source.len(), 64, "staged source identity exists");
        // A historical row-exact import is not a durable writer schema:
        // fail at connect before any operation can even be admitted.
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, "rw12_stage_cutover_r1"),
            Err(PgAdmissionError::Unqualified)
        ));
        let after: i64 = inspector
            .query_one("SELECT count(*) FROM rw12_stage_cutover_r1.jobs", &[])
            .unwrap()
            .get(0);
        assert_eq!(before, after);
    }

    #[test]
    fn pg18_concurrent_duplicate_never_creates_second_job() {
        let Ok(dsn) = std::env::var("ORDIVON_PG_TEST_DSN") else {
            return;
        };
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let gate = Arc::new(Barrier::new(5));
        let mut workers = Vec::new();
        for n in 0..4 {
            let dsn = dsn.clone();
            let schema = scratch.name.clone();
            let gate = gate.clone();
            workers.push(thread::spawn(move || {
                let mut store = PgAdmissionStore::connect(&dsn, &schema).unwrap();
                let request = payload("same-key", &format!("job-{n}"), "workspace-one", 2);
                gate.wait();
                store.admit(&request)
            }));
        }
        gate.wait();
        let mut created = 0usize;
        for worker in workers {
            match worker.join().unwrap() {
                Ok(PgAdmissionOutcome::Created(_)) => created += 1,
                Ok(PgAdmissionOutcome::Existing(_)) => (),
                Err(PgAdmissionError::Database(error))
                    if error.code()
                        == Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE) => {}
                unexpected => panic!("unsafe concurrent admission result: {unexpected:?}"),
            }
        }
        assert_eq!(created, 1);
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("idempotency_keys"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
    }
}
