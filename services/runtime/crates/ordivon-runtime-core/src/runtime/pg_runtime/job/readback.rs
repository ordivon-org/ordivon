//! PG Job readback use case.
use super::*;

impl PgRuntime {
    /// Projection only: never calls reconciliation or the OS execution provider.
    pub fn get(
        &self,
        principal: &str,
        job: &str,
        event_limit: u32,
    ) -> RuntimeResult<RuntimeJobInspection> {
        if event_limit > MAX_INSPECTION_EVENT_LIMIT {
            return Err(RuntimeError::invalid("event limit exceeded", "eventLimit"));
        }
        let mut db = self.store()?;
        self.authorize(&mut db, job, principal)?;
        let readback = db
            .observe_job_inspection_readonly(job, &self.config.source_sha256, event_limit)
            .map_err(pg)?
            .ok_or_else(|| error("inconclusive PG lifecycle or inspection"))?;
        let snapshot = readback.snapshot;
        let (a, p, operation) = self.readback_attempt(&mut db, &snapshot)?;
        let metadata = readback
            .inspection
            .ok_or_else(|| error("missing inspection metadata"))?;
        let created = metadata.created_at_ms;
        let mut by_kind = std::collections::BTreeMap::new();
        let (mut count, mut bytes, mut truncated) = (0_u64, 0_u64, 0_u64);
        let (mut attempt_count, mut attempt_bytes, mut attempt_truncated) = (0_u64, 0_u64, 0_u64);
        let mut result_available = false;
        for item in &readback.artifacts {
            let r = &item.registration;
            let length =
                u64::try_from(r.byte_length).map_err(|_| error("negative Artifact length"))?;
            count += 1;
            bytes = bytes
                .checked_add(length)
                .ok_or_else(|| error("Artifact byte count overflow"))?;
            truncated += u64::from(r.truncated);
            *by_kind.entry(r.kind.clone()).or_insert(0_u64) += 1;
            if item.attempt_id == snapshot.attempt_id {
                attempt_count += 1;
                attempt_bytes = attempt_bytes
                    .checked_add(length)
                    .ok_or_else(|| error("Attempt Artifact byte count overflow"))?;
                attempt_truncated += u64::from(r.truncated);
                result_available |= r.kind == "execution_result";
            }
        }
        let mut previous = created;
        let events_truncated = metadata.events.len() > event_limit as usize;
        let timeline = metadata
            .events
            .into_iter()
            .take(event_limit as usize)
            .map(|r| {
                let at = r.observed_at_ms;
                let delta = at.saturating_sub(previous);
                previous = at;
                RuntimeInspectionEvent {
                    sequence: r.sequence,
                    attempt_id: r.attempt_id,
                    event_type: r.event_type,
                    origin: r.origin,
                    previous_state: r.previous_state,
                    new_state: r.new_state,
                    reason_code: r.reason_code,
                    observed_at_ms: at,
                    elapsed_ms: at.saturating_sub(created),
                    delta_ms: delta,
                    detail: None,
                }
            })
            .collect();
        let terminal = snapshot.resolution.is_some();
        let exit = readback.exit_code;
        Ok(RuntimeJobInspection {
            schema_version: 2,
            generated_at_ms: now()? as u64,
            migration_version: 0,
            job: RuntimeInspectionJob {
                job_id: job.into(),
                client_request_id: metadata.client_request_id,
                operation_digest: operation,
                workspace_id: p.workspace_id,
                source_revision: p.source_revision,
                workspace_source_digest: p.workspace_source_digest,
                created_at_ms: created,
                desired_state: if snapshot.desired_state == "run" {
                    JobDesiredState::Run
                } else {
                    JobDesiredState::Cancelled
                },
                resolution: snapshot
                    .resolution
                    .as_deref()
                    .map(JobResolution::parse)
                    .transpose()?,
                mechanically_converged: terminal,
                semantic_completion_evaluated: false,
            },
            attempts: vec![RuntimeInspectionAttempt {
                attempt_id: a.attempt_id,
                attempt_number: a.attempt_number,
                state: a.state,
                termination_intent: a.termination_intent,
                created_at_ms: a.created_at_ms,
                // Same committed Attempt snapshot as the terminal facts.
                // Runner binding is an observation, not physical process start.
                started_at_ms: snapshot.started_at_ms.and_then(|v| u64::try_from(v).ok()),
                finished_at_ms: snapshot.finished_at_ms.map(|v| v as u64),
                // Do not invent physical duration from mixed clock semantics.
                duration_ms: None,
                exit_code: exit,
                result_available: terminal && result_available,
                reservation_state: ReservationState::parse(&snapshot.reservation_state)?,
                reservation_release_reason: None,
                conditions: vec![],
                artifact_count: attempt_count,
                artifact_bytes: attempt_bytes,
                truncated_artifacts: attempt_truncated,
            }],
            attempts_truncated: metadata.has_other_attempts,
            artifacts: RuntimeInspectionArtifactSummary {
                count,
                bytes,
                truncated,
                by_kind,
            },
            episodes: RuntimeInspectionEpisodes::default(),
            timeline,
            events_truncated,
        })
    }
}
