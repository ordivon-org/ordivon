// Execution provider identity and host prerequisite commitments.
// This seam owns observation and verification, not deployment policy or durable admission.
impl Runtime {
    fn current_execution_provider_snapshot(
        &self,
        target: super::ExecutionTarget,
    ) -> RuntimeResult<ExecutionProviderSnapshot> {
        match target {
            super::ExecutionTarget::LocalLinux => LocalLinuxProvider::new(
                self.node_identity.platform,
                &self.executor,
            )
            .snapshot(),
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
                    wsl_distribution: None,
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
        let credential_authorities = self
            .credential_authorities
            .keys()
            .cloned()
            .collect::<Vec<_>>();

        let linux = LocalLinuxProvider::new(self.node_identity.platform, &self.executor)
            .capabilities();

        let windows_configured = self.windows.is_some();
        let (windows_provider, windows_authorities, windows_contexts, windows_issue) =
            if let Some(windows) = &self.windows {
                match self.current_execution_provider_snapshot(super::ExecutionTarget::WindowsNative)
                {
                    Ok(provider) => {
                        let mut contexts = Vec::new();
                        for context in [
                            super::WindowsExecutionContextRequest::new(
                                super::WindowsExecutionIdentity::Service,
                                super::WindowsPayloadPrivilege::Limited,
                            ),
                            super::WindowsExecutionContextRequest::new(
                                super::WindowsExecutionIdentity::Service,
                                super::WindowsPayloadPrivilege::Elevated,
                            ),
                            super::WindowsExecutionContextRequest::new(
                                super::WindowsExecutionIdentity::ActiveUser,
                                super::WindowsPayloadPrivilege::Limited,
                            ),
                            super::WindowsExecutionContextRequest::new(
                                super::WindowsExecutionIdentity::ActiveUser,
                                super::WindowsPayloadPrivilege::Elevated,
                            ),
                        ] {
                            if snapshot_windows_runtime_context_for(windows, context).is_ok() {
                                contexts.push(context);
                            }
                        }
                        let authorities = contexts
                            .iter()
                            .filter_map(|context| context.legacy_authority())
                            .collect::<Vec<_>>();
                        let issue = contexts
                            .is_empty()
                            .then(|| "WINDOWS_CONTEXT_UNAVAILABLE".to_string());
                        (Some(provider), authorities, contexts, issue)
                    }
                    Err(_) => (
                        None,
                        Vec::new(),
                        Vec::new(),
                        Some("EXECUTION_PROVIDER_UNAVAILABLE".to_string()),
                    ),
                }
            } else {
                (None, Vec::new(), Vec::new(), None)
            };
        let windows_immutable_input_authorities = windows_authorities
            .contains(&super::WindowsAuthority::Limited)
            .then_some(vec![super::WindowsAuthority::Limited])
            .unwrap_or_default();
        let windows_privileged_profiles = self
            .windows
            .as_ref()
            .map(|windows| {
                let mut ids = windows
                    .elevated_profiles
                    .iter()
                    .map(|profile| profile.id.clone())
                    .collect::<Vec<_>>();
                ids.sort();
                ids.dedup();
                ids
            })
            .unwrap_or_default();
        let windows_maintenance_fence_configured = self
            .windows
            .as_ref()
            .is_some_and(|windows| windows.maintenance_lease_path.is_some());
        let windows = RuntimeExecutionTargetCapability {
            target: super::ExecutionTarget::WindowsNative,
            configured: windows_configured,
            available: windows_provider.is_some() && !windows_authorities.is_empty(),
            execution_profiles: vec![super::ExecutionProfile::TrustedLocal],
            windows_authorities,
            windows_contexts,
            windows_immutable_input_authorities: windows_immutable_input_authorities.clone(),
            windows_privileged_profiles,
            windows_maintenance_fence_configured,
            structured_plan: false,
            immutable_inputs: !windows_immutable_input_authorities.is_empty(),
            host_dependency_commitments: false,
            host_dependency_continuity_scope: None,
            execution_provider: windows_provider,
            availability_issue: windows_issue,
        };

        let targets = match self.node_identity.platform {
            super::RuntimeNodePlatform::Linux => vec![linux],
            super::RuntimeNodePlatform::Windows => vec![windows],
            super::RuntimeNodePlatform::Other => Vec::new(),
        };
        RuntimeCapabilities {
            schema_version: RUNTIME_SCHEMA_VERSION,
            node: self.node_identity.clone(),
            default_runtime_ms: self.default_runtime_ms,
            max_runtime_ms: self.executor.max_runtime_ms,
            max_output_bytes: self.executor.max_output_bytes,
            allowed_executable_roots,
            input_authorities,
            credential_authorities,
            targets,
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
        request: &JobRunRequest,
    ) -> RuntimeResult<Vec<HostDependencyBinding>> {
        super::host_dependency::validate_bindings(
            &request.execution.host_dependencies,
            request.execution.execution_target,
            request.execution.execution_profile,
        )
    }

    fn verify_committed_host_dependencies(&self, job_id: &str) -> RuntimeResult<()> {
        super::host_dependency::verify_committed_bindings(
            &self.registry.host_dependencies(job_id)?,
        )
    }
}
