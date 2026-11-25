//! PG Job observation use case.
use super::*;

impl PgRuntime {
    pub fn observe(
        &self,
        principal: &str,
        request: &JobObserveRequest,
    ) -> RuntimeResult<JobObservation> {
        if request.schema_version != 1
            || request.wait_ms > MAX_TASK_WAIT_MS
            || request.stdout_tail_bytes > MAX_TASK_TAIL_BYTES
            || request.stderr_tail_bytes > MAX_TASK_TAIL_BYTES
        {
            return Err(RuntimeError::invalid(
                "invalid observation limits",
                "waitMs",
            ));
        }
        let deadline = Instant::now() + Duration::from_millis(request.wait_ms);
        let mut initial_signature = None;
        let mut db = self.store()?;
        let mut verified_committed_job = false;
        loop {
            // An authorization success proves this durable Job identity.
            // Every later PG projection/observation failure must preserve it
            // for reconcile-first semantics, including after a LISTEN wait.
            self.authorize(&mut db, &request.job_id, principal)
                .map_err(|e| {
                    if verified_committed_job {
                        e.with_operation_id(&request.job_id)
                    } else {
                        e
                    }
                })?;
            verified_committed_job = true;
            // A concurrent PG writer may abort this reconciliation after
            // durable DISPATCH_ISSUED or an OS handoff. Direct job.observe
            // must never repeat that physical effect on SQLSTATE 40001:
            // recover by projecting the exact already-authorized Job only.
            let reconciliation = self.reconcile(&mut db, &request.job_id);
            let value =
                project_committed_job_after_reconcile(&request.job_id, reconciliation, || {
                    self.project(&mut db, request)
                })?;
            // Gateway observes change_or_terminal. Only compare durable
            // observable state, not time-dependent display projections.
            let signature = (
                value.status.clone(),
                value.desired_state,
                value.attempt_state,
                value.termination_intent,
                value.execution_terminal,
                value.delivery_disposition,
                value.recovery_required,
                value.stdout_available_bytes,
                value.stderr_available_bytes,
                value.artifacts.len(),
            );
            let changed = initial_signature
                .as_ref()
                .is_some_and(|start| start != &signature);
            if initial_signature.is_none() {
                initial_signature = Some(signature);
            }
            if value.execution_terminal
                || request.wait_ms == 0
                || Instant::now() >= deadline
                || (request.wait_until == JobObserveWaitUntil::ChangeOrTerminal && changed)
            {
                return Ok(value);
            }
            if value.attempt_state == Some(AttemptState::Accepted) {
                use postgres::fallible_iterator::FallibleIterator;
                db.client
                    .batch_execute("LISTEN ordivon_runtime_schedule")
                    .map_err(pg_read_error)
                    .map_err(|e| e.with_operation_id(&request.job_id))?;
                let wait = deadline
                    .saturating_duration_since(Instant::now())
                    .min(Duration::from_secs(1));
                let _ = db
                    .client
                    .notifications()
                    .timeout_iter(wait)
                    .next()
                    .map_err(pg_read_error)
                    .map_err(|e| e.with_operation_id(&request.job_id))?;
            } else if let Some(attempt_id) = value.attempt_id.as_deref() {
                let bundle = self
                    .config
                    .executor
                    .store_root
                    .join("pg-attempts")
                    .join(attempt_id);
                let start = fs::read(bundle.join("runner-start.json"))
                    .ok()
                    .and_then(|bytes| serde_json::from_slice::<RunnerStartEvidence>(&bytes).ok());
                super::super::platform::wait_for_attempt_change(
                    &bundle,
                    start
                        .as_ref()
                        .map(|evidence| evidence.control_group.as_str()),
                    deadline.saturating_duration_since(Instant::now()),
                );
            } else {
                thread::sleep(
                    Duration::from_millis(250)
                        .min(deadline.saturating_duration_since(Instant::now())),
                );
            }
        }
    }
}
