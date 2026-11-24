//! One already-admitted Attempt's exact bundle, PG handoff, and native systemd spawn.
//! A false result means no further native reconciliation is needed at this cut.
use super::{
    error, fs, io, now, pg, prepare_private_pg_attempt_bundle, universal, AttemptRecord,
    AttemptState, AttemptTerminationIntent, ExecutionProfile, PgAdmissionStore, PgBundleReady,
    PgDispatchIssued, PgRuntime, RunnerRequest, RuntimeError, RuntimeErrorCode,
    RuntimeExecutionPlan, RuntimeResult,
};
use std::path::Path;

impl PgRuntime {
    pub(super) fn dispatch_accepted_attempt(
        &self,
        db: &mut PgAdmissionStore,
        a: &mut AttemptRecord,
        plan: &RuntimeExecutionPlan,
        provider: &serde_json::Value,
        operation: &str,
        allow_dispatch: bool,
    ) -> RuntimeResult<bool> {
        // Job authority is already bound by the exact PG Attempt, not a parallel argument.
        let owned_job_id = a.job_id.clone();
        let job = owned_job_id.as_str();
        if a.state == AttemptState::Accepted
            && a.termination_intent == AttemptTerminationIntent::Natural
        {
            if !allow_dispatch {
                return Ok(false);
            }
            let runner = self
                .config
                .executor
                .runner_path
                .as_deref()
                .ok_or_else(|| error("runner missing"))?;
            super::platform::validate_runner(runner)?;
            if provider["executionProvider"]["executableDigest"].as_str()
                != Some(&universal::sha256_file(runner).map_err(io)?)
            {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ProviderStateMismatch,
                    "native runner changed after admission",
                    Some("executionProvider"),
                    false,
                )
                .with_operation_id(job));
            }
            // Revalidate the *committed* bytes before dispatch; Runner owns
            // continuous path-drift witnessing after it starts.
            super::host_dependency::verify_committed_bindings(&plan.host_dependencies)?;
            let token = universal::sha256_bytes(
                format!("runtime-launch-v1\0{}\0{operation}", a.attempt_id).as_bytes(),
            );
            if universal::sha256_bytes(token.as_bytes()) != a.launch_token_digest {
                return Err(error("launch token mismatch"));
            }
            // Derive the Workspace-private Cargo backing from the committed plan.
            // New plans bind it into one native systemd mount namespace; old
            // FD198 plans continue to use the original Runner compatibility path.
            // Do not rewrite a committed environment or its source identity.
            let build_target_backing =
                if crate::runtime::build_target_contract::requires_private_cargo_build_target(plan)
                {
                    let backing = self
                        .config
                        .executor
                        .workspace_build_cache_path(&plan.workspace_id)
                        .join("cargo");
                    fs::create_dir_all(&backing).map_err(|error| {
                        RuntimeError::new(
                            RuntimeErrorCode::IoError,
                            format!("prepare Workspace-private Cargo cache: {error}"),
                            Some("workspaceId"),
                            false,
                        )
                    })?;
                    Some(backing.to_string_lossy().into_owned())
                } else {
                    None
                };
            if !self.claim_resources(db, a, plan)? {
                return Ok(false);
            }
            let req = RunnerRequest {
                workspace_read_paths: plan.budget.scheduling.as_ref().and_then(|s| {
                    if s.workspace_access.read_paths.is_empty() {
                        None
                    } else {
                        Some(s.workspace_access.read_paths.clone())
                    }
                }),
                schema_version: 1,
                job_id: Some(job.into()),
                attempt_id: Some(a.attempt_id.clone()),
                launch_token: Some(token),
                unit_name: Some(a.unit_name.clone()),
                // Reuse the existing Unix Runner child privilege drop, leaving
                // the Runner's PG/result bundle under its original UID 0.
                // The task's Workspace identity comes only from the
                // operator-configured native owner, never a caller field.
                payload: if plan.execution_profile == ExecutionProfile::ContainedLocal {
                    let (Some(uid), Some(gid)) = (
                        self.config.executor.workspace_uid,
                        self.config.executor.workspace_gid,
                    ) else {
                        return Err(RuntimeError::invalid(
                            "contained_local requires configured nonroot task owner",
                            "execution.executionProfile",
                        ));
                    };
                    if uid == 0 || gid == 0 {
                        return Err(RuntimeError::invalid(
                            "contained_local task owner may not be root",
                            "execution.executionProfile",
                        ));
                    }
                    Some(universal::RunnerPayloadConfig {
                        uid,
                        gid,
                        workspace_view: plan.workspace_path.clone(),
                        cwd_view: plan.cwd.clone(),
                        runtime_view: self
                            .config
                            .executor
                            .workspace_cache_path(&plan.workspace_id)
                            .join("home")
                            .to_string_lossy()
                            .into_owned(),
                        cache_view: self
                            .config
                            .executor
                            .workspace_cache_path(&plan.workspace_id)
                            .to_string_lossy()
                            .into_owned(),
                    })
                } else {
                    None
                },
                // Ordinary trusted jobs preserve their historical
                // environment. The contained child must never inherit
                // control-plane environment from the trusted Runner.
                inherit_host_environment: plan.execution_profile
                    != ExecutionProfile::ContainedLocal,
                task_id: a.attempt_id.clone(),
                workspace_id: plan.workspace_id.clone(),
                workspace_path: plan.workspace_path.clone(),
                workspace_source_digest: plan.workspace_source_digest.clone(),
                build_target_backing,
                input_presentation_root: None,
                input_commitments: vec![],
                host_dependencies: plan
                    .host_dependencies
                    .iter()
                    .map(|binding| universal::RunnerHostDependencyCommitment {
                        path: binding.path.clone(),
                        digest: binding.expected_digest.clone(),
                    })
                    .collect(),
                executable: plan.executable.clone(),
                executable_digest: plan.executable_digest.clone(),
                args: plan.args.clone(),
                cwd: plan.cwd.clone(),
                env: plan.env.clone(),
                steps: plan
                    .steps
                    .iter()
                    .map(|step| universal::RunnerExecutionStep {
                        id: step.id.clone(),
                        executable: step.executable.clone(),
                        executable_digest: step.executable_digest.clone(),
                        args: step.args.clone(),
                        cwd: step.cwd.clone(),
                        env: step.env.clone(),
                        timeout_ms: step.timeout_ms,
                        continue_on_error: step.continue_on_error,
                    })
                    .collect(),
                timeout_ms: plan.timeout_ms,
                stdout_limit_bytes: plan.stdout_limit_bytes,
                stderr_limit_bytes: plan.stderr_limit_bytes,
            };
            prepare_private_pg_attempt_bundle(Path::new(&a.bundle_path))?;
            let request_path = Path::new(&a.bundle_path).join("request.json");
            let bytes = serde_json::to_vec(&req).map_err(io)?;
            // Existing published bytes must match; never replace a committed bundle.
            if request_path.exists() {
                if fs::read(&request_path).map_err(io)? != bytes {
                    return Err(error("bundle bytes differ"));
                }
            } else {
                universal::write_bytes_atomic(&request_path, &bytes).map_err(io)?;
            }
            let digest = universal::sha256_bytes(&bytes);
            if a.bundle_digest.is_none() {
                a.row_version = db
                    .commit_bundle_ready_pg(&PgBundleReady {
                        attempt_id: a.attempt_id.clone(),
                        expected_row_version: a.row_version as i64,
                        bundle_digest: digest.clone(),
                        observed_at_ms: now()?,
                        expected_source_sha256: self.config.source_sha256.clone(),
                    })
                    .map_err(pg)? as u64;
            } else if a.bundle_digest.as_deref() != Some(&digest) {
                return Err(error("bundle digest mismatch"));
            }
            // This commit is intent only. Never reissue a physical launch after this boundary.
            let (issuer_schema, issuer_principal) =
                if let Some((principal, schema)) = &self.config.harness_dispatch_issuer {
                    (Some(schema.as_str()), Some(principal.as_str()))
                } else {
                    (self.config.harness_issuer_schema.as_deref(), None)
                };
            let issued_version = db
                .mark_dispatch_issued_pg(
                    &PgDispatchIssued {
                        attempt_id: a.attempt_id.clone(),
                        expected_row_version: a.row_version as i64,
                        expected_bundle_digest: digest.clone(),
                        observed_at_ms: now()?,
                        expected_source_sha256: self.config.source_sha256.clone(),
                    },
                    issuer_schema,
                    issuer_principal,
                )
                .map_err(pg)?;
            // One issuer owns this at-most-once physical call. If a STOP
            // committed after DISPATCH_ISSUED but before we ever called
            // systemd, settle without inventing a Runner start/exit.
            // Never apply this fact from a recovering or different issuer.
            if db
                .settle_cancel_before_native_handoff(&PgDispatchIssued {
                    attempt_id: a.attempt_id.clone(),
                    expected_row_version: issued_version,
                    expected_bundle_digest: digest,
                    observed_at_ms: now()?,
                    expected_source_sha256: self.config.source_sha256.clone(),
                })
                .map_err(pg)?
            {
                return Ok(false);
            }
            let output = super::platform::systemd_run(&super::platform::SystemdRunSpec {
                unit_name: &a.unit_name,
                runner: self
                    .config
                    .executor
                    .runner_path
                    .as_deref()
                    .ok_or_else(|| error("runner missing"))?,
                bundle_path: Path::new(&a.bundle_path),
                workspace_path: Path::new(&plan.workspace_path),
                workspace_git_common_dir: plan.workspace_git_common_dir.as_deref().map(Path::new),
                cargo_target_mount:
                    if crate::runtime::build_target_contract::requires_native_cargo_target_mount(
                        plan,
                    ) {
                        req.build_target_backing.as_deref().map(Path::new)
                    } else {
                        None
                    },
                input_set_path: None,
                credential_source_root: None,
                credential_names: &[],
                runtime_ceiling_ms: plan
                    .timeout_ms
                    .checked_add(5000)
                    .ok_or_else(|| error("timeout overflow"))?,
                budget: &plan.budget,
                execution_profile: plan.execution_profile,
                environment: &plan.env,
            })?;
            if !output.status.success() {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::DispatchOutcomeUnknown,
                    format!(
                        "native launch not confirmed for Job {job}: {}",
                        String::from_utf8_lossy(&output.stderr)
                    ),
                    Some("jobId"),
                    false,
                )
                .with_operation_id(job.to_string()));
            }
            let Some(current) = self.refresh_reconciling_attempt(db, job, &a.attempt_id)? else {
                return Ok(false);
            };
            *a = current;
            // A cancellation may win *after* the pre-handoff CAS and while
            // systemd-run delivers to the asynchronous Manager. Request an
            // exact Unit stop; the later OS+PG reconciliation alone may
            // certify terminal state. This is NOT a NoFutureSpawn ACK.
            if a.termination_intent == AttemptTerminationIntent::StopRequested
                && !a.state.is_terminal()
            {
                let _ = super::platform::stop_unit_no_block(&a.unit_name)?;
            }
        }
        Ok(true)
    }
}
