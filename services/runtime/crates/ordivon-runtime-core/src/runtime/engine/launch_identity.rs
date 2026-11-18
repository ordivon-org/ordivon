// Windows and Linux launch/start evidence binding for admitted attempts.
// Runner and provider evidence retain the existing identity and recovery semantics.
impl Runtime {
    fn bind_native_windows_dispatch_owner(
        &self,
        attempt: &AttemptRecord,
        dispatch: &WindowsNativeLaunchObservation,
    ) -> RuntimeResult<AttemptRecord> {
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
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "native Windows dispatch owner does not match the committed execution provider",
                Some("executionProvider"),
                false,
            ));
        }
        let observed_unix_ms = now_ms()?;
        let evidence = WindowsLauncherStartEvidence {
            schema_version: RUNTIME_SCHEMA_VERSION,
            job_id: attempt.job_id.clone(),
            attempt_id: attempt.attempt_id.clone(),
            launch_token_digest: attempt.launch_token_digest.clone(),
            request_digest: sha256_file(&Path::new(&attempt.bundle_path).join(RUNNER_REQUEST_FILE))
                .map_err(map_universal_error)?,
            job_name: format!("Ordivon.{}", attempt.attempt_id),
            launcher_process_id: dispatch.launcher_process_id,
            launcher_process_creation_time_file_time:
                dispatch.launcher_process_creation_time_file_time,
            launcher_image_digest: provider.executable_digest,
            observed_unix_ms,
        };
        let bytes = serde_json::to_vec(&evidence).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("cannot serialize parent-observed Windows launcher start evidence: {error}"),
                Some("windowsLauncherStart"),
                false,
            )
        })?;
        let path = Path::new(&attempt.bundle_path).join(WINDOWS_LAUNCHER_START_FILE);
        write_bytes_synced(&path, &bytes)?;
        let (validated, start_digest) =
            self.validate_windows_launcher_start_evidence(attempt)?;
        self.registry.bind_supervisor_owner(
            &attempt.attempt_id,
            attempt.row_version,
            &AttemptSupervisorOwner::WindowsLauncherV1 {
                launcher_process_id: validated.launcher_process_id,
                launcher_process_creation_time_file_time:
                    validated.launcher_process_creation_time_file_time,
                launcher_image_digest: validated.launcher_image_digest,
                job_name: validated.job_name,
                start_evidence_digest: start_digest,
            },
            validated.observed_unix_ms,
        )
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
        self.windows.as_ref().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "committed windows_native Job has no configured Windows provider",
                Some("executionTarget"),
                true,
            )
        })?;
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
        let expected_request_digest =
            sha256_file(&Path::new(&attempt.bundle_path).join(RUNNER_REQUEST_FILE))
                .map_err(map_universal_error)?;
        if evidence.schema_version != RUNTIME_SCHEMA_VERSION
            || evidence.job_id != attempt.job_id
            || evidence.attempt_id != attempt.attempt_id
            || evidence.launch_token_digest != attempt.launch_token_digest
            || evidence.request_digest != expected_request_digest
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
        let requested_windows_context = plan
            .windows_context
            .unwrap_or_else(|| plan.windows_authority.canonical_context());
        let expected_token_class = match requested_windows_context.identity {
            super::WindowsExecutionIdentity::ActiveUser => super::WindowsTokenClass::ActiveUser,
            super::WindowsExecutionIdentity::Service
                if requested_windows_context.privilege == super::WindowsPayloadPrivilege::Elevated =>
            {
                super::WindowsTokenClass::Elevated
            }
            super::WindowsExecutionIdentity::Service => super::WindowsTokenClass::Limited,
        };
        let broker_backed = context.privileged_broker_digest.is_some();
        let expected_environment_source = match requested_windows_context.identity {
            super::WindowsExecutionIdentity::ActiveUser => "windows_active_user_profile_allowlist_v1",
            _ if broker_backed => "windows_privileged_broker_profile_allowlist_v1",
            _ => "windows_user_machine_profile_allowlist_v1",
        };
        if context.token_class != expected_token_class
            || context.environment_source != expected_environment_source
            || (plan.windows_context.is_some()
                && (context.payload_identity != Some(requested_windows_context.identity)
                    || context.payload_privilege != Some(requested_windows_context.privilege)))
            || (plan.windows_context.is_none()
                && (context.payload_identity.is_some() || context.payload_privilege.is_some()))
            || (requested_windows_context.transport_authority() == super::WindowsAuthority::Limited
                && broker_backed)
            || (requested_windows_context.identity == super::WindowsExecutionIdentity::ActiveUser
                && (!broker_backed || context.session_id.is_none()))
            || (requested_windows_context.identity != super::WindowsExecutionIdentity::ActiveUser
                && context.session_id.is_some())
            || (broker_backed && windows.privileged_broker.is_none())
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "committed Windows requested/effective authority or privileged provider binding is inconsistent",
                Some("windowsExecutionContext"),
                false,
            ));
        }
        if let Some(expected_broker_digest) = context.privileged_broker_digest.as_deref() {
            windows
                .privileged_broker
                .as_ref()
                .ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "broker-bound Windows execution context has no configured privileged broker",
                        Some("windowsExecutionContext.privilegedBrokerDigest"),
                        false,
                    )
                })?
                .verify_digest(expected_broker_digest)?;
        }
        let expected_job_name = format!("Ordivon.{}", attempt.attempt_id);
        let expected_request_digest =
            sha256_file(&Path::new(&attempt.bundle_path).join(RUNNER_REQUEST_FILE))
                .map_err(map_universal_error)?;
        let (expected_executable, expected_executable_digest, expected_executable_field) =
            if let Some(first_step) = plan.steps.first() {
                (
                    first_step.executable.as_str(),
                    first_step.executable_digest.as_str(),
                    "execution.steps[0].executable",
                )
            } else {
                (
                    plan.executable.as_str(),
                    plan.executable_digest.as_str(),
                    "execution.executable",
                )
            };
        let expected_image =
            windows_visible_path(Path::new(expected_executable), expected_executable_field)?;
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
        let token_authority_matches = match (
            requested_windows_context.identity,
            requested_windows_context.privilege,
        ) {
            (super::WindowsExecutionIdentity::Service, super::WindowsPayloadPrivilege::Limited) => {
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
                    && matches!(evidence.execution_identity.as_str(), "" | "service")
            }
            (super::WindowsExecutionIdentity::Service, super::WindowsPayloadPrivilege::Elevated) => {
                evidence.token_is_elevated
                    && evidence.token_integrity_level_rid >= 12288
                    && evidence.administrators_group_attributes != u32::MAX
                    && (evidence.administrators_group_attributes & 0x4) != 0
                    && (evidence.administrators_group_attributes & 0x10) == 0
                    && evidence.token_selection == "current_elevated"
                    && matches!(evidence.execution_identity.as_str(), "" | "service")
            }
            (super::WindowsExecutionIdentity::ActiveUser, super::WindowsPayloadPrivilege::Limited) => {
                !evidence.token_is_elevated
                    && evidence.token_integrity_level_rid <= 8192
                    && (evidence.administrators_group_attributes == u32::MAX
                        || (evidence.administrators_group_attributes & 0x4) == 0
                        || (evidence.administrators_group_attributes & 0x10) != 0)
                    && evidence.token_selection == "active_user"
                    && evidence.execution_identity == "active_user"
                    && evidence.session_id.is_some()
            }
            (super::WindowsExecutionIdentity::ActiveUser, super::WindowsPayloadPrivilege::Elevated) => {
                evidence.token_is_elevated
                    && evidence.token_integrity_level_rid >= 12288
                    && evidence.administrators_group_attributes != u32::MAX
                    && (evidence.administrators_group_attributes & 0x4) != 0
                    && (evidence.administrators_group_attributes & 0x10) == 0
                    && matches!(evidence.token_elevation_type, 1 | 2)
                    && matches!(evidence.token_selection.as_str(), "active_user_elevated_current" | "active_user_elevated_linked")
                    && evidence.execution_identity == "active_user"
                    && evidence.session_id.is_some()
            }
        };
        if evidence.schema_version != RUNTIME_SCHEMA_VERSION
            || evidence.job_id != attempt.job_id
            || evidence.attempt_id != attempt.attempt_id
            || evidence.launch_token_digest != attempt.launch_token_digest
            || evidence.request_digest != expected_request_digest
            || evidence.job_name != expected_job_name
            || evidence.launcher_process_id == 0
            || evidence.process_id == 0
            || evidence.process_creation_time_file_time == 0
            || evidence.image_digest != expected_executable_digest
            || evidence.token_user_sid != context.token_user_sid
            || (requested_windows_context.identity == super::WindowsExecutionIdentity::ActiveUser
                && evidence.session_id != context.session_id)
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
        Ok((evidence, start_digest))
    }

    fn bind_windows_start(&self, attempt: &AttemptRecord) -> RuntimeResult<AttemptRecord> {
        let (evidence, start_digest) = self.validate_windows_start_evidence(attempt)?;
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
        let launcher_image_digest = evidence.launcher_image_digest.clone().ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                "native Windows start evidence omitted launcher image digest",
                Some("windowsStart.launcherImageDigest"),
                false,
            )
        })?;
        if let Some(existing) = self
            .registry
            .attempt_supervisor_owner(&attempt.attempt_id)?
        {
            if !native_windows_owner_matches_launcher_identity(
                &existing,
                evidence.launcher_process_id,
                evidence.launcher_process_creation_time_file_time,
                evidence.launcher_image_digest.as_deref(),
                &evidence.job_name,
            ) {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::LaunchIdentityMismatch,
                    "native Windows target-start evidence disagrees with the parent-observed launcher owner",
                    Some("windowsStart"),
                    false,
                ));
            }
            return self.registry.get_attempt(&attempt.attempt_id);
        }
        self.registry.bind_supervisor_owner(
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
}
