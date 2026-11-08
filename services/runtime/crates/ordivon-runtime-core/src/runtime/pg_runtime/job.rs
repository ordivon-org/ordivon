//! PostgreSQL Runtime Job admission, observation, cancellation, and projection.
use super::*;

impl PgRuntime {
    pub fn run(&self, proposal: &JobRunProposal) -> RuntimeResult<JobObservation> {
        super::engine::validate_resource_run_proposal_structure(proposal)?;
        proposal
            .execution
            .budget
            .scheduling
            .clone()
            .unwrap_or_default()
            .validate()
            .map_err(|e| RuntimeError::invalid(e, "execution.budget.scheduling"))?;
        let identity = super::types::proposal_request_identity_digest(proposal)?;
        let mut db = self.store()?;
        // Replay before consulting mutable Workspace/executable state or policy.
        if let Some(row) = db.client.query_opt("SELECT job_id,request_digest FROM jobs WHERE principal=$1 AND client_request_id=$2", &[&proposal.principal,&proposal.client_request_id]).map_err(io)? {
            if row.get::<_,String>(1)!=identity { return Err(pg(PgAdmissionError::IdempotencyConflict)); }
            return self.observe(&proposal.principal, &JobObserveRequest { schema_version:1,job_id:row.get(0),wait_ms:proposal.wait_ms,wait_until:JobObserveWaitUntil::Terminal,stdout_tail_bytes:proposal.stdout_tail_bytes,stderr_tail_bytes:proposal.stderr_tail_bytes,stdout_offset:None,stderr_offset:None });
        }
        let e = &proposal.execution;
        if e.execution_target != ExecutionTarget::LocalLinux
            || e.execution_profile != ExecutionProfile::TrustedLocal
            || e.windows_context.is_some()
            || e.windows_authority != WindowsAuthority::Limited
            || !e.foreign_references.is_empty()
        {
            return Err(RuntimeError::invalid(
                "PG vertical supports a trusted_local local_linux execution (only Host Dependency bindings supported)",
                "execution",
            ));
        }
        // Reuse the installed Runtime validator. The committed PG plan
        // freezes the exact file set before native dispatch.
        let host_dependencies = super::host_dependency::validate_bindings(
            &e.host_dependencies,
            e.execution_target,
            e.execution_profile,
        )?;
        let timeout = e
            .timeout_ms
            .unwrap_or(self.config.executor.max_runtime_ms.min(30_000));
        let stdout = e
            .stdout_limit_bytes
            .unwrap_or(self.config.executor.max_output_bytes.min(1024 * 1024));
        let stderr = e
            .stderr_limit_bytes
            .unwrap_or(self.config.executor.max_output_bytes.min(1024 * 1024));
        if timeout == 0
            || timeout > self.config.executor.max_runtime_ms
            || stdout == 0
            || stderr == 0
            || stdout > self.config.executor.max_output_bytes
            || stderr > self.config.executor.max_output_bytes
        {
            return Err(RuntimeError::invalid(
                "execution limits exceed operator ceilings",
                "execution",
            ));
        }
        let runner = self
            .config
            .executor
            .runner_path
            .as_deref()
            .ok_or_else(|| error("native runner required"))?;
        super::platform::validate_runner(runner)?;
        let record = universal::load_workspace_record(&self.config.executor, &e.workspace_id)
            .map_err(super::super::error::map_universal_error)?;
        let cwd =
            universal::resolve_workspace_cwd(&record, &e.cwd_relative, "execution.cwdRelative")
                .map_err(io)?;
        let executable = super::platform::validate_executable(
            &self.config.executor,
            &e.executable,
            "execution.executable",
        )?;
        let source =
            universal::workspace_source_state_digest(&self.config.executor, &e.workspace_id)
                .map_err(io)?;
        // An Agent-authored plan is resolved only at new admission. Every
        // executable and cwd is checked through existing native authorities,
        // then frozen into the PostgreSQL execution plan and Runner bundle.
        let mut frozen_steps = Vec::with_capacity(e.steps.len());
        let mut cumulative_step_budget = 0_u64;
        for (index, step) in e.steps.iter().enumerate() {
            let path = super::platform::validate_executable(
                &self.config.executor,
                &step.executable,
                &format!("execution.steps[{index}].executable"),
            )?;
            let cwd = universal::resolve_workspace_cwd(
                &record,
                &step.cwd_relative,
                &format!("execution.steps[{index}].cwdRelative"),
            )
            .map_err(io)?;
            let ceiling = step
                .timeout_ms
                .unwrap_or(self.config.executor.max_runtime_ms.min(30_000));
            if ceiling == 0 || ceiling > self.config.executor.max_runtime_ms {
                return Err(RuntimeError::invalid(
                    "invalid plan step timeout",
                    "execution.steps",
                ));
            }
            cumulative_step_budget =
                cumulative_step_budget.checked_add(ceiling).ok_or_else(|| {
                    RuntimeError::invalid("plan step budget overflow", "execution.steps")
                })?;
            frozen_steps.push(RuntimeExecutionStep {
                id: step.id.clone(),
                executable: path.to_string_lossy().into_owned(),
                executable_digest: universal::sha256_file(&path).map_err(io)?,
                args: step.args.clone(),
                cwd: cwd.to_string_lossy().into_owned(),
                env: step.env.clone(),
                timeout_ms: ceiling,
                continue_on_error: step.continue_on_error,
            });
        }
        // When a plan supplies no job-wide timeout, the sum of resolved
        // per-step budgets is the exact finite ceiling, as on the mature Runner.
        let timeout = if !frozen_steps.is_empty() && e.timeout_ms.is_none() {
            cumulative_step_budget
        } else {
            timeout
        };
        if timeout == 0 || timeout > self.config.executor.max_runtime_ms {
            return Err(RuntimeError::invalid(
                "plan exceeds configured runtime maximum",
                "execution.timeoutMs",
            ));
        }
        let mut plan = RuntimeExecutionPlan {
            schema_version: 1,
            workspace_id: e.workspace_id.clone(),
            workspace_path: record.workspace_path.clone(),
            source_revision: record.source_revision.clone(),
            workspace_source_digest: Some(source),
            workspace_git_common_dir: None,
            executable: executable.to_string_lossy().into_owned(),
            executable_digest: universal::sha256_file(&executable).map_err(io)?,
            args: e.args.clone(),
            cwd: cwd.to_string_lossy().into_owned(),
            env: e.env.clone(),
            timeout_ms: timeout,
            stdout_limit_bytes: stdout,
            stderr_limit_bytes: stderr,
            steps: frozen_steps,
            budget: e.budget.clone(),
            execution_profile: e.execution_profile,
            execution_target: e.execution_target,
            windows_authority: e.windows_authority,
            windows_context: None,
            windows_execution_context: None,
            foreign_references: vec![],
            host_dependencies,
            input_set_id: None,
            effective_inputs: vec![],
            credential_set_id: None,
            principal: proposal.principal.clone(),
        };
        let mut contract = self.scheduling_contract(&plan)?;
        if e.budget.scheduling.is_none() {
            if let Some(max) = plan.budget.memory_max_bytes {
                contract.resources.memory_bytes = contract.resources.memory_bytes.min(max);
            }
            if let Some(max) = plan.budget.tasks_max {
                contract.resources.pids = contract.resources.pids.min(max);
            }
            if let Some(max) = plan.budget.cpu_quota_percent {
                contract.resources.cpu_millis =
                    contract.resources.cpu_millis.min(max.saturating_mul(10));
            }
        }
        if plan
            .budget
            .memory_max_bytes
            .is_some_and(|v| v < contract.resources.memory_bytes)
            || plan
                .budget
                .tasks_max
                .is_some_and(|v| v < contract.resources.pids)
            || plan
                .budget
                .cpu_quota_percent
                .is_some_and(|v| v.saturating_mul(10) < contract.resources.cpu_millis)
        {
            return Err(RuntimeError::invalid(
                "resource request exceeds its hard execution ceiling",
                "execution.budget.scheduling",
            ));
        }
        if let (Some(high), Some(max)) = (contract.memory_high_bytes, plan.budget.memory_max_bytes)
        {
            if high > max {
                return Err(RuntimeError::invalid(
                    "memoryHighBytes exceeds memoryMaxBytes",
                    "execution.budget.scheduling",
                ));
            }
        }
        for relative in &contract.workspace_access.write_paths {
            let path =
                fs::canonicalize(Path::new(&plan.workspace_path).join(relative)).map_err(io)?;
            if !path.starts_with(&plan.workspace_path) || !path.is_dir() {
                return Err(RuntimeError::invalid(
                    "writePaths requires existing contained directories",
                    "execution.budget.scheduling.workspaceAccess",
                ));
            }
        }
        if contract.workspace_access.read_only || !contract.workspace_access.write_paths.is_empty()
        {
            plan.workspace_git_common_dir = Some(
                universal::workspace_git_common_dir_at(Path::new(&plan.workspace_path))
                    .map_err(io)?
                    .to_string_lossy()
                    .into_owned(),
            );
        }
        if !contract.workspace_access.write_paths.is_empty() {
            let _ = universal::workspace_source_readset_digest_at(
                Path::new(&plan.workspace_path),
                &contract.workspace_access.write_paths,
            )
            .map_err(io)?;
        }
        if !contract.workspace_access.read_paths.is_empty() {
            plan.workspace_source_digest = Some(
                universal::workspace_source_readset_digest_at(
                    Path::new(&plan.workspace_path),
                    &contract.workspace_access.read_paths,
                )
                .map_err(io)?,
            );
        }
        plan.budget.scheduling = Some(contract);
        let plan_json = encode(&plan)?;
        let plan_digest = universal::sha256_bytes(plan_json.as_bytes());
        // An Operation commits to the resolved execution world and native
        // provider. The proposal identity remains stable for exact replay.
        // Use the existing canonical Job identity contract rather than a
        // PostgreSQL-specific digest scheme.
        let provider_digest = universal::sha256_file(runner).map_err(io)?;
        let operation_digest = JobIdentityContract::operation_digest(
            &identity,
            &plan_digest,
            OperationIdentityBindings::Provider {
                provider_digest: &provider_digest,
            },
        );
        let job = format!("job-{}", Uuid::now_v7());
        let attempt = format!("attempt-{}", Uuid::now_v7());
        let bundle = self
            .config
            .executor
            .store_root
            .join("pg-attempts")
            .join(&attempt);
        let token = universal::sha256_bytes(
            format!("runtime-launch-v1\0{attempt}\0{operation_digest}").as_bytes(),
        );
        let input = PgAdmissionInput {
            job_id: job.clone(),
            attempt_id: attempt.clone(),
            reservation_id: format!("reservation-{}", Uuid::now_v7()),
            principal: proposal.principal.clone(),
            client_request_id: proposal.client_request_id.clone(),
            request_digest: identity,
            operation_digest,
            workspace_id: e.workspace_id.clone(),
            workspace_snapshot_json: encode(
                &json!({"workspace":record,"executionProvider":{"contract":"local_linux_runner_v1","executableDigest":universal::sha256_file(runner).map_err(io)?}}),
            )?,
            execution_plan_digest: plan_digest,
            execution_plan_json: plan_json,
            launch_token_digest: universal::sha256_bytes(token.as_bytes()),
            bundle_path: bundle.to_string_lossy().into_owned(),
            unit_name: format!("ordivon-pg-{attempt}.service"),
            global_limit: 0,
            created_at_ms: now()?,
            expected_source_sha256: self.config.source_sha256.clone(),
        };
        let job = match db.admit(&input).map_err(pg)? {
            PgAdmissionOutcome::Created(j) | PgAdmissionOutcome::Existing(j) => j,
        };
        let _ = self.schedule_pending_jobs();
        self.observe(
            &proposal.principal,
            &JobObserveRequest {
                schema_version: 1,
                job_id: job,
                wait_ms: proposal.wait_ms,
                wait_until: JobObserveWaitUntil::Terminal,
                stdout_tail_bytes: proposal.stdout_tail_bytes,
                stderr_tail_bytes: proposal.stderr_tail_bytes,
                stdout_offset: None,
                stderr_offset: None,
            },
        )
    }
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
        loop {
            self.authorize(&mut db, &request.job_id, principal)?;
            self.reconcile(&mut db, &request.job_id)?;
            let value = self.project(&mut db, request)?;
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
                    .map_err(io)?;
                let wait = deadline
                    .saturating_duration_since(Instant::now())
                    .min(Duration::from_secs(1));
                let _ = db
                    .client
                    .notifications()
                    .timeout_iter(wait)
                    .next()
                    .map_err(io)?;
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
                super::platform::wait_for_attempt_change(
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
        db.request_cancel_intent(&PgCancelIntent {
            job_id: request.job_id.clone(),
            observed_at_ms: now()?,
            expected_source_sha256: self.config.source_sha256.clone(),
        })
        .map_err(pg)?;
        let (a, _, _) = self.attempt(&mut db, &request.job_id)?;
        if !a.state.is_terminal() {
            fs::create_dir_all(&a.bundle_path).map_err(io)?;
            universal::write_json_atomic(
                &Path::new(&a.bundle_path).join("cancel-requested.json"),
                &json!({"requestedAtMs":now()?}),
            )
            .map_err(io)?;
            if a.state == AttemptState::Accepted {
                self.reconcile(&mut db, &request.job_id)?;
                return self.project(
                    &mut db,
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
        let (a, p, operation) = self.attempt(&mut db, job)?;
        let j = db
            .client
            .query_one(
                "SELECT client_request_id,created_at_ms FROM jobs WHERE job_id=$1",
                &[&job],
            )
            .map_err(io)?;
        let counts=db.client.query_one("SELECT count(*),COALESCE(sum(byte_length),0)::bigint,count(*) FILTER(WHERE truncated) FROM artifacts WHERE job_id=$1",&[&job]).map_err(io)?;
        let mut by_kind = std::collections::BTreeMap::new();
        for row in db
            .client
            .query(
                "SELECT kind,count(*) FROM artifacts WHERE job_id=$1 GROUP BY kind",
                &[&job],
            )
            .map_err(io)?
        {
            by_kind.insert(row.get(0), row.get::<_, i64>(1) as u64);
        }
        let events=db.client.query("SELECT event_sequence,event_type,origin,previous_state,new_state,reason_code,observed_at_ms FROM job_events WHERE job_id=$1 ORDER BY event_sequence LIMIT $2",&[&job,&(i64::from(event_limit)+1)]).map_err(io)?;
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
            .map_err(io)?
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
                attempt_number: 1,
                state: a.state,
                termination_intent: a.termination_intent,
                created_at_ms: a.created_at_ms,
                started_at_ms: None,
                finished_at_ms: snapshot.finished_at_ms.map(|v| v as u64),
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
