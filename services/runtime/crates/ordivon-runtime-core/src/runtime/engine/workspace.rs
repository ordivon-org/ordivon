const WORKSPACE_LIST_LIVE_PROJECTION_PARALLELISM: usize = 4;

impl Runtime {
    fn ensure_workspace_headroom(&self) -> RuntimeResult<()> {
        ensure_workspace_headroom(&self.workspace_headroom)
    }

    pub fn open_workspace(
        &self,
        request: &GitWorkspaceCreateRequest,
    ) -> RuntimeResult<CompactWorkspaceOpenResult> {
        let _topology = self.lock_topology()?;
        self.ensure_workspace_headroom()?;
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
        let mut projection_inputs = Vec::with_capacity(records.len());
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
            projection_inputs.push((record, active_job_ids));
        }

        // The default list projection is intentionally cheaper than the exact source-state
        // proof path, but it still needs live Git HEAD/dirty truth for each item on the
        // requested page. Those probes are independent across Workspaces, so bound their
        // fan-out instead of serially paying one full `git status` latency per item. Exact
        // source-state hashing remains serial because it is the proof-strength path and may
        // read every tracked/untracked byte in each Workspace.
        let head_dirty = if request.include_source_state_digest || projection_inputs.len() <= 1 {
            projection_inputs
                .iter()
                .map(|(record, _)| workspace_head_and_dirty_at(Path::new(&record.workspace_path)))
                .collect::<Vec<_>>()
        } else {
            let worker_count = projection_inputs
                .len()
                .min(WORKSPACE_LIST_LIVE_PROJECTION_PARALLELISM);
            let chunk_size = projection_inputs.len().div_ceil(worker_count);
            thread::scope(|scope| -> RuntimeResult<Vec<_>> {
                let mut handles = Vec::with_capacity(worker_count);
                // chunks() partitions the sorted input contiguously. Joining handles
                // in spawn order preserves input order even if workers finish out of order.
                for chunk in projection_inputs.chunks(chunk_size) {
                    handles.push(scope.spawn(move || {
                        chunk
                            .iter()
                            .map(|(record, _)| {
                                workspace_head_and_dirty_at(Path::new(&record.workspace_path))
                            })
                            .collect::<Vec<_>>()
                    }));
                }
                let mut projections = Vec::with_capacity(projection_inputs.len());
                for handle in handles {
                    let mut worker = handle.join().map_err(|_| {
                        RuntimeError::new(
                            RuntimeErrorCode::ToolFailed,
                            "workspace live-projection worker panicked",
                            Some("workspaceId"),
                            false,
                        )
                    })?;
                    projections.append(&mut worker);
                }
                Ok(projections)
            })?
        };

        for ((record, active_job_ids), head_dirty) in
            projection_inputs.into_iter().zip(head_dirty)
        {
            let (current_head_revision, head_mode, dirty) = match head_dirty {
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
                    head_mode,
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
        // Git status-v2 binds the current HEAD revision and its branch/detached
        // mode in the same observation; do not manufacture "detached" from
        // Workspace creation lineage or perform two conflicting HEAD probes.
        let (current_head_revision, head_mode, _) =
            workspace_head_and_dirty_at(Path::new(&record.workspace_path))
                .map_err(map_universal_error)?;
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
                current_head_revision,
                head_mode,
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
        self.with_workspace_lease(&request.workspace_id, || {
            let active = self
                .registry
                .active_job_ids_for_workspace(&request.workspace_id)?;
            ensure_workspace_mutation_allowed(&active)?;
            mutate_workspace(&self.executor, request).map_err(map_universal_error)
        })
    }

    pub fn close_workspace(
        &self,
        request: &WorkspaceCloseRequest,
    ) -> RuntimeResult<WorkspaceCloseResult> {
        let _topology = self.lock_topology()?;
        self.with_workspace_lease(&request.workspace_id, || {
            let active = self
                .registry
                .active_job_ids_for_workspace(&request.workspace_id)?;
            let dependents = workspace_cleanup_dependents(&self.executor, &request.workspace_id)
                .map_err(map_universal_error)?;
            ensure_workspace_close_allowed(&active, &dependents)?;
            remove_git_workspace(&self.executor, request).map_err(map_universal_error)
        })
    }

}
