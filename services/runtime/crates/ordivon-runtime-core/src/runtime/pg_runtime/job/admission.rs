//! PostgreSQL Job admission: exact-key replay, plan qualification, immutable identity and dispatch intent.
use super::*;
impl PgRuntime {
    pub fn run(&self, proposal: &JobRunProposal) -> RuntimeResult<JobObservation> {
        self.run_with_execution_profile_policy(proposal, None)
    }

    /// Authenticate new effects by the server-bound ingress profile without
    /// breaking already-committed exact-key recovery. Replay MUST remain before
    /// this mutable policy check: the former trusted Job is not re-spawned.
    pub fn run_with_execution_profile_policy(
        &self,
        proposal: &JobRunProposal,
        required_new_profile: Option<ExecutionProfile>,
    ) -> RuntimeResult<JobObservation> {
        super::admission_validation::validate_resource_run_proposal_structure(proposal)?;
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
        if let Some(row) = db.client.query_opt("SELECT job_id,request_digest FROM jobs WHERE principal=$1 AND client_request_id=$2", &[&proposal.principal,&proposal.client_request_id]).map_err(pg_read_error)? {
            if row.get::<_,String>(1)!=identity { return Err(pg(PgAdmissionError::IdempotencyConflict)); }
            let committed_job: String = row.get(0);
            let mut first_wait_ms = proposal.wait_ms;
            return observe_committed_job_with_bounded_busy_recovery(
                &committed_job,
                || self.observe(&proposal.principal, &JobObserveRequest { schema_version:1,job_id:committed_job.clone(),wait_ms:std::mem::replace(&mut first_wait_ms, 0),wait_until:JobObserveWaitUntil::Terminal,stdout_tail_bytes:proposal.stdout_tail_bytes,stderr_tail_bytes:proposal.stderr_tail_bytes,stdout_offset:None,stderr_offset:None }),
            );
        }
        let e = &proposal.execution;
        // Only NEW admission is subject to the current ingress profile.
        // Existing principal+clientRequestId was reconciled above.
        authorize_new_execution_profile(e.execution_profile, required_new_profile)?;
        // ForeignReferences are not authorization. A real Harness dispatch
        // fence is only a source-owned exact-physical-intent indicator: do not
        // modify its environment before the actual issuer authority check.
        // Only an operator-configured issuer path may preserve the source environment;
        // the hint never authenticates the caller and PG still checks currentness.
        let preserve_harness_fenced_request = preserve_qualified_issuer_environment(
            self.config.harness_issuer_schema.as_deref(),
            &e.foreign_references,
        );
        if preserve_harness_fenced_request
            && e.execution_profile == ExecutionProfile::ContainedLocal
        {
            return Err(RuntimeError::invalid(
                "issuer-bound Tool environment cannot be rewritten for contained_local",
                "execution.executionProfile",
            ));
        }

        #[cfg(not(windows))]
        if !supports_native_pg_execution(e, false) {
            return Err(RuntimeError::invalid(
                "PG vertical supports local_linux trusted_local or contained_local execution only",
                "execution",
            ));
        }
        #[cfg(windows)]
        self.validate_native_windows_proposal(proposal)?;
        // A current Issuer must not authorize unrelated physical steps/budgets.
        if self.config.harness_issuer_schema.is_some()
            && (!e.steps.is_empty() || !e.host_dependencies.is_empty() || !e.budget.is_empty())
        {
            return Err(RuntimeError::invalid(
                "issuer-fenced execution does not authorize custom budget/steps/host prerequisites",
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
        let workspace_generated_cache = self
            .config
            .executor
            .workspace_cache_path(&record.workspace_id);
        let shared_package_cache = self.config.executor.shared_caches_root();
        let linux_shared_package_cache =
            cfg!(target_os = "linux").then_some(shared_package_cache.as_path());
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
                env: if e.execution_profile == ExecutionProfile::ContainedLocal {
                    pg_contained_workspace_environment(
                        step.env.clone(),
                        &self.config.executor,
                        &record.workspace_id,
                        Path::new(&record.workspace_path),
                    )?
                } else {
                    pg_workspace_tool_environment(
                        step.env.clone(),
                        preserve_harness_fenced_request,
                        &workspace_generated_cache,
                        linux_shared_package_cache,
                    )
                },
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
            // Contained tasks can read their original Git worktree metadata
            // through the native read-only common-dir bind. Never grant a
            // writable mount of the shared source repository to an Agent.
            workspace_git_common_dir: if e.execution_profile == ExecutionProfile::ContainedLocal {
                Some(
                    universal::workspace_git_common_dir_at(Path::new(&record.workspace_path))
                        .map_err(io)?
                        .to_string_lossy()
                        .into_owned(),
                )
            } else {
                None
            },
            executable: executable.to_string_lossy().into_owned(),
            executable_digest: universal::sha256_file(&executable).map_err(io)?,
            args: e.args.clone(),
            cwd: cwd.to_string_lossy().into_owned(),
            env: if e.execution_profile == ExecutionProfile::ContainedLocal {
                pg_contained_workspace_environment(
                    e.env.clone(),
                    &self.config.executor,
                    &record.workspace_id,
                    Path::new(&record.workspace_path),
                )?
            } else {
                pg_workspace_tool_environment(
                    e.env.clone(),
                    preserve_harness_fenced_request,
                    &workspace_generated_cache,
                    linux_shared_package_cache,
                )
            },
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
            // ForeignReference is an externally supplied identity/correlation
            // commitment, NEVER a credential or an authorization to dispatch.
            // Structural uniqueness is checked by the shared Runtime validator,
            // request identity hashes it, and the PG plan freezes it verbatim
            // for the native Runner and later terminal evidence.
            foreign_references: e.foreign_references.clone(),
            host_dependencies,
            input_set_id: None,
            effective_inputs: vec![],
            credential_set_id: None,
            principal: proposal.principal.clone(),
        };
        #[cfg(windows)]
        self.bind_native_windows_plan(proposal, &mut plan)?;
        let mut contract = self.scheduling_contract(&plan)?;
        #[cfg(windows)]
        {
            if !contract.workspace_access.exclusive()
                && plan.windows_authority != WindowsAuthority::Limited
            {
                return Err(RuntimeError::invalid(
                    "Windows Workspace scoping requires a limited native payload",
                    "execution.budget.scheduling.workspaceAccess",
                ));
            }
            if contract.memory_high_bytes.is_some() || contract.io_weight.is_some() {
                return Err(RuntimeError::invalid(
                    "Windows Job Objects do not expose these Linux soft controls",
                    "execution.budget.scheduling",
                ));
            }
        }

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
            let workspace = Path::new(&plan.workspace_path);
            #[cfg(windows)]
            let workspace = fs::canonicalize(workspace).map_err(io)?;
            let path = fs::canonicalize(workspace.join(relative)).map_err(io)?;
            #[cfg(not(windows))]
            let contained = path.starts_with(workspace);
            #[cfg(windows)]
            let contained = path.strip_prefix(&workspace).is_ok_and(|scope| {
                !scope.as_os_str().is_empty()
                    && scope
                        .to_string_lossy()
                        .replace('\\', "/")
                        .eq_ignore_ascii_case(relative)
            });
            if !contained || !path.is_dir() {
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
                &json!({"workspace":record,"executionProvider":{"contract":if cfg!(windows) {"windows_native_launcher_v1"} else {"local_linux_runner_v1"},"executableDigest":provider_digest}}),
            )?,
            execution_plan_digest: plan_digest,
            execution_plan_json: plan_json,
            launch_token_digest: universal::sha256_bytes(token.as_bytes()),
            bundle_path: bundle.to_string_lossy().into_owned(),
            unit_name: if cfg!(windows) {
                format!("Ordivon.{attempt}")
            } else {
                format!("ordivon-pg-{attempt}.service")
            },
            global_limit: 0,
            created_at_ms: now()?,
            expected_source_sha256: self.config.source_sha256.clone(),
        };
        // Planning is intentionally outside the coarse PG admission lock:
        // Git/source hashing is potentially expensive. The exact Workspace
        // lifetime identity MUST nonetheless be rebound after acquiring the
        // same global lock as workspace.close/open/mutate, before INSERT jobs.
        // The native Runner separately verifies frozen source/readset bytes
        // before physical execution; this cheap fence prevents an orphaned
        // durable Job when the Workspace was closed or replaced meanwhile.
        let workspace_guard = || {
            universal::ensure_workspace_mutation_quiescent(&self.config.executor, &e.workspace_id)
                .map_err(|_| PgAdmissionError::WorkspaceStale)?;
            let current = universal::load_workspace_record(&self.config.executor, &e.workspace_id)
                .map_err(|_| PgAdmissionError::WorkspaceStale)?;
            if current != record {
                return Err(PgAdmissionError::WorkspaceStale);
            }
            Ok(())
        };
        let job = match db
            .admit_with_workspace_guard(
                &input,
                &workspace_guard,
                self.config.harness_issuer_schema.as_deref(),
            )
            .map_err(pg)?
        {
            PgAdmissionOutcome::Created(j) | PgAdmissionOutcome::Existing(j) => j,
        };
        let _ = self.schedule_pending_jobs();
        let mut first_wait_ms = proposal.wait_ms;
        observe_committed_job_with_bounded_busy_recovery(&job, || {
            self.observe(
                &proposal.principal,
                &JobObserveRequest {
                    schema_version: 1,
                    job_id: job.clone(),
                    wait_ms: std::mem::replace(&mut first_wait_ms, 0),
                    wait_until: JobObserveWaitUntil::Terminal,
                    stdout_tail_bytes: proposal.stdout_tail_bytes,
                    stderr_tail_bytes: proposal.stderr_tail_bytes,
                    stdout_offset: None,
                    stderr_offset: None,
                },
            )
        })
    }
}
