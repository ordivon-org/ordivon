impl Registry {
    #[cfg(test)]
    pub(super) fn list_nonterminal_attempts(&self) -> RuntimeResult<Vec<AttemptRecord>> {
        self.list_nonterminal_attempts_with_limit(None)
    }

    #[cfg(test)]
    fn list_nonterminal_attempts_with_limit(
        &self,
        limit: Option<u32>,
    ) -> RuntimeResult<Vec<AttemptRecord>> {
        let connection = self.open_connection()?;
        let sql = if limit.is_some() {
            "SELECT attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,bundle_digest,boot_id,unit_name,invocation_id,control_group,main_pid,process_start_identity,runner_start_digest,result_digest,exit_code,infrastructure_error_digest,created_at_ms,started_at_ms,finished_at_ms,row_version FROM attempts WHERE state NOT IN ('succeeded','failed','timed_out','cancelled','lost','orphaned') ORDER BY created_at_ms DESC,attempt_id DESC LIMIT ?1"
        } else {
            "SELECT attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,bundle_digest,boot_id,unit_name,invocation_id,control_group,main_pid,process_start_identity,runner_start_digest,result_digest,exit_code,infrastructure_error_digest,created_at_ms,started_at_ms,finished_at_ms,row_version FROM attempts WHERE state NOT IN ('succeeded','failed','timed_out','cancelled','lost','orphaned') ORDER BY created_at_ms,attempt_id"
        };
        let mut statement = connection
            .prepare(sql)
            .map_err(|error| RuntimeError::from_sql(error, "cannot prepare reconciliation scan"))?;
        if let Some(limit) = limit {
            let rows = statement
                .query_map([limit], raw_attempt_from_row)
                .map_err(|error| {
                    RuntimeError::from_sql(error, "cannot scan nonterminal Attempts")
                })?;
            rows.map(|row| {
                row.map_err(|error| RuntimeError::from_sql(error, "cannot decode Attempt row"))?
                    .into_record()
            })
            .collect()
        } else {
            let rows = statement
                .query_map([], raw_attempt_from_row)
                .map_err(|error| {
                    RuntimeError::from_sql(error, "cannot scan nonterminal Attempts")
                })?;
            rows.map(|row| {
                row.map_err(|error| RuntimeError::from_sql(error, "cannot decode Attempt row"))?
                    .into_record()
            })
            .collect()
        }
    }

    pub(super) fn list_maintenance_attempts_bounded(
        &self,
        limit: u32,
    ) -> RuntimeResult<Vec<AttemptRecord>> {
        if limit == 0 {
            return Err(RuntimeError::invalid("limit must be positive", "limit"));
        }
        let connection = self.open_connection()?;
        let mut statement = connection
            .prepare(
                "SELECT a.attempt_id,a.job_id,a.attempt_number,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.bundle_digest,a.boot_id,a.unit_name,a.invocation_id,a.control_group,a.main_pid,a.process_start_identity,a.runner_start_digest,a.result_digest,a.exit_code,a.infrastructure_error_digest,a.created_at_ms,a.started_at_ms,a.finished_at_ms,a.row_version FROM attempts a LEFT JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE a.state NOT IN ('succeeded','failed','timed_out','cancelled','lost','orphaned') OR (a.state='orphaned' AND r.state='held_orphaned') OR COALESCE(a.recovery_required,0)=1 ORDER BY CASE WHEN COALESCE(a.recovery_required,0)=1 THEN 0 WHEN a.state='orphaned' AND r.state='held_orphaned' THEN 1 ELSE 2 END,a.created_at_ms,a.attempt_id LIMIT ?1",
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot prepare maintenance reconciliation scan"))?;
        let rows = statement
            .query_map([limit], raw_attempt_from_row)
            .map_err(|error| RuntimeError::from_sql(error, "cannot scan maintenance Attempts"))?;
        rows.map(|row| {
            row.map_err(|error| {
                RuntimeError::from_sql(error, "cannot decode maintenance Attempt row")
            })?
            .into_record()
        })
        .collect()
    }

    pub(super) fn list_held_orphaned_attempts(&self) -> RuntimeResult<Vec<AttemptRecord>> {
        let connection = self.open_connection()?;
        let mut statement = connection
            .prepare(
                "SELECT a.attempt_id,a.job_id,a.attempt_number,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.bundle_digest,a.boot_id,a.unit_name,a.invocation_id,a.control_group,a.main_pid,a.process_start_identity,a.runner_start_digest,a.result_digest,a.exit_code,a.infrastructure_error_digest,a.created_at_ms,a.started_at_ms,a.finished_at_ms,a.row_version FROM attempts a JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE a.state='orphaned' AND r.state='held_orphaned' ORDER BY a.created_at_ms,a.attempt_id",
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot prepare orphan reconciliation scan"))?;
        let rows = statement
            .query_map([], raw_attempt_from_row)
            .map_err(|error| RuntimeError::from_sql(error, "cannot scan held orphaned Attempts"))?;
        rows.map(|row| {
            row.map_err(|error| {
                RuntimeError::from_sql(error, "cannot decode orphaned Attempt row")
            })?
            .into_record()
        })
        .collect()
    }

    pub(super) fn recover_orphaned_terminal(
        &self,
        request: &TerminalCommit,
    ) -> RuntimeResult<JobProjection> {
        if !matches!(
            request.state,
            AttemptState::Succeeded
                | AttemptState::Failed
                | AttemptState::TimedOut
                | AttemptState::Cancelled
                | AttemptState::Lost
        ) {
            return Err(RuntimeError::invalid(
                "orphan recovery requires a conclusive terminal state",
                "state",
            ));
        }
        validate_digest(&request.result_digest, "resultDigest")?;
        for artifact in &request.artifacts {
            validate_artifact_registration(artifact)?;
        }
        let mut connection = self.open_connection()?;
        let transaction = immediate(&mut connection, "orphan recovery transaction")?;
        let attempt = load_attempt(&transaction, &request.attempt_id)?;
        let job = load_job(&transaction, &attempt.job_id)?;
        let reservation = load_reservation(&transaction, &attempt.attempt_id)?;
        if attempt.state != AttemptState::Orphaned
            || job.resolution != Some(JobResolution::Orphaned)
            || reservation.state != ReservationState::HeldOrphaned
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::OrphanRemediationDenied,
                "Attempt, Job, or reservation changed before Runner-result recovery",
                Some("attemptId"),
                false,
            ));
        }
        if attempt.row_version != request.expected_row_version {
            return Err(state_conflict(
                "Attempt row version changed before orphan recovery",
            ));
        }
        let changed = transaction
            .execute(
                "UPDATE attempts SET state=?1,result_digest=?2,exit_code=?3,infrastructure_error_digest=?4,finished_at_ms=?5,row_version=row_version+1 WHERE attempt_id=?6 AND row_version=?7 AND state='orphaned'",
                params![
                    request.state.as_db(),
                    request.result_digest,
                    request.exit_code,
                    request.infrastructure_error_digest,
                    request.finished_at_ms,
                    request.attempt_id,
                    request.expected_row_version,
                ],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot recover orphaned Attempt"))?;
        if changed != 1 {
            return Err(state_conflict("Attempt changed during orphan recovery"));
        }
        for artifact in &request.artifacts {
            transaction
                .execute(
                    "INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10)",
                    params![
                        artifact.artifact_id,
                        attempt.job_id,
                        attempt.attempt_id,
                        artifact.kind,
                        artifact.relative_path,
                        artifact.digest,
                        artifact.media_type,
                        artifact.byte_length,
                        i64::from(artifact.truncated),
                        request.finished_at_ms,
                    ],
                )
                .map_err(|error| RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    format!("cannot register recovered Artifact {}: {error}", artifact.artifact_id),
                    Some("artifacts"),
                    false,
                ))?;
        }
        release_reservation(
            &transaction,
            &attempt.attempt_id,
            request.finished_at_ms,
            &request.reason_code,
        )?;
        let resolution = resolution_for_state(request.state)?;
        transaction
            .execute(
                "UPDATE jobs SET resolution=?1,row_version=row_version+1 WHERE job_id=?2 AND resolution='orphaned'",
                params![resolution.as_db(), attempt.job_id],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot correct orphaned Job resolution"))?;
        append_event(
            &transaction,
            &attempt.job_id,
            Some(&attempt.attempt_id),
            "RUNNER_RESULT_RECOVERED",
            "SYSTEM_OBSERVED",
            Some(AttemptState::Orphaned),
            Some(request.state),
            &request.reason_code,
            serde_json::json!({"resultDigest": request.result_digest, "exitCode": request.exit_code}),
            request.finished_at_ms,
        )?;
        append_event(
            &transaction,
            &attempt.job_id,
            Some(&attempt.attempt_id),
            "JOB_RESOLUTION_CORRECTED",
            "SYSTEM_DERIVED",
            Some(AttemptState::Orphaned),
            Some(request.state),
            &request.reason_code,
            serde_json::json!({"resolution": resolution.as_db()}),
            request.finished_at_ms,
        )?;
        transaction
            .commit()
            .map_err(|error| RuntimeError::from_sql(error, "cannot commit orphan recovery"))?;
        Ok(load_job_snapshot(&connection, &attempt.job_id)?.projection)
    }

    #[cfg(feature = "operator-tools")]
    pub(crate) fn repair_admin_batch(
        &self,
        operations: &[AdminRepairOperation],
    ) -> RuntimeResult<()> {
        let mut connection = self.open_connection()?;
        let transaction = immediate(&mut connection, "administrative Runtime repair batch")?;
        for operation in operations {
            match operation {
                AdminRepairOperation::Terminal { terminal, audit } => {
                    repair_terminal_admin_transaction(&transaction, terminal, audit)?;
                }
                AdminRepairOperation::Reservation {
                    attempt_id,
                    expected_attempt_row_version,
                    audit,
                } => {
                    repair_terminal_reservation_admin_transaction(
                        &transaction,
                        attempt_id,
                        *expected_attempt_row_version,
                        audit,
                    )?;
                }
            }
        }
        let remaining = inspect_runtime_invariants_connection(&transaction)?;
        if !remaining.is_empty() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                format!(
                    "administrative Runtime repair would leave {} invariant violations",
                    remaining.len()
                ),
                Some("violations"),
                false,
            ));
        }
        transaction.commit().map_err(|error| {
            RuntimeError::from_sql(error, "cannot commit administrative Runtime repair batch")
        })
    }

    pub(super) fn converge_terminal_reservation(
        &self,
        attempt_id: &str,
        observed_at_ms: u64,
    ) -> RuntimeResult<bool> {
        let mut connection = self.open_connection()?;
        let attempt = load_attempt(&connection, attempt_id)?;
        let job = load_job(&connection, &attempt.job_id)?;
        let reservation = load_reservation(&connection, attempt_id)?;
        let target = terminal_reservation_target(&attempt, &job)?;
        if reservation.state == target {
            return Ok(false);
        }

        let transaction = immediate(&mut connection, "terminal reservation convergence")?;
        let attempt = load_attempt(&transaction, attempt_id)?;
        let job = load_job(&transaction, &attempt.job_id)?;
        let reservation = load_reservation(&transaction, attempt_id)?;
        let target = terminal_reservation_target(&attempt, &job)?;
        if reservation.state == target {
            transaction.commit().map_err(|error| {
                RuntimeError::from_sql(error, "cannot close converged terminal reservation")
            })?;
            return Ok(false);
        }
        if target == ReservationState::HeldOrphaned {
            hold_orphaned_reservation(
                &transaction,
                attempt_id,
                observed_at_ms,
                "TERMINAL_ORPHAN_RESERVATION_CONVERGED",
            )?;
        } else {
            release_reservation(
                &transaction,
                attempt_id,
                observed_at_ms,
                "TERMINAL_RESERVATION_CONVERGED",
            )?;
        }
        append_event(
            &transaction,
            &attempt.job_id,
            Some(attempt_id),
            "TERMINAL_RESERVATION_CONVERGED",
            "SYSTEM_DERIVED",
            Some(attempt.state),
            Some(attempt.state),
            "TERMINAL_RESERVATION_CONVERGED",
            serde_json::json!({
                "previousReservationState": reservation.state.as_db(),
                "newReservationState": target.as_db(),
            }),
            observed_at_ms,
        )?;
        transaction.commit().map_err(|error| {
            RuntimeError::from_sql(error, "cannot commit terminal reservation convergence")
        })?;
        Ok(true)
    }

    #[cfg(test)]
    pub(super) fn inspect_runtime_invariants(&self) -> RuntimeResult<Vec<RuntimeInvariantViolation>> {
        let connection = self.open_connection()?;
        inspect_runtime_invariants_connection(&connection)
    }

}
