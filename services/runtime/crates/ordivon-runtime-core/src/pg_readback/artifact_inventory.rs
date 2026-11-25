//! Snapshot-bound Artifact inventory; no filesystem reads or new authority.
use super::types::{PgJobSnapshot, PgObservedArtifact};
use crate::pg_admission::{PgAdmissionError, PgArtifactRegistration};
use postgres::Transaction;

/// Ordinary lifecycle verification needs only the chosen terminal Attempt.
/// The public Job projection additionally lists historical same-Job rows, with
/// their original Attempt identifiers, but never borrows their stream/result.
pub(super) fn read_artifact_inventory(
    tx: &mut Transaction<'_>,
    snapshot: &PgJobSnapshot,
    include_job_inventory: bool,
) -> Result<Option<Vec<PgObservedArtifact>>, PgAdmissionError> {
    if !include_job_inventory && snapshot.resolution.is_none() {
        return Ok(Some(Vec::new()));
    }
    let rows = if include_job_inventory {
        tx.query(
            "SELECT r.job_id,r.attempt_id,a.job_id,r.artifact_id,r.kind,r.relative_path,r.digest,r.media_type,r.byte_length,r.truncated,r.created_at_ms
             FROM artifacts r LEFT JOIN attempts a ON a.attempt_id=r.attempt_id
             WHERE r.job_id=$1 OR r.attempt_id=$2 ORDER BY r.artifact_id",
            &[&snapshot.job_id, &snapshot.attempt_id],
        )?
    } else {
        tx.query(
            "SELECT r.job_id,r.attempt_id,a.job_id,r.artifact_id,r.kind,r.relative_path,r.digest,r.media_type,r.byte_length,r.truncated,r.created_at_ms
             FROM artifacts r LEFT JOIN attempts a ON a.attempt_id=r.attempt_id
             WHERE r.attempt_id=$1 ORDER BY r.artifact_id",
            &[&snapshot.attempt_id],
        )?
    };
    let mut artifacts = Vec::with_capacity(rows.len());
    for row in rows {
        if row.get::<_, String>(0) != snapshot.job_id
            || row.get::<_, Option<String>>(2).as_deref() != Some(snapshot.job_id.as_str())
        {
            return Ok(None);
        }
        artifacts.push(PgObservedArtifact {
            attempt_id: row.get(1),
            registration: PgArtifactRegistration {
                artifact_id: row.get(3),
                kind: row.get(4),
                relative_path: row.get(5),
                digest: row.get(6),
                media_type: row.get(7),
                byte_length: row.get(8),
                truncated: row.get(9),
                created_at_ms: row.get(10),
            },
        });
    }
    Ok(Some(artifacts))
}
