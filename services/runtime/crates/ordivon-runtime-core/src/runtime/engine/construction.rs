impl Runtime {
    pub fn new(config: RuntimeConfig) -> RuntimeResult<Self> {
        let default_runtime_ms = config.executor.max_runtime_ms;
        Self::new_with_authorities_and_default_runtime(
            config,
            Vec::new(),
            Vec::new(),
            default_runtime_ms,
        )
    }

    /// Test convenience for operator-owned immutable input authorities.
    /// Production construction uses the explicit default-runtime boundary.
    #[cfg(test)]
    pub(crate) fn new_with_input_authorities(
        config: RuntimeConfig,
        input_authorities: Vec<InputAuthority>,
    ) -> RuntimeResult<Self> {
        let default_runtime_ms = config.executor.max_runtime_ms;
        Self::new_with_authorities_and_default_runtime(
            config,
            input_authorities,
            Vec::new(),
            default_runtime_ms,
        )
    }

    /// Construction boundary for an operator-owned default timeout distinct from the hard maximum.
    /// Existing constructors intentionally preserve the historical default=max behavior.
    pub fn new_with_input_authorities_and_default_runtime(
        config: RuntimeConfig,
        input_authorities: Vec<InputAuthority>,
        default_runtime_ms: u64,
    ) -> RuntimeResult<Self> {
        Self::new_with_authorities_and_default_runtime(
            config,
            input_authorities,
            Vec::new(),
            default_runtime_ms,
        )
    }

    /// Construction boundary for artifact and credential authorities.
    ///
    /// Artifact authorities remain caller-digest-bound. Credential authorities are principal-
    /// authorized opaque-name sources whose content digests stay Runtime-internal.
    pub fn new_with_authorities_and_default_runtime(
        config: RuntimeConfig,
        input_authorities: Vec<InputAuthority>,
        credential_authorities: Vec<CredentialAuthority>,
        default_runtime_ms: u64,
    ) -> RuntimeResult<Self> {
        Self::new_with_authorities_default_runtime_and_workspace_headroom(
            config, input_authorities, credential_authorities, default_runtime_ms, None,
        )
    }

    pub fn new_with_authorities_default_runtime_and_workspace_headroom(
        config: RuntimeConfig,
        input_authorities: Vec<InputAuthority>,
        credential_authorities: Vec<CredentialAuthority>,
        default_runtime_ms: u64,
        workspace_headroom: Option<WorkspaceHeadroomConfig>,
    ) -> RuntimeResult<Self> {
        super::validate_logical_id(&config.node_id, "nodeId")?;
        config.executor.validate().map_err(map_universal_error)?;
        if default_runtime_ms == 0 || default_runtime_ms > config.executor.max_runtime_ms {
            return Err(RuntimeError::invalid(
                "defaultRuntimeMs must be positive and no greater than maxRuntimeMs",
                "defaultRuntimeMs",
            ));
        }
        if config.windows.is_some() && !cfg!(windows) {
            return Err(RuntimeError::invalid(
                "Windows execution provider is supported only on a native Windows Runtime; route windows_native work to that Runtime instead",
                "windows",
            ));
        }
        if let Some(windows) = &config.windows {
            windows.validate()?;
        }
        if let Some(headroom) = workspace_headroom.as_ref() {
            if !headroom.path.is_absolute() {
                return Err(RuntimeError::invalid("workspace headroom path must be absolute", "workspaceHeadroom.path"));
            }
            if headroom.minimum_free_bytes == 0 {
                return Err(RuntimeError::invalid("workspace minimum free bytes must be positive", "workspaceHeadroom.minimumFreeBytes"));
            }
        }
        if config.startup_grace_ms == 0 {
            return Err(RuntimeError::invalid(
                "startupGraceMs must be positive",
                "startupGraceMs",
            ));
        }
        if Instant::now()
            .checked_add(Duration::from_millis(config.startup_grace_ms))
            .is_none()
        {
            return Err(RuntimeError::invalid(
                "startupGraceMs exceeds platform monotonic clock range",
                "startupGraceMs",
            ));
        }
        let mut configured_input_authorities = BTreeMap::new();
        for authority in input_authorities {
            validate_input_authority_name(&authority.name, "inputAuthorities.name")?;
            if !authority.root.is_absolute() {
                return Err(RuntimeError::invalid(
                    "input authority root must be absolute",
                    "inputAuthorities.root",
                ));
            }
            let root = open_directory_nofollow(&authority.root)
                .map_err(|error| io_error("open input authority root", error))?;
            let metadata = root
                .metadata()
                .map_err(|error| io_error("inspect input authority root", error))?;
            if !metadata.is_dir() {
                return Err(RuntimeError::invalid(
                    "input authority root must be a directory",
                    "inputAuthorities.root",
                ));
            }
            if configured_input_authorities
                .insert(
                    authority.name,
                    OpenedInputAuthority {
                        root: Arc::new(root),
                    },
                )
                .is_some()
            {
                return Err(RuntimeError::invalid(
                    "input authority names must be unique",
                    "inputAuthorities.name",
                ));
            }
        }
        let mut configured_credential_authorities = BTreeMap::new();
        for authority in credential_authorities {
            validate_input_authority_name(
                &authority.name,
                "credentialAuthorities.name",
            )?;
            if !authority.root.is_absolute() {
                return Err(RuntimeError::invalid(
                    "credential authority root must be absolute",
                    "credentialAuthorities.root",
                ));
            }
            if authority.allowed_principals.is_empty() {
                return Err(RuntimeError::invalid(
                    "credential authority must allow at least one authenticated principal",
                    "credentialAuthorities.allowedPrincipals",
                ));
            }
            let mut allowed_principals = BTreeSet::new();
            for principal in authority.allowed_principals {
                if principal.is_empty()
                    || principal.len() > 256
                    || principal.chars().any(char::is_control)
                {
                    return Err(RuntimeError::invalid(
                        "credential authority principal must be non-empty, control-free, and at most 256 characters",
                        "credentialAuthorities.allowedPrincipals",
                    ));
                }
                if !allowed_principals.insert(principal) {
                    return Err(RuntimeError::invalid(
                        "credential authority allowed principals must be unique",
                        "credentialAuthorities.allowedPrincipals",
                    ));
                }
            }
            let root = open_directory_nofollow(&authority.root)
                .map_err(|error| io_error("open credential authority root", error))?;
            let metadata = root
                .metadata()
                .map_err(|error| io_error("inspect credential authority root", error))?;
            if !metadata.is_dir() {
                return Err(RuntimeError::invalid(
                    "credential authority root must be a directory",
                    "credentialAuthorities.root",
                ));
            }
            if configured_credential_authorities
                .insert(
                    authority.name,
                    OpenedCredentialAuthority {
                        root: Arc::new(root),
                        allowed_principals,
                    },
                )
                .is_some()
            {
                return Err(RuntimeError::invalid(
                    "credential authority names must be unique",
                    "credentialAuthorities.name",
                ));
            }
        }
        let registry = Registry::initialize(config.registry)?;
        let execution_path = configured_execution_path()?;
        let execution_home = configured_execution_home()?;
        let runtime = Self {
            node_identity: super::RuntimeNodeIdentity {
                node_id: config.node_id,
                platform: super::RuntimeNodePlatform::current(),
                native: true,
            },
            registry,
            executor: config.executor,
            default_runtime_ms,
            startup_grace_ms: config.startup_grace_ms,
            execution_path,
            execution_home,
            windows: config.windows,
            input_authorities: configured_input_authorities,
            credential_authorities: configured_credential_authorities,
            workspace_headroom,
            lifecycle_lock: Arc::new(Mutex::new(())),
            control_terminal_lock: Arc::new(Mutex::new(())),
        };
        runtime.reconcile_recoverable_orphans()?;
        Ok(runtime)
    }

    #[cfg(test)]
    pub(crate) fn registry(&self) -> &Registry {
        &self.registry
    }

    pub fn inspect_job(
        &self,
        job_id: &str,
        event_limit: u32,
    ) -> RuntimeResult<super::RuntimeJobInspection> {
        let registry = self.registry.config();
        super::inspection::inspect_job(
            &super::RuntimeInspectionConfig {
                db_path: registry.db_path.clone(),
                busy_timeout_ms: registry.busy_timeout_ms,
            },
            job_id,
            event_limit,
            false,
        )
    }

    fn lock_lifecycle(&self) -> RuntimeResult<MutexGuard<'_, ()>> {
        self.lifecycle_lock.lock().map_err(|_| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryUnavailable,
                "Workspace lifecycle lock is poisoned",
                None,
                true,
            )
        })
    }

    fn lock_control_terminal(&self) -> RuntimeResult<MutexGuard<'_, ()>> {
        self.control_terminal_lock.lock().map_err(|_| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryUnavailable,
                "Runtime control-terminal lock is poisoned",
                None,
                true,
            )
        })
    }

}
