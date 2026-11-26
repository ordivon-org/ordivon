impl Registry {
    pub(super) fn initialize(config: RegistryConfig) -> RuntimeResult<Self> {
        config.validate()?;
        create_private_directory(&config.store_root)?;
        create_private_directory(&config.attempts_root())?;
        let mut admission_options = OpenOptions::new();
        admission_options.read(true).write(true).create(true).truncate(false);
        #[cfg(unix)]
        admission_options.mode(0o600);
        let admission_fence = admission_options
            .open(config.admission_fence_path())
            .map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryUnavailable,
                    format!("cannot open admission fence: {error}"),
                    None,
                    false,
                )
            })?;
        drop(admission_fence);
        set_private_file(&config.admission_fence_path())?;
        if let Some(parent) = config.db_path.parent() {
            create_private_directory(parent)?;
        }
        let registry = Self {
            config,
            write_gate: Arc::new(Mutex::new(())),
        };
        let mut connection = registry.open_connection()?;
        registry.ensure_wal_mode(&connection)?;
        registry.apply_migrations(&mut connection)?;
        registry.ensure_query_indexes(&mut connection)?;
        registry.ensure_execution_provider_storage(&mut connection)?;
        registry.ensure_attempt_supervisor_owner_storage(&mut connection)?;
        registry.ensure_host_dependency_storage(&mut connection)?;
        registry.ensure_runtime_release_storage(&mut connection)?;
        set_private_file(&registry.config.db_path)?;
        Ok(registry)
    }

    pub(super) fn config(&self) -> &RegistryConfig {
        &self.config
    }

    pub(super) fn lock_write_gate(
        &self,
        context: &'static str,
    ) -> RuntimeResult<RegistryWriteGuard<'_>> {
        let wait_started = Instant::now();
        let guard = self.write_gate.lock().map_err(|_| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryUnavailable,
                "Runtime Registry write gate is poisoned",
                None,
                true,
            )
        })?;
        Ok(RegistryWriteGuard {
            guard: Some(guard),
            context,
            wait_ms: elapsed_duration_ms(wait_started),
            transaction_started: None,
        })
    }

    pub(crate) fn open_connection(&self) -> RuntimeResult<Connection> {
        let flags = OpenFlags::SQLITE_OPEN_READ_WRITE
            | OpenFlags::SQLITE_OPEN_CREATE
            | OpenFlags::SQLITE_OPEN_NO_MUTEX;
        let connection = Connection::open_with_flags(&self.config.db_path, flags)
            .map_err(|error| safe_same_request_sql_error(error, "cannot open runtime registry"))?;
        connection
            .busy_timeout(Duration::from_millis(self.config.busy_timeout_ms))
            .map_err(|error| {
                safe_same_request_sql_error(error, "cannot set registry busy timeout")
            })?;
        connection
            .pragma_update(None, "foreign_keys", true)
            .map_err(|error| safe_same_request_sql_error(error, "cannot enable foreign keys"))?;
        connection
            .pragma_update(None, "trusted_schema", false)
            .map_err(|error| safe_same_request_sql_error(error, "cannot disable trusted schema"))?;
        connection
            .pragma_update(None, "synchronous", "FULL")
            .map_err(|error| safe_same_request_sql_error(error, "cannot set synchronous mode"))?;
        Ok(connection)
    }

    fn ensure_wal_mode(&self, connection: &Connection) -> RuntimeResult<()> {
        let mode: String = connection
            .query_row("PRAGMA journal_mode=WAL", [], |row| row.get(0))
            .map_err(|error| RuntimeError::from_sql(error, "cannot enable WAL mode"))?;
        if !mode.eq_ignore_ascii_case("wal") {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryUnavailable,
                format!("SQLite refused WAL mode and returned {mode}"),
                None,
                false,
            ));
        }
        Ok(())
    }

    fn ensure_query_indexes(&self, connection: &mut Connection) -> RuntimeResult<()> {
        let transaction = immediate(self, connection, "Runtime query index maintenance")?;
        transaction
            .execute(DROP_REDUNDANT_EVENT_SEQUENCE_INDEX_SQL, [])
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot drop redundant Job event lookup index")
            })?;
        for (sql, error_context) in [
            (
                JOB_CLIENT_REQUEST_LOOKUP_INDEX_SQL,
                "cannot ensure Job client request lookup index",
            ),
            (
                JOB_WORKSPACE_LOOKUP_INDEX_SQL,
                "cannot ensure Job Workspace lookup index",
            ),
            (
                JOB_PRINCIPAL_LOOKUP_INDEX_SQL,
                "cannot ensure Job principal lookup index",
            ),
            (
                JOB_RESOLUTION_STATUS_INDEX_SQL,
                "cannot ensure Job resolution status index",
            ),
            (
                ATTEMPT_RECOVERY_STATUS_INDEX_SQL,
                "cannot ensure Attempt recovery status index",
            ),
            (
                ARTIFACT_JOB_LOOKUP_INDEX_SQL,
                "cannot ensure Artifact Job lookup index",
            ),
        ] {
            transaction
                .execute(sql, [])
                .map_err(|error| RuntimeError::from_sql(error, error_context))?;
        }
        transaction.commit().map_err(|error| {
            RuntimeError::from_sql(error, "cannot commit Runtime query index maintenance")
        })?;
        let redundant_exists: bool = connection
            .query_row(
                "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='index' AND name=?1)",
                [REDUNDANT_EVENT_SEQUENCE_INDEX],
                |row| row.get(0),
            )
            .map_err(|error| {
                RuntimeError::from_sql(
                    error,
                    "cannot verify redundant Job event lookup index removal",
                )
            })?;
        if redundant_exists {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "redundant Job event lookup index remains after maintenance",
                None,
                false,
            ));
        }
        for (index, verify_context, missing_message) in [
            (
                JOB_CLIENT_REQUEST_LOOKUP_INDEX,
                "cannot verify Job client request lookup index",
                "Job client request lookup index is missing after maintenance",
            ),
            (
                JOB_WORKSPACE_LOOKUP_INDEX,
                "cannot verify Job Workspace lookup index",
                "Job Workspace lookup index is missing after maintenance",
            ),
            (
                JOB_PRINCIPAL_LOOKUP_INDEX,
                "cannot verify Job principal lookup index",
                "Job principal lookup index is missing after maintenance",
            ),
            (
                ARTIFACT_JOB_LOOKUP_INDEX,
                "cannot verify Artifact Job lookup index",
                "Artifact Job lookup index is missing after maintenance",
            ),
        ] {
            let exists: bool = connection
                .query_row(
                    "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='index' AND name=?1)",
                    [index],
                    |row| row.get(0),
                )
                .map_err(|error| RuntimeError::from_sql(error, verify_context))?;
            if !exists {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    missing_message,
                    None,
                    false,
                ));
            }
        }
        Ok(())
    }

    fn ensure_execution_provider_storage(&self, connection: &mut Connection) -> RuntimeResult<()> {
        let transaction = immediate(self, connection, "Execution Provider storage maintenance")?;
        transaction
            .execute_batch(EXECUTION_PROVIDER_STORAGE_SQL)
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot ensure Execution Provider storage")
            })?;
        transaction.commit().map_err(|error| {
            RuntimeError::from_sql(
                error,
                "cannot commit Execution Provider storage maintenance",
            )
        })?;
        let exists: bool = connection
            .query_row(
                "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name=?1)",
                [EXECUTION_PROVIDER_TABLE],
                |row| row.get(0),
            )
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot verify Execution Provider storage")
            })?;
        if !exists {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "Execution Provider storage is missing after maintenance",
                None,
                false,
            ));
        }
        Ok(())
    }

    fn ensure_attempt_supervisor_owner_storage(
        &self,
        connection: &mut Connection,
    ) -> RuntimeResult<()> {
        let transaction = immediate(self, connection, "Attempt Supervisor Owner storage maintenance")?;
        transaction
            .execute_batch(ATTEMPT_SUPERVISOR_OWNER_STORAGE_SQL)
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot ensure Attempt Supervisor Owner storage")
            })?;
        transaction.commit().map_err(|error| {
            RuntimeError::from_sql(
                error,
                "cannot commit Attempt Supervisor Owner storage maintenance",
            )
        })?;
        let exists: bool = connection
            .query_row(
                "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name=?1)",
                [ATTEMPT_SUPERVISOR_OWNER_TABLE],
                |row| row.get(0),
            )
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot verify Attempt Supervisor Owner storage")
            })?;
        if !exists {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "Attempt Supervisor Owner storage is missing after maintenance",
                None,
                false,
            ));
        }
        Ok(())
    }

    fn ensure_host_dependency_storage(&self, connection: &mut Connection) -> RuntimeResult<()> {
        let transaction = immediate(self, connection, "Host Dependency storage maintenance")?;
        transaction
            .execute_batch(HOST_DEPENDENCY_STORAGE_SQL)
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot ensure Host Dependency storage")
            })?;
        transaction.commit().map_err(|error| {
            RuntimeError::from_sql(error, "cannot commit Host Dependency storage maintenance")
        })?;
        let exists: bool = connection
            .query_row(
                "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name=?1)",
                [HOST_DEPENDENCY_TABLE],
                |row| row.get(0),
            )
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot verify Host Dependency storage")
            })?;
        if !exists {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "Host Dependency storage is missing after maintenance",
                None,
                false,
            ));
        }
        Ok(())
    }

    fn ensure_runtime_release_storage(&self, connection: &mut Connection) -> RuntimeResult<()> {
        let transaction = immediate(self, connection, "Runtime Release storage maintenance")?;
        transaction
            .execute_batch(RUNTIME_RELEASE_STORAGE_SQL)
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot ensure Runtime Release storage")
            })?;
        transaction.commit().map_err(|error| {
            RuntimeError::from_sql(error, "cannot commit Runtime Release storage maintenance")
        })?;
        for (kind, name) in [
            ("table", RUNTIME_RELEASE_TABLE),
            ("index", RUNTIME_RELEASE_INDEX),
        ] {
            let exists: bool = connection
                .query_row(
                    "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type=?1 AND name=?2)",
                    params![kind, name],
                    |row| row.get(0),
                )
                .map_err(|error| {
                    RuntimeError::from_sql(error, "cannot verify Runtime Release storage")
                })?;
            if !exists {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    format!("Runtime Release {kind} {name} is missing after maintenance"),
                    None,
                    false,
                ));
            }
        }
        Ok(())
    }

}
