// Cleanup and reconciliation of Runtime-owned prepared inputs and credentials.
impl Runtime {
    pub(super) fn reconcile_prepared_input_sets(&self, stale_age_ms: u64) -> RuntimeResult<()> {
        let root = self.executor.input_materializations_root();
        fs::create_dir_all(&root)
            .map_err(|error| io_error("create input materialization root", error))?;
        let now = SystemTime::now();
        for entry in
            fs::read_dir(&root).map_err(|error| io_error("enumerate prepared input sets", error))?
        {
            let entry = entry.map_err(|error| io_error("read prepared input set entry", error))?;
            let metadata = entry
                .metadata()
                .map_err(|error| io_error("inspect prepared input set", error))?;
            if !metadata.is_dir() {
                continue;
            }
            let name = entry.file_name();
            let Some(job_id) = name.to_str() else {
                continue;
            };
            if !job_id.starts_with("job-") {
                continue;
            }
            match self.registry.get_job(job_id) {
                Ok(job) => {
                    let plan: RuntimeExecutionPlan = serde_json::from_str(&job.execution_plan_json)
                        .map_err(|error| {
                            RuntimeError::new(
                                RuntimeErrorCode::RegistryCorrupt,
                                format!("stored execution plan is invalid: {error}"),
                                Some("executionPlan"),
                                false,
                            )
                        })?;
                    if plan.effective_inputs.is_empty() || plan.input_set_id.is_none() {
                        continue;
                    }
                    if self.ensure_job_input_ownership(job_id).is_err() {
                        // One corrupt Job must not block Runtime startup. Its Attempt owns
                        // deterministic failure/quarantine; never reopen current source authority.
                        continue;
                    }
                }
                Err(error) if error.code == RuntimeErrorCode::JobNotFound => {
                    let old_enough = metadata
                        .modified()
                        .ok()
                        .and_then(|modified| now.duration_since(modified).ok())
                        .is_some_and(|age| age.as_millis() >= u128::from(stale_age_ms));
                    if old_enough {
                        self.discard_prepared_input_set(&entry.path())?;
                    }
                }
                Err(error) => return Err(error),
            }
        }

        // Copy-in-progress state is guarded by a process-held flock. A hard crash releases
        // the lock automatically, allowing stale staging state to be collected without
        // guessing how long a valid large copy may take.
        for entry in fs::read_dir(&root)
            .map_err(|error| io_error("enumerate input staging leases", error))?
        {
            let entry = entry.map_err(|error| io_error("read input staging lease entry", error))?;
            let name = entry.file_name();
            let Some(job_id) = name
                .to_str()
                .and_then(|name| name.strip_prefix('.'))
                .and_then(|name| name.strip_suffix(".lease"))
                .filter(|job_id| job_id.starts_with("job-"))
            else {
                continue;
            };
            let metadata = fs::symlink_metadata(entry.path())
                .map_err(|error| io_error("inspect input staging lease", error))?;
            if metadata.file_type().is_symlink() || !metadata.is_file() {
                continue;
            }
            let old_enough = metadata
                .modified()
                .ok()
                .and_then(|modified| now.duration_since(modified).ok())
                .is_some_and(|age| age.as_millis() >= u128::from(stale_age_ms));
            if !old_enough {
                continue;
            }
            let lease = match OpenOptions::new().read(true).write(true).open(entry.path()) {
                Ok(lease) => lease,
                Err(_) => continue,
            };
            if lease.try_lock().is_err() {
                continue;
            }
            let prefix = format!(".{job_id}.staging-");
            for staging in fs::read_dir(&root)
                .map_err(|error| io_error("enumerate abandoned input staging directories", error))?
            {
                let staging = staging
                    .map_err(|error| io_error("read abandoned input staging entry", error))?;
                let staging_name = staging.file_name();
                if staging_name
                    .to_str()
                    .is_some_and(|name| name.starts_with(&prefix))
                    && staging
                        .file_type()
                        .map(|kind| kind.is_dir())
                        .unwrap_or(false)
                {
                    fs::remove_dir_all(staging.path()).map_err(|error| {
                        io_error("remove abandoned input staging directory", error)
                    })?;
                }
            }
            fs::remove_file(entry.path())
                .map_err(|error| io_error("remove abandoned input staging lease", error))?;
            drop(lease);
            sync_directory(&root)?;
        }
        Ok(())
    }

