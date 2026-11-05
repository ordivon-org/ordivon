impl Runtime {
    fn ensure_newly_admitted_job_dispatched(&self, job_id: &str) -> RuntimeResult<()> {
        let attempt = self.registry.get_latest_attempt(job_id)?.ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "newly admitted Job has no Attempt",
                Some("jobId"),
                false,
            )
        })?;
        if attempt.state == AttemptState::Accepted {
            self.ensure_attempt_dispatched(&attempt)
                .map_err(|error| error.with_operation_id(job_id.to_string()))?;
        }
        Ok(())
    }

    fn ensure_attempt_dispatched(&self, attempt: &AttemptRecord) -> RuntimeResult<()> {
        if let Err(error) = self.verify_committed_execution_provider(&attempt.job_id) {
            if error.code == RuntimeErrorCode::ProviderStateMismatch {
                self.commit_control_terminal(
                    attempt,
                    AttemptState::Failed,
                    "EXECUTION_PROVIDER_PRECONDITION_DRIFT",
                    Some(error.to_string()),
                )?;
                return Ok(());
            }
            return Err(error);
        }
        if let Err(error) = self.verify_committed_host_dependencies(&attempt.job_id) {
            if matches!(
                error.code,
                RuntimeErrorCode::WorkspaceStateMismatch | RuntimeErrorCode::InvalidRequest
            ) {
                self.commit_control_terminal(
                    attempt,
                    AttemptState::Failed,
                    "HOST_DEPENDENCY_PRECONDITION_DRIFT",
                    Some(error.to_string()),
                )?;
                return Ok(());
            }
            return Err(error);
        }
        if let Err(error) = self.ensure_job_input_ownership(&attempt.job_id) {
            if matches!(
                error.code,
                RuntimeErrorCode::ReconciliationRequired | RuntimeErrorCode::WorkspaceStateMismatch
            ) {
                self.commit_control_terminal(
                    attempt,
                    AttemptState::Failed,
                    "INPUT_PRECONDITION_DRIFT",
                    Some(error.to_string()),
                )?;
                return Ok(());
            }
            return Err(error);
        }
        let mut attempt = attempt.clone();
        if attempt.bundle_digest.is_none() {
            attempt = match self.materialize_bundle(&attempt) {
                Ok(current) => current,
                Err(error) if error.code == RuntimeErrorCode::AttemptStateConflict => {
                    let current = self.registry.get_attempt(&attempt.attempt_id)?;
                    if current.bundle_digest.is_none() && current.state == AttemptState::Accepted {
                        self.materialize_bundle(&current)?
                    } else {
                        current
                    }
                }
                Err(error) => return Err(error),
            };
        }
        match attempt.state {
            AttemptState::Accepted => match self.dispatch_attempt(&attempt) {
                Ok(()) => Ok(()),
                Err(error) if error.code == RuntimeErrorCode::AttemptStateConflict => {
                    let current = self.registry.get_attempt(&attempt.attempt_id)?;
                    match current.state {
                        AttemptState::Starting
                        | AttemptState::Running
                        | AttemptState::Stopping
                        | AttemptState::Recovering => self.reconcile_attempt(&current.attempt_id),
                        state if state.is_terminal() => Ok(()),
                        _ => Err(error),
                    }
                }
                Err(error) => Err(error),
            },
            AttemptState::Starting
            | AttemptState::Running
            | AttemptState::Stopping
            | AttemptState::Recovering => {
                self.reconcile_attempt(&attempt.attempt_id)?;
                Ok(())
            }
            _ => Ok(()),
        }
    }

    fn inherit_host_environment(&self) -> bool {
        false
    }

    #[cfg(unix)]
    fn ensure_trusted_workspace_tmp_presentation(
        &self,
        workspace_id: &str,
    ) -> RuntimeResult<PathBuf> {
        let presentation = self
            .executor
            .workspace_tmp_presentation_path(workspace_id)
            .map_err(map_universal_error)?;
        let canonical_backing = self
            .executor
            .canonical_workspace_tmp_path(workspace_id)
            .map_err(map_universal_error)?;
        let parent = presentation.parent().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::IoError,
                "trusted temporary presentation has no parent directory",
                Some("workspaceId"),
                false,
            )
        })?;
        for _ in 0..2 {
            match fs::symlink_metadata(parent) {
                Ok(metadata) => {
                    let mode = metadata.mode() & 0o777;
                    let owner = metadata.uid();
                    let effective_uid = unsafe { libc::geteuid() };
                    if metadata.file_type().is_symlink()
                        || !metadata.is_dir()
                        || owner != effective_uid
                        || mode != 0o700
                    {
                        return Err(RuntimeError::new(
                            RuntimeErrorCode::WorkspaceStateMismatch,
                            format!(
                                "trusted temporary presentation root {} must be a non-symlink directory owned by uid {} with mode 0700; observed uid {} mode {:04o}",
                                parent.display(), effective_uid, owner, mode
                            ),
                            Some("workspaceId"),
                            false,
                        ));
                    }
                    break;
                }
                Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                    let mut builder = fs::DirBuilder::new();
                    builder.mode(0o700);
                    match builder.create(parent) {
                        Ok(()) => continue,
                        Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => continue,
                        Err(error) => {
                            return Err(io_error(
                                &format!("create temporary presentation root {}", parent.display()),
                                error,
                            ));
                        }
                    }
                }
                Err(error) => {
                    return Err(io_error(
                        &format!("inspect temporary presentation root {}", parent.display()),
                        error,
                    ));
                }
            }
        }

        for _ in 0..2 {
            match fs::symlink_metadata(&presentation) {
                Ok(metadata) => {
                    if !metadata.file_type().is_symlink() {
                        return Err(RuntimeError::new(
                            RuntimeErrorCode::WorkspaceStateMismatch,
                            format!(
                                "trusted temporary presentation {} is not a symlink",
                                presentation.display()
                            ),
                            Some("workspaceId"),
                            false,
                        ));
                    }
                    let target = fs::read_link(&presentation).map_err(|error| {
                        io_error(
                            &format!("read temporary presentation {}", presentation.display()),
                            error,
                        )
                    })?;
                    if target != canonical_backing {
                        return Err(RuntimeError::new(
                            RuntimeErrorCode::WorkspaceStateMismatch,
                            format!(
                                "trusted temporary presentation {} points at {}, expected {}",
                                presentation.display(),
                                target.display(),
                                canonical_backing.display()
                            ),
                            Some("workspaceId"),
                            false,
                        ));
                    }
                    return Ok(presentation);
                }
                Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                    match std::os::unix::fs::symlink(&canonical_backing, &presentation) {
                        Ok(()) => return Ok(presentation),
                        Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {
                            continue;
                        }
                        Err(error) => {
                            return Err(io_error(
                                &format!(
                                    "create temporary presentation {}",
                                    presentation.display()
                                ),
                                error,
                            ));
                        }
                    }
                }
                Err(error) => {
                    return Err(io_error(
                        &format!("inspect temporary presentation {}", presentation.display()),
                        error,
                    ));
                }
            }
        }
        Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "trusted temporary presentation changed concurrently during creation",
            Some("workspaceId"),
            true,
        ))
    }

    #[cfg(not(unix))]
    fn ensure_trusted_workspace_tmp_presentation(
        &self,
        _workspace_id: &str,
    ) -> RuntimeResult<PathBuf> {
        Err(RuntimeError::new(
            RuntimeErrorCode::ToolUnavailable,
            "trusted-local temporary presentation requires a native platform implementation",
            Some("workspaceId"),
            false,
        ))
    }

    fn execution_environment(
        &self,
        record: &crate::universal::WorkspaceRecord,
        execution_profile: super::ExecutionProfile,
    ) -> RuntimeResult<BTreeMap<String, String>> {
        let workspace_cache = self.executor.workspace_cache_path(&record.workspace_id);
        let workspace_tmp = self.executor.workspace_tmp_path(&record.workspace_id);
        let build_cache = self
            .executor
            .workspace_build_cache_path(&record.workspace_id);
        let package_cache = match execution_profile {
            super::ExecutionProfile::TrustedLocal => self.executor.shared_caches_root(),
            super::ExecutionProfile::ContainedLocal => workspace_cache.join("tooling"),
        };
        let cargo_target_backing = build_cache.join("cargo");
        for path in [
            &workspace_cache,
            &build_cache,
            &cargo_target_backing,
            &workspace_tmp,
            &package_cache,
        ] {
            fs::create_dir_all(path).map_err(|error| {
                io_error(&format!("create execution cache {}", path.display()), error)
            })?;
        }
        let mut environment = BTreeMap::new();
        environment.insert("PATH".to_string(), self.execution_path.clone());
        let execution_home = match execution_profile {
            crate::runtime::ExecutionProfile::TrustedLocal => self.execution_home.clone(),
            super::ExecutionProfile::ContainedLocal => {
                let contained_home = workspace_cache.join("home");
                fs::create_dir_all(&contained_home).map_err(|error| {
                    io_error(
                        &format!(
                            "create contained execution home {}",
                            contained_home.display()
                        ),
                        error,
                    )
                })?;
                contained_home.to_string_lossy().into_owned()
            }
        };
        environment.insert("HOME".to_string(), execution_home);
        environment.insert("LANG".to_string(), "C.UTF-8".to_string());
        environment.insert("LC_ALL".to_string(), "C.UTF-8".to_string());
        let tmp_presentation = match execution_profile {
            super::ExecutionProfile::TrustedLocal => {
                self.ensure_trusted_workspace_tmp_presentation(&record.workspace_id)?
            }
            super::ExecutionProfile::ContainedLocal => workspace_tmp.clone(),
        };
        environment.insert(
            "TMPDIR".to_string(),
            tmp_presentation.to_string_lossy().into_owned(),
        );
        environment.insert(
            "XDG_CACHE_HOME".to_string(),
            workspace_cache.to_string_lossy().into_owned(),
        );
        let cargo_target = match execution_profile {
            super::ExecutionProfile::TrustedLocal => {
                PathBuf::from(TRUSTED_BUILD_TARGET_PRESENTATION)
            }
            super::ExecutionProfile::ContainedLocal => cargo_target_backing,
        };
        for (name, path) in [
            ("CARGO_TARGET_DIR", cargo_target),
            ("UV_CACHE_DIR", package_cache.join("uv")),
            ("PIP_CACHE_DIR", package_cache.join("pip")),
            ("npm_config_cache", package_cache.join("npm")),
            ("PNPM_HOME", package_cache.join("pnpm")),
            ("COREPACK_HOME", package_cache.join("corepack")),
            (
                "BUN_INSTALL_CACHE_DIR",
                package_cache.join("bun/install-cache"),
            ),
            ("GOMODCACHE", package_cache.join("go/mod")),
            ("GOCACHE", package_cache.join("go/build")),
        ] {
            environment.insert(name.to_string(), path.to_string_lossy().into_owned());
        }
        for name in [
            "HOME",
            "TMPDIR",
            "XDG_CACHE_HOME",
            "CARGO_TARGET_DIR",
            "UV_CACHE_DIR",
            "PIP_CACHE_DIR",
            "npm_config_cache",
            "PNPM_HOME",
            "COREPACK_HOME",
            "BUN_INSTALL_CACHE_DIR",
            "GOMODCACHE",
            "GOCACHE",
        ] {
            if name == "CARGO_TARGET_DIR"
                && environment.get(name).map(String::as_str)
                    == Some(TRUSTED_BUILD_TARGET_PRESENTATION)
            {
                continue;
            }
            let path = Path::new(environment.get(name).expect("execution path is present"));
            fs::create_dir_all(path).map_err(|error| {
                io_error(
                    &format!("create execution environment path {}", path.display()),
                    error,
                )
            })?;
        }
        Ok(environment)
    }

    fn materialize_bundle(&self, attempt: &AttemptRecord) -> RuntimeResult<AttemptRecord> {
        if attempt.state != AttemptState::Accepted {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AttemptStateConflict,
                "only accepted Attempts may materialize a bundle",
                Some("attemptId"),
                false,
            ));
        }
        let snapshot = self.registry.job_snapshot(&attempt.job_id)?;
        let job = snapshot.job;
        let stored_attempt = snapshot.attempt.ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "Job has no Attempt while materializing bundle",
                Some("attemptId"),
                false,
            )
        })?;
        if stored_attempt.attempt_id != attempt.attempt_id
            || stored_attempt.row_version != attempt.row_version
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AttemptStateConflict,
                "Attempt changed before bundle materialization",
                Some("attemptId"),
                false,
            ));
        }
        let plan: RuntimeExecutionPlan =
            serde_json::from_str(&job.execution_plan_json).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    format!("stored execution plan is invalid: {error}"),
                    Some("executionPlan"),
                    false,
                )
            })?;
        let launch_token = sha256_bytes(
            format!(
                "runtime-launch-v1\0{}\0{}",
                attempt.attempt_id, job.operation_digest
            )
            .as_bytes(),
        );
        if sha256_bytes(launch_token.as_bytes()) != attempt.launch_token_digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "stored launch-token digest is inconsistent",
                Some("launchTokenDigest"),
                false,
            ));
        }
        let request = RunnerRequest {
            schema_version: UNIVERSAL_EXEC_SCHEMA_VERSION,
            job_id: Some(job.job_id.clone()),
            attempt_id: Some(attempt.attempt_id.clone()),
            launch_token: Some(launch_token.clone()),
            unit_name: Some(attempt.unit_name.clone()),
            payload: self.payload_config(&attempt.attempt_id, &plan)?,
            inherit_host_environment: self.inherit_host_environment(),
            task_id: attempt.attempt_id.clone(),
            workspace_id: plan.workspace_id.clone(),
            workspace_path: plan.workspace_path.clone(),
            workspace_source_digest: plan.workspace_source_digest.clone(),
            build_target_backing: if plan.execution_target == super::ExecutionTarget::LocalLinux
                && plan.execution_profile == super::ExecutionProfile::TrustedLocal
                && (plan.env.get("CARGO_TARGET_DIR").map(String::as_str)
                    == Some(TRUSTED_BUILD_TARGET_PRESENTATION)
                    || plan.steps.iter().any(|step| {
                        step.env.get("CARGO_TARGET_DIR").map(String::as_str)
                            == Some(TRUSTED_BUILD_TARGET_PRESENTATION)
                    })) {
                Some(
                    self.executor
                        .workspace_build_cache_path(&plan.workspace_id)
                        .join("cargo")
                        .to_string_lossy()
                        .into_owned(),
                )
            } else {
                None
            },
            input_presentation_root: if plan.execution_target == super::ExecutionTarget::LocalLinux
                && !plan.effective_inputs.is_empty()
            {
                Some(CONTAINED_INPUT_ROOT.to_string())
            } else {
                None
            },
            input_commitments: if plan.execution_target == super::ExecutionTarget::LocalLinux {
                plan.effective_inputs
                    .iter()
                    .map(|input| RunnerInputCommitment {
                        presentation_path: Path::new(CONTAINED_INPUT_ROOT)
                            .join(&input.presentation_relative_path)
                            .to_string_lossy()
                            .into_owned(),
                        digest: input.digest.clone(),
                        byte_length: input.byte_length,
                    })
                    .collect()
            } else {
                Vec::new()
            },
            host_dependencies: self
                .registry
                .host_dependencies(&attempt.job_id)?
                .into_iter()
                .map(|dependency| RunnerHostDependencyCommitment {
                    path: dependency.path,
                    digest: dependency.expected_digest,
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
                .map(|step| RunnerExecutionStep {
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
        let request_bytes = serde_json::to_vec(&request).map_err(serialization_error)?;
        let plan_bytes = serde_json::to_vec(&plan).map_err(serialization_error)?;
        let manifest = BundleManifest {
            schema_version: RUNTIME_SCHEMA_VERSION,
            job_id: job.job_id.clone(),
            attempt_id: attempt.attempt_id.clone(),
            request_digest: sha256_bytes(&request_bytes),
            plan_digest: sha256_bytes(&plan_bytes),
            launch_token_digest: sha256_bytes(launch_token.as_bytes()),
            created_at_ms: attempt.created_at_ms,
        };
        let manifest_bytes = serde_json::to_vec(&manifest).map_err(serialization_error)?;
        let bundle_digest = sha256_bytes(&manifest_bytes);
        if manifest.launch_token_digest != attempt.launch_token_digest
            || manifest.plan_digest != job.execution_plan_digest
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "reconstructed bundle identity does not match Registry",
                Some("attemptId"),
                false,
            ));
        }

        let final_path = PathBuf::from(&attempt.bundle_path);
        let parent = final_path.parent().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::IoError,
                "Attempt bundle has no parent directory",
                Some("bundlePath"),
                false,
            )
        })?;
        fs::create_dir_all(parent).map_err(|error| io_error("create attempts root", error))?;
        if final_path.exists() {
            verify_published_bundle(&final_path, &request_bytes, &plan_bytes, &manifest_bytes)?;
        } else {
            let staging = parent.join(format!(
                ".{}.staging-{}",
                attempt.attempt_id,
                Uuid::now_v7()
            ));
            fs::create_dir(&staging).map_err(|error| io_error("create staging bundle", error))?;
            let publish = (|| {
                protect_posix_path(&staging, 0o700, "protect staging bundle")?;
                write_bytes_synced(&staging.join(RUNNER_REQUEST_FILE), &request_bytes)?;
                write_bytes_synced(&staging.join(PLAN_FILE), &plan_bytes)?;
                write_bytes_synced(&staging.join(BUNDLE_MANIFEST_FILE), &manifest_bytes)?;
                sync_directory(&staging)?;
                match durable_runtime_rename(
                    &staging,
                    &final_path,
                    false,
                    "commit Attempt bundle",
                ) {
                    Ok(()) => {}
                    Err(error) if final_path.is_dir() => {
                        let _ = error;
                        fs::remove_dir_all(&staging).map_err(|cleanup_error| {
                            io_error("remove losing bundle staging directory", cleanup_error)
                        })?;
                    }
                    Err(error) => return Err(error),
                }
                verify_published_bundle(&final_path, &request_bytes, &plan_bytes, &manifest_bytes)
            })();
            if publish.is_err() {
                let _ = fs::remove_dir_all(&staging);
            }
            publish?;
        }
        match self.registry.mark_bundle_ready(
            &attempt.attempt_id,
            attempt.row_version,
            &bundle_digest,
            now_ms()?,
        ) {
            Ok(current) => Ok(current),
            Err(error) if error.code == RuntimeErrorCode::AttemptStateConflict => {
                let current = self.registry.get_attempt(&attempt.attempt_id)?;
                if current.bundle_digest.as_deref() == Some(bundle_digest.as_str()) {
                    Ok(current)
                } else {
                    Err(error)
                }
            }
            Err(error) => Err(error),
        }
    }

    fn dispatch_attempt(&self, attempt: &AttemptRecord) -> RuntimeResult<()> {
        let starting = self.registry.mark_dispatch_issued(
            &attempt.attempt_id,
            attempt.row_version,
            now_ms()?,
        )?;
        let plan = self.registry.execution_plan(&starting.job_id)?;
        let bundle_path = canonical_directory(Path::new(&starting.bundle_path), "bundlePath")
            .map_err(map_universal_error)?;
        let output = match plan.execution_target {
            super::ExecutionTarget::LocalLinux => {
                let input_set_path = if plan.input_set_id.is_some() {
                    self.ensure_job_input_ownership(&starting.job_id)?;
                    let path = self.executor.job_input_path(&starting.job_id);
                    let requests = effective_input_requests_from_plan(&plan)?;
                    verify_effective_input_set(&path, &requests)?;
                    Some(path)
                } else {
                    None
                };
                let (credential_source_root, credential_names) =
                    if let Some(credential_set_id) = plan.credential_set_id.as_deref() {
                        self.ensure_job_credential_ownership(&starting.job_id)?;
                        let path = self.executor.job_credential_path(&starting.job_id);
                        let names = verify_credential_snapshot(&path, credential_set_id)?;
                        (Some(path), names)
                    } else {
                        (None, Vec::new())
                    };
                LocalLinuxProvider::new(self.node_identity.platform, &self.executor)
                    .realize_prepared(
                        &plan,
                        &starting,
                        LocalLinuxRealizationInputs {
                            bundle_path: &bundle_path,
                            input_set_path: input_set_path.as_deref(),
                            credential_source_root: credential_source_root.as_deref(),
                            credential_names: &credential_names,
                        },
                    )?
            }
            super::ExecutionTarget::WindowsNative => {
                let windows = self.windows.as_ref().ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "committed windows_native Job has no configured Windows provider",
                        Some("executionTarget"),
                        true,
                    )
                })?;
                let input_source_root = if plan.input_set_id.is_some() {
                    self.ensure_job_input_ownership(&starting.job_id)?;
                    let path = self.executor.job_input_path(&starting.job_id);
                    let requests = effective_input_requests_from_plan(&plan)?;
                    verify_effective_input_set(&path, &requests)?;
                    Some(path)
                } else {
                    None
                };
                let input_bindings_digest = if plan.effective_inputs.is_empty() {
                    None
                } else {
                    Some(windows_input_bindings_digest(&plan.effective_inputs))
                };
                let input_presentation_root = if plan.effective_inputs.is_empty() {
                    None
                } else {
                    Some(required_environment_value_case_insensitive(
                        &plan.env,
                        "ORDIVON_INPUT_ROOT",
                        "executionPlan.env",
                    )?)
                };
                let runner_request_digest =
                    sha256_file(&bundle_path.join(RUNNER_REQUEST_FILE)).map_err(map_universal_error)?;
                    let requested_windows_context = plan
                        .windows_context
                        .unwrap_or_else(|| plan.windows_authority.canonical_context());
                    let dispatch = match spawn_windows_native(&WindowsNativeRunSpec {
                        config: windows,
                        bundle_path: &bundle_path,
                        job_id: &starting.job_id,
                        attempt_id: &starting.attempt_id,
                        launch_token_digest: &starting.launch_token_digest,
                        request_digest: &runner_request_digest,
                        authority: plan.windows_authority,
                        payload_privilege: requested_windows_context.privilege,
                        expected_privileged_broker_digest: plan
                            .windows_execution_context
                            .as_ref()
                            .and_then(|context| context.privileged_broker_digest.as_deref()),
                        expected_user_sid: plan
                            .windows_execution_context
                            .as_ref()
                            .filter(|_| requested_windows_context.identity == super::WindowsExecutionIdentity::ActiveUser)
                            .map(|context| context.token_user_sid.as_str()),
                        expected_session_id: plan
                            .windows_execution_context
                            .as_ref()
                            .filter(|_| requested_windows_context.identity == super::WindowsExecutionIdentity::ActiveUser)
                            .and_then(|context| context.session_id),
                        executable: Path::new(&plan.executable),
                        args: &plan.args,
                        cwd: Path::new(&plan.cwd),
                        environment: &plan.env,
                        input_source_root: input_source_root.as_deref(),
                        input_set_id: plan.input_set_id.as_deref(),
                        input_presentation_root,
                        input_bindings_digest: input_bindings_digest.as_deref(),
                        budget: &plan.budget,
                        timeout_ms: plan.timeout_ms,
                        stdout_limit_bytes: plan.stdout_limit_bytes,
                        stderr_limit_bytes: plan.stderr_limit_bytes,
                    }) {
                        Ok(dispatch) => dispatch,
                        Err(error) => {
                            self.commit_control_terminal(
                                &starting,
                                AttemptState::Failed,
                                "RUNNER_START_FAILED",
                                Some(format!(
                                    "native Windows launcher spawn failed: {}",
                                    error.message
                                )),
                            )?;
                            return Ok(());
                        }
                    };
                    let bound =
                        self.bind_native_windows_dispatch_owner(&starting, &dispatch)?;
                    return self.await_launch_evidence(&bound);
            }
        };
        if !output.status.success() {
            let detail = format!(
                "{} launch failed: {}",
                plan.execution_target.as_str(),
                String::from_utf8_lossy(&output.stderr).trim()
            );
            self.commit_control_terminal(
                &starting,
                AttemptState::Failed,
                "RUNNER_START_FAILED",
                Some(detail),
            )?;
            return Ok(());
        }
        self.await_launch_evidence(&starting)
    }

    fn reconcile_runner_result(&self, attempt: &AttemptRecord) -> RuntimeResult<()> {
        match self.commit_runner_result(attempt) {
            Ok(_) => Ok(()),
            Err(error)
                if matches!(
                    error.code,
                    RuntimeErrorCode::RegistryCorrupt
                        | RuntimeErrorCode::ResultIdentityConflict
                        | RuntimeErrorCode::ArtifactIdentityConflict
                        | RuntimeErrorCode::LaunchIdentityMismatch
                ) =>
            {
                self.commit_control_terminal(
                    attempt,
                    AttemptState::Orphaned,
                    "RUNNER_RESULT_QUARANTINED",
                    Some(error.to_string()),
                )?;
                Ok(())
            }
            Err(error) => Err(error),
        }
    }

    fn commit_runner_result(&self, attempt: &AttemptRecord) -> RuntimeResult<JobObservation> {
        let mut current = self.registry.get_attempt(&attempt.attempt_id)?;
        for retry in 0..=1 {
            if current.state == AttemptState::Orphaned
                && self.recover_orphaned_runner_result(&current)?
            {
                return self.observation_from_registry(&current.job_id, 0, 0);
            }
            if current.state.is_terminal() {
                if current.state != AttemptState::Orphaned {
                    self.release_attempt_supervisor(&current)?;
                }
                return self.observation_from_registry(&current.job_id, 0, 0);
            }
            let mut terminal = self.prepare_runner_terminal(&current)?;
            self.append_terminal_evidence(&current, &mut terminal)?;
            match self.registry.commit_terminal(&terminal) {
                Ok(_) => {
                    self.release_attempt_supervisor(&current)?;
                    self.cleanup_payload_view(&current.attempt_id)?;
                    return self.observation_from_registry(&current.job_id, 4096, 4096);
                }
                Err(error)
                    if retry == 0 && error.code == RuntimeErrorCode::AttemptStateConflict =>
                {
                    current = self.registry.get_attempt(&attempt.attempt_id)?;
                }
                Err(error) => return Err(error),
            }
        }
        unreachable!("terminal commit retry loop always returns")
    }

    fn prepare_runner_terminal(&self, current: &AttemptRecord) -> RuntimeResult<TerminalCommit> {
        let mut terminal = prepare_runner_terminal_from_bundle(current)?;
        let plan = self.registry.execution_plan(&current.job_id)?;
        if plan.execution_target == super::ExecutionTarget::WindowsNative {
            let (_, digest) = self.validate_windows_start_evidence(current)?;
            let path = Path::new(&current.bundle_path).join(WINDOWS_START_FILE);
            terminal.artifacts.push(ArtifactRegistration {
                artifact_id: format!("{}.windows-start", current.attempt_id),
                kind: "windows_start".to_string(),
                relative_path: WINDOWS_START_FILE.to_string(),
                digest,
                media_type: "application/json".to_string(),
                byte_length: fs::metadata(&path)
                    .map_err(|error| io_error("inspect Windows start evidence", error))?
                    .len(),
                truncated: false,
            });
        }
        Ok(terminal)
    }

}

#[cfg(test)]
#[test]
fn native_formal_runtime_dispatch_methods_contract() {
    let _: fn(&Runtime, &AttemptRecord) -> RuntimeResult<()> = Runtime::ensure_attempt_dispatched;
    let _: fn(&Runtime, &AttemptRecord) -> RuntimeResult<()> = Runtime::dispatch_attempt;
}
