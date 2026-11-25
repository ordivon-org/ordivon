//! Projection-only Job inspection; no new dispatch, reconciliation or native effect.
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
        let snapshot = match db
            .observe_job_readonly(job, &self.config.source_sha256)
            .map_err(pg)?
        {
            PgJobReadback::Observed(s) => s,
            _ => return Err(error("inconclusive PG lifecycle")),
        };
        let (a, p, operation) = self.readback_attempt(&mut db, &snapshot)?;
        let j = db
            .client
            .query_one(
                "SELECT client_request_id,created_at_ms FROM jobs WHERE job_id=$1",
                &[&job],
            )
            .map_err(pg_read_error)?;
        let counts=db.client.query_one("SELECT count(*),COALESCE(sum(byte_length),0)::bigint,count(*) FILTER(WHERE truncated) FROM artifacts WHERE job_id=$1",&[&job]).map_err(pg_read_error)?;
        let mut by_kind = std::collections::BTreeMap::new();
        for row in db
            .client
            .query(
                "SELECT kind,count(*) FROM artifacts WHERE job_id=$1 GROUP BY kind",
                &[&job],
            )
            .map_err(pg_read_error)?
        {
            by_kind.insert(row.get(0), row.get::<_, i64>(1) as u64);
        }
        let events=db.client.query("SELECT event_sequence,event_type,origin,previous_state,new_state,reason_code,observed_at_ms FROM job_events WHERE job_id=$1 ORDER BY event_sequence LIMIT $2",&[&job,&(i64::from(event_limit)+1)]).map_err(pg_read_error)?;
        let created = j.get::<_, i64>(1) as u64;
        let mut previous = created;
        let timeline = events
            .iter()
            .take(event_limit as usize)
            .map(|r| {
                let at = r.get::<_, i64>(6) as u64;
                let delta = at.saturating_sub(previous);
                previous = at;
                RuntimeInspectionEvent {
                    sequence: r.get::<_, i64>(0) as u64,
                    attempt_id: Some(a.attempt_id.clone()),
                    event_type: r.get(1),
                    origin: r.get(2),
                    previous_state: r.get(3),
                    new_state: r.get(4),
                    reason_code: r.get(5),
                    observed_at_ms: at,
                    elapsed_ms: at.saturating_sub(created),
                    delta_ms: delta,
                    detail: None,
                }
            })
            .collect();
        let terminal = snapshot.resolution.is_some();
        let exit = db
            .client
            .query_one(
                "SELECT exit_code FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .map_err(pg_read_error)?
            .get(0);
        Ok(RuntimeJobInspection {
            schema_version: 2,
            generated_at_ms: now()? as u64,
            migration_version: 0,
            job: RuntimeInspectionJob {
                job_id: job.into(),
                client_request_id: j.get(0),
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
                result_available: terminal && by_kind.contains_key("execution_result"),
                reservation_state: ReservationState::parse(&snapshot.reservation_state)?,
                reservation_release_reason: None,
                conditions: vec![],
                artifact_count: counts.get::<_, i64>(0) as u64,
                artifact_bytes: counts.get::<_, i64>(1) as u64,
                truncated_artifacts: counts.get::<_, i64>(2) as u64,
            }],
            attempts_truncated: false,
            artifacts: RuntimeInspectionArtifactSummary {
                count: counts.get::<_, i64>(0) as u64,
                bytes: counts.get::<_, i64>(1) as u64,
                truncated: counts.get::<_, i64>(2) as u64,
                by_kind,
            },
            episodes: RuntimeInspectionEpisodes::default(),
            timeline,
            events_truncated: events.len() > event_limit as usize,
        })
    }
}
