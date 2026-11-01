//! Consistent, read-only PostgreSQL lifecycle projection for migration consumers.
//! It does not dispatch, reconcile, authorize, or certify a physical effect.
use crate::pg_admission::{
    pg_artifact_manifest_digest, valid_pg_artifacts, PgAdmissionError, PgAdmissionStore,
    PgArtifactRegistration,
};
use postgres::{IsolationLevel, Transaction};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PgJobSnapshot {
    pub job_id: String,
    pub desired_state: String,
    pub resolution: Option<String>,
    pub current_attempt_id: Option<String>,
    pub attempt_id: String,
    pub attempt_state: String,
    pub termination_intent: String,
    pub reservation_state: String,
    pub result_digest: Option<String>,
    pub finished_at_ms: Option<i64>,
    pub job_row_version: i64,
    pub attempt_row_version: i64,
}

impl PgJobSnapshot {
    // A coherent projection is not a proof that the process ran or an external
    // effect happened. It only excludes contradictory durable PG rows.
    fn lifecycle_coherent(&self) -> bool {
        if self.job_row_version < 0
            || self.attempt_row_version < 0
            || !matches!(self.desired_state.as_str(), "run" | "cancelled")
            || !matches!(
                self.termination_intent.as_str(),
                "natural" | "stop_requested" | "deadline_exceeded"
            )
        {
            return false;
        }
        match self.resolution.as_deref() {
            None => {
                self.current_attempt_id.as_deref() == Some(self.attempt_id.as_str())
                    && matches!(
                        self.attempt_state.as_str(),
                        "accepted" | "starting" | "running" | "stopping" | "recovering"
                    )
                    && self.reservation_state == "active"
                    && self.result_digest.is_none()
                    && self.finished_at_ms.is_none()
            }
            Some(resolution) => {
                self.current_attempt_id.is_none()
                    && self.attempt_state == resolution
                    && matches!(
                        resolution,
                        "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
                    )
                    && self
                        .result_digest
                        .as_deref()
                        .is_some_and(|value| !value.is_empty())
                    && self.finished_at_ms.is_some_and(|value| value >= 0)
                    && self.reservation_state
                        == if resolution == "orphaned" {
                            "held_orphaned"
                        } else {
                            "released"
                        }
            }
        }
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgJobReadback {
    Observed(Box<PgJobSnapshot>),
    Inconclusive,
}

/// Check terminal event digests in the same repeatable-read snapshot.
/// This qualifies recorded evidence only, never a physical effect.
fn terminal_events_coherent(
    tx: &mut Transaction<'_>,
    snapshot: &PgJobSnapshot,
) -> Result<bool, PgAdmissionError> {
    let Some(resolution) = snapshot.resolution.as_deref() else {
        return Ok(true);
    };
    let rows = tx.query(
        "SELECT event_type,origin,new_state,detail_json,detail_digest FROM job_events WHERE job_id=$1 AND attempt_id=$2 AND event_type IN ('PROCESS_EXITED','JOB_TERMINAL')",
        &[&snapshot.job_id, &snapshot.attempt_id],
    )?;
    if rows.len() != 2 {
        return Ok(false);
    }
    let artifact_rows = tx.query(
        "SELECT job_id,artifact_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms FROM artifacts WHERE attempt_id=$1 ORDER BY artifact_id",
        &[&snapshot.attempt_id],
    )?;
    let mut artifacts = Vec::with_capacity(artifact_rows.len());
    for row in artifact_rows {
        if row.get::<_, String>(0) != snapshot.job_id {
            return Ok(false);
        }
        artifacts.push(PgArtifactRegistration {
            artifact_id: row.get(1),
            kind: row.get(2),
            relative_path: row.get(3),
            digest: row.get(4),
            media_type: row.get(5),
            byte_length: row.get(6),
            truncated: row.get(7),
            created_at_ms: row.get(8),
        });
    }
    if !valid_pg_artifacts(&artifacts) {
        return Ok(false);
    }
    let expected_manifest = if artifacts.is_empty() {
        None
    } else {
        Some(pg_artifact_manifest_digest(&artifacts))
    };
    let mut process_observed = false;
    let mut terminal_recorded = false;
    for row in rows {
        let event_type: String = row.get(0);
        let origin: String = row.get(1);
        let state: Option<String> = row.get(2);
        let detail_json: String = row.get(3);
        let digest: String = row.get(4);
        if format!(
            "sha256:{}",
            hex::encode(Sha256::digest(detail_json.as_bytes()))
        ) != digest
            || state.as_deref() != Some(resolution)
        {
            return Ok(false);
        }
        let Ok(detail) = serde_json::from_str::<serde_json::Value>(&detail_json) else {
            return Ok(false);
        };
        match event_type.as_str() {
            "PROCESS_EXITED" if origin == "SYSTEM_OBSERVED" => {
                if process_observed
                    || detail.get("resultDigest").and_then(|v| v.as_str())
                        != snapshot.result_digest.as_deref()
                    || detail.get("artifactSetDigest").and_then(|v| v.as_str())
                        != expected_manifest.as_deref()
                {
                    return Ok(false);
                }
                process_observed = true;
            }
            "JOB_TERMINAL" if origin == "SYSTEM_DERIVED" => {
                if terminal_recorded
                    || detail.get("resolution").and_then(|v| v.as_str()) != Some(resolution)
                {
                    return Ok(false);
                }
                terminal_recorded = true;
            }
            _ => return Ok(false),
        }
    }
    Ok(process_observed && terminal_recorded)
}

impl PgAdmissionStore {
    /// Read a single consistent Job/Attempt/Reservation snapshot without
    /// changing durable state. Only the qualified, source-bound PG writer
    /// namespace can be observed; a staged import is never current truth.
    /// An incoherent or absent row is INCONCLUSIVE, not a missing/terminal Job.
    pub fn observe_job_readonly(
        &mut self,
        job_id: &str,
        expected_source_sha256: &str,
    ) -> Result<PgJobReadback, PgAdmissionError> {
        if job_id.is_empty()
            || expected_source_sha256.len() != 64
            || !expected_source_sha256
                .bytes()
                .all(|byte| byte.is_ascii_hexdigit())
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()?;
        let owner = tx.query_opt(
            "SELECT state, source_sha256, promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = owner.get(0);
        let source: String = owner.get(1);
        let permitted: bool = owner.get(2);
        if state != "QUALIFIED_WRITER" || source != expected_source_sha256 || !permitted {
            return Err(PgAdmissionError::Unqualified);
        }
        let Some(job) = tx.query_opt(
            "SELECT desired_state, resolution, current_attempt_id, row_version FROM jobs WHERE job_id=$1",
            &[&job_id],
        )? else {
            return Ok(PgJobReadback::Inconclusive);
        };
        let Some(attempt) = tx.query_opt(
            "SELECT attempt_id, state, termination_intent, result_digest, finished_at_ms, row_version \
             FROM attempts WHERE job_id=$1 ORDER BY attempt_number DESC LIMIT 1",
            &[&job_id],
        )? else {
            return Ok(PgJobReadback::Inconclusive);
        };
        let attempt_id: String = attempt.get(0);
        let Some(reservation) = tx.query_opt(
            "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
            &[&attempt_id],
        )?
        else {
            return Ok(PgJobReadback::Inconclusive);
        };
        let snapshot = PgJobSnapshot {
            job_id: job_id.to_owned(),
            desired_state: job.get(0),
            resolution: job.get(1),
            current_attempt_id: job.get(2),
            job_row_version: job.get(3),
            attempt_id,
            attempt_state: attempt.get(1),
            termination_intent: attempt.get(2),
            result_digest: attempt.get(3),
            finished_at_ms: attempt.get(4),
            attempt_row_version: attempt.get(5),
            reservation_state: reservation.get(0),
        };
        if !snapshot.lifecycle_coherent() || !terminal_events_coherent(&mut tx, &snapshot)? {
            return Ok(PgJobReadback::Inconclusive);
        }
        // Read-only transaction commit is not an effectful admission.
        tx.commit()?;
        Ok(PgJobReadback::Observed(Box::new(snapshot)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn snapshot() -> PgJobSnapshot {
        PgJobSnapshot {
            job_id: "j".into(),
            desired_state: "run".into(),
            resolution: None,
            current_attempt_id: Some("a".into()),
            attempt_id: "a".into(),
            attempt_state: "accepted".into(),
            termination_intent: "natural".into(),
            reservation_state: "active".into(),
            result_digest: None,
            finished_at_ms: None,
            job_row_version: 0,
            attempt_row_version: 0,
        }
    }

    #[test]
    fn accepted_and_cancel_requested_are_nonterminal_without_false_effect_claim() {
        let mut s = snapshot();
        assert!(s.lifecycle_coherent());
        s.desired_state = "cancelled".into();
        s.termination_intent = "stop_requested".into();
        assert!(s.lifecycle_coherent());
        s.attempt_state = "stopping".into();
        assert!(s.lifecycle_coherent());
        s.current_attempt_id = None;
        assert!(!s.lifecycle_coherent());
    }

    #[test]
    fn terminal_requires_corresponding_attempt_evidence_and_released_capacity() {
        let mut s = snapshot();
        s.resolution = Some("succeeded".into());
        s.current_attempt_id = None;
        s.attempt_state = "succeeded".into();
        s.reservation_state = "released".into();
        s.result_digest = Some("sha256:result".into());
        s.finished_at_ms = Some(20);
        assert!(s.lifecycle_coherent());
        s.result_digest = None;
        assert!(!s.lifecycle_coherent());
        s.result_digest = Some("sha256:result".into());
        s.reservation_state = "active".into();
        assert!(!s.lifecycle_coherent());
        s.reservation_state = "released".into();
        s.attempt_state = "running".into();
        assert!(!s.lifecycle_coherent());
    }

    #[test]
    fn orphan_never_projects_as_released_capacity() {
        let mut s = snapshot();
        s.resolution = Some("orphaned".into());
        s.current_attempt_id = None;
        s.attempt_state = "orphaned".into();
        s.reservation_state = "held_orphaned".into();
        s.result_digest = Some("sha256:orphan".into());
        s.finished_at_ms = Some(9);
        assert!(s.lifecycle_coherent());
        s.reservation_state = "released".into();
        assert!(!s.lifecycle_coherent());
    }

    #[test]
    fn unfinished_attempt_with_terminal_artifacts_is_inconclusive() {
        let mut s = snapshot();
        s.result_digest = Some("sha256:premature".into());
        assert!(!s.lifecycle_coherent());
        s.result_digest = None;
        s.finished_at_ms = Some(12);
        assert!(!s.lifecycle_coherent());
    }
}
