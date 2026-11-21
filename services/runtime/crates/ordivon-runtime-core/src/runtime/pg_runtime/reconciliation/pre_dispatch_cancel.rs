//! No-spawn accepted cancellation committed from original PostgreSQL stop evidence.
use super::*;

impl PgRuntime {
    /// A PG-fenced accepted cancellation is already past the only boundary
    /// where this Attempt could be dispatched. Materialize the existing
    /// deterministic cancellation Artifact without decoding an executable
    /// Plan that must never run. The terminal PG CAS still arbitrates races.
    pub(super) fn reconcile_accepted_cancel(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
        a: &AttemptRecord,
    ) -> RuntimeResult<()> {
        let path = PathBuf::from(&a.bundle_path);
        // STOP_REQUESTED fences eligible_attempt in the same PG authority.
        // Accepted means dispatch intent has not crossed its atomic boundary;
        // a concurrent dispatcher must fail its expected-row-version CAS.
        let cancelled_at: i64 = db.client.query_one(
            "SELECT min(observed_at_ms) FROM job_events WHERE attempt_id=$1 AND event_type='STOP_REQUESTED'",
            &[&a.attempt_id],
        ).map_err(pg_read_error)?.get::<_,Option<i64>>(0)
            .ok_or_else(|| error("cancelled admission omitted stop event"))?;
        let bytes = serde_json::to_vec(&json!({"schemaVersion":1,
            "jobId":job,"attemptId":a.attempt_id,"dispatchIssued":false,
            "terminalState":"cancelled","finishedAtMs":cancelled_at}))
        .map_err(io)?;
        prepare_private_pg_attempt_bundle(&path)?;
        let evidence_path = path.join("admission-cancel-evidence.json");
        // All bytes are deterministic from committed PG identity and its
        // first stop event, including across concurrent exact replays.
        if evidence_path.exists() {
            if fs::read(&evidence_path).map_err(io)? != bytes {
                return Err(error("admission cancel evidence mismatch"));
            }
        } else {
            universal::write_bytes_atomic(&evidence_path, &bytes).map_err(io)?;
        }
        let digest = universal::sha256_bytes(&bytes);
        db.commit_terminal_with_artifacts(
            &PgTerminalNoArtifacts {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: a.row_version as i64,
                terminal_state: "cancelled".into(),
                result_digest: digest.clone(),
                reason_code: "CANCELLED_BEFORE_DISPATCH".into(),
                exit_code: None,
                finished_at_ms: cancelled_at,
                expected_source_sha256: self.config.source_sha256.clone(),
            },
            &[PgArtifactRegistration {
                artifact_id: format!("artifact-{}-admission-cancel", a.attempt_id),
                kind: "admission_cancel_evidence".into(),
                relative_path: "admission-cancel-evidence.json".into(),
                digest,
                media_type: "application/json".into(),
                byte_length: bytes.len() as i64,
                truncated: false,
                created_at_ms: cancelled_at,
            }],
        )
        .map_err(pg)?;
        Ok(())
    }
}
