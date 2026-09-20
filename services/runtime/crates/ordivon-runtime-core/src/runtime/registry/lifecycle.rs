impl Registry {
    pub(super) fn mark_bundle_ready(
        &self,
        attempt_id: &str,
        expected_row_version: u64,
        bundle_digest: &str,
        observed_at_ms: u64,
    ) -> RuntimeResult<AttemptRecord> {
        validate_digest(bundle_digest, "bundleDigest")?;
        let mut connection = self.open_connection()?;
        let transaction = immediate(&mut connection, "bundle-ready transaction")?;
        let attempt = load_attempt(&transaction, attempt_id)?;
        if attempt.state != AttemptState::Accepted || attempt.row_version != expected_row_version {
            return Err(state_conflict(
                "Attempt is not the expected accepted version",
            ));
        }
        let changed = transaction
            .execute(
                "UPDATE attempts SET bundle_digest=?1,row_version=row_version+1 WHERE attempt_id=?2 AND state='accepted' AND row_version=?3",
                params![bundle_digest, attempt_id, expected_row_version],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot bind bundle identity"))?;
        if changed != 1 {
            return Err(state_conflict("Attempt changed while binding bundle"));
        }
        append_event(
            &transaction,
            &attempt.job_id,
            Some(attempt_id),
            "BUNDLE_READY",
            "SYSTEM_OBSERVED",
            Some(AttemptState::Accepted),
            Some(AttemptState::Accepted),
            "BUNDLE_COMMITTED",
            serde_json::json!({"bundleDigest": bundle_digest}),
            observed_at_ms,
        )?;
        transaction
            .commit()
            .map_err(|error| RuntimeError::from_sql(error, "cannot commit bundle identity"))?;
        load_attempt(&connection, attempt_id)
    }

    pub(super) fn mark_dispatch_issued(
        &self,
        attempt_id: &str,
        expected_row_version: u64,
        observed_at_ms: u64,
    ) -> RuntimeResult<AttemptRecord> {
        let mut connection = self.open_connection()?;
        let transaction = immediate(&mut connection, "dispatch-intent transaction")?;
        let attempt = load_attempt(&transaction, attempt_id)?;
        if attempt.state != AttemptState::Accepted
            || attempt.row_version != expected_row_version
            || attempt.bundle_digest.is_none()
        {
            return Err(state_conflict(
                "Attempt must be accepted with a committed bundle",
            ));
        }
        let changed = transaction
            .execute(
                "UPDATE attempts SET state='starting',row_version=row_version+1 WHERE attempt_id=?1 AND state='accepted' AND row_version=?2 AND bundle_digest IS NOT NULL",
                params![attempt_id, expected_row_version],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot persist dispatch intent"))?;
        if changed != 1 {
            return Err(state_conflict("Attempt changed before dispatch intent"));
        }
        let evidence = attempt.bundle_digest.clone().unwrap_or_default();
        append_event(
            &transaction,
            &attempt.job_id,
            Some(attempt_id),
            "DISPATCH_ISSUED",
            "SYSTEM_DERIVED",
            Some(AttemptState::Accepted),
            Some(AttemptState::Starting),
            "AT_MOST_ONCE_BOUNDARY_COMMITTED",
            serde_json::json!({"bundleDigest": evidence}),
            observed_at_ms,
        )?;
        transaction
            .commit()
            .map_err(|error| RuntimeError::from_sql(error, "cannot commit dispatch intent"))?;
        load_attempt(&connection, attempt_id)
    }

    pub(super) fn bind_running(
        &self,
        attempt_id: &str,
        expected_row_version: u64,
        identity: &RunnerIdentity,
    ) -> RuntimeResult<AttemptRecord> {
        validate_runner_identity(identity)?;
        let mut connection = self.open_connection()?;
        let transaction = immediate(&mut connection, "runner-bind transaction")?;
        let attempt = load_attempt(&transaction, attempt_id)?;
        if attempt_runner_identity_matches(&attempt, identity) {
            return Ok(attempt);
        }
        if !matches!(
            attempt.state,
            AttemptState::Starting | AttemptState::Recovering
        ) || attempt.row_version != expected_row_version
            || attempt.unit_name != identity.unit_name
        {
            return Err(state_conflict(
                "Attempt is not bindable to this Runner identity",
            ));
        }

        let changed = transaction
            .execute(
                "UPDATE attempts SET state='running',boot_id=?1,invocation_id=?2,control_group=?3,main_pid=?4,process_start_identity=?5,runner_start_digest=?6,started_at_ms=COALESCE(started_at_ms,?7),row_version=row_version+1 WHERE attempt_id=?8 AND row_version=?9 AND state IN ('starting','recovering')",
                params![
                    identity.boot_id,
                    identity.invocation_id,
                    identity.control_group,
                    identity.main_pid,
                    identity.process_start_identity,
                    identity.runner_start_digest,
                    identity.observed_at_ms,
                    attempt_id,
                    expected_row_version,
                ],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot bind Runner identity"))?;
        if changed != 1 {
            return Err(state_conflict("Attempt changed while binding Runner"));
        }
        append_event(
            &transaction,
            &attempt.job_id,
            Some(attempt_id),
            "RUNNER_BOUND",
            "SYSTEM_OBSERVED",
            Some(attempt.state),
            Some(AttemptState::Running),
            "RUNNER_IDENTITY_MATCHED",
            serde_json::json!({
                "bootId": identity.boot_id,
                "unitName": identity.unit_name,
                "invocationId": identity.invocation_id,
                "controlGroup": identity.control_group,
                "mainPid": identity.main_pid,
                "processStartIdentity": identity.process_start_identity,
            }),
            identity.observed_at_ms,
        )?;
        transaction
            .commit()
            .map_err(|error| RuntimeError::from_sql(error, "cannot commit Runner identity"))?;
        load_attempt(&connection, attempt_id)
    }

    pub(crate) fn attempt_supervisor_owner(
        &self,
        attempt_id: &str,
    ) -> RuntimeResult<Option<AttemptSupervisorOwner>> {
        let connection = self.open_connection()?;
        let row: Option<(String, String)> = connection
            .query_row(
                "SELECT owner_json,owner_digest FROM attempt_supervisor_owners WHERE attempt_id=?1",
                [attempt_id],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .optional()
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot read Attempt Supervisor Owner")
            })?;
        let Some((owner_json, owner_digest)) = row else {
            return Ok(None);
        };
        if sha256_bytes(owner_json.as_bytes()) != owner_digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "stored Attempt Supervisor Owner digest does not match side truth",
                Some("attemptSupervisorOwner"),
                false,
            ));
        }
        let owner: AttemptSupervisorOwner = serde_json::from_str(&owner_json).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("stored Attempt Supervisor Owner is invalid: {error}"),
                Some("attemptSupervisorOwner"),
                false,
            )
        })?;
        validate_attempt_supervisor_owner(&owner)?;
        Ok(Some(owner))
    }

    pub(crate) fn bind_supervisor_owner(
        &self,
        attempt_id: &str,
        expected_row_version: u64,
        owner: &AttemptSupervisorOwner,
        observed_at_ms: u64,
    ) -> RuntimeResult<AttemptRecord> {
        validate_attempt_supervisor_owner(owner)?;
        let owner_json = serde_json::to_string(owner).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("cannot serialize Attempt Supervisor Owner: {error}"),
                Some("attemptSupervisorOwner"),
                false,
            )
        })?;
        let owner_digest = sha256_bytes(owner_json.as_bytes());
        let start_evidence_digest = owner.start_evidence_digest();
        let mut connection = self.open_connection()?;
        let transaction = immediate(&mut connection, "supervisor-owner bind transaction")?;
        let attempt = load_attempt(&transaction, attempt_id)?;
        let existing: Option<(String, String)> = transaction
            .query_row(
                "SELECT owner_json,owner_digest FROM attempt_supervisor_owners WHERE attempt_id=?1",
                [attempt_id],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .optional()
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot inspect existing Attempt Supervisor Owner")
            })?;
        let bound_state = if attempt.state == AttemptState::Stopping {
            AttemptState::Stopping
        } else {
            AttemptState::Running
        };
        if let Some((existing_json, existing_digest)) = existing {
            if sha256_bytes(existing_json.as_bytes()) != existing_digest {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "stored Attempt Supervisor Owner digest does not match side truth",
                    Some("attemptSupervisorOwner"),
                    false,
                ));
            }
            if existing_digest == owner_digest
                && matches!(
                    attempt.state,
                    AttemptState::Running | AttemptState::Stopping
                )
                && attempt.runner_start_digest.as_deref() == Some(start_evidence_digest)
            {
                return Ok(attempt);
            }
            return Err(state_conflict(
                "Attempt is already bound to a different Supervisor Owner",
            ));
        }
        if !matches!(
            attempt.state,
            AttemptState::Starting | AttemptState::Recovering | AttemptState::Stopping
        ) || attempt.row_version != expected_row_version
        {
            return Err(state_conflict(
                "Attempt is not bindable to this Supervisor Owner",
            ));
        }
        transaction
            .execute(
                "INSERT INTO attempt_supervisor_owners(attempt_id,owner_json,owner_digest) VALUES(?1,?2,?3)",
                params![attempt_id, owner_json, owner_digest],
            )
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot persist Attempt Supervisor Owner")
            })?;
        let changed = transaction
            .execute(
                "UPDATE attempts SET state=CASE WHEN state='stopping' THEN 'stopping' ELSE 'running' END,runner_start_digest=?1,started_at_ms=COALESCE(started_at_ms,?2),row_version=row_version+1 WHERE attempt_id=?3 AND row_version=?4 AND state IN ('starting','recovering','stopping')",
                params![
                    start_evidence_digest,
                    observed_at_ms,
                    attempt_id,
                    expected_row_version,
                ],
            )
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot bind Attempt Supervisor Owner")
            })?;
        if changed != 1 {
            return Err(state_conflict(
                "Attempt changed while binding Supervisor Owner",
            ));
        }
        append_event(
            &transaction,
            &attempt.job_id,
            Some(attempt_id),
            "RUNNER_BOUND",
            "SYSTEM_OBSERVED",
            Some(attempt.state),
            Some(bound_state),
            "SUPERVISOR_OWNER_MATCHED",
            serde_json::json!({
                "ownerContract": owner.contract_name(),
                "ownerDigest": owner_digest,
            }),
            observed_at_ms,
        )?;
        transaction.commit().map_err(|error| {
            RuntimeError::from_sql(error, "cannot commit Attempt Supervisor Owner")
        })?;
        load_attempt(&connection, attempt_id)
    }

    pub(super) fn request_deadline_termination(
        &self,
        attempt_id: &str,
        observed_at_ms: u64,
    ) -> RuntimeResult<AttemptRecord> {
        let mut connection = self.open_connection()?;
        let transaction = immediate(&mut connection, "deadline-intent transaction")?;
        let attempt = load_attempt(&transaction, attempt_id)?;
        let job = load_job(&transaction, &attempt.job_id)?;
        if attempt.state.is_terminal()
            || attempt.termination_intent == AttemptTerminationIntent::DeadlineExceeded
            || attempt.termination_intent == AttemptTerminationIntent::StopRequested
            || job.desired_state == JobDesiredState::Cancelled
        {
            transaction.commit().map_err(|error| {
                RuntimeError::from_sql(error, "cannot close deadline-intent replay")
            })?;
            return load_attempt(&connection, attempt_id);
        }
        if job.resolution.is_some() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                "unresolved Attempt belongs to a resolved Job",
                Some("attemptId"),
                false,
            ));
        }
        if !matches!(
            attempt.state,
            AttemptState::Starting
                | AttemptState::Running
                | AttemptState::Recovering
                | AttemptState::Stopping
        ) {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AttemptStateConflict,
                "deadline termination requires a dispatched nonterminal Attempt",
                Some("attemptId"),
                false,
            ));
        }
        let changed = transaction
            .execute(
                "UPDATE attempts SET state='stopping',termination_intent='deadline_exceeded',row_version=row_version+1 WHERE attempt_id=?1 AND row_version=?2 AND state IN ('starting','running','recovering','stopping') AND termination_intent='natural'",
                params![attempt_id, attempt.row_version],
            )
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot persist Attempt deadline intent")
            })?;
        if changed != 1 {
            return Err(state_conflict(
                "Attempt changed while committing outer deadline intent",
            ));
        }
        append_event(
            &transaction,
            &attempt.job_id,
            Some(attempt_id),
            "DEADLINE_EXCEEDED",
            "SYSTEM_DERIVED",
            Some(attempt.state),
            Some(AttemptState::Stopping),
            "OUTER_DEADLINE_INTENT_COMMITTED",
            serde_json::json!({}),
            observed_at_ms,
        )?;
        transaction.commit().map_err(|error| {
            RuntimeError::from_sql(error, "cannot commit Attempt deadline intent")
        })?;
        load_attempt(&connection, attempt_id)
    }

    pub(super) fn request_cancel(
        &self,
        job_id: &str,
        observed_at_ms: u64,
    ) -> RuntimeResult<JobProjection> {
        let mut connection = self.open_connection()?;
        let transaction = immediate(&mut connection, "cancel-intent transaction")?;
        let job = load_job(&transaction, job_id)?;
        if job.resolution.is_some() {
            if job.resolution == Some(JobResolution::Orphaned) {
                let attempt_id: String = transaction
                    .query_row(
                        "SELECT attempt_id FROM attempts WHERE job_id=?1 ORDER BY attempt_number DESC LIMIT 1",
                        [job_id],
                        |row| row.get(0),
                    )
                    .optional()
                    .map_err(|error| RuntimeError::from_sql(error, "cannot load orphaned Job Attempt"))?
                    .ok_or_else(|| {
                        RuntimeError::new(
                            RuntimeErrorCode::RegistryCorrupt,
                            "orphaned Job has no Attempt",
                            Some("jobId"),
                            false,
                        )
                    })?;
                let attempt = load_attempt(&transaction, &attempt_id)?;
                let reservation = load_reservation(&transaction, &attempt_id)?;
                if attempt.state != AttemptState::Orphaned
                    || reservation.state != ReservationState::HeldOrphaned
                {
                    return Err(RuntimeError::new(
                        RuntimeErrorCode::ReconciliationRequired,
                        "orphaned Job is not backed by a held orphaned Attempt",
                        Some("jobId"),
                        false,
                    ));
                }
                let intent_changed = job.desired_state != JobDesiredState::Cancelled
                    || attempt.termination_intent != AttemptTerminationIntent::StopRequested;
                transaction
                    .execute(
                        "UPDATE jobs SET desired_state='cancelled',row_version=row_version+1 WHERE job_id=?1 AND resolution='orphaned' AND desired_state!='cancelled'",
                        [job_id],
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot persist orphan cancel intent"))?;
                transaction
                    .execute(
                        "UPDATE attempts SET termination_intent='stop_requested',row_version=row_version+1 WHERE attempt_id=?1 AND state='orphaned' AND termination_intent!='stop_requested'",
                        [&attempt_id],
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot persist orphan stop intent"))?;
                if intent_changed {
                    append_event(
                        &transaction,
                        job_id,
                        Some(&attempt_id),
                        "STOP_REQUESTED",
                        "SYSTEM_DERIVED",
                        Some(AttemptState::Orphaned),
                        Some(AttemptState::Orphaned),
                        "ORPHAN_CANCEL_INTENT_COMMITTED",
                        serde_json::json!({}),
                        observed_at_ms,
                    )?;
                }
                #[cfg(test)]
                let commit_result = commit_with_test_fault(transaction, TestCommitPoint::Cancel);
                #[cfg(not(test))]
                let commit_result = transaction.commit();
                if let Err(error) = commit_result {
                    return self.reconcile_cancel_commit_failure(
                        &connection,
                        job_id,
                        error,
                        "cannot commit orphan cancel intent",
                    );
                }
                return Ok(load_job_snapshot(&connection, job_id)?.projection);
            }
            transaction.commit().map_err(|error| {
                RuntimeError::from_sql(error, "cannot close terminal cancel replay")
            })?;
            return Ok(load_job_snapshot(&connection, job_id)?.projection);
        }
        let attempt_id = job.current_attempt_id.clone().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "unresolved Job has no current Attempt",
                Some("currentAttemptId"),
                false,
            )
        })?;
        let attempt = load_attempt(&transaction, &attempt_id)?;
        if attempt.state.is_terminal() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                "Attempt is terminal but Job is unresolved",
                Some("jobId"),
                false,
            ));
        }
        transaction
            .execute(
                "UPDATE jobs SET desired_state='cancelled',row_version=row_version+1 WHERE job_id=?1 AND resolution IS NULL",
                [job_id],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot persist cancel intent"))?;
        if attempt.state == AttemptState::Accepted {
            let result_digest = sha256_bytes(
                format!("runtime-cancel-before-dispatch\0{job_id}\0{attempt_id}").as_bytes(),
            );
            transaction
                .execute(
                    "UPDATE attempts SET state='cancelled',termination_intent='stop_requested',result_digest=?1,finished_at_ms=?2,row_version=row_version+1 WHERE attempt_id=?3 AND state='accepted'",
                    params![result_digest, observed_at_ms, attempt_id],
                )
                .map_err(|error| RuntimeError::from_sql(error, "cannot cancel accepted Attempt"))?;
            release_reservation(
                &transaction,
                &attempt_id,
                observed_at_ms,
                "CANCELLED_BEFORE_DISPATCH",
            )?;
            transaction
                .execute(
                    "UPDATE jobs SET resolution='cancelled',current_attempt_id=NULL,row_version=row_version+1 WHERE job_id=?1 AND resolution IS NULL",
                    [job_id],
                )
                .map_err(|error| RuntimeError::from_sql(error, "cannot resolve cancelled Job"))?;
            append_event(
                &transaction,
                job_id,
                Some(&attempt_id),
                "STOP_REQUESTED",
                "SYSTEM_DERIVED",
                Some(AttemptState::Accepted),
                Some(AttemptState::Cancelled),
                "CANCELLED_BEFORE_DISPATCH",
                serde_json::json!({}),
                observed_at_ms,
            )?;
        } else if attempt.state != AttemptState::Stopping {
            transaction
                .execute(
                    "UPDATE attempts SET state='stopping',termination_intent='stop_requested',row_version=row_version+1 WHERE attempt_id=?1 AND state IN ('starting','running','recovering')",
                    [&attempt_id],
                )
                .map_err(|error| RuntimeError::from_sql(error, "cannot move Attempt to stopping"))?;
            append_event(
                &transaction,
                job_id,
                Some(&attempt_id),
                "STOP_REQUESTED",
                "SYSTEM_DERIVED",
                Some(attempt.state),
                Some(AttemptState::Stopping),
                "CANCEL_INTENT_COMMITTED",
                serde_json::json!({}),
                observed_at_ms,
            )?;
        }
        #[cfg(test)]
        let commit_result = commit_with_test_fault(transaction, TestCommitPoint::Cancel);
        #[cfg(not(test))]
        let commit_result = transaction.commit();
        if let Err(error) = commit_result {
            return self.reconcile_cancel_commit_failure(
                &connection,
                job_id,
                error,
                "cannot commit cancel intent",
            );
        }
        Ok(load_job_snapshot(&connection, job_id)?.projection)
    }

    fn reconcile_cancel_commit_failure(
        &self,
        connection: &Connection,
        job_id: &str,
        error: rusqlite::Error,
        context: &str,
    ) -> RuntimeResult<JobProjection> {
        let mut commit_error = RuntimeError::from_sql(error, context);
        if !connection.is_autocommit() {
            return Err(unknown_commit_outcome(
                "cancel-intent commit outcome remains inside an open SQLite transaction",
                &commit_error,
                None,
            ));
        }
        match load_job_snapshot(connection, job_id) {
            Ok(snapshot) if snapshot.job.resolution.is_some() => Ok(snapshot.projection),
            Ok(snapshot)
                if snapshot.job.desired_state == JobDesiredState::Cancelled
                    && snapshot.attempt.as_ref().is_some_and(|attempt| {
                        attempt.termination_intent == AttemptTerminationIntent::StopRequested
                    }) =>
            {
                Ok(snapshot.projection)
            }
            Ok(snapshot)
                if snapshot.job.desired_state == JobDesiredState::Run
                    && snapshot.attempt.as_ref().is_some_and(|attempt| {
                        attempt.termination_intent == AttemptTerminationIntent::Natural
                    }) =>
            {
                commit_error.retryable = true;
                Err(commit_error)
            }
            Ok(snapshot) => Err(committed_reconciliation(
                &snapshot.job.job_id,
                "cancel-intent commit raced with another durable Job/Attempt transition",
            )),
            Err(reconcile_error) => Err(unknown_commit_outcome(
                "cancel-intent commit outcome cannot be proven",
                &commit_error,
                Some(&reconcile_error),
            )),
        }
    }

    pub(super) fn commit_terminal(&self, request: &TerminalCommit) -> RuntimeResult<JobProjection> {
        if !request.state.is_terminal() {
            return Err(RuntimeError::invalid(
                "terminal commit requires a terminal Attempt state",
                "state",
            ));
        }
        validate_digest(&request.result_digest, "resultDigest")?;
        for artifact in &request.artifacts {
            validate_artifact_registration(artifact)?;
        }
        let mut connection = self.open_connection()?;
        let transaction = immediate(&mut connection, "terminal transaction")?;
        let attempt = load_attempt(&transaction, &request.attempt_id)?;
        let job = load_job(&transaction, &attempt.job_id)?;
        if attempt.state.is_terminal() {
            if attempt.result_digest.as_deref() == Some(request.result_digest.as_str())
                && attempt.state == request.state
            {
                transaction.commit().map_err(|error| {
                    RuntimeError::from_sql(error, "cannot close terminal replay")
                })?;
                return Ok(load_job_snapshot(&connection, &job.job_id)?.projection);
            }
            return Err(RuntimeError::new(
                RuntimeErrorCode::ResultIdentityConflict,
                "Attempt already has a different terminal result",
                Some("resultDigest"),
                false,
            ));
        }
        if attempt.row_version != request.expected_row_version {
            return Err(state_conflict(
                "Attempt row version changed before terminal commit",
            ));
        }
        if !attempt.state.can_transition_to(request.state) {
            return Err(state_conflict(format!(
                "invalid Attempt transition {:?} -> {:?}",
                attempt.state, request.state
            )));
        }
        if job.resolution.is_some() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::JobAlreadyResolved,
                "Job is already resolved",
                Some("jobId"),
                false,
            ));
        }

        let changed = transaction
            .execute(
                "UPDATE attempts SET state=?1,result_digest=?2,exit_code=?3,infrastructure_error_digest=?4,finished_at_ms=?5,row_version=row_version+1 WHERE attempt_id=?6 AND row_version=?7 AND state NOT IN ('succeeded','failed','timed_out','cancelled','lost','orphaned')",
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
            .map_err(|error| RuntimeError::from_sql(error, "cannot commit terminal Attempt"))?;
        if changed != 1 {
            return Err(state_conflict("Attempt changed during terminal commit"));
        }
        for artifact in &request.artifacts {
            let inserted = transaction.execute(
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
            );
            if let Err(error) = inserted {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    format!("cannot register Artifact {}: {error}", artifact.artifact_id),
                    Some("artifacts"),
                    false,
                ));
            }
        }
        if request.state == AttemptState::Orphaned {
            hold_orphaned_reservation(
                &transaction,
                &attempt.attempt_id,
                request.finished_at_ms,
                &request.reason_code,
            )?;
        } else {
            release_reservation(
                &transaction,
                &attempt.attempt_id,
                request.finished_at_ms,
                &request.reason_code,
            )?;
        }

        let resolution = resolution_for_state(request.state)?;
        transaction
            .execute(
                "UPDATE jobs SET resolution=?1,current_attempt_id=NULL,row_version=row_version+1 WHERE job_id=?2 AND resolution IS NULL",
                params![resolution.as_db(), attempt.job_id],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot resolve Job"))?;
        append_event(
            &transaction,
            &attempt.job_id,
            Some(&attempt.attempt_id),
            "PROCESS_EXITED",
            "SYSTEM_OBSERVED",
            Some(attempt.state),
            Some(request.state),
            &request.reason_code,
            serde_json::json!({
                "resultDigest": request.result_digest,
                "exitCode": request.exit_code,
            }),
            request.finished_at_ms,
        )?;
        append_event(
            &transaction,
            &attempt.job_id,
            Some(&attempt.attempt_id),
            "JOB_TERMINAL",
            "SYSTEM_DERIVED",
            Some(attempt.state),
            Some(request.state),
            &request.reason_code,
            serde_json::json!({"resolution": resolution.as_db()}),
            request.finished_at_ms,
        )?;
        #[cfg(test)]
        let commit_result = commit_with_test_fault(transaction, TestCommitPoint::Terminal);
        #[cfg(not(test))]
        let commit_result = transaction.commit();
        if let Err(error) = commit_result {
            let mut commit_error =
                RuntimeError::from_sql(error, "cannot commit terminal transaction");
            if !connection.is_autocommit() {
                return Err(unknown_commit_outcome(
                    "terminal commit outcome remains inside an open SQLite transaction",
                    &commit_error,
                    None,
                ));
            }
            return match load_attempt(&connection, &request.attempt_id) {
                Ok(current)
                    if current.state == request.state
                        && current.result_digest.as_deref()
                            == Some(request.result_digest.as_str()) =>
                {
                    match load_job_snapshot(&connection, &current.job_id) {
                        Ok(snapshot) => Ok(snapshot.projection),
                        Err(reconcile_error) => Err(committed_reconciliation(
                            &current.job_id,
                            &format!(
                                "terminal result committed but Job projection requires reconciliation: {}",
                                reconcile_error.message
                            ),
                        )),
                    }
                }
                Ok(current)
                    if !current.state.is_terminal()
                        && current.row_version == request.expected_row_version =>
                {
                    commit_error.retryable = true;
                    Err(commit_error)
                }
                Ok(current) => Err(committed_reconciliation(
                    &current.job_id,
                    "terminal commit raced with another durable Attempt transition",
                )),
                Err(reconcile_error) => Err(unknown_commit_outcome(
                    "terminal commit outcome cannot be proven",
                    &commit_error,
                    Some(&reconcile_error),
                )),
            };
        }
        Ok(load_job_snapshot(&connection, &attempt.job_id)?.projection)
    }

}
