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
        let (_a, p, operation) = self.readback_attempt(&mut db, &snapshot)?;
        let j = db
            .client
            .query_one(
                "SELECT client_request_id,created_at_ms FROM jobs WHERE job_id=$1",
                &[&job],
            )
            .map_err(pg_read_error)?;
        let invalid_links: bool = db.client.query_one(
            "SELECT EXISTS(SELECT 1 FROM artifacts r LEFT JOIN attempts a ON a.attempt_id=r.attempt_id WHERE r.job_id=$1 AND a.job_id IS DISTINCT FROM r.job_id) OR EXISTS(SELECT 1 FROM job_events e LEFT JOIN attempts a ON a.attempt_id=e.attempt_id WHERE e.job_id=$1 AND e.attempt_id IS NOT NULL AND a.job_id IS DISTINCT FROM e.job_id)",
            &[&job],
        ).map_err(pg_read_error)?.get(0);
        if invalid_links {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                "contradictory Job/Attempt evidence relationship",
                Some("jobId"),
                false,
            )
            .with_operation_id(job));
        }
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
        let events=db.client.query("SELECT event_sequence,event_type,origin,previous_state,new_state,reason_code,observed_at_ms,attempt_id FROM job_events WHERE job_id=$1 ORDER BY event_sequence LIMIT $2",&[&job,&(i64::from(event_limit)+1)]).map_err(pg_read_error)?;
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
                    attempt_id: r.get(7),
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
        let cap = crate::runtime::inspection_contract::MAX_INSPECTION_ATTEMPTS;
        // Match the existing storage-neutral, bounded Job inspection contract.
        // Each Attempt's result and artifact counts belong only to that Attempt.
        let attempt_rows = db.client.query(
            "SELECT a.attempt_id,a.attempt_number,a.state,a.termination_intent,a.created_at_ms,a.started_at_ms,a.finished_at_ms,a.exit_code,r.state,r.release_reason,x.count,x.bytes,x.truncated,x.has_result
             FROM (SELECT * FROM attempts WHERE job_id=$1 ORDER BY attempt_number LIMIT $2) a
             LEFT JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id
             CROSS JOIN LATERAL (SELECT count(*) AS count,COALESCE(sum(byte_length),0)::bigint AS bytes,count(*) FILTER(WHERE truncated) AS truncated,COALESCE(bool_or(kind='execution_result'),false) AS has_result FROM artifacts WHERE attempt_id=a.attempt_id AND job_id=a.job_id) x
             ORDER BY a.attempt_number",
            &[&job, &(i64::from(cap)+1)],
        ).map_err(pg_read_error)?;
        let attempts_truncated = attempt_rows.len() > cap as usize;
        let mut attempts = Vec::with_capacity(attempt_rows.len().min(cap as usize));
        for row in attempt_rows.iter().take(cap as usize) {
            let state = AttemptState::parse(&row.get::<_, String>(2))?;
            let created_at_ms = row.get::<_, i64>(4) as u64;
            let finished_at_ms = row.get::<_, Option<i64>>(6).map(|v| v as u64);
            let reservation_state = row.get::<_, Option<String>>(8).ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::ReconciliationRequired,
                    "historical Attempt has no reservation evidence",
                    Some("jobId"),
                    false,
                )
                .with_operation_id(job)
            })?;
            attempts.push(RuntimeInspectionAttempt {
                attempt_id: row.get(0),
                attempt_number: u32::try_from(row.get::<_, i64>(1)).map_err(|_| {
                    RuntimeError::invalid("invalid attempt number", "attemptNumber")
                })?,
                state,
                termination_intent: AttemptTerminationIntent::parse(&row.get::<_, String>(3))?,
                created_at_ms,
                started_at_ms: row.get::<_, Option<i64>>(5).map(|v| v as u64),
                finished_at_ms,
                duration_ms: finished_at_ms.map(|v| v.saturating_sub(created_at_ms)),
                exit_code: row.get(7),
                result_available: state.is_terminal() && row.get::<_, bool>(13),
                reservation_state: ReservationState::parse(&reservation_state)?,
                reservation_release_reason: row.get(9),
                conditions: vec![],
                artifact_count: row.get::<_, i64>(10) as u64,
                artifact_bytes: row.get::<_, i64>(11) as u64,
                truncated_artifacts: row.get::<_, i64>(12) as u64,
            });
        }
        // A bounded read can never establish mechanical convergence for an
        // omitted Attempt. This still does not prove native NoFutureSpawn.
        let mechanically_converged = terminal
            && !attempts_truncated
            && !attempts.is_empty()
            && attempts.iter().all(|attempt| {
                attempt.state.is_terminal()
                    && attempt.reservation_state == ReservationState::Released
            });
        let episode_rows = db
            .client
            .query(
                "SELECT event_type,count(*) FROM job_events WHERE job_id=$1 GROUP BY event_type",
                &[&job],
            )
            .map_err(pg_read_error)?;
        let episode_counts: std::collections::BTreeMap<String, u64> = episode_rows
            .iter()
            .map(|r| (r.get(0), r.get::<_, i64>(1) as u64))
            .collect();
        let count = |kind: &str| episode_counts.get(kind).copied().unwrap_or(0);
        let duplicate_dispatches: i64 = db.client.query_one(
            "SELECT COALESCE(sum(extra),0)::bigint FROM (SELECT count(*)-1 AS extra FROM job_events WHERE job_id=$1 AND event_type='DISPATCH_ISSUED' GROUP BY attempt_id HAVING count(*)>1) duplicates",
            &[&job],
        ).map_err(pg_read_error)?.get(0);
        let episodes = RuntimeInspectionEpisodes {
            dispatches: count("DISPATCH_ISSUED"),
            duplicate_dispatches: duplicate_dispatches as u64,
            stop_requests: count("STOP_REQUESTED"),
            reconciliation_failures: count("RECONCILIATION_FAILED"),
            reconciliation_convergences: count("RECONCILIATION_CONVERGED"),
            runner_result_recoveries: count("RUNNER_RESULT_RECOVERED"),
            resolution_corrections: count("JOB_RESOLUTION_CORRECTED"),
            administrative_repairs: count("ADMIN_TERMINAL_REPAIR"),
        };
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
                mechanically_converged,
                semantic_completion_evaluated: false,
            },
            attempts,
            attempts_truncated,
            artifacts: RuntimeInspectionArtifactSummary {
                count: counts.get::<_, i64>(0) as u64,
                bytes: counts.get::<_, i64>(1) as u64,
                truncated: counts.get::<_, i64>(2) as u64,
                by_kind,
            },
            episodes,
            timeline,
            events_truncated: events.len() > event_limit as usize,
        })
    }
}
