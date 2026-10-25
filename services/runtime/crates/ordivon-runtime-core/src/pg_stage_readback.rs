//! Source-sealed historical PostgreSQL read consumer, NEVER a writer authority.
//!
//! This reader is deliberately admitted only against a verified NON-AUTHORITY
//! import; it is not a live Registry replacement. It makes the historical
//! Rust-visible Job/Attempt/event/Artifact contract testable against the exact
//! frozen source. Do not silently reinterpret a historical replay as a current
//! Job observation or use this session to advance lifecycle state.
use postgres::{Client, IsolationLevel, NoTls};
use serde::{Deserialize, Serialize};

#[derive(Debug)]
pub enum PgStageReadError {
    InvalidInput,
    NotHistoricalSource,
    Database(postgres::Error),
}
impl From<postgres::Error> for PgStageReadError {
    fn from(e: postgres::Error) -> Self {
        Self::Database(e)
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct PgHistoricalJob {
    pub job_id: String,
    pub principal: String,
    pub client_request_id: String,
    pub operation_digest: String,
    pub workspace_id: String,
    pub desired_state: String,
    pub resolution: Option<String>,
    pub current_attempt_id: Option<String>,
    pub row_version: i64,
    pub attempts: Vec<PgHistoricalAttempt>,
    pub events: Vec<PgHistoricalEvent>,
    pub artifacts: Vec<PgHistoricalArtifact>,
    pub idempotency_operation_digest: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct PgHistoricalAttempt {
    pub attempt_id: String,
    pub state: String,
    pub row_version: i64,
    pub result_digest: Option<String>,
    pub recovery_required: Option<i64>,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct PgHistoricalEvent {
    pub event_id: String,
    pub event_sequence: i64,
    pub event_type: String,
    pub detail_digest: String,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct PgHistoricalArtifact {
    pub artifact_id: String,
    pub attempt_id: String,
    pub kind: String,
    pub relative_path: String,
    pub digest: String,
    pub byte_length: i64,
    pub truncated: i64,
}

fn safe_schema(s: &str) -> bool {
    s.starts_with("rw12_stage_")
        && s.len() <= 63
        && s.bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'_')
}
fn exact_sha256(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|b| b.is_ascii_hexdigit())
}

/// A read-only session tied to one checked immutable SQLite snapshot checksum.
pub struct PgHistoricalStageReader {
    client: Client,
    source_sha256: String,
}

impl PgHistoricalStageReader {
    pub fn connect(
        dsn: &str,
        schema: &str,
        expected_source_sha256: &str,
    ) -> Result<Self, PgStageReadError> {
        if !safe_schema(schema) || !exact_sha256(expected_source_sha256) {
            return Err(PgStageReadError::InvalidInput);
        }
        let mut client = Client::connect(dsn, NoTls)?;
        // A separate reader and session-level write fence. Never expose
        // the inner Client or mutate this target to make acceptance pass.
        client.query_one(
            "SELECT set_config('search_path',$1,false)",
            &[&format!("\"{schema}\"")],
        )?;
        let current: Option<String> = client.query_one("SELECT current_schema()", &[])?.get(0);
        if current.as_deref() != Some(schema) {
            return Err(PgStageReadError::NotHistoricalSource);
        }
        client.batch_execute("SET default_transaction_read_only = on")?;
        let row = client.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )?;
        let Some(row) = row else {
            return Err(PgStageReadError::NotHistoricalSource);
        };
        let state: String = row.get(0);
        let source: String = row.get(1);
        let writer: bool = row.get(2);
        if state != "VERIFIED_NON_AUTHORITY" || writer || source != expected_source_sha256 {
            return Err(PgStageReadError::NotHistoricalSource);
        }
        Ok(Self {
            client,
            source_sha256: source,
        })
    }

    pub fn source_sha256(&self) -> &str {
        &self.source_sha256
    }

    /// Exact row identities and digest-bearing evidence for ONE historical Job.
    /// Caller must never treat this source-frozen projection as a live status.
    pub fn read_job(&mut self, job_id: &str) -> Result<Option<PgHistoricalJob>, PgStageReadError> {
        if job_id.is_empty() || job_id.len() > 256 {
            return Err(PgStageReadError::InvalidInput);
        }
        // A multi-table Job projection must come from ONE consistent MVCC
        // snapshot even if another privileged connection changes the staging
        // database between reads. Read-only Repeatable Read does not confer
        // writer authority and cannot promote the historical source.
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()?;
        let row = tx.query_opt(
            "SELECT job_id,principal,client_request_id,operation_digest,workspace_id, \
             desired_state,resolution,current_attempt_id,row_version \
             FROM jobs WHERE job_id=$1",
            &[&job_id],
        )?;
        let Some(row) = row else {
            return Ok(None);
        };
        let attempts = tx
            .query(
                "SELECT attempt_id,state,row_version,result_digest,recovery_required \
                 FROM attempts WHERE job_id=$1 ORDER BY attempt_number,attempt_id",
                &[&job_id],
            )?
            .into_iter()
            .map(|r| PgHistoricalAttempt {
                attempt_id: r.get(0),
                state: r.get(1),
                row_version: r.get(2),
                result_digest: r.get(3),
                recovery_required: r.get(4),
            })
            .collect();
        let events = tx
            .query(
                "SELECT event_id,event_sequence,event_type,detail_digest \
                 FROM job_events WHERE job_id=$1 ORDER BY event_sequence",
                &[&job_id],
            )?
            .into_iter()
            .map(|r| PgHistoricalEvent {
                event_id: r.get(0),
                event_sequence: r.get(1),
                event_type: r.get(2),
                detail_digest: r.get(3),
            })
            .collect();
        let artifacts = tx
            .query(
                "SELECT artifact_id,attempt_id,kind,relative_path,digest,byte_length,truncated \
                 FROM artifacts WHERE job_id=$1 ORDER BY artifact_id",
                &[&job_id],
            )?
            .into_iter()
            .map(|r| PgHistoricalArtifact {
                artifact_id: r.get(0),
                attempt_id: r.get(1),
                kind: r.get(2),
                relative_path: r.get(3),
                digest: r.get(4),
                byte_length: r.get(5),
                truncated: r.get(6),
            })
            .collect();
        let replay = tx.query_opt(
            "SELECT operation_digest FROM idempotency_keys WHERE job_id=$1",
            &[&job_id],
        )?;
        let historical = PgHistoricalJob {
            job_id: row.get(0),
            principal: row.get(1),
            client_request_id: row.get(2),
            operation_digest: row.get(3),
            workspace_id: row.get(4),
            desired_state: row.get(5),
            resolution: row.get(6),
            current_attempt_id: row.get(7),
            row_version: row.get(8),
            attempts,
            events,
            artifacts,
            idempotency_operation_digest: replay.map(|r| r.get(0)),
        };
        tx.commit()?;
        Ok(Some(historical))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Immutable independent source evidence captured from the exact 5.41GB
    // sqlite3 backup and recorded under snapshot.json. This test does NOT
    // connect to, maintain, or extend SQLite: only the PG reader under test
    // is executable here. The original stage import independently checked
    // every typed row of the 6,501,423-row frozen source.
    const SOURCE_SHA256: &str = "e3790cb41bac3e17f17ffa7c29f03d7074478ce3e79c1f9ee50ce205270cac62";
    const FIRST_JOB: &str = "job-019f8b3b-63c0-7852-b0a6-19ac869e5da3";
    const SNAPSHOT_INFLIGHT_JOB: &str = "job-01a174af-f49e-7eb1-a55e-4a885c5c711d";
    const ARTIFACT_JOB: &str = "job-01a174af-d91c-72e3-b4a2-ae2ecba52a92";

    #[test]
    fn native_pg18_history_matches_independent_frozen_source_witnesses() {
        let Ok(dsn) = std::env::var("ORDIVON_PG_STAGE_TEST_DSN") else {
            return;
        };
        let mut reader =
            PgHistoricalStageReader::connect(&dsn, "rw12_stage_cutover_r1", SOURCE_SHA256)
                .expect("source-qualified PostgreSQL staging reader");
        assert_eq!(reader.source_sha256(), SOURCE_SHA256);
        assert!(matches!(
            PgHistoricalStageReader::connect(&dsn, "rw12_stage_cutover_r1", &"0".repeat(64)),
            Err(PgStageReadError::NotHistoricalSource)
        ));
        assert!(matches!(
            PgHistoricalStageReader::connect(&dsn, "public", SOURCE_SHA256),
            Err(PgStageReadError::InvalidInput)
        ));
        let first = reader.read_job(FIRST_JOB).unwrap().unwrap();
        assert_eq!(first.principal, "principal:local-owner");
        assert_eq!(
            first.client_request_id,
            "dogfood:ordivon:0a7d4c98-758a-4ffc-af06-5fce7418c7a2"
        );
        assert_eq!(
            first.operation_digest,
            "sha256:f345a661295a5fce8dbd5b563f726c36fe847f6263e8ef96bc7be1c95e15ebc0"
        );
        assert_eq!(
            first.workspace_id,
            "dogfood-ordivon-c114f67f-a8a7-406f-9710-1f52aed2a389"
        );
        assert_eq!(first.desired_state, "run");
        assert_eq!(first.resolution.as_deref(), Some("succeeded"));
        assert_eq!(first.current_attempt_id, None);
        assert_eq!(first.row_version, 1);
        assert_eq!(first.attempts.len(), 1);
        assert_eq!(first.attempts[0].state, "succeeded");
        assert_eq!(first.attempts[0].row_version, 4);
        assert_eq!(
            first.attempts[0].result_digest.as_deref(),
            Some("sha256:2904563eb5381abd5e641f706e12114a6800b4cfd41935b261120bb19388c69a")
        );
        assert_eq!(first.events.len(), 8);
        assert_eq!(first.events[0].event_sequence, 1);
        assert_eq!(first.events[0].event_type, "REQUEST_RECEIVED");
        assert_eq!(
            first.events[0].detail_digest,
            "sha256:0d9249ab4c4cbfed2e88f84742738a4e06b2d2a9578607559a5a0b97322adc9e"
        );
        assert_eq!(first.events[7].event_sequence, 8);
        assert_eq!(first.events[7].event_type, "JOB_TERMINAL");
        assert_eq!(first.artifacts.len(), 3);
        assert_eq!(first.artifacts[0].kind, "execution_result");
        assert_eq!(first.artifacts[0].relative_path, "result.json");
        assert_eq!(first.artifacts[0].byte_length, 996);
        assert_eq!(first.artifacts[1].byte_length, 0);
        assert_eq!(first.artifacts[2].byte_length, 346);
        assert_eq!(
            first.idempotency_operation_digest.as_deref(),
            Some(first.operation_digest.as_str())
        );

        // Frozen in-progress data must remain in-progress, rather than being
        // fabricated into a terminal result by historical readback.
        let running = reader.read_job(SNAPSHOT_INFLIGHT_JOB).unwrap().unwrap();
        assert_eq!(running.resolution, None);
        assert_eq!(running.row_version, 0);
        assert_eq!(running.attempts.len(), 1);
        assert_eq!(running.attempts[0].state, "running");
        assert_eq!(running.attempts[0].row_version, 3);
        assert_eq!(running.events.len(), 6);
        assert!(running.artifacts.is_empty());

        // An Artifact-heavy historical Job is a distinct consumer from a
        // result with no outputs; all six registered receipts must survive.
        let with_artifacts = reader.read_job(ARTIFACT_JOB).unwrap().unwrap();
        assert_eq!(with_artifacts.resolution.as_deref(), Some("succeeded"));
        assert_eq!(with_artifacts.events.len(), 8);
        assert_eq!(with_artifacts.artifacts.len(), 6);
        assert_eq!(with_artifacts.artifacts[0].kind, "resource_receipt");
        assert_eq!(with_artifacts.artifacts[0].byte_length, 832);
        assert_eq!(
            with_artifacts.artifacts[5].kind,
            "workspace_source_observation"
        );
        assert_eq!(with_artifacts.artifacts[5].byte_length, 585);

        assert!(reader.read_job("no-such-historical-job").unwrap().is_none());
        assert!(matches!(
            reader.read_job(""),
            Err(PgStageReadError::InvalidInput)
        ));
        // Physical negative control: even an administrative PostgreSQL
        // connection is read-only through this historical reader.
        let forbidden = reader
            .client
            .batch_execute("UPDATE jobs SET desired_state='cancelled' WHERE false");
        assert_eq!(
            forbidden.as_ref().err().and_then(|e| e.code()),
            Some(&postgres::error::SqlState::READ_ONLY_SQL_TRANSACTION),
            "historical reader must reject mutations"
        );
    }
}
