impl Registry {
    pub(super) fn get_job(&self, job_id: &str) -> RuntimeResult<RuntimeJobRecord> {
        let connection = self.open_connection()?;
        RegistryStorageBoundary::load_job(&connection, job_id)
    }

    pub(crate) fn execution_provider(
        &self,
        job_id: &str,
    ) -> RuntimeResult<Option<ExecutionProviderSnapshot>> {
        let connection = self.open_connection()?;
        let job = RegistryStorageBoundary::load_job(&connection, job_id)?;
        let workspace_snapshot: serde_json::Value =
            serde_json::from_str(&job.workspace_snapshot_json).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    format!("stored Workspace snapshot is invalid: {error}"),
                    Some("workspaceSnapshot"),
                    false,
                )
            })?;
        let committed_digest = match workspace_snapshot.get("executionProviderDigest") {
            None => None,
            Some(serde_json::Value::String(value)) => {
                if validate_digest(value, "executionProviderDigest").is_err() {
                    return Err(RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "stored execution provider commitment digest is invalid",
                        Some("workspaceSnapshot.executionProviderDigest"),
                        false,
                    ));
                }
                Some(value.as_str())
            }
            Some(_) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "stored execution provider commitment digest is not text",
                    Some("workspaceSnapshot.executionProviderDigest"),
                    false,
                ));
            }
        };
        let host_committed_digest = match workspace_snapshot.get("hostDependenciesDigest") {
            None => None,
            Some(serde_json::Value::String(value)) => {
                if validate_digest(value, "hostDependenciesDigest").is_err() {
                    return Err(RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "stored Host Dependency commitment digest is invalid",
                        Some("workspaceSnapshot.hostDependenciesDigest"),
                        false,
                    ));
                }
                Some(value.as_str())
            }
            Some(_) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "stored Host Dependency commitment digest is not text",
                    Some("workspaceSnapshot.hostDependenciesDigest"),
                    false,
                ));
            }
        };
        let host_row_digest: Option<String> = connection
            .query_row(
                "SELECT bindings_digest FROM job_host_dependencies WHERE job_id=?1",
                [job_id],
                |row| row.get(0),
            )
            .optional()
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot read Host Dependency commitment")
            })?;
        let host_digest = match (host_committed_digest, host_row_digest.as_deref()) {
            (None, None) => None,
            (None, Some(_)) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Host Dependency row exists without a committed Job marker",
                    Some("hostDependencies"),
                    false,
                ));
            }
            (Some(_), None) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "committed Host Dependency row is missing",
                    Some("hostDependencies"),
                    false,
                ));
            }
            (Some(committed), Some(row_digest)) if committed == row_digest => Some(committed),
            (Some(_), Some(_)) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Host Dependency row digest does not match the Job commitment",
                    Some("hostDependencies"),
                    false,
                ));
            }
        };
        let release_committed_digest = match workspace_snapshot.get("runtimeReleaseEffectDigest") {
            None => None,
            Some(serde_json::Value::String(value)) => {
                if validate_digest(value, "runtimeReleaseEffectDigest").is_err() {
                    return Err(RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "stored Runtime Release commitment digest is invalid",
                        Some("workspaceSnapshot.runtimeReleaseEffectDigest"),
                        false,
                    ));
                }
                Some(value.as_str())
            }
            Some(_) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "stored Runtime Release commitment digest is not text",
                    Some("workspaceSnapshot.runtimeReleaseEffectDigest"),
                    false,
                ));
            }
        };
        let release_row_digest: Option<String> = connection
            .query_row(
                "SELECT binding_digest FROM job_runtime_release_effects WHERE job_id=?1",
                [job_id],
                |row| row.get(0),
            )
            .optional()
            .map_err(|error| {
                RuntimeError::from_sql(error, "cannot read Runtime Release commitment")
            })?;
        let release_digest = match (release_committed_digest, release_row_digest.as_deref()) {
            (None, None) => None,
            (None, Some(_)) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Runtime Release row exists without a committed Job marker",
                    Some("runtimeReleaseEffect"),
                    false,
                ));
            }
            (Some(_), None) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "committed Runtime Release row is missing",
                    Some("runtimeReleaseEffect"),
                    false,
                ));
            }
            (Some(committed), Some(row_digest)) if committed == row_digest => Some(committed),
            (Some(_), Some(_)) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Runtime Release row digest does not match the Job commitment",
                    Some("runtimeReleaseEffect"),
                    false,
                ));
            }
        };
        let row: Option<(String, String)> = connection
            .query_row(
                "SELECT snapshot_json,snapshot_digest FROM job_execution_providers WHERE job_id=?1",
                [job_id],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot read Job execution provider"))?;
        let (committed_digest, snapshot_json, snapshot_digest) = match (committed_digest, row) {
            (None, None) => return Ok(None),
            (None, Some(_)) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "execution provider row exists without a committed Job marker",
                    Some("executionProvider"),
                    false,
                ));
            }
            (Some(_), None) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "committed Job execution provider row is missing",
                    Some("executionProvider"),
                    false,
                ));
            }
            (Some(committed_digest), Some((snapshot_json, snapshot_digest))) => {
                (committed_digest, snapshot_json, snapshot_digest)
            }
        };
        if snapshot_digest != committed_digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "execution provider row digest does not match the Job commitment",
                Some("executionProvider"),
                false,
            ));
        }
        let identity_bindings = match (host_digest, release_digest) {
            (Some(host_digest), None) => OperationIdentityBindings::ProviderWithHostDependencies {
                provider_digest: committed_digest,
                host_dependencies_digest: host_digest,
            },
            (None, Some(release_digest)) => OperationIdentityBindings::ProviderWithRuntimeRelease {
                provider_digest: committed_digest,
                runtime_release_digest: release_digest,
            },
            (None, None) => OperationIdentityBindings::Provider {
                provider_digest: committed_digest,
            },
            (Some(_), Some(_)) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Job cannot bind both Host Dependencies and Runtime Release side truth",
                    Some("hostDependencies"),
                    false,
                ));
            }
        };
        let expected_operation_digest = JobIdentityContract::operation_digest(
            &job.request_digest,
            &job.execution_plan_digest,
            identity_bindings,
        );
        if job.operation_digest != expected_operation_digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "execution provider commitment does not match the Job operation identity",
                Some("executionProvider"),
                false,
            ));
        }
        if sha256_bytes(snapshot_json.as_bytes()) != snapshot_digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "stored execution provider snapshot digest does not match its bytes",
                Some("executionProvider"),
                false,
            ));
        }
        let snapshot: ExecutionProviderSnapshot =
            serde_json::from_str(&snapshot_json).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    format!("stored execution provider snapshot is invalid: {error}"),
                    Some("executionProvider"),
                    false,
                )
            })?;
        validate_execution_provider_snapshot(&snapshot, "executionProvider").map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("stored execution provider snapshot violates its contract: {error}"),
                Some("executionProvider"),
                false,
            )
        })?;
        Ok(Some(snapshot))
    }

    pub(crate) fn host_dependencies(
        &self,
        job_id: &str,
    ) -> RuntimeResult<Vec<HostDependencyBinding>> {
        let connection = self.open_connection()?;
        let job = RegistryStorageBoundary::load_job(&connection, job_id)?;
        let workspace_snapshot: serde_json::Value =
            serde_json::from_str(&job.workspace_snapshot_json).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    format!("stored Workspace snapshot is invalid: {error}"),
                    Some("workspaceSnapshot"),
                    false,
                )
            })?;
        let committed_digest = match workspace_snapshot.get("hostDependenciesDigest") {
            None => None,
            Some(serde_json::Value::String(value)) => {
                validate_digest(value, "hostDependenciesDigest").map_err(|_| {
                    RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "stored Host Dependency commitment digest is invalid",
                        Some("workspaceSnapshot.hostDependenciesDigest"),
                        false,
                    )
                })?;
                Some(value.clone())
            }
            Some(_) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "stored Host Dependency commitment digest is not text",
                    Some("workspaceSnapshot.hostDependenciesDigest"),
                    false,
                ));
            }
        };
        let row: Option<(String, String)> = connection
            .query_row(
                "SELECT bindings_json,bindings_digest FROM job_host_dependencies WHERE job_id=?1",
                [job_id],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot read Job Host Dependencies"))?;
        let (json, digest) = match (committed_digest.as_deref(), row) {
            (None, None) => return Ok(Vec::new()),
            (None, Some(_)) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Host Dependency row exists without a committed Job marker",
                    Some("hostDependencies"),
                    false,
                ));
            }
            (Some(_), None) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "committed Host Dependency row is missing",
                    Some("hostDependencies"),
                    false,
                ));
            }
            (Some(committed), Some((json, digest))) if committed == digest => (json, digest),
            (Some(_), Some(_)) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Host Dependency row digest does not match the Job commitment",
                    Some("hostDependencies"),
                    false,
                ));
            }
        };
        if sha256_bytes(json.as_bytes()) != digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "stored Host Dependency digest does not match its bytes",
                Some("hostDependencies"),
                false,
            ));
        }
        let bindings: Vec<HostDependencyBinding> =
            serde_json::from_str(&json).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    format!("stored Host Dependency bindings are invalid: {error}"),
                    Some("hostDependencies"),
                    false,
                )
            })?;
        validate_host_dependency_bindings(&bindings, "hostDependencies").map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("stored Host Dependency bindings violate their contract: {error}"),
                Some("hostDependencies"),
                false,
            )
        })?;
        Ok(bindings)
    }

    pub(super) fn get_attempt(&self, attempt_id: &str) -> RuntimeResult<AttemptRecord> {
        let connection = self.open_connection()?;
        RegistryStorageBoundary::load_attempt(&connection, attempt_id)
    }

    #[cfg(any(test, feature = "operator-tools"))]
    pub(super) fn get_reservation(&self, attempt_id: &str) -> RuntimeResult<ReservationRecord> {
        let connection = self.open_connection()?;
        RegistryStorageBoundary::load_reservation(&connection, attempt_id)
    }

    pub(super) fn get_latest_attempt(&self, job_id: &str) -> RuntimeResult<Option<AttemptRecord>> {
        let connection = self.open_connection()?;
        let attempt_id: Option<String> = connection
            .query_row(
                "SELECT attempt_id FROM attempts WHERE job_id=?1 ORDER BY attempt_number DESC LIMIT 1",
                [job_id],
                |row| row.get(0),
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot find latest Attempt"))?;
        attempt_id
            .map(|attempt_id| RegistryStorageBoundary::load_attempt(&connection, &attempt_id))
            .transpose()
    }

    pub(super) fn get_artifact(
        &self,
        job_id: &str,
        artifact_id: &str,
    ) -> RuntimeResult<RuntimeArtifactRecord> {
        let connection = self.open_connection()?;
        connection
            .query_row(
                "SELECT artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms FROM artifacts WHERE job_id=?1 AND artifact_id=?2",
                params![job_id, artifact_id],
                |row| {
                    Ok(RuntimeArtifactRecord {
                        artifact_id: row.get(0)?,
                        job_id: row.get(1)?,
                        attempt_id: row.get(2)?,
                        kind: row.get(3)?,
                        relative_path: row.get(4)?,
                        digest: row.get(5)?,
                        media_type: row.get(6)?,
                        byte_length: row.get(7)?,
                        truncated: row.get::<_, i64>(8)? != 0,
                        created_at_ms: row.get(9)?,
                    })
                },
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot load Artifact"))?
            .ok_or_else(|| RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Artifact not found for Job",
                Some("artifactId"),
                false,
            ))
    }

    pub(crate) fn job_snapshot(&self, job_id: &str) -> RuntimeResult<JobSnapshot> {
        let connection = self.open_connection()?;
        load_job_snapshot(&connection, job_id)
    }

    #[cfg(test)]
    pub(super) fn project_job(&self, job_id: &str) -> RuntimeResult<JobProjection> {
        Ok(self.job_snapshot(job_id)?.projection)
    }

    pub(super) fn active_job_ids_for_workspace(&self, workspace_id: &str) -> RuntimeResult<Vec<String>> {
        let connection = self.open_connection()?;
        let mut statement = connection
            .prepare(
                "SELECT DISTINCT jobs.job_id FROM jobs LEFT JOIN attempts ON attempts.job_id=jobs.job_id LEFT JOIN concurrency_reservations ON concurrency_reservations.attempt_id=attempts.attempt_id WHERE jobs.workspace_id=?1 AND (jobs.resolution IS NULL OR concurrency_reservations.state IN ('active','held_orphaned')) ORDER BY jobs.created_at_ms DESC,jobs.job_id DESC",
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot prepare active Workspace Job query"))?;
        let rows = statement
            .query_map([workspace_id], |row| row.get::<_, String>(0))
            .map_err(|error| RuntimeError::from_sql(error, "cannot query active Workspace Jobs"))?;
        rows.map(|row| {
            row.map_err(|error| RuntimeError::from_sql(error, "cannot decode active Workspace Job"))
        })
        .collect()
    }

    pub(super) fn list_workspace_reconciliation_attempts(
        &self,
        workspace_id: &str,
        limit: u32,
    ) -> RuntimeResult<Vec<AttemptRecord>> {
        if limit == 0 {
            return Err(RuntimeError::invalid("limit must be positive", "limit"));
        }
        let connection = self.open_connection()?;
        let mut statement = connection
            .prepare(
                "SELECT DISTINCT a.attempt_id,a.job_id,a.attempt_number,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.bundle_digest,a.boot_id,a.unit_name,a.invocation_id,a.control_group,a.main_pid,a.process_start_identity,a.runner_start_digest,a.result_digest,a.exit_code,a.infrastructure_error_digest,a.created_at_ms,a.started_at_ms,a.finished_at_ms,a.row_version FROM attempts a JOIN jobs j ON j.job_id=a.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE j.workspace_id=?1 AND (a.attempt_id=j.current_attempt_id OR r.state IN ('active','held_orphaned')) ORDER BY a.created_at_ms DESC,a.attempt_id DESC LIMIT ?2",
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot prepare Workspace reconciliation scan"))?;
        let rows = statement
            .query_map(params![workspace_id, limit], RegistryStorageBoundary::decode_attempt_row)
            .map_err(|error| RuntimeError::from_sql(error, "cannot scan Workspace Attempts"))?;
        rows.map(|row| {
            row.map_err(|error| RuntimeError::from_sql(error, "cannot decode Workspace Attempt"))?
                .into_record()
        })
        .collect()
    }

    pub(super) fn list_jobs(
        &self,
        request: &RuntimeJobListRequest,
    ) -> RuntimeResult<RuntimeJobListResult> {
        if request.limit == 0 || request.limit > MAX_RUNTIME_LIST_LIMIT {
            return Err(RuntimeError::invalid(
                format!("limit must be in 1..={MAX_RUNTIME_LIST_LIMIT}"),
                "limit",
            ));
        }
        if let Some(client_request_id) = request.client_request_id.as_deref() {
            validate_client_request_id(client_request_id, "clientRequestId")?;
        }
        if let Some(workspace_id) = request.workspace_id.as_deref() {
            validate_identifier(workspace_id, "workspaceId")?;
        }
        let connection = self.open_connection()?;
        let transaction = connection.unchecked_transaction().map_err(|error| {
            RuntimeError::from_sql(error, "cannot begin Job list read snapshot")
        })?;
        let fetch_limit = request.limit + 1;
        let mut jobs = Vec::new();
        match (
            &request.client_request_id,
            &request.workspace_id,
            &request.cursor,
        ) {
            (Some(client_request_id), Some(workspace_id), Some(cursor)) => {
                let mut statement = transaction
                    .prepare(
                        "SELECT job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version FROM jobs WHERE client_request_id=?1 AND workspace_id=?2 AND (created_at_ms<?3 OR (created_at_ms=?3 AND job_id<?4)) ORDER BY created_at_ms DESC,job_id DESC LIMIT ?5",
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot prepare identity-bounded Job list"))?;
                let rows = statement
                    .query_map(
                        params![
                            client_request_id,
                            workspace_id,
                            cursor.created_at_ms,
                            cursor.job_id,
                            fetch_limit
                        ],
                        RegistryStorageBoundary::decode_job_row,
                    )
                    .map_err(|error| {
                        RuntimeError::from_sql(error, "cannot query identity-bounded Job list")
                    })?;
                for row in rows {
                    jobs.push(
                        row.map_err(|error| {
                            RuntimeError::from_sql(error, "cannot decode Job row")
                        })?
                        .into_record()?,
                    );
                }
            }
            (Some(client_request_id), Some(workspace_id), None) => {
                let mut statement = transaction
                    .prepare(
                        "SELECT job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version FROM jobs WHERE client_request_id=?1 AND workspace_id=?2 ORDER BY created_at_ms DESC,job_id DESC LIMIT ?3",
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot prepare identity-bounded Job list"))?;
                let rows = statement
                    .query_map(
                        params![client_request_id, workspace_id, fetch_limit],
                        RegistryStorageBoundary::decode_job_row,
                    )
                    .map_err(|error| {
                        RuntimeError::from_sql(error, "cannot query identity-bounded Job list")
                    })?;
                for row in rows {
                    jobs.push(
                        row.map_err(|error| {
                            RuntimeError::from_sql(error, "cannot decode Job row")
                        })?
                        .into_record()?,
                    );
                }
            }
            (Some(client_request_id), None, Some(cursor)) => {
                let mut statement = transaction
                    .prepare(
                        "SELECT job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version FROM jobs WHERE client_request_id=?1 AND (created_at_ms<?2 OR (created_at_ms=?2 AND job_id<?3)) ORDER BY created_at_ms DESC,job_id DESC LIMIT ?4",
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot prepare filtered Job list"))?;
                let rows = statement
                    .query_map(
                        params![
                            client_request_id,
                            cursor.created_at_ms,
                            cursor.job_id,
                            fetch_limit
                        ],
                        RegistryStorageBoundary::decode_job_row,
                    )
                    .map_err(|error| {
                        RuntimeError::from_sql(error, "cannot query filtered Job list")
                    })?;
                for row in rows {
                    jobs.push(
                        row.map_err(|error| {
                            RuntimeError::from_sql(error, "cannot decode Job row")
                        })?
                        .into_record()?,
                    );
                }
            }
            (Some(client_request_id), None, None) => {
                let mut statement = transaction
                    .prepare(
                        "SELECT job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version FROM jobs WHERE client_request_id=?1 ORDER BY created_at_ms DESC,job_id DESC LIMIT ?2",
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot prepare filtered Job list"))?;
                let rows = statement
                    .query_map(params![client_request_id, fetch_limit], RegistryStorageBoundary::decode_job_row)
                    .map_err(|error| {
                        RuntimeError::from_sql(error, "cannot query filtered Job list")
                    })?;
                for row in rows {
                    jobs.push(
                        row.map_err(|error| {
                            RuntimeError::from_sql(error, "cannot decode Job row")
                        })?
                        .into_record()?,
                    );
                }
            }
            (None, Some(workspace_id), Some(cursor)) => {
                let mut statement = transaction
                    .prepare(
                        "SELECT job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version FROM jobs WHERE workspace_id=?1 AND (created_at_ms<?2 OR (created_at_ms=?2 AND job_id<?3)) ORDER BY created_at_ms DESC,job_id DESC LIMIT ?4",
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot prepare Workspace Job list"))?;
                let rows = statement
                    .query_map(
                        params![
                            workspace_id,
                            cursor.created_at_ms,
                            cursor.job_id,
                            fetch_limit
                        ],
                        RegistryStorageBoundary::decode_job_row,
                    )
                    .map_err(|error| {
                        RuntimeError::from_sql(error, "cannot query Workspace Job list")
                    })?;
                for row in rows {
                    jobs.push(
                        row.map_err(|error| {
                            RuntimeError::from_sql(error, "cannot decode Job row")
                        })?
                        .into_record()?,
                    );
                }
            }
            (None, Some(workspace_id), None) => {
                let mut statement = transaction
                    .prepare(
                        "SELECT job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version FROM jobs WHERE workspace_id=?1 ORDER BY created_at_ms DESC,job_id DESC LIMIT ?2",
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot prepare Workspace Job list"))?;
                let rows = statement
                    .query_map(params![workspace_id, fetch_limit], RegistryStorageBoundary::decode_job_row)
                    .map_err(|error| {
                        RuntimeError::from_sql(error, "cannot query Workspace Job list")
                    })?;
                for row in rows {
                    jobs.push(
                        row.map_err(|error| {
                            RuntimeError::from_sql(error, "cannot decode Job row")
                        })?
                        .into_record()?,
                    );
                }
            }
            (None, None, Some(cursor)) => {
                let mut statement = transaction
                    .prepare(
                        "SELECT job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version FROM jobs WHERE created_at_ms<?1 OR (created_at_ms=?1 AND job_id<?2) ORDER BY created_at_ms DESC,job_id DESC LIMIT ?3",
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot prepare Job list"))?;
                let rows = statement
                    .query_map(
                        params![cursor.created_at_ms, cursor.job_id, fetch_limit],
                        RegistryStorageBoundary::decode_job_row,
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot query Job list"))?;
                for row in rows {
                    jobs.push(
                        row.map_err(|error| {
                            RuntimeError::from_sql(error, "cannot decode Job row")
                        })?
                        .into_record()?,
                    );
                }
            }
            (None, None, None) => {
                let mut statement = transaction
                    .prepare(
                        "SELECT job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version FROM jobs ORDER BY created_at_ms DESC,job_id DESC LIMIT ?1",
                    )
                    .map_err(|error| RuntimeError::from_sql(error, "cannot prepare Job list"))?;
                let rows = statement
                    .query_map([fetch_limit], RegistryStorageBoundary::decode_job_row)
                    .map_err(|error| RuntimeError::from_sql(error, "cannot query Job list"))?;
                for row in rows {
                    jobs.push(
                        row.map_err(|error| {
                            RuntimeError::from_sql(error, "cannot decode Job row")
                        })?
                        .into_record()?,
                    );
                }
            }
        }

        let has_more = jobs.len() > request.limit as usize;
        jobs.truncate(request.limit as usize);
        let next_cursor = if has_more {
            jobs.last().map(|job| RuntimeJobListCursor {
                created_at_ms: job.created_at_ms,
                job_id: job.job_id.clone(),
            })
        } else {
            None
        };
        let observed_at_ms = now_ms()?;
        let mut summaries = Vec::with_capacity(jobs.len());
        for job in jobs {
            let attempt = match job.current_attempt_id.as_deref() {
                Some(attempt_id) => Some(RegistryStorageBoundary::load_attempt(&transaction, attempt_id)?),
                None => {
                    let attempt_id: Option<String> = transaction
                        .query_row(
                            "SELECT attempt_id FROM attempts WHERE job_id=?1 ORDER BY attempt_number DESC LIMIT 1",
                            [&job.job_id],
                            |row| row.get(0),
                        )
                        .optional()
                        .map_err(|error| RuntimeError::from_sql(error, "cannot find latest Attempt"))?;
                    attempt_id
                        .map(|attempt_id| RegistryStorageBoundary::load_attempt(&transaction, &attempt_id))
                        .transpose()?
                }
            };
            let recovery_condition_active = attempt
                .as_ref()
                .map(|attempt| attempt_recovery_condition_active(&transaction, &attempt.attempt_id))
                .transpose()?
                .unwrap_or(false);
            let artifact_count: u32 = transaction
                .query_row(
                    "SELECT COUNT(*) FROM artifacts WHERE job_id=?1",
                    [&job.job_id],
                    |row| row.get(0),
                )
                .map_err(|error| RuntimeError::from_sql(error, "cannot count Job Artifacts"))?;
            let execution_reason_code =
                job_execution_reason_code(&transaction, &job.job_id, job.resolution.is_some())?;
            let projection = project_job(
                &job,
                attempt.as_ref(),
                recovery_condition_active,
                artifact_count > 0,
                execution_reason_code,
            );
            let plan: RuntimeExecutionPlan = serde_json::from_str(&job.execution_plan_json)
                .map_err(|error| {
                    RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        format!("stored execution plan is invalid: {error}"),
                        Some("executionPlan"),
                        false,
                    )
                })?;
            let executable_name = Path::new(&plan.executable)
                .file_name()
                .and_then(|name| name.to_str())
                .unwrap_or(&plan.executable)
                .to_string();
            let cwd_relative = Path::new(&plan.cwd)
                .strip_prefix(&plan.workspace_path)
                .ok()
                .and_then(|path| path.to_str())
                .filter(|path| !path.is_empty())
                .unwrap_or(".")
                .to_string();
            let started_at_ms = attempt.as_ref().and_then(|attempt| attempt.started_at_ms);
            let finished_at_ms = attempt.as_ref().and_then(|attempt| attempt.finished_at_ms);
            let duration_start = started_at_ms.unwrap_or(job.created_at_ms);
            let duration_end = finished_at_ms.unwrap_or(observed_at_ms);
            summaries.push(RuntimeJobSummary {
                job_id: job.job_id,
                operation_digest: job.operation_digest,
                status: projection.status,
                desired_state: projection.desired_state,
                attempt_id: projection.attempt_id,
                attempt_state: projection.attempt_state,
                termination_intent: projection.termination_intent,
                exit_code: projection.exit_code,
                execution_terminal: projection.execution_terminal,
                execution_disposition: projection.execution_disposition,
                execution_reason_code: projection.execution_reason_code,
                delivery_disposition: projection.delivery_disposition,
                recovery_required: projection.recovery_required,
                semantic_completion_evaluated: projection.semantic_completion_evaluated,
                client_request_id: job.client_request_id,
                workspace_id: job.workspace_id,
                source_revision: plan.source_revision,
                executable_name,
                cwd_relative,
                created_at_ms: job.created_at_ms,
                started_at_ms,
                finished_at_ms,
                duration_ms: duration_end.saturating_sub(duration_start),
                result_available: projection.result_available,
                artifacts_available: projection.artifacts_available,
                artifact_count,
                poll_after_ms: projection.poll_after_ms,
            });
        }
        transaction.commit().map_err(|error| {
            RuntimeError::from_sql(error, "cannot close Job list read snapshot")
        })?;
        Ok(RuntimeJobListResult {
            jobs: summaries,
            next_cursor,
        })
    }

    pub(super) fn list_artifacts(&self, job_id: &str) -> RuntimeResult<Vec<RuntimeArtifactRecord>> {
        let connection = self.open_connection()?;
        let mut statement = connection
            .prepare(
                "SELECT artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms FROM artifacts WHERE job_id=?1 ORDER BY created_at_ms,artifact_id",
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot prepare Artifact query"))?;
        let rows = statement
            .query_map([job_id], |row| {
                Ok(RuntimeArtifactRecord {
                    artifact_id: row.get(0)?,
                    job_id: row.get(1)?,
                    attempt_id: row.get(2)?,
                    kind: row.get(3)?,
                    relative_path: row.get(4)?,
                    digest: row.get(5)?,
                    media_type: row.get(6)?,
                    byte_length: row.get(7)?,
                    truncated: row.get::<_, i64>(8)? != 0,
                    created_at_ms: row.get(9)?,
                })
            })
            .map_err(|error| RuntimeError::from_sql(error, "cannot query Artifacts"))?;
        rows.map(|row| row.map_err(|error| RuntimeError::from_sql(error, "cannot decode Artifact")))
            .collect()
    }

    pub(super) fn execution_plan(&self, job_id: &str) -> RuntimeResult<super::RuntimeExecutionPlan> {
        let job = self.get_job(job_id)?;
        serde_json::from_str(&job.execution_plan_json).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("stored execution plan is invalid: {error}"),
                Some("executionPlan"),
                false,
            )
        })
    }

    pub(super) fn runtime_release_effect_for_job(
        &self,
        job_id: &str,
    ) -> RuntimeResult<Option<RuntimeReleaseEffectBinding>> {
        let connection = self.open_connection()?;
        let job = RegistryStorageBoundary::load_job(&connection, job_id)?;
        let workspace_snapshot: serde_json::Value =
            serde_json::from_str(&job.workspace_snapshot_json).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    format!("stored Workspace snapshot is invalid: {error}"),
                    Some("workspaceSnapshot"),
                    false,
                )
            })?;
        let committed_digest = match workspace_snapshot.get("runtimeReleaseEffectDigest") {
            None => None,
            Some(serde_json::Value::String(value)) => {
                validate_digest(value, "runtimeReleaseEffectDigest").map_err(|_| {
                    RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "stored Runtime Release commitment digest is invalid",
                        Some("workspaceSnapshot.runtimeReleaseEffectDigest"),
                        false,
                    )
                })?;
                Some(value.clone())
            }
            Some(_) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "stored Runtime Release commitment digest is not text",
                    Some("workspaceSnapshot.runtimeReleaseEffectDigest"),
                    false,
                ));
            }
        };
        let row = connection
            .query_row(
                "SELECT effect_id,contract,request_digest,workspace_id,commit_revision,candidate_manifest_digest,expected_tool_count,receipt_path,binding_digest FROM job_runtime_release_effects WHERE job_id=?1",
                [job_id],
                |row| {
                    Ok((
                        row.get::<_, String>(0)?, row.get::<_, String>(1)?,
                        row.get::<_, String>(2)?, row.get::<_, String>(3)?,
                        row.get::<_, String>(4)?, row.get::<_, String>(5)?,
                        row.get::<_, u32>(6)?, row.get::<_, String>(7)?,
                        row.get::<_, String>(8)?,
                    ))
                },
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot read Runtime Release effect"))?;
        let row = match (committed_digest.as_deref(), row) {
            (None, None) => return Ok(None),
            (None, Some(_)) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Runtime Release row exists without a committed Job marker",
                    Some("runtimeReleaseEffect"),
                    false,
                ));
            }
            (Some(_), None) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "committed Runtime Release row is missing",
                    Some("runtimeReleaseEffect"),
                    false,
                ));
            }
            (Some(committed), Some(row)) if committed == row.8 => row,
            (Some(_), Some(_)) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Runtime Release row digest does not match the Job commitment",
                    Some("runtimeReleaseEffect"),
                    false,
                ));
            }
        };
        let (
            effect_id,
            contract,
            request_digest,
            workspace_id,
            commit,
            candidate_manifest_digest,
            expected_tool_count,
            receipt_path,
            binding_digest,
        ) = row;
        if contract != "runtime_release_v1" {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "stored Runtime Release contract is unsupported",
                Some("runtimeReleaseEffect.contract"),
                false,
            ));
        }
        let binding = RuntimeReleaseEffectBinding {
            contract: RuntimeReleaseContract::RuntimeReleaseV1,
            effect_id,
            request_digest,
            workspace_id,
            commit,
            candidate_manifest_digest,
            expected_tool_count,
            receipt_path,
        };
        let encoded = serde_json::to_string(&binding).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                format!("cannot serialize stored Runtime Release effect: {error}"),
                None,
                false,
            )
        })?;
        if sha256_bytes(encoded.as_bytes()) != binding_digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "stored Runtime Release effect digest does not match side truth",
                Some("runtimeReleaseEffect"),
                false,
            ));
        }
        Ok(Some(binding))
    }

    pub(super) fn find_runtime_release_effect(
        &self,
        principal: &str,
        client_request_id: &str,
    ) -> RuntimeResult<Option<(RuntimeJobRecord, RuntimeReleaseEffectBinding)>> {
        validate_identifier(principal, "principal")?;
        validate_client_request_id(client_request_id, "clientRequestId")?;
        let connection = self.open_connection()?;
        let job_id: Option<String> = connection
            .query_row(
                "SELECT j.job_id FROM jobs j JOIN job_runtime_release_effects r ON r.job_id=j.job_id WHERE j.principal=?1 AND j.client_request_id=?2",
                params![principal, client_request_id],
                |row| row.get(0),
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot find Runtime Release effect"))?;
        let Some(job_id) = job_id else {
            return Ok(None);
        };
        let job = RegistryStorageBoundary::load_job(&connection, &job_id)?;
        drop(connection);
        let release = self
            .runtime_release_effect_for_job(&job_id)?
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Runtime Release Job lost its side truth",
                    Some("runtimeReleaseEffect"),
                    false,
                )
            })?;
        Ok(Some((job, release)))
    }

}
