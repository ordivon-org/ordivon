impl Registry {
    pub(super) fn find_idempotent_job(
        &self,
        principal: &str,
        client_request_id: &str,
        request_identity_digest: &str,
        compatible_request_identity_digest: Option<&str>,
    ) -> RuntimeResult<Option<RuntimeJobRecord>> {
        validate_identifier(principal, "principal")?;
        validate_client_request_id(client_request_id, "clientRequestId")?;
        JobIdentityContract::validate_request_identity_digest(request_identity_digest)?;
        if let Some(digest) = compatible_request_identity_digest {
            JobIdentityContract::validate_request_identity_digest(digest)?;
        }
        let connection = self.open_connection()?;
        let job_id: Option<String> = connection
            .query_row(
                "SELECT job_id FROM idempotency_keys WHERE principal=?1 AND client_request_id=?2",
                params![principal, client_request_id],
                |row| row.get(0),
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot find idempotent Job"))?;
        let Some(job_id) = job_id else {
            return Ok(None);
        };
        let job = load_job(&connection, &job_id)?;
        let stored_identity = JobIdentityContract::stored_request_identity_digest(&job)?;
        if !JobIdentityContract::compatible_request_identity_matches(
            &stored_identity,
            request_identity_digest,
            compatible_request_identity_digest,
        ) {
            return Err(JobIdentityContract::idempotency_conflict());
        }
        Ok(Some(job))
    }

    pub(super) fn submit(&self, request: &SubmitRequest) -> RuntimeResult<AdmissionOutcome> {
        let ids = self.preallocate_admission_ids();
        self.submit_preallocated(request, &ids)
    }

    pub(super) fn preallocate_admission_ids(&self) -> PreallocatedAdmissionIds {
        PreallocatedAdmissionIds {
            job_id: format!("job-{}", Uuid::now_v7()),
            attempt_id: format!("attempt-{}", Uuid::now_v7()),
            reservation_id: format!("reservation-{}", Uuid::now_v7()),
        }
    }

    pub(super) fn submit_preallocated(
        &self,
        request: &SubmitRequest,
        ids: &PreallocatedAdmissionIds,
    ) -> RuntimeResult<AdmissionOutcome> {
        validate_submit(request)?;
        let created_at_ms = now_ms()?;
        let plan_json = serde_json::to_string(&request.plan).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::InvalidRequest,
                format!("cannot serialize execution plan: {error}"),
                Some("plan"),
                false,
            )
        })?;
        let execution_provider_json = request
            .execution_provider
            .as_ref()
            .map(serde_json::to_string)
            .transpose()
            .map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::InvalidRequest,
                    format!("cannot serialize execution provider snapshot: {error}"),
                    Some("executionProvider"),
                    false,
                )
            })?;
        let execution_provider_digest = execution_provider_json
            .as_deref()
            .map(|json| sha256_bytes(json.as_bytes()));
        let host_dependencies_json = if request.host_dependencies.is_empty() {
            None
        } else {
            Some(
                serde_json::to_string(&request.host_dependencies).map_err(|error| {
                    RuntimeError::new(
                        RuntimeErrorCode::InvalidRequest,
                        format!("cannot serialize Host Dependency bindings: {error}"),
                        Some("hostDependencies"),
                        false,
                    )
                })?,
            )
        };
        let host_dependencies_digest = host_dependencies_json
            .as_deref()
            .map(|json| sha256_bytes(json.as_bytes()));
        let runtime_release_json = request
            .runtime_release_effect
            .as_ref()
            .map(serde_json::to_string)
            .transpose()
            .map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::InvalidRequest,
                    format!("cannot serialize Runtime Release binding: {error}"),
                    Some("runtimeReleaseEffect"),
                    false,
                )
            })?;
        let runtime_release_digest = runtime_release_json
            .as_deref()
            .map(|json| sha256_bytes(json.as_bytes()));
        let plan_digest = sha256_bytes(plan_json.as_bytes());
        let identity = JobIdentityContract::from_submit(
            request,
            &plan_digest,
            execution_provider_digest.as_deref(),
            host_dependencies_digest.as_deref(),
            runtime_release_digest.as_deref(),
        )?;
        let request_digest = identity.request_digest;
        let operation_digest = identity.operation_digest;
        let mut workspace_snapshot = serde_json::json!({
            "workspaceId": request.plan.workspace_id,
            "workspacePath": request.plan.workspace_path,
            "sourceRevision": request.plan.source_revision,
            "workspaceSourceDigest": request.plan.workspace_source_digest,
        });
        if let Some(provider_digest) = execution_provider_digest.as_deref() {
            workspace_snapshot["executionProviderDigest"] =
                serde_json::Value::String(provider_digest.to_string());
        }
        if let Some(host_digest) = host_dependencies_digest.as_deref() {
            workspace_snapshot["hostDependenciesDigest"] =
                serde_json::Value::String(host_digest.to_string());
        }
        if let Some(release_digest) = runtime_release_digest.as_deref() {
            workspace_snapshot["runtimeReleaseEffectDigest"] =
                serde_json::Value::String(release_digest.to_string());
        }
        let workspace_snapshot_json = workspace_snapshot.to_string();
        let job_id = ids.job_id.clone();
        let attempt_id = ids.attempt_id.clone();
        let reservation_id = ids.reservation_id.clone();
        let launch_token =
            sha256_bytes(format!("runtime-launch-v1\0{attempt_id}\0{operation_digest}").as_bytes());
        let launch_token_digest = sha256_bytes(launch_token.as_bytes());
        let unit_name = format!("ordivon-{attempt_id}.service");
        let bundle_path = self
            .config
            .attempt_path(&attempt_id)
            .to_string_lossy()
            .into_owned();

        let job = RuntimeJobRecord {
            job_id: job_id.clone(),
            principal: request.plan.principal.clone(),
            client_request_id: request.client_request_id.clone(),
            request_digest: request_digest.clone(),
            operation_digest: operation_digest.clone(),
            workspace_id: request.plan.workspace_id.clone(),
            workspace_snapshot_json: workspace_snapshot_json.clone(),
            execution_plan_json: plan_json.clone(),
            execution_plan_digest: plan_digest.clone(),
            created_at_ms,
            desired_state: JobDesiredState::Run,
            resolution: None,
            current_attempt_id: Some(attempt_id.clone()),
            row_version: 0,
        };
        let attempt = AttemptRecord {
            attempt_id: attempt_id.clone(),
            job_id: job_id.clone(),
            attempt_number: AttemptLifecycleContract::INITIAL_ATTEMPT_NUMBER,
            state: AttemptLifecycleContract::initial_state(),
            termination_intent: AttemptLifecycleContract::initial_termination_intent(),
            launch_token_digest: launch_token_digest.clone(),
            bundle_path: bundle_path.clone(),
            bundle_digest: None,
            boot_id: None,
            unit_name: unit_name.clone(),
            invocation_id: None,
            control_group: None,
            main_pid: None,
            process_start_identity: None,
            runner_start_digest: None,
            result_digest: None,
            exit_code: None,
            infrastructure_error_digest: None,
            created_at_ms,
            started_at_ms: None,
            finished_at_ms: None,
            row_version: 0,
        };
        let reservation = ReservationRecord {
            reservation_id: reservation_id.clone(),
            attempt_id: attempt_id.clone(),
            global_limit: request.global_limit,
            state: ReservationContract::initial_state(),
            acquired_at_ms: created_at_ms,
            released_at_ms: None,
            release_reason: None,
        };

        let mut connection = self.open_connection()?;
        let transaction = connection
            .transaction_with_behavior(TransactionBehavior::Immediate)
            .map_err(|error| RuntimeError::from_sql(error, "cannot begin admission transaction"))?;

        if let Some(existing_job_id) = transaction
            .query_row(
                "SELECT job_id FROM idempotency_keys WHERE principal=?1 AND client_request_id=?2",
                params![request.plan.principal, request.client_request_id],
                |row| row.get::<_, String>(0),
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot check idempotency key"))?
        {
            let existing = load_job(&transaction, &existing_job_id)?;
            let matches = JobIdentityContract::exact_replay_matches(
                &existing,
                request.request_identity_digest.as_deref(),
                &operation_digest,
            )?;
            if !matches {
                return Err(JobIdentityContract::idempotency_conflict());
            }
            transaction
                .commit()
                .map_err(|error| RuntimeError::from_sql(error, "cannot close replay transaction"))?;
            return Ok(AdmissionOutcome::Existing {
                job: Box::new(existing),
            });
        }

        // New admission shares the deployment fence until its Registry transaction commits.
        // Exact replay deliberately returns above this boundary, so deployment cannot make a
        // previously committed request unreplayable.
        let _admission_fence = self.acquire_admission_fence()?;

        let workspace_active: u32 = transaction
            .query_row(
                "SELECT COUNT(*) FROM concurrency_reservations r JOIN attempts a ON a.attempt_id=r.attempt_id JOIN jobs j ON j.job_id=a.job_id WHERE r.state IN ('active','held_orphaned') AND j.workspace_id=?1",
                [&request.plan.workspace_id],
                |row| row.get(0),
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot count workspace reservations"))?;
        if ReservationContract::capacity_exhausted(workspace_active, WORKSPACE_EXECUTION_LIMIT) {
            let (holder_job_ids, holder_workspace_ids) = capacity_holders(
                &transaction,
                Some(&request.plan.workspace_id),
                WORKSPACE_EXECUTION_LIMIT,
            )?;
            return Err(RuntimeError::concurrency(
                format!(
                    "workspace execution concurrency limit reached (active={workspace_active}, limit={WORKSPACE_EXECUTION_LIMIT})"
                ),
                "workspaceId",
                super::RuntimeCapacity {
                    scope: "workspace".to_string(),
                    active: workspace_active,
                    limit: WORKSPACE_EXECUTION_LIMIT,
                    workspace_id: Some(request.plan.workspace_id.clone()),
                    holder_job_ids,
                    holder_workspace_ids,
                    holders_truncated: workspace_active > WORKSPACE_EXECUTION_LIMIT,
                },
            ));
        }

        let global_active: u32 = transaction
            .query_row(
                "SELECT COUNT(*) FROM concurrency_reservations WHERE state IN ('active','held_orphaned')",
                [],
                |row| row.get(0),
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot count global reservations"))?;
        if ReservationContract::capacity_exhausted(global_active, request.global_limit) {
            let holder_limit = request.global_limit.min(16);
            let (holder_job_ids, holder_workspace_ids) =
                capacity_holders(&transaction, None, holder_limit)?;
            return Err(RuntimeError::concurrency(
                format!(
                    "global execution concurrency limit reached (active={global_active}, limit={})",
                    request.global_limit
                ),
                "globalLimit",
                super::RuntimeCapacity {
                    scope: "global".to_string(),
                    active: global_active,
                    limit: request.global_limit,
                    workspace_id: None,
                    holder_job_ids,
                    holder_workspace_ids,
                    holders_truncated: global_active > holder_limit,
                },
            ));
        }
        transaction
            .execute(
                "INSERT INTO jobs(job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,NULL,?12,0)",
                params![
                    job.job_id,
                    job.principal,
                    job.client_request_id,
                    job.request_digest,
                    job.operation_digest,
                    job.workspace_id,
                    job.workspace_snapshot_json,
                    job.execution_plan_json,
                    job.execution_plan_digest,
                    created_at_ms,
                    job.desired_state.as_db(),
                    attempt.attempt_id,
                ],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot insert Job"))?;
        if let (Some(snapshot_json), Some(snapshot_digest)) = (
            execution_provider_json.as_deref(),
            execution_provider_digest.as_deref(),
        ) {
            transaction
                .execute(
                    "INSERT INTO job_execution_providers(job_id,snapshot_json,snapshot_digest) VALUES(?1,?2,?3)",
                    params![job_id, snapshot_json, snapshot_digest],
                )
                .map_err(|error| {
                    RuntimeError::from_sql(error, "cannot bind Job execution provider")
                })?;
        }
        if let (Some(bindings_json), Some(bindings_digest)) = (
            host_dependencies_json.as_deref(),
            host_dependencies_digest.as_deref(),
        ) {
            transaction
                .execute(
                    "INSERT INTO job_host_dependencies(job_id,bindings_json,bindings_digest) VALUES(?1,?2,?3)",
                    params![job_id, bindings_json, bindings_digest],
                )
                .map_err(|error| RuntimeError::from_sql(error, "cannot bind Job Host Dependencies"))?;
        }
        if let (Some(release), Some(binding_digest)) = (
            request.runtime_release_effect.as_ref(),
            runtime_release_digest.as_deref(),
        ) {
            transaction
                .execute(
                    "INSERT INTO job_runtime_release_effects(job_id,effect_id,contract,request_digest,workspace_id,commit_revision,candidate_manifest_digest,expected_tool_count,receipt_path,binding_digest) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10)",
                    params![
                        job_id,
                        release.effect_id,
                        "runtime_release_v1",
                        release.request_digest,
                        release.workspace_id,
                        release.commit,
                        release.candidate_manifest_digest,
                        release.expected_tool_count,
                        release.receipt_path,
                        binding_digest,
                    ],
                )
                .map_err(|error| RuntimeError::from_sql(error, "cannot bind Job Runtime Release effect"))?;
        }
        transaction
            .execute(
                "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,bundle_digest,boot_id,unit_name,invocation_id,control_group,main_pid,process_start_identity,runner_start_digest,result_digest,exit_code,infrastructure_error_digest,created_at_ms,started_at_ms,finished_at_ms,row_version) VALUES(?1,?2,?3,?4,?5,?6,?7,NULL,NULL,?8,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,?9,NULL,NULL,0)",
                params![
                    attempt.attempt_id,
                    attempt.job_id,
                    attempt.attempt_number,
                    attempt.state.as_db(),
                    attempt.termination_intent.as_db(),
                    attempt.launch_token_digest,
                    attempt.bundle_path,
                    attempt.unit_name,
                    created_at_ms,
                ],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot insert Attempt"))?;
        transaction
            .execute(
                "INSERT INTO idempotency_keys(principal,client_request_id,operation_digest,job_id,created_at_ms) VALUES(?1,?2,?3,?4,?5)",
                params![
                    request.plan.principal,
                    request.client_request_id,
                    operation_digest,
                    job_id,
                    created_at_ms,
                ],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot insert idempotency key"))?;

        transaction
            .execute(
                "INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,released_at_ms,release_reason,state_observed_at_ms) VALUES(?1,?2,?3,?4,?5,NULL,NULL,?5)",
                params![
                    reservation.reservation_id,
                    reservation.attempt_id,
                    reservation.global_limit,
                    reservation.state.as_db(),
                    reservation.acquired_at_ms,
                ],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot reserve execution capacity"))?;

        append_event(
            &transaction,
            &job_id,
            Some(&attempt_id),
            "REQUEST_RECEIVED",
            "SYSTEM_DERIVED",
            None,
            None,
            "REQUEST_ACCEPTED",
            serde_json::json!({"requestDigest": request_digest}),
            created_at_ms,
        )?;
        append_event(
            &transaction,
            &job_id,
            Some(&attempt_id),
            "JOB_RECORD_CREATED",
            "SYSTEM_DERIVED",
            None,
            None,
            "JOB_CREATED",
            serde_json::json!({"operationDigest": operation_digest}),
            created_at_ms,
        )?;
        append_event(
            &transaction,
            &job_id,
            Some(&attempt_id),
            "ATTEMPT_CREATED",
            "SYSTEM_DERIVED",
            None,
            Some(AttemptState::Accepted),
            "ATTEMPT_ACCEPTED",
            serde_json::json!({"attemptNumber": attempt.attempt_number}),
            created_at_ms,
        )?;

        #[cfg(test)]
        let commit_result = commit_with_test_fault(transaction, TestCommitPoint::Admission);
        #[cfg(not(test))]
        let commit_result = transaction.commit();
        if let Err(error) = commit_result {
            let mut commit_error = RuntimeError::from_sql(error, "cannot commit admission");
            if !connection.is_autocommit() {
                return Err(unknown_commit_outcome(
                    "admission commit outcome remains inside an open SQLite transaction",
                    &commit_error,
                    None,
                ));
            }
            let durable = connection
                .query_row(
                    "SELECT operation_digest,job_id FROM idempotency_keys WHERE principal=?1 AND client_request_id=?2",
                    params![request.plan.principal, request.client_request_id],
                    |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)),
                )
                .optional();
            match durable {
                Ok(Some((existing_operation_digest, existing_job_id))) => {
                    if existing_operation_digest != operation_digest {
                        return Err(JobIdentityContract::idempotency_conflict());
                    }
                    return match load_job(&connection, &existing_job_id) {
                        Ok(existing) => Ok(AdmissionOutcome::Existing {
                            job: Box::new(existing),
                        }),
                        Err(reconcile_error) => Err(committed_reconciliation(
                            &existing_job_id,
                            &format!(
                                "admission committed but Job projection requires reconciliation: {}",
                                reconcile_error.message
                            ),
                        )),
                    };
                }
                Ok(None) => {
                    commit_error.retryable = true;
                    return Err(commit_error);
                }
                Err(error) => {
                    let reconcile_error = RuntimeError::from_sql(
                        error,
                        "cannot reconcile admission after commit failure",
                    );
                    return Err(unknown_commit_outcome(
                        "admission commit outcome cannot be proven",
                        &commit_error,
                        Some(&reconcile_error),
                    ));
                }
            }
        }
        Ok(AdmissionOutcome::Created(Box::new(CreatedAdmission {
            job,
            attempt,
            reservation,
            launch_token,
        })))
    }

    fn acquire_admission_fence(&self) -> RuntimeResult<File> {
        let path = self.config.admission_fence_path();
        let mut options = OpenOptions::new();
        options.read(true).write(true).create(true).truncate(false);
        #[cfg(unix)]
        options.mode(0o600);
        let file = options
            .open(&path)
            .map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryUnavailable,
                    format!("cannot open admission fence {}: {error}", path.display()),
                    None,
                    true,
                )
            })?;
        match file.try_lock_shared() {
            Ok(()) => Ok(file),
            Err(std::fs::TryLockError::WouldBlock) => {
                Err(RuntimeError::deployment_in_progress())
            }
            Err(std::fs::TryLockError::Error(error)) => Err(RuntimeError::new(
                RuntimeErrorCode::RegistryUnavailable,
                format!("cannot acquire admission fence {}: {error}", path.display()),
                None,
                true,
            )),
        }
    }

}
