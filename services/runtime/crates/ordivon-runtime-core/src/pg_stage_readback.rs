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

#[cfg(all(test, feature = "transactional-runtime"))]
mod tests {
    use super::*;
    use rusqlite::OpenFlags;

    #[test]
    fn historical_pg18_readback_matches_frozen_sqlite_job_evidence() {
        let (Ok(pg_dsn), Ok(sqlite_source)) = (
            std::env::var("ORDIVON_PG_STAGE_TEST_DSN"),
            std::env::var("ORDIVON_PG_STAGE_SQLITE_SOURCE"),
        ) else {
            return;
        };
        let frozen = rusqlite::Connection::open_with_flags(
            format!("file:{sqlite_source}?mode=ro&immutable=1"),
            OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_URI,
        )
        .unwrap();
        let expected_source = "e3790cb41bac3e17f17ffa7c29f03d7074478ce3e79c1f9ee50ce205270cac62";
        let mut reader =
            PgHistoricalStageReader::connect(&pg_dsn, "rw12_stage_cutover_r1", expected_source)
                .unwrap();
        assert_eq!(reader.source_sha256(), expected_source);
        assert!(matches!(
            PgHistoricalStageReader::connect(&pg_dsn, "rw12_stage_cutover_r1", &"0".repeat(64)),
            Err(PgStageReadError::NotHistoricalSource)
        ));
        assert!(matches!(
            PgHistoricalStageReader::connect(&pg_dsn, "public", expected_source),
            Err(PgStageReadError::InvalidInput)
        ));
        let id: String = frozen
            .query_row("SELECT job_id FROM jobs ORDER BY job_id LIMIT 1", [], |r| {
                r.get(0)
            })
            .unwrap();
        let pg = reader.read_job(&id).unwrap().unwrap();
        let job = frozen
            .query_row(
                "SELECT principal,client_request_id,operation_digest,workspace_id, \
                 desired_state,resolution,current_attempt_id,row_version \
                 FROM jobs WHERE job_id=?",
                [&id],
                |r| {
                    Ok((
                        r.get::<_, String>(0)?,
                        r.get::<_, String>(1)?,
                        r.get::<_, String>(2)?,
                        r.get::<_, String>(3)?,
                        r.get::<_, String>(4)?,
                        r.get::<_, Option<String>>(5)?,
                        r.get::<_, Option<String>>(6)?,
                        r.get::<_, i64>(7)?,
                    ))
                },
            )
            .unwrap();
        assert_eq!(pg.principal, job.0);
        assert_eq!(pg.client_request_id, job.1);
        assert_eq!(pg.operation_digest, job.2);
        assert_eq!(pg.workspace_id, job.3);
        assert_eq!(pg.desired_state, job.4);
        assert_eq!(pg.resolution, job.5);
        assert_eq!(pg.current_attempt_id, job.6);
        assert_eq!(pg.row_version, job.7);

        let attempts = frozen
            .prepare(
                "SELECT attempt_id,state,row_version,result_digest,recovery_required \
                 FROM attempts WHERE job_id=? ORDER BY attempt_number,attempt_id",
            )
            .unwrap()
            .query_map([&id], |r| {
                Ok(PgHistoricalAttempt {
                    attempt_id: r.get(0)?,
                    state: r.get(1)?,
                    row_version: r.get(2)?,
                    result_digest: r.get(3)?,
                    recovery_required: r.get(4)?,
                })
            })
            .unwrap()
            .collect::<Result<Vec<_>, _>>()
            .unwrap();
        assert_eq!(pg.attempts, attempts);
        let events = frozen
            .prepare(
                "SELECT event_id,event_sequence,event_type,detail_digest \
                 FROM job_events WHERE job_id=? ORDER BY event_sequence",
            )
            .unwrap()
            .query_map([&id], |r| {
                Ok(PgHistoricalEvent {
                    event_id: r.get(0)?,
                    event_sequence: r.get(1)?,
                    event_type: r.get(2)?,
                    detail_digest: r.get(3)?,
                })
            })
            .unwrap()
            .collect::<Result<Vec<_>, _>>()
            .unwrap();
        assert_eq!(pg.events, events);
        let artifacts = frozen
            .prepare(
                "SELECT artifact_id,attempt_id,kind,relative_path,digest,byte_length,truncated \
                 FROM artifacts WHERE job_id=? ORDER BY artifact_id",
            )
            .unwrap()
            .query_map([&id], |r| {
                Ok(PgHistoricalArtifact {
                    artifact_id: r.get(0)?,
                    attempt_id: r.get(1)?,
                    kind: r.get(2)?,
                    relative_path: r.get(3)?,
                    digest: r.get(4)?,
                    byte_length: r.get(5)?,
                    truncated: r.get(6)?,
                })
            })
            .unwrap()
            .collect::<Result<Vec<_>, _>>()
            .unwrap();
        assert_eq!(pg.artifacts, artifacts);
        let idem: Option<String> = frozen
            .query_row(
                "SELECT operation_digest FROM idempotency_keys WHERE job_id=?",
                [&id],
                |r| r.get(0),
            )
            .ok();
        assert_eq!(pg.idempotency_operation_digest, idem);
        assert!(reader.read_job("no-such-historical-job").unwrap().is_none());
        assert!(matches!(
            reader.read_job(""),
            Err(PgStageReadError::InvalidInput)
        ));
        // Verify a *physical* write attempt fails even under database superuser:
        // the Rust consumer session is fenced read-only.
        let forbidden = reader
            .client
            .batch_execute("UPDATE jobs SET desired_state='cancelled' WHERE false");
        assert!(
            forbidden.as_ref().err().and_then(|e| e.code())
                == Some(&postgres::error::SqlState::READ_ONLY_SQL_TRANSACTION),
            "historical read session must reject mutation: {forbidden:?}"
        );
    }
}
