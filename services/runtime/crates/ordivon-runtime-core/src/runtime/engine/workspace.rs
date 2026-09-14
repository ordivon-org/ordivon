impl Runtime {
    pub fn open_workspace(
        &self,
        request: &GitWorkspaceCreateRequest,
    ) -> RuntimeResult<CompactWorkspaceOpenResult> {
        let _guard = self.lock_lifecycle()?;
        create_git_workspace_compact(&self.executor, request).map_err(map_universal_error)
    }

    pub fn get_workspace(
        &self,
        request: &RuntimeWorkspaceGetRequest,
    ) -> RuntimeResult<RuntimeWorkspaceSummary> {
        if request.schema_version != RUNTIME_SCHEMA_VERSION {
            return Err(RuntimeError::invalid(
                "unsupported runtime schema version",
                "schemaVersion",
            ));
        }
        let record = load_workspace_record(&self.executor, &request.workspace_id)
            .map_err(map_universal_error)?;
        self.workspace_summary(&record)
    }

    pub fn list_workspaces(
        &self,
        request: &RuntimeWorkspaceListRequest,
    ) -> RuntimeResult<RuntimeWorkspaceListResult> {
        if request.schema_version != RUNTIME_SCHEMA_VERSION {
            return Err(RuntimeError::invalid(
                "unsupported runtime schema version",
                "schemaVersion",
            ));
        }
        if request.limit == 0 || request.limit > super::MAX_RUNTIME_LIST_LIMIT {
            return Err(RuntimeError::invalid(
                format!("limit must be in 1..={}", super::MAX_RUNTIME_LIST_LIMIT),
                "limit",
            ));
        }
        if let Some(cursor) = &request.cursor {
            crate::universal::validate_id(&cursor.workspace_id, "cursor.workspaceId")
                .map_err(map_universal_error)?;
        }
        let inventory =
            list_open_workspace_record_inventory(&self.executor).map_err(map_universal_error)?;
        let (records, next_cursor) =
            workspace_record_page(inventory.records, request.limit, request.cursor.as_ref());
        let mut workspaces = Vec::with_capacity(records.len());
        let mut issues = inventory
            .issues
            .into_iter()
            .map(|issue| {
                workspace_issue(
                    &issue.workspace_id,
                    RuntimeWorkspaceIssueStage::Inventory,
                    map_universal_error(issue.error),
                )
            })
            .collect::<Vec<_>>();
        for record in records {
            let active_job_ids = match self
                .registry
                .active_job_ids_for_workspace(&record.workspace_id)
            {
                Ok(active_job_ids) => active_job_ids,
                Err(error) if error.is_reconciliation_fatal() => return Err(error),
                Err(error) => {
                    issues.push(workspace_issue(
                        &record.workspace_id,
                        RuntimeWorkspaceIssueStage::ActiveJobs,
                        error,
                    ));
                    continue;
                }
            };
            let (current_head_revision, dirty) =
                match workspace_head_and_dirty_at(Path::new(&record.workspace_path)) {
                    Ok(projection) => projection,
                    Err(error) => {
                        let stage = if error.code
                            == crate::universal::UniversalExecErrorCode::RevisionNotFound
                        {
                            RuntimeWorkspaceIssueStage::HeadRevision
                        } else {
                            RuntimeWorkspaceIssueStage::DirtyProbe
                        };
                        issues.push(workspace_issue(
                            &record.workspace_id,
                            stage,
                            map_universal_error(error),
                        ));
                        continue;
                    }
                };
            let source_state_digest = if request.include_source_state_digest {
                match workspace_source_state_digest(&self.executor, &record.workspace_id) {
                    Ok(digest) => Some(digest),
                    Err(error) => {
                        issues.push(workspace_issue(
                            &record.workspace_id,
                            RuntimeWorkspaceIssueStage::SourceStateDigest,
                            map_universal_error(error),
                        ));
                        continue;
                    }
                }
            } else {
                None
            };
            workspaces.push(Self::workspace_summary_from_parts(
                &record,
                current_head_revision,
                dirty,
                source_state_digest,
                active_job_ids,
            ));
        }
        Ok(RuntimeWorkspaceListResult {
            workspaces,
            next_cursor,
            issues,
        })
    }

    fn workspace_summary(
        &self,
        record: &crate::universal::WorkspaceRecord,
    ) -> RuntimeResult<RuntimeWorkspaceSummary> {
        let active_job_ids = self
            .registry
            .active_job_ids_for_workspace(&record.workspace_id)?;
        let diff = crate::universal::workspace_diff(
            &self.executor,
            &WorkspaceDiffRequest {
                schema_version: UNIVERSAL_EXEC_SCHEMA_VERSION,
                workspace_id: record.workspace_id.clone(),
                max_bytes: 1,
            },
        )
        .map_err(map_universal_error)?;
        Ok(Self::workspace_summary_from_parts(
            record,
            workspace_head_revision(&self.executor, &record.workspace_id)
                .map_err(map_universal_error)?,
            diff.byte_length > 0 || !diff.untracked_paths.is_empty(),
            Some(
                workspace_source_state_digest(&self.executor, &record.workspace_id)
                    .map_err(map_universal_error)?,
            ),
            active_job_ids,
        ))
    }

    fn workspace_summary_from_parts(
        record: &crate::universal::WorkspaceRecord,
        current_head_revision: String,
        dirty: bool,
        source_state_digest: Option<String>,
        active_job_ids: Vec<String>,
    ) -> RuntimeWorkspaceSummary {
        RuntimeWorkspaceSummary {
            workspace_id: record.workspace_id.clone(),
            source_repo: record.source_repo.clone(),
            source_revision: record.source_revision.clone(),
            current_head_revision,
            created_at_ms: u64::try_from(record.created_unix_ms).unwrap_or(u64::MAX),
            head_mode: "detached".to_string(),
            dirty,
            source_state_digest,
            active_job_ids,
        }
    }

    pub fn mutate_workspace(
        &self,
        request: &WorkspaceMutateRequest,
    ) -> RuntimeResult<WorkspaceMutateResult> {
        let _guard = self.lock_lifecycle()?;
        let active = self
            .registry
            .active_job_ids_for_workspace(&request.workspace_id)?;
        if !active.is_empty() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceBusy,
                format!(
                    "workspace source state is committed by active or held Jobs: {}",
                    active.join(", ")
                ),
                Some("workspaceId"),
                true,
            ));
        }
        mutate_workspace(&self.executor, request).map_err(map_universal_error)
    }

    pub fn patch_workspace(
        &self,
        request: &WorkspacePatchRequest,
    ) -> RuntimeResult<WorkspacePatchResult> {
        let _guard = self.lock_lifecycle()?;
        let active = self
            .registry
            .active_job_ids_for_workspace(&request.workspace_id)?;
        if !active.is_empty() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceBusy,
                format!(
                    "workspace source state is committed by active or held Jobs: {}",
                    active.join(", ")
                ),
                Some("workspaceId"),
                true,
            ));
        }
        patch_workspace(&self.executor, request).map_err(map_universal_error)
    }

    pub fn patch_workspace_durable(
        &self,
        request: &DurableWorkspacePatchRequest,
    ) -> RuntimeResult<DurableWorkspacePatchResult> {
        validate_durable_patch_request(request)?;
        let request_digest = durable_patch_request_digest(request)?;
        let _guard = self.lock_lifecycle()?;
        let active = self
            .registry
            .active_job_ids_for_workspace(&request.patch.workspace_id)?;
        if !active.is_empty() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceBusy,
                format!(
                    "workspace source state is committed by active or held Jobs: {}",
                    active.join(", ")
                ),
                Some("patch.workspaceId"),
                true,
            ));
        }

        let (operation, replayed) = if let Some(existing) = self
            .registry
            .find_workspace_patch_operation(&request.principal, &request.client_request_id)?
        {
            if existing.request_digest != request_digest {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::IdempotencyConflict,
                    "clientRequestId is already bound to a different Workspace Patch request",
                    Some("clientRequestId"),
                    false,
                ));
            }
            (existing, true)
        } else {
            let plan = plan_workspace_patch(&self.executor, &request.patch)
                .map_err(map_universal_error)?;
            self.registry
                .prepare_workspace_patch_operation(request, &request_digest, &plan)?
        };

        if operation.state == WorkspacePatchOperationState::Unknown {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                "Workspace Patch files no longer match a wholly uncommitted or committed state",
                Some("clientRequestId"),
                false,
            ));
        }
        if operation.state == WorkspacePatchOperationState::Committed {
            let patch = operation.result.ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "committed Workspace Patch omitted its result",
                    Some("result"),
                    false,
                )
            })?;
            return Ok(DurableWorkspacePatchResult {
                operation_id: operation.operation_id,
                client_request_id: operation.client_request_id,
                request_digest: operation.request_digest,
                replayed: true,
                patch,
            });
        }

        let patch = match inspect_workspace_patch_plan(&self.executor, &operation.plan)
            .map_err(map_universal_error)?
        {
            WorkspacePatchPlanState::Before => {
                match patch_workspace(&self.executor, &request.patch) {
                    Ok(result) => result,
                    Err(error)
                        if error.code
                            == crate::UniversalExecErrorCode::WorkspaceMutationIncomplete =>
                    {
                        self.registry
                            .mark_workspace_patch_unknown(&operation.operation_id)?;
                        return Err(RuntimeError::new(
                            RuntimeErrorCode::ReconciliationRequired,
                            error.message,
                            error.field.as_deref(),
                            false,
                        ));
                    }
                    Err(error) => return Err(map_universal_error(error)),
                }
            }
            WorkspacePatchPlanState::After => result_from_workspace_patch_plan(
                &self.executor,
                &operation.plan,
                operation.max_diff_bytes,
            )
            .map_err(map_universal_error)?,
            WorkspacePatchPlanState::Mixed => {
                self.registry
                    .mark_workspace_patch_unknown(&operation.operation_id)?;
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ReconciliationRequired,
                    "Workspace Patch has a mixed or externally changed file state",
                    Some("clientRequestId"),
                    false,
                ));
            }
        };
        self.registry
            .commit_workspace_patch_operation(&operation.operation_id, &patch)?;
        Ok(DurableWorkspacePatchResult {
            operation_id: operation.operation_id,
            client_request_id: operation.client_request_id,
            request_digest: operation.request_digest,
            replayed,
            patch,
        })
    }

    pub fn workspace_patch_status(
        &self,
        request: &WorkspacePatchStatusRequest,
    ) -> RuntimeResult<WorkspacePatchOperationStatus> {
        validate_patch_status_request(request)?;
        let _guard = self.lock_lifecycle()?;
        let mut operation = self
            .registry
            .find_workspace_patch_operation(&request.principal, &request.client_request_id)?
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::JobNotFound,
                    "Workspace Patch operation not found",
                    Some("clientRequestId"),
                    false,
                )
            })?;
        if operation.state == WorkspacePatchOperationState::Prepared {
            match inspect_workspace_patch_plan(&self.executor, &operation.plan)
                .map_err(map_universal_error)?
            {
                WorkspacePatchPlanState::Before => {}
                WorkspacePatchPlanState::After => {
                    let result = result_from_workspace_patch_plan(
                        &self.executor,
                        &operation.plan,
                        operation.max_diff_bytes,
                    )
                    .map_err(map_universal_error)?;
                    self.registry
                        .commit_workspace_patch_operation(&operation.operation_id, &result)?;
                    operation.state = WorkspacePatchOperationState::Committed;
                    operation.result = Some(result);
                }
                WorkspacePatchPlanState::Mixed => {
                    self.registry
                        .mark_workspace_patch_unknown(&operation.operation_id)?;
                    operation.state = WorkspacePatchOperationState::Unknown;
                }
            }
        }
        Ok(WorkspacePatchOperationStatus {
            operation_id: operation.operation_id,
            client_request_id: operation.client_request_id,
            request_digest: operation.request_digest,
            workspace_id: operation.workspace_id,
            state: operation.state,
            patch: operation.result,
        })
    }

    pub fn close_workspace(
        &self,
        request: &WorkspaceCloseRequest,
    ) -> RuntimeResult<WorkspaceCloseResult> {
        let _guard = self.lock_lifecycle()?;
        let active = self
            .registry
            .active_job_ids_for_workspace(&request.workspace_id)?;
        if !active.is_empty() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceBusy,
                format!("workspace has active or held Jobs: {}", active.join(", ")),
                Some("workspaceId"),
                true,
            ));
        }
        let dependents = workspace_cleanup_dependents(&self.executor, &request.workspace_id)
            .map_err(map_universal_error)?;
        if !dependents.is_empty() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceBusy,
                format!(
                    "workspace owns paths required as Git authority by open Workspaces: {}",
                    dependents.join(", ")
                ),
                Some("workspaceId"),
                true,
            ));
        }
        remove_git_workspace(&self.executor, request).map_err(map_universal_error)
    }

}
