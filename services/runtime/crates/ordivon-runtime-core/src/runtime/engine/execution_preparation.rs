// A contained Job's HOME and tool caches are materialized by Runtime in its
// Workspace-owned roots. Linux's systemd provider binds these environment
// values into its mount namespace; caller overrides must not turn a restricted
// task into a host-directory bind request (including per-step overrides).
// TrustedLocal intentionally retains the operator-authorized broader contract.
fn validate_contained_mount_environment(
    runtime_environment: &BTreeMap<String, String>,
    caller_overrides: &BTreeMap<String, String>,
    field_prefix: &str,
) -> RuntimeResult<()> {
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
        if let Some(value) = caller_overrides.get(name) {
            if runtime_environment.get(name) != Some(value) {
                return Err(RuntimeError::invalid(
                    "contained_local mount-bound environment paths are Runtime-owned",
                    &format!("{field_prefix}.{name}"),
                ));
            }
        }
    }
    Ok(())
}

#[cfg(test)]
mod contained_mount_environment_tests {
    use super::*;

    #[test]
    fn runtime_owned_paths_can_be_repeated_but_not_retargeted_to_host_secrets() {
        let base = BTreeMap::from([
            ("HOME".to_string(), "/cache/workspace/home".to_string()),
            ("TMPDIR".to_string(), "/cache/workspace/tmp".to_string()),
            ("UV_CACHE_DIR".to_string(), "/cache/workspace/uv".to_string()),
        ]);
        validate_contained_mount_environment(&base, &BTreeMap::new(), "execution.env").unwrap();
        let same = BTreeMap::from([(
            "HOME".to_string(),
            "/cache/workspace/home".to_string(),
        )]);
        validate_contained_mount_environment(&base, &same, "execution.env").unwrap();
        let safe_unrelated = BTreeMap::from([(
            "MY_APP_SETTING".to_string(),
            "value".to_string(),
        )]);
        validate_contained_mount_environment(&base, &safe_unrelated, "execution.env").unwrap();

        for (name, target) in [
            ("HOME", "/root/synthetic-private"),
            ("TMPDIR", "/root/synthetic-private"),
            ("UV_CACHE_DIR", "/etc/ordivon"),
            ("PIP_CACHE_DIR", "/root/synthetic-private"),
            ("CARGO_TARGET_DIR", "/root/synthetic-private"),
        ] {
            let forged = BTreeMap::from([(name.to_string(), target.to_string())]);
            for origin in ["execution.env", "execution.steps[0].env"] {
                let error = validate_contained_mount_environment(&base, &forged, origin)
                    .expect_err("caller must not turn a cache or HOME into a host bind");
                assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
                assert_eq!(error.field.as_deref(), Some(format!("{origin}.{name}").as_str()));
                assert!(!error.retryable);
            }
        }
    }
}

