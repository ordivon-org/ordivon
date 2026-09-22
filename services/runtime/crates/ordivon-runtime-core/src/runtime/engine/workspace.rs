impl Runtime {
    pub fn open_workspace(
        &self,
        request: &GitWorkspaceCreateRequest,
    ) -> RuntimeResult<CompactWorkspaceOpenResult> {
        let _guard = self.lock_lifecycle()?;
        create_git_workspace(&self.executor, request).map_err(map_universal_error)
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
            workspaces.push(project_workspace_summary(
                &record,
                WorkspaceProjectionFacts {
                    current_head_revision,
                    dirty,
                    source_state_digest,
                    active_job_ids,
                },
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
        Ok(project_workspace_summary(
            record,
            WorkspaceProjectionFacts {
                current_head_revision: workspace_head_revision(&self.executor, &record.workspace_id)
                    .map_err(map_universal_error)?,
                dirty: diff.byte_length > 0 || !diff.untracked_paths.is_empty(),
                source_state_digest: Some(
                    workspace_source_state_digest(&self.executor, &record.workspace_id)
                        .map_err(map_universal_error)?,
                ),
                active_job_ids,
            },
        ))
    }

    pub fn mutate_workspace(
        &self,
        request: &WorkspaceMutateRequest,
    ) -> RuntimeResult<WorkspaceMutateResult> {
        let _guard = self.lock_lifecycle()?;
        let active = self
            .registry
            .active_job_ids_for_workspace(&request.workspace_id)?;
        ensure_workspace_mutation_allowed(&active)?;
        mutate_workspace(&self.executor, request).map_err(map_universal_error)
    }

    pub fn close_workspace(
        &self,
        request: &WorkspaceCloseRequest,
    ) -> RuntimeResult<WorkspaceCloseResult> {
        let _guard = self.lock_lifecycle()?;
        let active = self
            .registry
            .active_job_ids_for_workspace(&request.workspace_id)?;
        let dependents = workspace_cleanup_dependents(&self.executor, &request.workspace_id)
            .map_err(map_universal_error)?;
        ensure_workspace_close_allowed(&active, &dependents)?;
        remove_git_workspace(&self.executor, request).map_err(map_universal_error)
    }

}