    pub(super) fn reconcile_prepared_credential_sets(
        &self,
        stale_age_ms: u64,
    ) -> RuntimeResult<()> {
        let root = self.executor.credential_materializations_root();
        fs::create_dir_all(&root)
            .map_err(|error| io_error("create credential materialization root", error))?;
        let now = SystemTime::now();

        for entry in fs::read_dir(&root)
            .map_err(|error| io_error("enumerate prepared credential sets", error))?
        {
            let entry =
                entry.map_err(|error| io_error("read prepared credential set entry", error))?;
            let metadata = entry
                .metadata()
                .map_err(|error| io_error("inspect prepared credential set", error))?;
            if !metadata.is_dir() {
                continue;
            }
            let name = entry.file_name();
            let Some(job_id) = name.to_str() else {
                continue;
            };
            if !job_id.starts_with("job-") {
                continue;
            }
            match self.registry.get_job(job_id) {
                Ok(job) => {
                    if job.resolution.is_some() {
                        self.discard_prepared_credential_set(&entry.path())?;
                        continue;
                    }
                    let plan: RuntimeExecutionPlan = serde_json::from_str(&job.execution_plan_json)
                        .map_err(|error| {
                            RuntimeError::new(
                                RuntimeErrorCode::RegistryCorrupt,
                                format!("stored execution plan is invalid: {error}"),
                                Some("executionPlan"),
                                false,
                            )
                        })?;
                    if plan.credential_set_id.is_none() {
                        continue;
                    }
                    if self.ensure_job_credential_ownership(job_id).is_err() {
                        // The committed unresolved Job owns its frozen encrypted credential
                        // snapshot. Never reopen the current credential authority during recovery.
                        continue;
                    }
                }
                Err(error) if error.code == RuntimeErrorCode::JobNotFound => {
                    let old_enough = metadata
                        .modified()
                        .ok()
                        .and_then(|modified| now.duration_since(modified).ok())
                        .is_some_and(|age| age.as_millis() >= u128::from(stale_age_ms));
                    if old_enough {
                        self.discard_prepared_credential_set(&entry.path())?;
                    }
                }
                Err(error) => return Err(error),
            }
        }

        let owned_root = self.executor.job_credentials_root();
        fs::create_dir_all(&owned_root)
            .map_err(|error| io_error("create Job credential ownership root", error))?;
        for entry in fs::read_dir(&owned_root)
            .map_err(|error| io_error("enumerate Job-owned encrypted credentials", error))?
        {
            let entry = entry
                .map_err(|error| io_error("read Job-owned encrypted credential entry", error))?;
            let metadata = entry
                .metadata()
                .map_err(|error| io_error("inspect Job-owned encrypted credential set", error))?;
            if !metadata.is_dir() {
                continue;
            }
            let name = entry.file_name();
            let Some(job_id) = name.to_str() else {
                continue;
            };
            if !job_id.starts_with("job-") {
                continue;
            }
            match self.registry.get_job(job_id) {
                Ok(job) if job.resolution.is_some() => {
                    fs::remove_dir_all(entry.path()).map_err(|error| {
                        io_error("retire resolved Job encrypted credentials", error)
                    })?;
                    sync_directory(&owned_root)?;
                }
                Ok(_) => {}
                Err(error) if error.code == RuntimeErrorCode::JobNotFound => {
                    let old_enough = metadata
                        .modified()
                        .ok()
                        .and_then(|modified| now.duration_since(modified).ok())
                        .is_some_and(|age| age.as_millis() >= u128::from(stale_age_ms));
                    if old_enough {
                        fs::remove_dir_all(entry.path()).map_err(|error| {
                            io_error("remove unowned Job encrypted credentials", error)
                        })?;
                        sync_directory(&owned_root)?;
                    }
                }
                Err(error) => return Err(error),
            }
        }

        for entry in fs::read_dir(&root)
            .map_err(|error| io_error("enumerate credential staging leases", error))?
        {
            let entry =
                entry.map_err(|error| io_error("read credential staging lease entry", error))?;
            let name = entry.file_name();
            let Some(job_id) = name
                .to_str()
                .and_then(|name| name.strip_prefix('.'))
                .and_then(|name| name.strip_suffix(".lease"))
                .filter(|job_id| job_id.starts_with("job-"))
            else {
                continue;
            };
            let metadata = fs::symlink_metadata(entry.path())
                .map_err(|error| io_error("inspect credential staging lease", error))?;
            if metadata.file_type().is_symlink() || !metadata.is_file() {
                continue;
            }
            let old_enough = metadata
                .modified()
                .ok()
                .and_then(|modified| now.duration_since(modified).ok())
                .is_some_and(|age| age.as_millis() >= u128::from(stale_age_ms));
            if !old_enough {
                continue;
            }
            let lease = match OpenOptions::new().read(true).write(true).open(entry.path()) {
                Ok(lease) => lease,
                Err(_) => continue,
            };
            if lease.try_lock().is_err() {
                continue;
            }
            let prefix = format!(".{job_id}.staging-");
            for staging in fs::read_dir(&root).map_err(|error| {
                io_error("enumerate abandoned credential staging directories", error)
            })? {
                let staging = staging
                    .map_err(|error| io_error("read abandoned credential staging entry", error))?;
                let staging_name = staging.file_name();
                if staging_name
                    .to_str()
                    .is_some_and(|name| name.starts_with(&prefix))
                    && staging
                        .file_type()
                        .map(|kind| kind.is_dir())
                        .unwrap_or(false)
                {
                    fs::remove_dir_all(staging.path()).map_err(|error| {
                        io_error("remove abandoned credential staging directory", error)
                    })?;
                }
            }
            fs::remove_file(entry.path())
                .map_err(|error| io_error("remove abandoned credential staging lease", error))?;
            drop(lease);
            sync_directory(&root)?;
        }
        Ok(())
    }
}