// Execution plan resolution, input/credential materialization and ownership checks.
// Durable Runtime admission remains the sole authority for committed execution inputs.
impl Runtime {
    // Recheck a persisted ContainedLocal plan BEFORE committing physical
    // dispatch intent. A pre-upgrade Job might already contain untrusted HOME
    // or cache bind sources; new-admission validation alone cannot make those
    // historical plan bytes safe to execute after a restart.
    fn verify_committed_contained_mount_environment(
        &self,
        plan: &RuntimeExecutionPlan,
    ) -> RuntimeResult<()> {
        if plan.execution_target != super::ExecutionTarget::LocalLinux
            || plan.execution_profile != super::ExecutionProfile::ContainedLocal
        {
            return Ok(());
        }
        let record = load_workspace_record(&self.executor, &plan.workspace_id)
            .map_err(map_universal_error)?;
        if record.workspace_path != plan.workspace_path {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "contained plan no longer binds the original physical Workspace",
                Some("workspaceId"),
                false,
            ));
        }
        let trusted = self.execution_environment(
            &record,
            super::ExecutionProfile::ContainedLocal,
        )?;
        validate_contained_mount_environment(
            &trusted,
            &plan.env,
            "executionPlan.env",
        )?;
        for (index, step) in plan.steps.iter().enumerate() {
            validate_contained_mount_environment(
                &trusted,
                &step.env,
                &format!("executionPlan.steps[{index}].env"),
            )?;
        }
        Ok(())
    }

    fn resolve_plan(&self, request: &JobRunRequest) -> RuntimeResult<RuntimeExecutionPlan> {
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
        let explicit_windows_context = request.execution.windows_context;
        if request.execution.execution_target != super::ExecutionTarget::WindowsNative
            && explicit_windows_context.is_some()
        {
            return Err(RuntimeError::invalid(
                "windowsContext is valid only for windows_native execution",
                "execution.windowsContext",
            ));
        }
        let requested_windows_context = explicit_windows_context
            .unwrap_or_else(|| request.execution.windows_authority.canonical_context());
        if explicit_windows_context.is_some()
            && !requested_windows_context.compatible_with_legacy(request.execution.windows_authority)
        {
            return Err(RuntimeError::invalid(
                "windowsContext conflicts with the non-default legacy windowsAuthority",
                "execution.windowsContext",
            ));
        }
        let effective_windows_authority = requested_windows_context.transport_authority();

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
                let (environment, context) = super::windows::resolve_windows_execution_context(
                    windows,
                    requested_windows_context,
                    explicit_windows_context,
                )?;
                (environment, Some(context))
            }
        };
        if request.execution.execution_target == super::ExecutionTarget::LocalLinux
            && request.execution.execution_profile == super::ExecutionProfile::ContainedLocal
        {
            validate_contained_mount_environment(
                &base_environment,
                &request.execution.env,
                "execution.env",
            )?;
            for (index, step) in request.execution.steps.iter().enumerate() {
                validate_contained_mount_environment(
                    &base_environment,
                    &step.env,
                    &format!("execution.steps[{index}].env"),
                )?;
            }
        }
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
                        super::windows::merge_windows_workspace_environment(
                            &base_environment,
                            &step.env,
                            requested_windows_context.identity
                                == super::WindowsExecutionIdentity::ActiveUser,
                            &workspace_path,
                        )?
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
                    super::windows::merge_windows_workspace_environment(
                        &base_environment,
                        &request.execution.env,
                        requested_windows_context.identity
                            == super::WindowsExecutionIdentity::ActiveUser,
                        &workspace_path,
                    )?
                }
            },
            timeout_ms: request.execution.timeout_ms,
            stdout_limit_bytes: request.execution.stdout_limit_bytes,
            stderr_limit_bytes: request.execution.stderr_limit_bytes,
            steps,
            budget: request.execution.budget.clone(),
            execution_profile: request.execution.execution_profile,
            execution_target: request.execution.execution_target,
            windows_authority: effective_windows_authority,
            windows_context: explicit_windows_context,
            windows_execution_context,
            foreign_references: request.execution.foreign_references.clone(),
            host_dependencies: Vec::new(),
            input_set_id: None,
            effective_inputs: Vec::new(),
            credential_set_id: None,
            principal: request.principal.clone(),
        })
    }

    fn materialize_input_bindings(
        &self,
        request: &JobRunRequest,
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
                        "materialized input digest does not match the caller commitment",
                        &format!("inputs[{index}].expectedDigest"),
                    ));
                }
                protect_posix_path(&target, 0o444, "protect materialized input")?;
            }
            sync_directory(&staging)?;
            durable_runtime_rename(
                &staging,
                &prepared_root,
                false,
                "publish prepared immutable input set",
            )?;
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

    pub(super) fn materialize_credential_bindings(
        &self,
        request: &JobRunRequest,
        job_id: &str,
        credentials: &[CredentialBindingRequest],
    ) -> RuntimeResult<PreparedCredentialSet> {
        let materialization_root = self.executor.credential_materializations_root();
        fs::create_dir_all(&materialization_root)
            .map_err(|error| io_error("create credential materialization root", error))?;
        let prepared_root = materialization_root.join(job_id);
        let owned_root = self.executor.job_credential_path(job_id);
        if prepared_root.exists() || owned_root.exists() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "preallocated encrypted credential snapshot identity already has physical state",
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
            .map_err(|error| io_error("create credential staging lease", error))?;
        if let Err(error) = lease.try_lock() {
            let error = match error {
                std::fs::TryLockError::WouldBlock => {
                    std::io::Error::from(std::io::ErrorKind::WouldBlock)
                }
                std::fs::TryLockError::Error(error) => error,
            };
            let _ = fs::remove_file(&lease_path);
            return Err(io_error("lock credential staging lease", error));
        }

        let staging =
            materialization_root.join(format!(".{job_id}.staging-{}", Uuid::now_v7()));
        let result = (|| {
            fs::create_dir(&staging)
                .map_err(|error| io_error("create credential staging directory", error))?;
            protect_posix_path(
                &staging,
                0o700,
                "protect credential staging directory",
            )?;

            for (index, credential) in credentials.iter().enumerate() {
                let authority = self
                    .credential_authorities
                    .get(&credential.authority)
                    .ok_or_else(|| {
                        RuntimeError::invalid(
                            "credential authority is unavailable",
                            &format!("credentials[{index}].authority"),
                        )
                    })?;
                if !authority.allowed_principals.contains(&request.principal) {
                    return Err(RuntimeError::new(
                        RuntimeErrorCode::InvalidRequest,
                        "authenticated principal is not authorized for credential authority",
                        Some(&format!("credentials[{index}].authority")),
                        false,
                    ));
                }
                // Authorization is deliberately checked before resolving the credential object.
                let source =
                    open_credential_file(authority.root.as_ref(), &credential.credential, index)?;
                let target = staging.join(&credential.credential);
                let _ = copy_input_and_digest(source, &target)?;
                protect_posix_path(&target, 0o400, "protect encrypted credential snapshot")?;
            }

            sync_directory(&staging)?;
            durable_runtime_rename(
                &staging,
                &prepared_root,
                false,
                "publish prepared encrypted credential snapshot set",
            )?;
            let (credential_set_id, _) = inspect_credential_snapshot(&prepared_root)?;
            Ok(PreparedCredentialSet {
                credential_set_id,
                prepared_root: prepared_root.clone(),
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

    fn discard_prepared_credential_set(&self, prepared_root: &Path) -> RuntimeResult<()> {
        if !prepared_root.exists() {
            return Ok(());
        }
        fs::remove_dir_all(prepared_root)
            .map_err(|error| io_error("remove unowned prepared credential set", error))?;
        if let Some(parent) = prepared_root.parent() {
            sync_directory(parent)?;
        }
        Ok(())
    }

    fn ensure_job_credential_ownership(&self, job_id: &str) -> RuntimeResult<()> {
        let plan = self.registry.execution_plan(job_id)?;
        let Some(credential_set_id) = plan.credential_set_id.as_deref() else {
            return Ok(());
        };

        let owned_root = self.executor.job_credential_path(job_id);
        let prepared_root = self.executor.credential_materializations_root().join(job_id);
        fs::create_dir_all(self.executor.job_credentials_root())
            .map_err(|error| io_error("create Job credential ownership root", error))?;

        if owned_root.exists() {
            let _ = verify_credential_snapshot(&owned_root, credential_set_id)?;
            if prepared_root.exists() {
                self.discard_prepared_credential_set(&prepared_root)?;
            }
            return Ok(());
        }
        if !prepared_root.exists() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                "committed Job credentials are missing both prepared and Job-owned snapshots",
                Some("executionPlan.credentialSetId"),
                true,
            ));
        }
        let _ = verify_credential_snapshot(&prepared_root, credential_set_id)?;
        match durable_runtime_rename(
            &prepared_root,
            &owned_root,
            false,
            "adopt prepared credentials for Job",
        ) {
            Ok(()) => {}
            Err(error) if owned_root.exists() => {
                let _ = error;
            }
            Err(error) => return Err(error),
        }
        let _ = verify_credential_snapshot(&owned_root, credential_set_id)?;
        Ok(())
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
        match durable_runtime_rename(
            &prepared_root,
            &owned_root,
            false,
            "adopt prepared immutable inputs for Job",
        ) {
            Ok(()) => {}
            Err(error) if owned_root.exists() => {
                let _ = error;
            }
            Err(error) => return Err(error),
        }
        verify_effective_input_set(&owned_root, &requests)?;
        Ok(())
    }
}
