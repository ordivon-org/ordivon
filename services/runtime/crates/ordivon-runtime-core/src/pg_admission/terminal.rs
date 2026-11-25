//! PostgreSQL admission owner: terminal.
use super::*;

impl PgAdmissionStore {
    /// Exact no-Artifact terminal/Job/reservation/event atomicity, no runner or
    /// external output effect. Arbitrary Artifact-bearing terminal commits are
    /// deliberately unsupported until a complete consumer-owned transaction.
    pub fn commit_terminal_no_artifacts(
        &mut self,
        i: &PgTerminalNoArtifacts,
    ) -> Result<PgTerminalOutcome, PgAdmissionError> {
        self.commit_terminal_artifacts_impl(i, &[])
    }
    pub fn commit_terminal_with_artifacts(
        &mut self,
        i: &PgTerminalNoArtifacts,
        artifacts: &[PgArtifactRegistration],
    ) -> Result<PgTerminalOutcome, PgAdmissionError> {
        if artifacts.is_empty() {
            return Err(PgAdmissionError::InvalidInput);
        }
        self.commit_terminal_artifacts_impl(i, artifacts)
    }
    fn commit_terminal_artifacts_impl(
        &mut self,
        i: &PgTerminalNoArtifacts,
        artifacts: &[PgArtifactRegistration],
    ) -> Result<PgTerminalOutcome, PgAdmissionError> {
        if !valid_pg_artifacts(artifacts) {
            return Err(PgAdmissionError::InvalidInput);
        }
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
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, true)?;
        let current=tx.query_opt(
            "SELECT job_id,state,result_digest,row_version,unit_name,launch_token_digest,bundle_digest FROM attempts WHERE attempt_id=$1 FOR UPDATE",
            &[&i.attempt_id])?.ok_or(PgAdmissionError::InvalidInput)?;
        let job_id: String = current.get(0);
        let previous: String = current.get(1);
        let digest: Option<String> = current.get(2);
        let version: i64 = current.get(3);
        let job = tx.query_one(
            "SELECT resolution,current_attempt_id,workspace_snapshot_json FROM jobs WHERE job_id=$1 FOR UPDATE",
            &[&job_id],
        )?;
        let job_resolution: Option<String> = job.get(0);
        let current_attempt: Option<String> = job.get(1);
        let existing = tx.query(
            "SELECT artifact_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms FROM artifacts WHERE attempt_id=$1 ORDER BY artifact_id",
            &[&i.attempt_id],
        )?;
        if artifacts.is_empty() && !existing.is_empty() {
            return Err(PgAdmissionError::Blocked);
        }
        let mut sorted = artifacts.to_vec();
        sorted.sort_by(|a, b| a.artifact_id.cmp(&b.artifact_id));
        let same_artifacts = existing.len() == sorted.len()
            && existing.iter().zip(&sorted).all(|(row, a)| {
                row.get::<_, String>(0) == a.artifact_id
                    && row.get::<_, String>(1) == a.kind
                    && row.get::<_, String>(2) == a.relative_path
                    && row.get::<_, String>(3) == a.digest
                    && row.get::<_, String>(4) == a.media_type
                    && row.get::<_, i64>(5) == a.byte_length
                    && row.get::<_, bool>(6) == a.truncated
                    && row.get::<_, i64>(7) == a.created_at_ms
            });
        if matches!(
            previous.as_str(),
            "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
        ) {
            if previous == i.terminal_state
                && digest.as_deref() == Some(&i.result_digest)
                && job_resolution.as_deref() == Some(&i.terminal_state)
                && same_artifacts
            {
                tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
                return Ok(PgTerminalOutcome::Existing(job_id));
            }
            return Err(PgAdmissionError::IdempotencyConflict);
        }
        if !existing.is_empty() {
            return Err(PgAdmissionError::Blocked);
        }
        // The Job's current Attempt is the only Attempt allowed to commit a
        // fresh terminal effect. A superseded Attempt may not resolve the Job,
        // release another Attempt's capacity, or append terminal events.
        // Completed exact replay above remains legal after the Job clears
        // current_attempt_id.
        if current_attempt.as_deref() != Some(i.attempt_id.as_str()) {
            return Err(PgAdmissionError::Blocked);
        }
        if version != i.expected_row_version
            || !terminal_transition(&previous, &i.terminal_state)
            || job_resolution.is_some()
        {
            return Err(PgAdmissionError::Blocked);
        }
        // The same serializable PG transaction owning terminal+Artifacts MUST
        // enforce a Windows native source-bound kernel event. A caller cannot
        // bypass this by skipping the normal native reconciliation adapter.
        // Linux systemd/cgroup jobs and non-result LOST/orphaned recovery are
        // untouched. The native caller separately proves original OS exit.
        // The provider is an admitted Job identity, not an inference from
        // a mutable file extension. Older R8 candidate admissions used a
        // Linux-looking ".service" name even for the Windows native provider:
        // that mismatch must BLOCK instead of silently bypassing the guard.
        let snapshot_json: String = job.get(2);
        let provider: serde_json::Value =
            serde_json::from_str(&snapshot_json).map_err(|_| PgAdmissionError::Unqualified)?;
        let declared_native = provider
            .pointer("/executionProvider/contract")
            .and_then(serde_json::Value::as_str)
            == Some("windows_native_launcher_v1");
        let native_name = format!("Ordivon.{}", i.attempt_id);
        let original_native: String = current.get(4);
        if declared_native || original_native == native_name {
            if original_native != native_name {
                return Err(PgAdmissionError::Blocked);
            }
            if matches!(
                i.terminal_state.as_str(),
                "succeeded" | "failed" | "timed_out" | "cancelled"
            ) {
                if artifacts.is_empty() {
                    return Err(PgAdmissionError::Blocked);
                }
                let bundle_digest: Option<String> = current.get(6);
                let bundle_digest = bundle_digest.ok_or(PgAdmissionError::Blocked)?;
                native_windows_drain::require_native_windows_drain_in_terminal_tx(
                    &mut tx,
                    &job_id,
                    &i.attempt_id,
                    &i.expected_source_sha256,
                    &current.get::<_, String>(5),
                    &bundle_digest,
                    &i.result_digest,
                    i.expected_row_version,
                )?;
            }
        }
        let changed=tx.execute(
            "UPDATE attempts SET state=$1,result_digest=$2,exit_code=$3,finished_at_ms=$4,row_version=row_version+1 WHERE attempt_id=$5 AND row_version=$6 AND state=$7",
            &[&i.terminal_state,&i.result_digest,&i.exit_code,&i.finished_at_ms,
              &i.attempt_id,&i.expected_row_version,&previous])?;
        if changed != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        for a in artifacts {
            tx.execute(
                "INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
                &[&a.artifact_id,&job_id,&i.attempt_id,&a.kind,&a.relative_path,
                &a.digest,&a.media_type,&a.byte_length,&a.truncated,&a.created_at_ms],
            )?;
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
        tx.execute("UPDATE job_allocations SET state='released',released_at_ms=$1 WHERE attempt_id=$2 AND state='active'", &[&i.finished_at_ms,&i.attempt_id])?;
        tx.query_one(
            "SELECT pg_notify('ordivon_runtime_schedule',current_schema())",
            &[],
        )?;
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
                if artifacts.is_empty() {
                    serde_json::json!({"resultDigest":i.result_digest,"exitCode":i.exit_code})
                } else {
                    serde_json::json!({
                        "resultDigest":i.result_digest,
                        "exitCode":i.exit_code,
                        "artifactSetDigest":pg_artifact_manifest_digest(artifacts)
                    })
                },
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
