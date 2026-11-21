//! Reconcile a committed Attempt with real systemd/Runner evidence.
//! This is the existing native OS-effect authority, not an additional recovery engine.

use super::{
    decode, error, fs, io, native_running_witness, now, observed_namespace_pid, pg, pg_read_error,
    prepare_private_pg_attempt_bundle, runner_result_still_absent, universal, AttemptState,
    AttemptTerminationIntent, ExecutionProfile, NativePidReadback, PgAdmissionError,
    PgAdmissionStore, PgArtifactRegistration, PgBundleReady, PgDispatchIssued, PgRuntime,
    PgTerminalNoArtifacts, RunnerRequest, RunnerStartEvidence, RuntimeError, RuntimeErrorCode,
    RuntimeResult, RECONCILIATION_STAGE_SQL, RELEASE_CURRENT_ATTEMPT_STATE_SQL,
};
use serde_json::json;
use std::path::{Path, PathBuf};

impl PgRuntime {
    pub(in crate::runtime::pg_runtime) fn reconcile(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<()> {
        self.reconcile_inner(db, job, false)
    }
    pub(in crate::runtime::pg_runtime) fn reconcile_inner(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
        allow_dispatch: bool,
    ) -> RuntimeResult<()> {
        // Preserve the existing one-query ReleaseEffect classification, now
        // also reading the terminal flag. The atomic terminal PG transition
        // deliberately clears current_attempt_id. A resolved Job has no
        // remaining native effect to reconcile; ONLY project/get then verify
        // its lifecycle, reservation, exact Attempt, and terminal events.
        // This does not make a historical Attempt eligible for Runner effects.
        let stage = db
            .client
            .query_one(RECONCILIATION_STAGE_SQL, &[&job])
            .map_err(pg_read_error)?;
        if stage.get::<_, Option<String>>(0).is_some() {
            return Ok(());
        }
        let is_release: bool = stage.get(1);
        if is_release {
            // Accepted means no physical release dispatch occurred. Any other
            // Attempt state without a release-specific operator receipt is
            // inconsistent; never reconcile it through the generic Runner.
            let row = db
                .client
                .query_opt(RELEASE_CURRENT_ATTEMPT_STATE_SQL, &[&job])
                .map_err(pg_read_error)?;
            return match row.map(|value| value.get::<_, String>(0)).as_deref() {
                Some("accepted") => Ok(()),
                _ => Err(RuntimeError::new(
                    RuntimeErrorCode::ReconciliationRequired,
                    "ReleaseEffect requires operator receipt reconciliation",
                    Some("runtimeReleaseEffect"),
                    false,
                )
                .with_operation_id(job)),
            };
        }
        // Decode the *same* committed current-Attempt row just once.
        // A pre-dispatch STOP_REQUESTED is locally finalizable without
        // consulting the frozen execution Plan or mutable Provider snapshot.
        // All other states preserve the existing strict full-Plan readback.
        let row = self.current_attempt_row(db, job)?;
        if row.get::<_, String>(1) == "accepted" && row.get::<_, String>(2) == "stop_requested" {
            let a = self.decode_attempt_identity(&row, job)?;
            return self.reconcile_accepted_cancel(db, job, &a);
        }
        let (mut a, plan, operation) = self.decode_attempt_record(&row, job)?;
        let provider: serde_json::Value = decode(
            &db.client
                .query_one(
                    "SELECT workspace_snapshot_json FROM jobs WHERE job_id=$1",
                    &[&job],
                )
                .map_err(pg_read_error)?
                .get::<_, String>(0),
        )?;
        if a.state == AttemptState::Accepted
            && a.termination_intent == AttemptTerminationIntent::Natural
        {
            if !allow_dispatch {
                return Ok(());
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
                if crate::runtime::build_target_contract::requires_private_cargo_build_target(&plan)
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
            if !self.claim_resources(db, &a, &plan)? {
                return Ok(());
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
                return Ok(());
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
                        &plan,
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
            a = self.attempt(db, job)?.0;
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
        let path = PathBuf::from(&a.bundle_path);
        // DISPATCH_ISSUED is intent, not a physical start. Only the native
        // Runner start receipt bound to the live systemd InvocationID, PID
        // and cgroup may advance this Attempt from starting to running.
        if a.state == AttemptState::Starting
            && a.termination_intent == AttemptTerminationIntent::Natural
        {
            let start_path = Path::new(&a.bundle_path).join("runner-start.json");
            match fs::symlink_metadata(&start_path) {
                Ok(metadata) if metadata.file_type().is_file() => {
                    let bytes = fs::read(&start_path).map_err(io)?;
                    let start: RunnerStartEvidence = serde_json::from_slice(&bytes).map_err(io)?;
                    let native = super::platform::systemctl_show(&a.unit_name)?;
                    // systemd MainPID is in the host namespace. PrivatePIDs
                    // may make RunnerStart.namespace_pid equal 1: never read
                    // host /proc/1 as though it were this Runner.
                    let host_pid = native
                        .get("MainPID")
                        .and_then(|pid| pid.parse::<u32>().ok())
                        .filter(|pid| *pid != 0);
                    let host_process_start = host_pid.and_then(super::platform::process_identity);
                    let namespace_pid = host_pid.and_then(observed_namespace_pid);
                    if native_running_witness(
                        &start,
                        &native,
                        job,
                        &a.attempt_id,
                        &a.launch_token_digest,
                        NativePidReadback {
                            host_pid,
                            namespace_pid,
                            process_start: host_process_start.as_deref(),
                        },
                        provider["executionProvider"]["executableDigest"]
                            .as_str()
                            .unwrap_or(""),
                    ) {
                        let input = crate::pg_admission::PgRunnerBound {
                            attempt_id: a.attempt_id.clone(),
                            expected_row_version: a.row_version as i64,
                            expected_bundle_digest: a
                                .bundle_digest
                                .clone()
                                .ok_or_else(|| error("issued Attempt omitted bundle digest"))?,
                            runner_start_digest: universal::sha256_bytes(&bytes),
                            native_invocation_id: start.invocation_id,
                            observed_at_ms: now()?,
                            expected_source_sha256: self.config.source_sha256.clone(),
                        };
                        match db.mark_runner_bound_pg(&input) {
                            Ok(new_version) => {
                                a.state = AttemptState::Running;
                                a.row_version = new_version as u64;
                            }
                            Err(PgAdmissionError::Blocked | PgAdmissionError::UnknownCommit) => {
                                // A concurrent cancellation/terminal won. Read its
                                // original PG Attempt; never redispatch or revive it.
                                a = self.attempt(db, job)?.0;
                            }
                            Err(err) => return Err(pg(err)),
                        }
                    }
                }
                Err(err) if err.kind() == std::io::ErrorKind::NotFound => {}
                Ok(_) => return Err(error("Runner start evidence is not a regular file")),
                Err(err) => return Err(io(err)),
            }
        }
        if !a.state.is_terminal() && path.join("result.json").exists() {
            // Reuse native identity, stdout/stderr digest and result validators.
            let start: RunnerStartEvidence =
                serde_json::from_slice(&fs::read(path.join("runner-start.json")).map_err(io)?)
                    .map_err(io)?;
            if start.job_id != job
                || start.attempt_id != a.attempt_id
                || start.launch_token_digest != a.launch_token_digest
                || start.unit_name != a.unit_name
                || start.invocation_id.is_empty()
            {
                return Err(error("runner start identity mismatch"));
            }
            let properties = super::platform::systemctl_show(&a.unit_name)?;
            if super::platform::unit_is_active(&properties)
                || super::platform::unit_has_pending_job(&properties)
            {
                return Ok(());
            }
            if super::platform::nonempty_property(&properties, "InvocationID")
                .is_some_and(|v| v != start.invocation_id)
                || super::platform::cgroup_has_processes(&start.control_group)?
            {
                return Err(error("runner process ownership has not converged"));
            }
            if start.runner_executable_digest.as_deref()
                != provider["executionProvider"]["executableDigest"].as_str()
            {
                return Err(error("runner evidence provider mismatch"));
            }
            let mut terminal = super::evidence::prepare_runner_terminal_from_bundle(&a)?;
            if let Some(artifact) = super::evidence::validate_workspace_source_observation_artifact(
                &a,
                plan.workspace_source_digest.as_deref(),
                true,
                super::evidence::SourceObservationRequirement::for_terminal(
                    terminal.state,
                    &terminal.reason_code,
                ),
            )? {
                terminal.artifacts.push(artifact);
            }
            let input = PgTerminalNoArtifacts {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: a.row_version as i64,
                terminal_state: terminal.state.as_db().into(),
                result_digest: terminal.result_digest,
                reason_code: terminal.reason_code,
                exit_code: terminal.exit_code,
                finished_at_ms: terminal.finished_at_ms as i64,
                expected_source_sha256: self.config.source_sha256.clone(),
            };
            let artifacts = terminal
                .artifacts
                .into_iter()
                .map(|v| PgArtifactRegistration {
                    artifact_id: v.artifact_id,
                    kind: v.kind,
                    relative_path: v.relative_path,
                    digest: v.digest,
                    media_type: v.media_type,
                    byte_length: v.byte_length as i64,
                    truncated: v.truncated,
                    created_at_ms: input.finished_at_ms,
                })
                .collect::<Vec<_>>();
            db.commit_terminal_with_artifacts(&input, &artifacts)
                .map_err(pg)?;
            // Reuse Universal Runtime's existing terminal-only systemd cleanup.
            // Preserve the failed Unit/InvocationID until the durable PG
            // terminal+Artifact+reservation transaction has committed.
            super::platform::release_terminal_unit(&a.unit_name);
        } else if !a.state.is_terminal() {
            // The kernel may have terminated the systemd-owned process tree
            // before Runner could write result.json. A missing result file is
            // not evidence that the process is still alive. Observe the exact
            // native Unit and its cgroup instead of inventing PID-tree logic.
            if a.unit_name != format!("ordivon-pg-{}.service", a.attempt_id) {
                return Err(error("Attempt native unit identity mismatch"));
            }
            let properties = super::platform::systemctl_show(&a.unit_name)?;
            if super::platform::unit_is_active(&properties)
                || super::platform::unit_has_pending_job(&properties)
            {
                return Ok(());
            }
            let start_path = path.join("runner-start.json");
            let (runner_start, runner_start_digest): (Option<RunnerStartEvidence>, String) =
                if start_path.exists() {
                    let bytes = fs::read(&start_path).map_err(io)?;
                    let start: RunnerStartEvidence = serde_json::from_slice(&bytes).map_err(io)?;
                    if start.control_group != format!("/system.slice/{}", a.unit_name)
                        || start.job_id != job
                        || start.attempt_id != a.attempt_id
                        || start.launch_token_digest != a.launch_token_digest
                        || start.unit_name != a.unit_name
                        || start.invocation_id.is_empty()
                    {
                        return Err(error("Runner identity mismatch during native cancellation"));
                    }
                    if super::platform::nonempty_property(&properties, "InvocationID")
                        .is_some_and(|observed| observed != start.invocation_id)
                    {
                        return Err(error("Native Unit invocation changed during cancellation"));
                    }
                    (Some(start), universal::sha256_bytes(&bytes))
                } else {
                    // A transient Unit can be absent while systemd-run has not
                    // finished dispatch. Without a bound Runner start, its
                    // absence cannot fence a late physical launch.
                    return Ok(());
                };
            let observed_cgroup = super::platform::nonempty_property(&properties, "ControlGroup");
            let cgroup = runner_start
                .as_ref()
                .map(|start| start.control_group.as_str())
                .or(observed_cgroup.as_deref());
            let Some(cgroup) = cgroup else {
                return Ok(());
            };
            let population = super::platform::cgroup_population(cgroup)?;
            let removed = population == super::platform::CgroupPopulation::Removed;
            if !matches!(
                properties.get("ActiveState").map(String::as_str),
                Some("inactive" | "failed")
            ) || !matches!(
                properties.get("LoadState").map(String::as_str),
                Some("loaded" | "not-found")
            ) || runner_start
                .as_ref()
                .and_then(|start| start.runner_executable_digest.as_deref())
                != provider["executionProvider"]["executableDigest"].as_str()
            {
                return Ok(());
            }
            // CollectMode=inactive retains a *failed* transient even after
            // systemd has killed its cgroup. Do not reset-failed first: its
            // invocation identity is valuable evidence until PG commits LOST.
            // Only the exact Runner start + same systemd InvocationID + no
            // MainPID can authorize the failed/removed classification.
            let bound_failed_unit = runner_start.as_ref().is_some_and(|start| {
                super::native_stop::failed_unit_matches_runner(
                    properties.get("LoadState").map(String::as_str),
                    properties.get("ActiveState").map(String::as_str),
                    properties.get("InvocationID").map(String::as_str),
                    &start.invocation_id,
                    properties.get("MainPID").map(String::as_str),
                )
            });
            if super::native_stop::decide_native_stop(
                super::platform::unit_is_active(&properties),
                super::platform::unit_has_pending_job(&properties),
                properties
                    .get("LoadState")
                    .is_some_and(|state| state == "not-found"),
                bound_failed_unit,
                runner_start.is_some(),
                population,
            ) != super::native_stop::NativeStopDecision::CommitLost
            {
                return Ok(());
            }
            // A failed-but-retained Unit can be queried again while the cgroup
            // is gone. Confirm it still owns the same invocation and is still
            // failed, not a different process launched under the same name.
            if bound_failed_unit {
                let recheck = super::platform::systemctl_show(&a.unit_name)?;
                if !super::native_stop::failed_unit_matches_runner(
                    recheck.get("LoadState").map(String::as_str),
                    recheck.get("ActiveState").map(String::as_str),
                    recheck.get("InvocationID").map(String::as_str),
                    runner_start
                        .as_ref()
                        .map(|start| start.invocation_id.as_str())
                        .unwrap_or(""),
                    recheck.get("MainPID").map(String::as_str),
                ) || super::platform::unit_has_pending_job(&recheck)
                    || super::platform::cgroup_population(cgroup)?
                        != super::platform::CgroupPopulation::Removed
                {
                    return Ok(());
                }
            }
            // Kernel cgroup quiescence proves the bound process tree is gone.
            // Without a Runner result the execution outcome remains LOST,
            // not a fabricated successful cancellation or external effect.
            let (terminal_state, reason_code) =
                ("lost", "NATIVE_CGROUP_QUIESCENT_NO_TERMINAL_RESULT");
            let native_receipt = json!({
                "schemaVersion": 1,
                "jobId": job,
                "attemptId": a.attempt_id,
                "unitName": a.unit_name,
                "activeState": properties.get("ActiveState"),
                "loadState": properties.get("LoadState"),
                "controlGroup": cgroup,
                "runnerStartObserved": runner_start.is_some(),
                "runnerStartDigest": runner_start_digest,
                "nativeCgroupState": population.as_str(),
                "failedUnitInvocationBound": bound_failed_unit,
                "nativeUnitResult": properties.get("Result"),
                "kernelCgroupPopulated": population.observed_population(),
                "kernelCgroupRemoved": removed,
                "finishedAtMs": now()?,
                "terminalState": terminal_state
            });
            let proposed_bytes = serde_json::to_vec(&native_receipt).map_err(io)?;
            let receipt_path = path.join("native-stop-evidence.json");
            let receipt_lock = fs::OpenOptions::new()
                .create(true)
                .truncate(false)
                .write(true)
                .open(path.join("native-stop-evidence.lock"))
                .map_err(io)?;
            // Rust std locks this File as flock(LOCK_EX) on Unix and
            // LockFileEx on Windows. Keep the exclusive guard alive until
            // the native receipt and PG terminal+Artifact CAS are resolved.
            // The lock is relinquished automatically when File is dropped.
            receipt_lock.lock().map_err(io)?;
            // A result that arrived while systemctl/cgroup was being queried
            // must take the existing digest/identity-verified result path on
            // the *next* reconciliation. Do not commit an irreversible LOST
            // terminal when that stronger Runner receipt is now available.
            // At this point the bound native cgroup is already quiescent, so
            // the Runner cannot subsequently publish this file from the
            // same owned process tree.
            if !runner_result_still_absent(&path)? {
                return Ok(());
            }
            let receipt_bytes = if receipt_path.exists() {
                // A PG COMMIT acknowledgement can be lost after immutable
                // native evidence was written. Native Unit LoadState may
                // subsequently change from inactive to not-found: do not
                // re-author the original evidence or make a retry impossible.
                // Recheck kernel quiescence above and then replay the original
                // receipt only for the same exact Attempt/Runner identity.
                let retained = fs::read(&receipt_path).map_err(io)?;
                let prior: serde_json::Value = serde_json::from_slice(&retained).map_err(io)?;
                if prior["schemaVersion"].as_u64() != Some(1)
                    || prior["jobId"].as_str() != Some(job)
                    || prior["attemptId"].as_str() != Some(a.attempt_id.as_str())
                    || prior["unitName"].as_str() != Some(a.unit_name.as_str())
                    || prior["controlGroup"].as_str() != Some(cgroup)
                    || prior["runnerStartDigest"].as_str() != Some(runner_start_digest.as_str())
                    || prior["runnerStartObserved"].as_bool() != Some(true)
                    || !matches!(
                        prior["nativeCgroupState"].as_str(),
                        Some("unpopulated" | "removed")
                    )
                    || prior["terminalState"].as_str() != Some(terminal_state)
                {
                    return Err(error("native stop evidence identity mismatch"));
                }
                retained
            } else {
                universal::write_bytes_atomic(&receipt_path, &proposed_bytes).map_err(io)?;
                proposed_bytes
            };
            let receipt_digest = universal::sha256_bytes(&receipt_bytes);
            let retained: serde_json::Value = serde_json::from_slice(&receipt_bytes).map_err(io)?;
            let finished_at_ms = retained["finishedAtMs"]
                .as_i64()
                .ok_or_else(|| error("native stop receipt omitted finish time"))?;
            let terminal = PgTerminalNoArtifacts {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: a.row_version as i64,
                terminal_state: terminal_state.to_string(),
                result_digest: receipt_digest.clone(),
                reason_code: reason_code.to_string(),
                exit_code: None,
                finished_at_ms,
                expected_source_sha256: self.config.source_sha256.clone(),
            };
            let artifact = PgArtifactRegistration {
                artifact_id: format!("artifact-{}-native-stop", a.attempt_id),
                kind: "native_stop_evidence".to_string(),
                relative_path: "native-stop-evidence.json".to_string(),
                digest: receipt_digest,
                media_type: "application/json".to_string(),
                byte_length: i64::try_from(receipt_bytes.len()).map_err(io)?,
                truncated: false,
                created_at_ms: finished_at_ms,
            };
            // Reuse the existing PG atomic terminal/reservation/Artifact
            // transaction. Kernel process absence is evidence of liveness,
            // not proof of a successful arbitrary external effect.
            db.commit_terminal_with_artifacts(&terminal, &[artifact])
                .map_err(pg)?;
            // Only now may systemd forget a failed transient. This ordering
            // keeps its positive failure/InvocationID evidence available for
            // the irreversible LOST decision and its durable receipt.
            super::platform::release_terminal_unit(&a.unit_name);
        }
        Ok(())
    }
}
