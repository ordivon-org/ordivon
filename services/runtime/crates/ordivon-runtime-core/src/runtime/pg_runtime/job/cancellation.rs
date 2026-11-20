//! PostgreSQL Job cancellation: persist cancellation intent, then request native stop.
//! A stop request is not a terminal witness; reconciliation retains UNKNOWN.
use super::*;

impl PgRuntime {
    pub fn cancel(
        &self,
        principal: &str,
        request: &JobCancelRequest,
    ) -> RuntimeResult<JobObservation> {
        if request.schema_version != 1 {
            return Err(RuntimeError::invalid(
                "schemaVersion must be 1",
                "schemaVersion",
            ));
        }
        let mut db = self.store()?;
        self.authorize(&mut db, &request.job_id, principal)?;
        // A generic Job cancellation is not an operator Release rollback.
        let is_release: bool = db
            .client
            .query_one(
                "SELECT EXISTS(SELECT 1 FROM job_runtime_release_effects WHERE job_id=$1)",
                &[&request.job_id],
            )
            .map_err(pg_read_error)
            .map_err(|e| e.with_operation_id(&request.job_id))?
            .get(0);
        if is_release {
            return Err(RuntimeError::new(
                RuntimeErrorCode::DeploymentInProgress,
                "Runtime ReleaseEffect requires operator receipt reconciliation",
                Some("runtimeReleaseEffect"),
                false,
            )
            .with_operation_id(&request.job_id));
        }
        let cancel_outcome = db
            .request_cancel_intent(&PgCancelIntent {
                job_id: request.job_id.clone(),
                observed_at_ms: now()?,
                expected_source_sha256: self.config.source_sha256.clone(),
            })
            .map_err(pg)?;
        // Post-commit control cannot become NOT_COMMITTED just because the
        // original Plan is damaged or readback/OS observation is unresolved.
        preserve_committed_job_identity(
            &request.job_id,
            self.cancel_committed(principal, request, &mut db, cancel_outcome),
        )
    }

    fn cancel_committed(
        &self,
        principal: &str,
        request: &JobCancelRequest,
        db: &mut PgAdmissionStore,
        cancel_outcome: PgCancelOutcome,
    ) -> RuntimeResult<JobObservation> {
        if matches!(cancel_outcome, PgCancelOutcome::Existing(_)) {
            // A terminal Job deliberately clears current_attempt_id; the
            // existing PG cancel transaction performs no write in this case.
            // Return the qualified historical Attempt projection instead of
            // attempting native stop against a nonexistent current Attempt.
            // Do not short-circuit an orphaned Job with held native capacity.
            if let PgJobReadback::Observed(snapshot) = db
                .observe_job_readonly(&request.job_id, &self.config.source_sha256)
                .map_err(pg)?
            {
                if snapshot
                    .resolution
                    .as_deref()
                    .is_some_and(|state| state != "orphaned")
                {
                    return self.project(
                        db,
                        &JobObserveRequest {
                            schema_version: 1,
                            job_id: request.job_id.clone(),
                            wait_ms: 0,
                            wait_until: JobObserveWaitUntil::Terminal,
                            stdout_tail_bytes: 4096,
                            stderr_tail_bytes: 4096,
                            stdout_offset: None,
                            stderr_offset: None,
                        },
                    );
                }
            }
        }
        let a = self.cancel_attempt_identity(db, &request.job_id)?;
        if !a.state.is_terminal() {
            prepare_private_pg_attempt_bundle(Path::new(&a.bundle_path))?;
            {
                // The same trusted root-owned Attempt inode is locked by the
                // Runner while checking cancel and spawning each payload.
                // Once this marker is durable and the lock is released, any
                // later Runner step must observe cancellation before spawn.
                let _spawn_guard =
                    universal::lock_attempt_spawn_fence(Path::new(&a.bundle_path)).map_err(io)?;
                universal::write_json_atomic(
                    &Path::new(&a.bundle_path).join("cancel-requested.json"),
                    &json!({"requestedAtMs":now()?}),
                )
                .map_err(io)?;
            }
            if a.state == AttemptState::Accepted {
                self.reconcile(db, &request.job_id)?;
                return self.project(
                    db,
                    &JobObserveRequest {
                        schema_version: 1,
                        job_id: request.job_id.clone(),
                        wait_ms: 0,
                        wait_until: JobObserveWaitUntil::Terminal,
                        stdout_tail_bytes: 4096,
                        stderr_tail_bytes: 4096,
                        stdout_offset: None,
                        stderr_offset: None,
                    },
                );
            }
            // systemd-run already sets KillMode=control-group,
            // TimeoutStopSec=2s and SendSIGKILL=yes. Reuse that native
            // stop policy: no extra PID walker, custom signal escalation or
            // immediate hard-kill wrapper is needed.
            if a.unit_name != format!("ordivon-pg-{}.service", a.attempt_id) {
                return Err(error("Attempt native unit identity mismatch"));
            }
            let stop = super::platform::stop_unit_no_block(&a.unit_name)?;
            if !stop.status.success() {
                // A transient Unit may already have been collected. This
                // failed submission is not proof of an active process; native
                // reconciliation owns the terminal/no-result decision.
                let unit = super::platform::systemctl_show(&a.unit_name)?;
                if super::platform::unit_is_active(&unit)
                    || super::platform::unit_has_pending_job(&unit)
                {
                    return Err(error(format!(
                        "cancel intent persisted; native stop not confirmed for {}",
                        request.job_id
                    )));
                }
            }
        }
        self.observe(
            principal,
            &JobObserveRequest {
                schema_version: 1,
                job_id: request.job_id.clone(),
                wait_ms: 0,
                wait_until: JobObserveWaitUntil::Terminal,
                stdout_tail_bytes: 4096,
                stderr_tail_bytes: 4096,
                stdout_offset: None,
                stderr_offset: None,
            },
        )
    }
}
