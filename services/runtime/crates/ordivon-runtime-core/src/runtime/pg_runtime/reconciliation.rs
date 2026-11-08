//! PostgreSQL Attempt readback, native reconciliation, and Job result projection.
use super::*;

impl PgRuntime {
    /// Service-owned recovery path. Does not admit commands or consume Job capacity.
    /// Each cancellation retains its original principal and exact durable Job identity.
    pub fn reconcile_cancelled_jobs(&self, limit: u32) -> RuntimeResult<serde_json::Value> {
        if limit == 0 || limit > 100 {
            return Err(RuntimeError::invalid("limit must be 1..100", "limit"));
        }
        let mut db = self.store()?;
        let pending = db.client.query(
            "SELECT job_id,principal FROM jobs WHERE desired_state='cancelled' AND resolution IS NULL ORDER BY created_at_ms,job_id LIMIT $1",
            &[&i64::from(limit)],
        ).map_err(io)?;
        drop(db);
        let mut terminal = 0_u32;
        let mut errors = 0_u32;
        for row in &pending {
            let request = JobCancelRequest {
                schema_version: 1,
                job_id: row.get(0),
            };
            match self.cancel(&row.get::<_, String>(1), &request) {
                Ok(value) if value.execution_terminal => terminal += 1,
                Ok(_) => (),
                Err(_) => errors += 1,
            }
        }
        Ok(json!({"inspected":pending.len(),"terminal":terminal,"errors":errors}))
    }
    pub(super) fn attempt(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<(AttemptRecord, RuntimeExecutionPlan, String)> {
        let r=db.client.query_one("SELECT a.attempt_id,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.unit_name,a.created_at_ms,a.row_version,a.bundle_digest,j.execution_plan_json,j.operation_digest FROM attempts a JOIN jobs j ON j.job_id=a.job_id WHERE j.job_id=$1 ORDER BY a.attempt_number DESC LIMIT 1", &[&job]).map_err(io)?;
        let a:AttemptRecord=serde_json::from_value(json!({"attemptId":r.get::<_,String>(0),"jobId":job,"attemptNumber":1,"state":r.get::<_,String>(1),"terminationIntent":r.get::<_,String>(2),"launchTokenDigest":r.get::<_,String>(3),"bundlePath":r.get::<_,String>(4),"unitName":r.get::<_,String>(5),"createdAtMs":r.get::<_,i64>(6),"rowVersion":r.get::<_,i64>(7),"bundleDigest":r.get::<_,Option<String>>(8)})).map_err(io)?;
        let expected = self
            .config
            .executor
            .store_root
            .join("pg-attempts")
            .join(&a.attempt_id);
        if Path::new(&a.bundle_path) != expected {
            return Err(error("Attempt bundle outside PG store"));
        }
        Ok((a, decode(&r.get::<_, String>(9))?, r.get(10)))
    }
    pub(super) fn reconcile(&self, db: &mut PgAdmissionStore, job: &str) -> RuntimeResult<()> {
        let (mut a, plan, operation) = self.attempt(db, job)?;
        let provider: serde_json::Value = decode(
            &db.client
                .query_one(
                    "SELECT workspace_snapshot_json FROM jobs WHERE job_id=$1",
                    &[&job],
                )
                .map_err(io)?
                .get::<_, String>(0),
        )?;
        if a.state == AttemptState::Accepted
            && a.termination_intent == AttemptTerminationIntent::Natural
        {
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
                return Err(error("native runner changed after admission"));
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
            let req = RunnerRequest {
                schema_version: 1,
                job_id: Some(job.into()),
                attempt_id: Some(a.attempt_id.clone()),
                launch_token: Some(token),
                unit_name: Some(a.unit_name.clone()),
                payload: None,
                inherit_host_environment: true,
                task_id: a.attempt_id.clone(),
                workspace_id: plan.workspace_id.clone(),
                workspace_path: plan.workspace_path.clone(),
                workspace_source_digest: plan.workspace_source_digest.clone(),
                build_target_backing: None,
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
            fs::create_dir_all(&a.bundle_path).map_err(io)?;
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
            db.mark_dispatch_issued_pg(&PgDispatchIssued {
                attempt_id: a.attempt_id.clone(),
                expected_row_version: a.row_version as i64,
                expected_bundle_digest: digest,
                observed_at_ms: now()?,
                expected_source_sha256: self.config.source_sha256.clone(),
            })
            .map_err(pg)?;
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
                workspace_git_common_dir: None,
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
        }
        let path = Path::new(&a.bundle_path);
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
        } else if !a.state.is_terminal()
            && a.termination_intent == AttemptTerminationIntent::StopRequested
        {
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
            let removed = population.is_none() && super::platform::cgroup_removed(cgroup)?;
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
            if super::native_stop::decide_native_stop(
                super::platform::unit_is_active(&properties),
                super::platform::unit_has_pending_job(&properties),
                runner_start.is_some(),
                population,
                removed,
            ) != super::native_stop::NativeStopDecision::CommitLost
            {
                return Ok(());
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
                "kernelCgroupPopulated": population,
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
            use std::os::fd::AsRawFd;
            // SAFETY: the open File owns a valid descriptor; the lock is released on drop.
            if unsafe { libc::flock(receipt_lock.as_raw_fd(), libc::LOCK_EX) } != 0 {
                return Err(io(std::io::Error::last_os_error()));
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
                    || !(prior["kernelCgroupPopulated"].as_bool() == Some(false)
                        || (prior["kernelCgroupPopulated"].is_null()
                            && prior["kernelCgroupRemoved"].as_bool() == Some(true)))
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
        }
        Ok(())
    }
    pub(super) fn project(
        &self,
        db: &mut PgAdmissionStore,
        request: &JobObserveRequest,
    ) -> RuntimeResult<JobObservation> {
        let snapshot = match db
            .observe_job_readonly(&request.job_id, &self.config.source_sha256)
            .map_err(pg)?
        {
            PgJobReadback::Observed(s) => s,
            _ => return Err(error("inconclusive PG lifecycle")),
        };
        let (a, p, operation) = self.attempt(db, &request.job_id)?;
        let terminal = snapshot.resolution.is_some();
        let rows=db.client.query("SELECT artifact_id,kind,digest,byte_length,truncated,relative_path FROM artifacts WHERE job_id=$1 ORDER BY artifact_id", &[&request.job_id]).map_err(io)?;
        let artifacts=rows.iter().map(|r|json!({"artifactId":r.get::<_,String>(0),"attemptId":a.attempt_id,"kind":r.get::<_,String>(1),"digest":r.get::<_,String>(2),"retainedBytes":r.get::<_,i64>(3),"truncated":r.get::<_,bool>(4)})).collect::<Vec<_>>();
        let exit: Option<i32> = db
            .client
            .query_one(
                "SELECT exit_code FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .map_err(io)?
            .get(0);
        // Preserve the existing projection for historical terminal variants.
        // An OS-only LOST reconciliation is the new explicit exception:
        // it has a committed native-stop Artifact, not a Runner result.json.
        let native_stop_only = rows
            .iter()
            .any(|row| row.get::<_, String>(1) == "native_stop_evidence");
        let result_available = terminal && !native_stop_only;
        let mut value = json!({"jobId":request.job_id,"operationDigest":operation,"status":snapshot.resolution.clone().unwrap_or(snapshot.attempt_state.clone()),"desiredState":snapshot.desired_state,"attemptId":a.attempt_id,"attemptState":snapshot.attempt_state,"terminationIntent":snapshot.termination_intent,"exitCode":exit,"executionTerminal":terminal,"executionDisposition":snapshot.resolution,"deliveryDisposition":if terminal {"committed"} else {"in_progress"},"effectiveLimits":{"timeoutMs":p.timeout_ms,"stdoutLimitBytes":p.stdout_limit_bytes,"stderrLimitBytes":p.stderr_limit_bytes},"recoveryRequired":!terminal && a.state==AttemptState::Starting,"semanticCompletionEvaluated":false,"resultAvailable":result_available,"artifactsAvailable":!artifacts.is_empty(),"artifacts":artifacts});
        for (kind, limit, offset) in [
            ("stdout", request.stdout_tail_bytes, request.stdout_offset),
            ("stderr", request.stderr_tail_bytes, request.stderr_offset),
        ] {
            // Lost/orphaned or other no-Artifact terminal outcomes have no
            // committed stream bytes. Do not fail observation merely because
            // a log is absent, and never project unregistered terminal bytes.
            if terminal && !rows.iter().any(|row| row.get::<_, String>(1) == kind) {
                continue;
            }
            let path = Path::new(&a.bundle_path).join(format!("{kind}.log"));
            if path.exists() {
                let bytes = {
                    use std::io::Read;
                    let file = fs::File::open(path).map_err(io)?;
                    let mut bytes = vec![];
                    file.take(self.config.executor.max_output_bytes + 1)
                        .read_to_end(&mut bytes)
                        .map_err(io)?;
                    if bytes.len() as u64 > self.config.executor.max_output_bytes {
                        return Err(error("output exceeds retained ceiling"));
                    }
                    bytes
                };
                let begin = offset
                    .unwrap_or((bytes.len() as u64).saturating_sub(limit))
                    .min(bytes.len() as u64) as usize;
                let end = (begin as u64 + limit).min(bytes.len() as u64) as usize;
                if terminal {
                    // Terminal stdout/stderr are registered evidence, not a
                    // mutable preview. Reuse the same PostgreSQL digest/size
                    // commitment enforced by artifact.read, on the very bytes
                    // returned to the Agent.
                    let expected = rows
                        .iter()
                        .find(|row| row.get::<_, String>(1) == kind)
                        .ok_or_else(|| error("terminal output Artifact registration missing"))?;
                    if expected.get::<_, String>(5) != format!("{kind}.log")
                        || expected.get::<_, i64>(3) != bytes.len() as i64
                        || expected.get::<_, String>(2) != universal::sha256_bytes(&bytes)
                    {
                        return Err(RuntimeError::new(
                            RuntimeErrorCode::ArtifactIdentityConflict,
                            "terminal output bytes disagree with PostgreSQL Artifact evidence",
                            Some("artifact"),
                            false,
                        ));
                    }
                }
                value[format!("{kind}Tail")] = json!(String::from_utf8_lossy(&bytes[begin..end]));
                value[format!("{kind}Offset")] = json!(begin);
                value[format!("{kind}NextOffset")] = json!(end);
                value[format!("{kind}AvailableBytes")] = json!(bytes.len());
                value[format!("{kind}Eof")] = json!(end == bytes.len());
            } else if terminal {
                return Err(error("terminal output Artifact file missing"));
            }
        }
        serde_json::from_value(value).map_err(io)
    }
}
