impl Runtime {
    pub fn new(config: RuntimeConfig) -> RuntimeResult<Self> {
        let default_runtime_ms = config.executor.max_runtime_ms;
        Self::new_with_input_authorities_and_default_runtime(config, Vec::new(), default_runtime_ms)
    }

    /// Construction boundary for operator-owned immutable input authorities.
    /// Authority roots are Runtime-instance configuration, never action input.
    pub fn new_with_input_authorities(
        config: RuntimeConfig,
        input_authorities: Vec<InputAuthority>,
    ) -> RuntimeResult<Self> {
        let default_runtime_ms = config.executor.max_runtime_ms;
        Self::new_with_input_authorities_and_default_runtime(
            config,
            input_authorities,
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
        super::validate_logical_id(&config.node_id, "nodeId")?;
        config.executor.validate().map_err(map_universal_error)?;
        if default_runtime_ms == 0 || default_runtime_ms > config.executor.max_runtime_ms {
            return Err(RuntimeError::invalid(
                "defaultRuntimeMs must be positive and no greater than maxRuntimeMs",
                "defaultRuntimeMs",
            ));
        }
        if let Some(windows) = &config.windows {
            windows.validate()?;
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
            let root = OpenOptions::new()
                .read(true)
                .custom_flags(libc::O_DIRECTORY | libc::O_CLOEXEC | libc::O_NOFOLLOW)
                .open(&authority.root)
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
            lifecycle_lock: Arc::new(Mutex::new(())),
            control_terminal_lock: Arc::new(Mutex::new(())),
        };
        runtime.reconcile_recoverable_orphans()?;
        Ok(runtime)
    }

    pub fn registry(&self) -> &Registry {
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
