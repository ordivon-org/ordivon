impl Runtime {
    fn current_execution_provider_snapshot(
        &self,
        target: super::ExecutionTarget,
    ) -> RuntimeResult<ExecutionProviderSnapshot> {
        match target {
            super::ExecutionTarget::LocalLinux => {
                if self.node_identity.platform != super::RuntimeNodePlatform::Linux {
                    return Err(RuntimeError::new(
                        RuntimeErrorCode::ToolUnavailable,
                        "local_linux execution is available only on a Linux Runtime node",
                        Some("execution.executionTarget"),
                        false,
                    ));
                }
                let runner_path = self.executor.runner_path.as_deref().ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::ToolUnavailable,
                        "local_linux runner is not configured on this Runtime node",
                        Some("runnerPath"),
                        false,
                    )
                })?;
                let runner = validate_runner(runner_path)?;
                Ok(ExecutionProviderSnapshot {
                    contract: ExecutionProviderContract::LocalLinuxRunnerV1,
                    executable_digest: sha256_file(&runner).map_err(map_universal_error)?,
                    wsl_distribution: None,
                })
            }
            super::ExecutionTarget::WindowsNative => {
                let windows = self.windows.as_ref().ok_or_else(|| {
                    RuntimeError::invalid(
                        "windows_native target is not configured on this Runtime",
                        "execution.executionTarget",
                    )
                })?;
                windows.validate()?;
                let launcher = fs::canonicalize(&windows.launcher_path).map_err(|error| {
                    io_error("canonicalize Windows execution provider launcher", error)
                })?;
                Ok(ExecutionProviderSnapshot {
                    contract: ExecutionProviderContract::WindowsNativeLauncherV1,
                    executable_digest: sha256_file(&launcher).map_err(map_universal_error)?,
                    wsl_distribution: windows.wsl_distribution.clone(),
                })
            }
        }
    }

    pub fn capabilities(&self) -> RuntimeCapabilities {
        let mut allowed_executable_roots = self
            .executor
            .allowed_executable_roots
            .iter()
            .map(|path| path.to_string_lossy().into_owned())
            .collect::<Vec<_>>();
        allowed_executable_roots.sort();
        allowed_executable_roots.dedup();
        let input_authorities = self.input_authorities.keys().cloned().collect::<Vec<_>>();

        let linux_configured = self.node_identity.platform == super::RuntimeNodePlatform::Linux
            && self.executor.runner_path.is_some();
        let linux_provider = linux_configured
            .then(|| self.current_execution_provider_snapshot(super::ExecutionTarget::LocalLinux))
            .transpose()
            .ok()
            .flatten();
        let linux = RuntimeExecutionTargetCapability {
            target: super::ExecutionTarget::LocalLinux,
            configured: linux_configured,
            available: linux_provider.is_some(),
            execution_profiles: if linux_configured {
                vec![
                    super::ExecutionProfile::TrustedLocal,
                    super::ExecutionProfile::ContainedLocal,
                ]
            } else {
                Vec::new()
            },
            windows_authorities: Vec::new(),
            windows_immutable_input_authorities: Vec::new(),
            structured_plan: linux_configured,
            immutable_inputs: linux_configured,
            host_dependency_commitments: linux_configured,
            host_dependency_continuity_scope: linux_configured
                .then(|| HOST_DEPENDENCY_CONTINUITY_SCOPE.to_string()),
            availability_issue: (linux_configured && linux_provider.is_none())
                .then(|| "EXECUTION_PROVIDER_UNAVAILABLE".to_string()),
            execution_provider: linux_provider,
        };

        let windows_configured = self.windows.is_some();
        let (windows_provider, windows_authorities, windows_issue) = if let Some(windows) =
            &self.windows
        {
            match self.current_execution_provider_snapshot(super::ExecutionTarget::WindowsNative) {
                Ok(provider) => {
                    let mut authorities = Vec::new();
                    for authority in [
                        super::WindowsAuthority::Limited,
                        super::WindowsAuthority::Elevated,
                    ] {
                        if snapshot_windows_runtime_context(windows, authority).is_ok() {
                            authorities.push(authority);
                        }
                    }
                    let issue = authorities
                        .is_empty()
                        .then(|| "WINDOWS_AUTHORITY_UNAVAILABLE".to_string());
                    (Some(provider), authorities, issue)
                }
                Err(_) => (
                    None,
                    Vec::new(),
                    Some("EXECUTION_PROVIDER_UNAVAILABLE".to_string()),
                ),
            }
        } else {
            (None, Vec::new(), None)
        };
        let windows_immutable_input_authorities = windows_authorities
            .contains(&super::WindowsAuthority::Limited)
            .then_some(vec![super::WindowsAuthority::Limited])
            .unwrap_or_default();
        let windows = RuntimeExecutionTargetCapability {
            target: super::ExecutionTarget::WindowsNative,
            configured: windows_configured,
            available: windows_provider.is_some() && !windows_authorities.is_empty(),
            execution_profiles: vec![super::ExecutionProfile::TrustedLocal],
            windows_authorities,
            windows_immutable_input_authorities: windows_immutable_input_authorities.clone(),
            structured_plan: false,
            immutable_inputs: !windows_immutable_input_authorities.is_empty(),
            host_dependency_commitments: false,
            host_dependency_continuity_scope: None,
            execution_provider: windows_provider,
            availability_issue: windows_issue,
        };

        RuntimeCapabilities {
            schema_version: RUNTIME_SCHEMA_VERSION,
            node: self.node_identity.clone(),
            default_runtime_ms: self.default_runtime_ms,
            max_runtime_ms: self.executor.max_runtime_ms,
            max_output_bytes: self.executor.max_output_bytes,
            allowed_executable_roots,
            input_authorities,
            targets: vec![linux, windows],
        }
    }

    fn verify_committed_execution_provider(&self, job_id: &str) -> RuntimeResult<()> {
        let plan = self.registry.execution_plan(job_id)?;
        let Some(expected) = self.registry.execution_provider(job_id)? else {
            // Historical Jobs predate provider commitment and retain their original semantics.
            return Ok(());
        };
        let observed = self.current_execution_provider_snapshot(plan.execution_target)?;
        if observed != expected {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ProviderStateMismatch,
                format!(
                    "execution provider changed after operation admission: expected {:?}, observed {:?}",
                    expected, observed
                ),
                Some("executionProvider"),
                false,
            ));
        }
        Ok(())
    }

    fn validate_host_dependencies(
        &self,
        request: &TaskRunRequest,
    ) -> RuntimeResult<Vec<HostDependencyBinding>> {
        if request.execution.host_dependencies.is_empty() {
            return Ok(Vec::new());
        }
        if request.execution.execution_target != super::ExecutionTarget::LocalLinux
            || request.execution.execution_profile != super::ExecutionProfile::TrustedLocal
        {
            return Err(RuntimeError::invalid(
                "Host Dependencies require trusted_local local_linux execution",
                "execution.hostDependencies",
            ));
        }
        let mut bindings = request.execution.host_dependencies.clone();
        bindings.sort_by(|left, right| left.path.cmp(&right.path));
        let mut previous: Option<&str> = None;
        for (index, binding) in bindings.iter().enumerate() {
            let path = Path::new(&binding.path);
            if !path.is_absolute() || binding.path.as_bytes().contains(&0) {
                return Err(RuntimeError::invalid(
                    "Host Dependency path must be absolute and NUL-free",
                    &format!("execution.hostDependencies[{index}].path"),
                ));
            }
            if previous == Some(binding.path.as_str()) {
                return Err(RuntimeError::invalid(
                    "Host Dependency paths must be unique",
                    "execution.hostDependencies",
                ));
            }
            previous = Some(&binding.path);
            let expected = binding
                .expected_digest
                .strip_prefix("sha256:")
                .ok_or_else(|| {
                    RuntimeError::invalid(
                        "Host Dependency expectedDigest must use sha256",
                        &format!("execution.hostDependencies[{index}].expectedDigest"),
                    )
                })?;
            if expected.len() != 64
                || !expected
                    .bytes()
                    .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
            {
                return Err(RuntimeError::invalid(
                    "Host Dependency expectedDigest must contain 64 lowercase hexadecimal characters",
                    &format!("execution.hostDependencies[{index}].expectedDigest"),
                ));
            }
            let metadata = fs::symlink_metadata(path).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::InvalidRequest,
                    format!("Host Dependency {} is unavailable: {error}", binding.path),
                    Some("execution.hostDependencies"),
                    false,
                )
            })?;
            if metadata.file_type().is_symlink() || !metadata.is_file() {
                return Err(RuntimeError::invalid(
                    "Host Dependency must be a regular non-symlink file",
                    &format!("execution.hostDependencies[{index}].path"),
                ));
            }
            let observed = sha256_file(path).map_err(map_universal_error)?;
            if observed != binding.expected_digest {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::InvalidRequest,
                    format!(
                        "Host Dependency {} does not match expected digest: expected {}, observed {}",
                        binding.path, binding.expected_digest, observed
                    ),
                    Some("execution.hostDependencies"),
                    false,
                ));
            }
        }
        Ok(bindings)
    }

    fn verify_committed_host_dependencies(&self, job_id: &str) -> RuntimeResult<()> {
        for binding in self.registry.host_dependencies(job_id)?.iter() {
            let path = Path::new(&binding.path);
            let metadata = fs::symlink_metadata(path).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::WorkspaceStateMismatch,
                    format!(
                        "committed Host Dependency {} is unavailable before dispatch: {error}",
                        binding.path
                    ),
                    Some("hostDependencies"),
                    false,
                )
            })?;
            if metadata.file_type().is_symlink() || !metadata.is_file() {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::WorkspaceStateMismatch,
                    format!(
                        "committed Host Dependency {} is not a regular non-symlink file",
                        binding.path
                    ),
                    Some("hostDependencies"),
                    false,
                ));
            }
            let observed = sha256_file(path).map_err(map_universal_error)?;
            if observed != binding.expected_digest {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::WorkspaceStateMismatch,
                    format!(
                        "committed Host Dependency {} changed after admission: expected {}, observed {}",
                        binding.path, binding.expected_digest, observed
                    ),
                    Some("hostDependencies"),
                    false,
                ));
            }
        }
        Ok(())
    }

    fn resolve_plan(&self, request: &TaskRunRequest) -> RuntimeResult<RuntimeExecutionPlan> {
        let record = load_workspace_record(&self.executor, &request.execution.workspace_id)
            .map_err(map_universal_error)?;
        let workspace_path =
            canonical_directory(Path::new(&record.workspace_path), "workspacePath")
                .map_err(map_universal_error)?;
        let cwd = resolve_workspace_cwd(
            &record,
            &request.execution.cwd_relative,
            "execution.cwdRelative",
        )
        .map_err(map_universal_error)?;
        let executable = validate_executable(
            &self.executor,
            &request.execution.executable,
            "execution.executable",
        )?;
        let (base_environment, windows_execution_context) = match request.execution.execution_target
        {
            super::ExecutionTarget::LocalLinux => (
                self.execution_environment(&record, request.execution.execution_profile)?,
                None,
            ),
            super::ExecutionTarget::WindowsNative => {
                let windows = self.windows.as_ref().ok_or_else(|| {
                    RuntimeError::invalid(
                        "windows_native target is not configured on this Runtime",
                        "execution.executionTarget",
                    )
                })?;
                if windows.wsl_distribution.is_some() && mounted_windows_path(&executable).is_none() {
                    return Err(RuntimeError::invalid(
                        "Linux-hosted windows_native executable must reside on a WSL-mounted Windows drive",
                        "execution.executable",
                    ));
                }
                let snapshot =
                    snapshot_windows_runtime_context(windows, request.execution.windows_authority)?;
                let token_class = match request.execution.windows_authority {
                    super::WindowsAuthority::Limited => super::WindowsTokenClass::Limited,
                    super::WindowsAuthority::Elevated => super::WindowsTokenClass::Elevated,
                };
                (
                    snapshot.environment,
                    Some(super::WindowsExecutionContext {
                        token_class,
                        token_user_sid: snapshot.token_user_sid,
                        environment_source: "windows_user_machine_profile_allowlist_v1".to_string(),
                    }),
                )
            }
        };
        let mut steps = Vec::with_capacity(request.execution.steps.len());
        for (step_index, step) in request.execution.steps.iter().enumerate() {
            let step_cwd = resolve_workspace_cwd(
                &record,
                &step.cwd_relative,
                &format!("execution.steps[{step_index}].cwdRelative"),
            )
            .map_err(map_universal_error)?;
            let step_executable = validate_executable(
                &self.executor,
                &step.executable,
                &format!("execution.steps[{step_index}].executable"),
            )?;
            steps.push(RuntimeExecutionStep {
                id: step.id.clone(),
                executable: step_executable.to_string_lossy().into_owned(),
                executable_digest: sha256_file(&step_executable).map_err(map_universal_error)?,
                args: step.args.clone(),
                cwd: step_cwd.to_string_lossy().into_owned(),
                env: match request.execution.execution_target {
                    super::ExecutionTarget::LocalLinux => {
                        merge_environment(&base_environment, &step.env)
                    }
                    super::ExecutionTarget::WindowsNative => {
                        merge_windows_environment(&base_environment, &step.env)?
                    }
                },
                timeout_ms: step.timeout_ms,
                continue_on_error: step.continue_on_error,
            });
        }
        Ok(RuntimeExecutionPlan {
            schema_version: RUNTIME_SCHEMA_VERSION,
            workspace_id: request.execution.workspace_id.clone(),
            workspace_path: workspace_path.to_string_lossy().into_owned(),
            source_revision: record.source_revision,
            workspace_source_digest: Some(
                workspace_source_state_digest(&self.executor, &request.execution.workspace_id)
                    .map_err(map_universal_error)?,
            ),
            workspace_git_common_dir: Some(
                workspace_git_common_dir_at(&workspace_path)
                    .map_err(map_universal_error)?
                    .to_string_lossy()
                    .into_owned(),
            ),
            executable: executable.to_string_lossy().into_owned(),
            executable_digest: sha256_file(&executable).map_err(map_universal_error)?,
            args: request.execution.args.clone(),
            cwd: cwd.to_string_lossy().into_owned(),
            env: match request.execution.execution_target {
                super::ExecutionTarget::LocalLinux => {
                    merge_environment(&base_environment, &request.execution.env)
                }
                super::ExecutionTarget::WindowsNative => {
                    merge_windows_environment(&base_environment, &request.execution.env)?
                }
            },
            timeout_ms: request.execution.timeout_ms,
            stdout_limit_bytes: request.execution.stdout_limit_bytes,
            stderr_limit_bytes: request.execution.stderr_limit_bytes,
            steps,
            budget: request.execution.budget.clone(),
            execution_profile: request.execution.execution_profile,
            execution_target: request.execution.execution_target,
            windows_authority: request.execution.windows_authority,
            windows_execution_context,
            foreign_references: request.execution.foreign_references.clone(),
            input_set_id: None,
            effective_inputs: Vec::new(),
            principal: request.principal.clone(),
        })
    }

    fn materialize_input_bindings(
        &self,
        request: &TaskRunRequest,
        request_identity_digest: &str,
        job_id: &str,
        inputs: &[InputBindingRequest],
    ) -> RuntimeResult<PreparedInputSet> {
        let set_digest = sha256_bytes(
            format!(
                "{}\0{}\0{}",
                request.principal, request.client_request_id, request_identity_digest
            )
            .as_bytes(),
        );
        let input_set_id = set_digest
            .strip_prefix("sha256:")
            .unwrap_or(&set_digest)
            .to_string();
        let materialization_root = self.executor.input_materializations_root();
        fs::create_dir_all(&materialization_root)
            .map_err(|error| io_error("create input materialization root", error))?;
        let prepared_root = materialization_root.join(job_id);
        let owned_root = self.executor.job_input_path(job_id);
        if prepared_root.exists() || owned_root.exists() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "preallocated immutable input identity already has physical state",
                Some("jobId"),
                false,
            ));
        }

        let lease_path = materialization_root.join(format!(".{job_id}.lease"));
        let mut lease_options = OpenOptions::new();
        lease_options.read(true).write(true).create_new(true);
        configure_private_create(&mut lease_options, 0o600);
        let lease = lease_options
            .open(&lease_path)
            .map_err(|error| io_error("create input staging lease", error))?;
        if let Err(error) = lease.try_lock() {
            let error = match error {
                std::fs::TryLockError::WouldBlock => {
                    std::io::Error::from(std::io::ErrorKind::WouldBlock)
                }
                std::fs::TryLockError::Error(error) => error,
            };
            let _ = fs::remove_file(&lease_path);
            return Err(io_error("lock input staging lease", error));
        }
        let staging = materialization_root.join(format!(".{job_id}.staging-{}", Uuid::now_v7()));
        let result = (|| {
            fs::create_dir(&staging)
                .map_err(|error| io_error("create input staging directory", error))?;
            protect_posix_path(&staging, 0o700, "protect input staging directory")?;
            for (index, input) in inputs.iter().enumerate() {
                let authority = self
                    .input_authorities
                    .get(&input.authority)
                    .ok_or_else(|| {
                        RuntimeError::invalid(
                            format!("unknown input authority {}", input.authority),
                            &format!("inputs[{index}].authority"),
                        )
                    })?;
                let source =
                    open_authority_file(authority.root.as_ref(), &input.relative_object, index)?;
                let target = staging.join(&input.presentation_relative_path);
                if let Some(parent) = target.parent() {
                    fs::create_dir_all(parent)
                        .map_err(|error| io_error("create input presentation tree", error))?;
                }
                let observed_digest = copy_input_and_digest(source, &target)?;
                if observed_digest != input.expected_digest {
                    return Err(RuntimeError::invalid(
                        format!(
                            "materialized input digest mismatch: expected {}, observed {observed_digest}",
                            input.expected_digest
                        ),
                        &format!("inputs[{index}].expectedDigest"),
                    ));
                }
                protect_posix_path(&target, 0o444, "protect materialized input")?;
            }
            sync_directory(&staging)?;
            fs::rename(&staging, &prepared_root)
                .map_err(|error| io_error("publish prepared immutable input set", error))?;
            sync_directory(&materialization_root)?;
            let effective_inputs = verify_effective_input_set(&prepared_root, inputs)?;
            Ok(PreparedInputSet {
                input_set_id,
                prepared_root: prepared_root.clone(),
                effective_inputs,
            })
        })();
        if result.is_err() {
            let _ = fs::remove_dir_all(&staging);
            let _ = fs::remove_dir_all(&prepared_root);
        }
        drop(lease);
        let _ = fs::remove_file(&lease_path);
        let _ = sync_directory(&materialization_root);
        result
    }

    fn discard_prepared_input_set(&self, prepared_root: &Path) -> RuntimeResult<()> {
        if !prepared_root.exists() {
            return Ok(());
        }
        fs::remove_dir_all(prepared_root)
            .map_err(|error| io_error("remove unowned prepared input set", error))?;
        if let Some(parent) = prepared_root.parent() {
            sync_directory(parent)?;
        }
        Ok(())
    }

    fn ensure_job_input_ownership(&self, job_id: &str) -> RuntimeResult<()> {
        let plan = self.registry.execution_plan(job_id)?;
        if plan.effective_inputs.is_empty() {
            if plan.input_set_id.is_some() {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "inputSetId exists without effective immutable inputs",
                    Some("executionPlan"),
                    false,
                ));
            }
            return Ok(());
        }
        if plan.input_set_id.is_none() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "effective immutable inputs have no committed inputSetId",
                Some("executionPlan"),
                false,
            ));
        }
        let requests = effective_input_requests_from_plan(&plan)?;
        let owned_root = self.executor.job_input_path(job_id);
        let prepared_root = self.executor.input_materializations_root().join(job_id);
        fs::create_dir_all(self.executor.job_inputs_root())
            .map_err(|error| io_error("create Job input ownership root", error))?;
        if owned_root.exists() {
            verify_effective_input_set(&owned_root, &requests)?;
            if prepared_root.exists() {
                self.discard_prepared_input_set(&prepared_root)?;
            }
            return Ok(());
        }
        if !prepared_root.exists() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                "committed Job immutable inputs are missing both prepared and Job-owned bytes",
                Some("executionPlan.inputSetId"),
                true,
            ));
        }
        verify_effective_input_set(&prepared_root, &requests)?;
        match fs::rename(&prepared_root, &owned_root) {
            Ok(()) => sync_directory(&self.executor.job_inputs_root())?,
            Err(error) if owned_root.exists() => {
                let _ = error;
            }
            Err(error) => return Err(io_error("adopt prepared immutable inputs for Job", error)),
        }
        verify_effective_input_set(&owned_root, &requests)?;
        Ok(())
    }

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
        let request = RunnerTaskRequest {
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
                match fs::rename(&staging, &final_path) {
                    Ok(()) => sync_directory(parent)?,
                    Err(error) if final_path.is_dir() => {
                        let _ = error;
                        fs::remove_dir_all(&staging).map_err(|cleanup_error| {
                            io_error("remove losing bundle staging directory", cleanup_error)
                        })?;
                    }
                    Err(error) => return Err(io_error("commit Attempt bundle", error)),
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
        let runtime_ceiling = plan.timeout_ms.saturating_add(5_000);
        let output = match plan.execution_target {
            super::ExecutionTarget::LocalLinux => {
                let runner_path = self.executor.runner_path.as_deref().ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::ToolUnavailable,
                        "local_linux runner is not configured on this Runtime node",
                        Some("runnerPath"),
                        false,
                    )
                })?;
                let runner = validate_runner(runner_path)?;
                let input_set_path = if plan.input_set_id.is_some() {
                    self.ensure_job_input_ownership(&starting.job_id)?;
                    let path = self.executor.job_input_path(&starting.job_id);
                    let requests = effective_input_requests_from_plan(&plan)?;
                    verify_effective_input_set(&path, &requests)?;
                    Some(path)
                } else {
                    None
                };
                dispatch_linux(&SystemdRunSpec {
                    unit_name: &starting.unit_name,
                    runner: &runner,
                    bundle_path: &bundle_path,
                    workspace_path: Path::new(&plan.workspace_path),
                    workspace_git_common_dir: plan
                        .workspace_git_common_dir
                        .as_deref()
                        .map(Path::new),
                    input_set_path: input_set_path.as_deref(),
                    runtime_ceiling_ms: runtime_ceiling,
                    budget: &plan.budget,
                    execution_profile: plan.execution_profile,
                    environment: &plan.env,
                })?
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
                if windows.wsl_distribution.is_none() {
                    let dispatch = dispatch_windows_native(&WindowsNativeRunSpec {
                        config: windows,
                        bundle_path: &bundle_path,
                        job_id: &starting.job_id,
                        attempt_id: &starting.attempt_id,
                        launch_token_digest: &starting.launch_token_digest,
                        authority: plan.windows_authority,
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
                    });
                    if let Err(error) = dispatch {
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
                    return self.await_launch_evidence(&starting);
                }
                dispatch_windows_via_wsl(&WindowsSystemdRunSpec {
                    config: windows,
                    unit_name: &starting.unit_name,
                    bundle_path: &bundle_path,
                    job_id: &starting.job_id,
                    attempt_id: &starting.attempt_id,
                    launch_token_digest: &starting.launch_token_digest,
                    authority: plan.windows_authority,
                    executable: Path::new(&plan.executable),
                    args: &plan.args,
                    cwd: Path::new(&plan.cwd),
                    environment: &plan.env,
                    input_source_root: input_source_root.as_deref(),
                    input_set_id: plan.input_set_id.as_deref(),
                    input_presentation_root,
                    input_bindings_digest: input_bindings_digest.as_deref(),
                    budget: &plan.budget,
                    runtime_ceiling_ms: runtime_ceiling,
                    timeout_ms: plan.timeout_ms,
                    stdout_limit_bytes: plan.stdout_limit_bytes,
                    stderr_limit_bytes: plan.stderr_limit_bytes,
                })?
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

    fn await_launch_evidence(&self, attempt: &AttemptRecord) -> RuntimeResult<()> {
        let deadline = Instant::now()
            .checked_add(Duration::from_millis(self.startup_grace_ms))
            .ok_or_else(|| {
                RuntimeError::invalid(
                    "startupGraceMs exceeds platform monotonic clock range",
                    "startupGraceMs",
                )
            })?;
        let plan = self.registry.execution_plan(&attempt.job_id)?;
        let start_path = Path::new(&attempt.bundle_path).join(match plan.execution_target {
            super::ExecutionTarget::LocalLinux => RUNNER_START_FILE,
            super::ExecutionTarget::WindowsNative => WINDOWS_START_FILE,
        });
        let mut poll_index = 0;
        loop {
            if Path::new(&attempt.bundle_path).join(RESULT_FILE).exists() {
                return self.reconcile_runner_result(attempt);
            }
            if start_path.exists() {
                match self.bind_attempt_start(attempt, plan.execution_target) {
                    Ok(_) => return Ok(()),
                    Err(error) if transient_main_pid_observation_loss(&error) => {
                        // MainPID absence can race with another observer that already bound this
                        // exact Attempt, or with the Runner's final atomic result publication.
                        // Re-read durable truth before surfacing an identity error. This does not
                        // forgive a mismatching identity value: only absence is deferred.
                        if Path::new(&attempt.bundle_path).join(RESULT_FILE).exists() {
                            return self.reconcile_runner_result(attempt);
                        }
                        let current = self.registry.get_attempt(&attempt.attempt_id)?;
                        if current.row_version != attempt.row_version
                            || current.state != attempt.state
                        {
                            if Path::new(&current.bundle_path).join(RESULT_FILE).exists() {
                                return self.reconcile_runner_result(&current);
                            }
                            return Ok(());
                        }
                        if Instant::now() < deadline {
                            sleep_until_poll(deadline, &mut poll_index);
                            continue;
                        }
                        return Err(error);
                    }
                    Err(error) if error.code == RuntimeErrorCode::LaunchIdentityMismatch => {
                        if Path::new(&attempt.bundle_path).join(RESULT_FILE).exists() {
                            return self.reconcile_runner_result(attempt);
                        }
                        return Err(error);
                    }
                    Err(error) => return Err(error),
                }
            }
            if Instant::now() >= deadline {
                break;
            }
            sleep_until_poll(deadline, &mut poll_index);
        }
        self.reconcile_attempt(&attempt.attempt_id)
    }

    fn bind_attempt_start(
        &self,
        attempt: &AttemptRecord,
        target: super::ExecutionTarget,
    ) -> RuntimeResult<AttemptRecord> {
        match target {
            super::ExecutionTarget::LocalLinux => self.bind_runner_start(attempt),
            super::ExecutionTarget::WindowsNative => self.bind_windows_start(attempt),
        }
    }

    fn validate_windows_launcher_start_evidence(
        &self,
        attempt: &AttemptRecord,
    ) -> RuntimeResult<(WindowsLauncherStartEvidence, String)> {
        let path = Path::new(&attempt.bundle_path).join(WINDOWS_LAUNCHER_START_FILE);
        let bytes = fs::read(&path)
            .map_err(|error| io_error("read Windows launcher start evidence", error))?;
        let evidence: WindowsLauncherStartEvidence =
            serde_json::from_slice(&bytes).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::LaunchIdentityMismatch,
                    format!("invalid Windows launcher start evidence: {error}"),
                    Some("windowsLauncherStart"),
                    false,
                )
            })?;
        let plan = self.registry.execution_plan(&attempt.job_id)?;
        if plan.execution_target != super::ExecutionTarget::WindowsNative {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "Windows launcher start evidence belongs to a non-Windows execution plan",
                Some("windowsLauncherStart"),
                false,
            ));
        }
        let windows = self.windows.as_ref().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "committed windows_native Job has no configured Windows provider",
                Some("executionTarget"),
                true,
            )
        })?;
        if windows.wsl_distribution.is_some() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "early Windows launcher evidence is reserved for native control-plane dispatch",
                Some("windowsLauncherStart"),
                false,
            ));
        }
        let provider = self
            .registry
            .execution_provider(&attempt.job_id)?
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "native Windows Attempt has no committed execution provider",
                    Some("executionProvider"),
                    false,
                )
            })?;
        let expected_job_name = format!("Ordivon.{}", attempt.attempt_id);
        if evidence.schema_version != RUNTIME_SCHEMA_VERSION
            || evidence.job_id != attempt.job_id
            || evidence.attempt_id != attempt.attempt_id
            || evidence.launch_token_digest != attempt.launch_token_digest
            || evidence.job_name != expected_job_name
            || evidence.launcher_process_id == 0
            || evidence.launcher_process_creation_time_file_time == 0
            || evidence.observed_unix_ms == 0
            || provider.contract != ExecutionProviderContract::WindowsNativeLauncherV1
            || provider.wsl_distribution.is_some()
            || evidence.launcher_image_digest != provider.executable_digest
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                "Windows launcher start identity does not match committed native Attempt",
                Some("windowsLauncherStart"),
                false,
            ));
        }
        let digest = sha256_bytes(&bytes);
        if digest != sha256_file(&path).map_err(map_universal_error)? {
            return Err(RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                "Windows launcher start evidence digest changed while reading",
                Some("windowsLauncherStart"),
                false,
            ));
        }
        Ok((evidence, digest))
    }

    fn validate_windows_start_evidence(
        &self,
        attempt: &AttemptRecord,
    ) -> RuntimeResult<(WindowsStartEvidence, String)> {
        let path = Path::new(&attempt.bundle_path).join(WINDOWS_START_FILE);
        let bytes =
            fs::read(&path).map_err(|error| io_error("read Windows start evidence", error))?;
        let evidence: WindowsStartEvidence = serde_json::from_slice(&bytes).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                format!("invalid Windows start evidence: {error}"),
                Some("windowsStart"),
                false,
            )
        })?;
        let plan = self.registry.execution_plan(&attempt.job_id)?;
        if plan.execution_target != super::ExecutionTarget::WindowsNative {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "Windows start evidence belongs to a non-Windows execution plan",
                Some("windowsStart"),
                false,
            ));
        }
        let windows = self.windows.as_ref().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "committed windows_native Job has no configured Windows provider",
                Some("executionTarget"),
                true,
            )
        })?;
        let context = plan.windows_execution_context.as_ref().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "committed windows_native Job has no frozen Windows execution context",
                Some("windowsExecutionContext"),
                false,
            )
        })?;
        let expected_token_class = match plan.windows_authority {
            super::WindowsAuthority::Limited => super::WindowsTokenClass::Limited,
            super::WindowsAuthority::Elevated => super::WindowsTokenClass::Elevated,
        };
        if context.token_class != expected_token_class
            || context.environment_source != "windows_user_machine_profile_allowlist_v1"
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "committed Windows requested/effective authority is inconsistent",
                Some("windowsExecutionContext"),
                false,
            ));
        }
        let expected_job_name = format!("Ordivon.{}", attempt.attempt_id);
        let expected_image =
            windows_visible_path(windows, Path::new(&plan.executable), "execution.executable")?;
        let observed_image = evidence
            .image_path
            .strip_prefix("\\\\?\\")
            .unwrap_or(&evidence.image_path);
        let expected_image_normalized = expected_image
            .strip_prefix("\\\\?\\")
            .unwrap_or(&expected_image);
        let expected_input_evidence = if plan.effective_inputs.is_empty() {
            (None, None, None)
        } else {
            let input_set_id = plan.input_set_id.as_deref().ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Windows immutable inputs have no committed inputSetId",
                    Some("executionPlan.inputSetId"),
                    false,
                )
            })?;
            let presentation_root = required_environment_value_case_insensitive(
                &plan.env,
                "ORDIVON_INPUT_ROOT",
                "executionPlan.env",
            )?;
            (
                Some(input_set_id),
                Some(presentation_root),
                Some(windows_input_bindings_digest(&plan.effective_inputs)),
            )
        };
        let token_authority_matches = match plan.windows_authority {
            super::WindowsAuthority::Limited => {
                !evidence.token_is_elevated
                    && evidence.token_integrity_level_rid <= 8192
                    && (evidence.administrators_group_attributes == u32::MAX
                        || (evidence.administrators_group_attributes & 0x4) == 0
                        || (evidence.administrators_group_attributes & 0x10) != 0)
                    && matches!(
                        evidence.token_selection.as_str(),
                        "lua_medium_filtered" | "current_limited"
                    )
                    && (evidence.token_selection != "lua_medium_filtered"
                        || evidence.administrators_group_attributes == u32::MAX
                        || (evidence.administrators_group_attributes & 0x10) != 0)
            }
            super::WindowsAuthority::Elevated => {
                evidence.token_is_elevated
                    && evidence.token_integrity_level_rid >= 12288
                    && evidence.administrators_group_attributes != u32::MAX
                    && (evidence.administrators_group_attributes & 0x4) != 0
                    && (evidence.administrators_group_attributes & 0x10) == 0
                    && evidence.token_selection == "current_elevated"
            }
        };
        if evidence.schema_version != RUNTIME_SCHEMA_VERSION
            || evidence.job_id != attempt.job_id
            || evidence.attempt_id != attempt.attempt_id
            || evidence.launch_token_digest != attempt.launch_token_digest
            || evidence.job_name != expected_job_name
            || evidence.launcher_process_id == 0
            || evidence.process_id == 0
            || evidence.process_creation_time_file_time == 0
            || evidence.image_digest != plan.executable_digest
            || evidence.token_user_sid != context.token_user_sid
            || evidence.token_type != 1
            || !token_authority_matches
            || evidence.power_request_type != "system_required"
            || !evidence.power_request_acquired
            || evidence.input_set_id.as_deref() != expected_input_evidence.0
            || evidence.input_presentation_root.as_deref() != expected_input_evidence.1
            || evidence.input_bindings_digest.as_deref() != expected_input_evidence.2.as_deref()
            || !observed_image.eq_ignore_ascii_case(expected_image_normalized)
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                "Windows start identity does not match committed Attempt",
                Some("windowsStart"),
                false,
            ));
        }
        let start_digest = sha256_bytes(&bytes);
        if start_digest != sha256_file(&path).map_err(map_universal_error)? {
            return Err(RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                "Windows start evidence digest changed while reading",
                Some("windowsStart"),
                false,
            ));
        }
        if windows.wsl_distribution.is_none() {
            let provider = self
                .registry
                .execution_provider(&attempt.job_id)?
                .ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "native Windows Attempt has no committed execution provider",
                        Some("executionProvider"),
                        false,
                    )
                })?;
            if provider.contract != ExecutionProviderContract::WindowsNativeLauncherV1
                || provider.wsl_distribution.is_some()
                || evidence
                    .launcher_process_creation_time_file_time
                    .is_none_or(|identity| identity == 0)
                || evidence.launcher_image_digest.as_deref()
                    != Some(provider.executable_digest.as_str())
            {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::LaunchIdentityMismatch,
                    "native Windows launcher owner identity does not match the committed provider",
                    Some("windowsStart"),
                    false,
                ));
            }
        }
        Ok((evidence, start_digest))
    }

    fn bind_windows_start(&self, attempt: &AttemptRecord) -> RuntimeResult<AttemptRecord> {
        let (evidence, start_digest) = self.validate_windows_start_evidence(attempt)?;
        let windows = self.windows.as_ref().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "committed windows_native Job has no configured Windows provider",
                Some("executionTarget"),
                true,
            )
        })?;
        if windows.wsl_distribution.is_none() {
            let launcher_process_creation_time_file_time = evidence
                .launcher_process_creation_time_file_time
                .filter(|identity| *identity != 0)
                .ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::LaunchIdentityMismatch,
                        "native Windows start evidence omitted launcher process creation identity",
                        Some("windowsStart.launcherProcessCreationTimeFileTime"),
                        false,
                    )
                })?;
            let launcher_image_digest =
                evidence.launcher_image_digest.clone().ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::LaunchIdentityMismatch,
                        "native Windows start evidence omitted launcher image digest",
                        Some("windowsStart.launcherImageDigest"),
                        false,
                    )
                })?;
            return self.registry.bind_supervisor_owner(
                &attempt.attempt_id,
                attempt.row_version,
                &AttemptSupervisorOwner::WindowsLauncherV1 {
                    launcher_process_id: evidence.launcher_process_id,
                    launcher_process_creation_time_file_time,
                    launcher_image_digest,
                    job_name: evidence.job_name.clone(),
                    start_evidence_digest: start_digest,
                },
                evidence.observed_unix_ms,
            );
        }
        let properties = systemctl_show(&attempt.unit_name)?;
        let invocation_id = nonempty_property(&properties, "InvocationID")
            .ok_or_else(|| missing_systemd_property("InvocationID"))?;
        let control_group = nonempty_property(&properties, "ControlGroup")
            .ok_or_else(|| missing_systemd_property("ControlGroup"))?;
        let main_pid: u32 = properties
            .get("MainPID")
            .ok_or_else(|| missing_systemd_property("MainPID"))?
            .parse()
            .map_err(|_| missing_systemd_property("MainPID"))?;
        if main_pid == 0 {
            return Err(missing_systemd_property("MainPID"));
        }
        let process_start_identity = process_identity(main_pid).ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                "Windows launcher systemd MainPID has no observable host process identity",
                Some("mainPid"),
                false,
            )
        })?;
        let boot_id = read_trimmed("/proc/sys/kernel/random/boot_id")?;
        self.registry.bind_running(
            &attempt.attempt_id,
            attempt.row_version,
            &RunnerIdentity {
                boot_id,
                unit_name: attempt.unit_name.clone(),
                invocation_id,
                control_group,
                main_pid,
                process_start_identity,
                runner_start_digest: start_digest,
                observed_at_ms: evidence.observed_unix_ms,
            },
        )
    }

    fn bind_runner_start(&self, attempt: &AttemptRecord) -> RuntimeResult<AttemptRecord> {
        let path = Path::new(&attempt.bundle_path).join(RUNNER_START_FILE);
        let bytes =
            fs::read(&path).map_err(|error| io_error("read runner-start evidence", error))?;
        let evidence: RunnerStartEvidence = serde_json::from_slice(&bytes).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                format!("invalid runner-start evidence: {error}"),
                Some("runnerStart"),
                false,
            )
        })?;
        if evidence.job_id != attempt.job_id
            || evidence.attempt_id != attempt.attempt_id
            || evidence.unit_name != attempt.unit_name
            || evidence.launch_token_digest != attempt.launch_token_digest
            || !self.payload_evidence_matches(evidence.payload_uid, evidence.payload_gid)
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                "runner-start identity does not match committed Attempt",
                Some("runnerStart"),
                false,
            ));
        }
        if let Some(provider) = self.registry.execution_provider(&attempt.job_id)? {
            if provider.contract == super::ExecutionProviderContract::LocalLinuxRunnerV1 {
                let observed = evidence.runner_executable_digest.as_deref().ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::LaunchIdentityMismatch,
                        "provider-bound Runner-start evidence omitted the actual Runner image digest",
                        Some("runnerStart.runnerExecutableDigest"),
                        false,
                    )
                })?;
                if observed != provider.executable_digest {
                    return Err(RuntimeError::new(
                        RuntimeErrorCode::LaunchIdentityMismatch,
                        format!(
                            "actual Runner image differs from the committed execution provider: expected {}, observed {}",
                            provider.executable_digest, observed
                        ),
                        Some("runnerStart.runnerExecutableDigest"),
                        false,
                    ));
                }
            }
        }
        let properties = systemctl_show(&attempt.unit_name)?;
        require_property(&properties, "InvocationID", &evidence.invocation_id)?;
        require_property(&properties, "ControlGroup", &evidence.control_group)?;
        let main_pid: u32 = properties
            .get("MainPID")
            .ok_or_else(|| missing_systemd_property("MainPID"))?
            .parse()
            .map_err(|_| missing_systemd_property("MainPID"))?;
        if evidence.namespace_pid == 0 || evidence.namespace_process_start_identity.is_empty() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                "runner-start omitted PID namespace identity",
                Some("namespacePid"),
                false,
            ));
        }
        let process_start_identity = process_identity(main_pid).ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                "systemd MainPID has no observable host process identity",
                Some("mainPid"),
                false,
            )
        })?;
        if let Some(provider) = self.registry.execution_provider(&attempt.job_id)? {
            if provider.contract == super::ExecutionProviderContract::LocalLinuxRunnerV1 {
                let proc_exe = PathBuf::from(format!("/proc/{main_pid}/exe"));
                match sha256_file(&proc_exe) {
                    Ok(os_observed) => {
                        if evidence.runner_executable_digest.as_deref()
                            != Some(os_observed.as_str())
                            || os_observed != provider.executable_digest
                        {
                            return Err(RuntimeError::new(
                                RuntimeErrorCode::LaunchIdentityMismatch,
                                format!(
                                    "systemd MainPID image differs from committed/self-reported Runner provider: committed {}, runner-start {:?}, OS observed {}",
                                    provider.executable_digest,
                                    evidence.runner_executable_digest,
                                    os_observed
                                ),
                                Some("runnerStart.runnerExecutableDigest"),
                                false,
                            ));
                        }
                    }
                    Err(error) => {
                        if process_identity(main_pid).as_deref()
                            == Some(process_start_identity.as_str())
                        {
                            return Err(RuntimeError::new(
                                RuntimeErrorCode::LaunchIdentityMismatch,
                                format!(
                                    "cannot independently inspect the live systemd MainPID Runner image: {error}"
                                ),
                                Some("mainPid"),
                                false,
                            ));
                        }
                    }
                }
            }
        }
        let runner_start_digest = sha256_bytes(&bytes);
        if runner_start_digest != sha256_file(&path).map_err(map_universal_error)? {
            return Err(RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                "runner-start evidence digest changed while reading",
                Some("runnerStart"),
                false,
            ));
        }
        let boot_id = read_trimmed("/proc/sys/kernel/random/boot_id")?;
        self.registry.bind_running(
            &attempt.attempt_id,
            attempt.row_version,
            &RunnerIdentity {
                boot_id,
                unit_name: evidence.unit_name,
                invocation_id: evidence.invocation_id,
                control_group: evidence.control_group,
                main_pid,
                process_start_identity,
                runner_start_digest,
                observed_at_ms: u64::try_from(evidence.observed_unix_ms).unwrap_or(u64::MAX),
            },
        )
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

    fn commit_runner_result(&self, attempt: &AttemptRecord) -> RuntimeResult<TaskObservation> {
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
