impl Runtime {
    pub fn find_runtime_release_for_apply(
        &self,
        request: &RuntimeReleaseRequest,
    ) -> RuntimeResult<Option<RuntimeReleaseAdmission>> {
        validate_runtime_release_request(request)?;
        let request_digest = runtime_release_request_identity_digest(request)?;
        let Some(job) = self.registry.find_idempotent_job(
            &request.principal,
            &request.client_request_id,
            &request_digest,
        )?
        else {
            return Ok(None);
        };
        let binding = self
            .registry
            .runtime_release_effect_for_job(&job.job_id)?
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "Runtime Release request identity is missing its release side truth",
                    Some("runtimeReleaseEffect"),
                    false,
                )
            })?;
        validate_release_binding_matches_request(&binding, request)?;
        let release = self.runtime_release_projection(&job.job_id, &binding)?;
        Ok(Some(RuntimeReleaseAdmission {
            replayed: true,
            release,
        }))
    }

    pub fn admit_runtime_release_effect(
        &self,
        request: &RuntimeReleaseRequest,
        proposal: &super::TaskRunProposal,
        receipt_path: &Path,
    ) -> RuntimeResult<RuntimeReleaseAdmission> {
        validate_runtime_release_request(request)?;
        validate_run_proposal_structure(proposal)?;
        if proposal.client_request_id != request.client_request_id
            || proposal.principal != request.principal
            || proposal.execution.workspace_id != request.workspace_id
        {
            return Err(RuntimeError::invalid(
                "Runtime Release proposal identity does not match the structured release request",
                "clientRequestId",
            ));
        }
        if !receipt_path.is_absolute() {
            return Err(RuntimeError::invalid(
                "Runtime Release receipt path must be absolute",
                "receiptPath",
            ));
        }
        let request_digest = runtime_release_request_identity_digest(request)?;
        let binding = RuntimeReleaseEffectBinding {
            contract: RuntimeReleaseContract::RuntimeReleaseV1,
            effect_id: runtime_release_effect_id(request),
            request_digest: request_digest.clone(),
            workspace_id: request.workspace_id.clone(),
            commit: request.commit.clone(),
            candidate_manifest_digest: request.candidate_manifest_digest.clone(),
            expected_tool_count: request.expected_tool_count,
            receipt_path: receipt_path.to_string_lossy().into_owned(),
        };
        let _guard = self.lock_lifecycle()?;
        if let Some(job) = self.registry.find_idempotent_job(
            &request.principal,
            &request.client_request_id,
            &request_digest,
        )? {
            let committed = self
                .registry
                .runtime_release_effect_for_job(&job.job_id)?
                .ok_or_else(|| {
                    RuntimeError::new(
                        RuntimeErrorCode::RegistryCorrupt,
                        "Runtime Release replay lost its release side truth",
                        Some("runtimeReleaseEffect"),
                        false,
                    )
                })?;
            validate_release_binding_matches_request(&committed, request)?;
            return Ok(RuntimeReleaseAdmission {
                replayed: true,
                release: self.runtime_release_projection(&job.job_id, &committed)?,
            });
        }

        let resolved = self.resolve_proposal(proposal);
        validate_run_request_structure(&resolved)?;
        validate_new_admission_policy(
            &resolved,
            self.executor.max_runtime_ms,
            self.executor.max_output_bytes,
        )?;
        self.reconcile_recoverable_orphans()?;
        let _ = self.reconcile_workspace(&request.workspace_id)?;
        let plan = self.resolve_plan(&resolved)?;
        let submit = SubmitRequest {
            schema_version: RUNTIME_SCHEMA_VERSION,
            client_request_id: request.client_request_id.clone(),
            request_identity_digest: Some(request_digest),
            execution_provider: Some(
                self.current_execution_provider_snapshot(resolved.execution.execution_target)?,
            ),
            runtime_release_effect: Some(binding.clone()),
            host_dependencies: Vec::new(),
            plan,
            global_limit: resolved.global_limit,
        };
        let job_id = match self.registry.submit(&submit)? {
            AdmissionOutcome::Created(created) => created.job.job_id.clone(),
            AdmissionOutcome::Existing { job } => job.job_id.clone(),
        };
        // Intentionally do not dispatch here. The durable Accepted Job is visible before any
        // self-replacing release can remove the initiating MCP connection. Normal Runtime
        // reconciliation owns the later at-most-once physical dispatch.
        Ok(RuntimeReleaseAdmission {
            replayed: false,
            release: self.runtime_release_projection(&job_id, &binding)?,
        })
    }

    pub fn get_runtime_release_effect(
        &self,
        request: &RuntimeReleaseGetRequest,
    ) -> RuntimeResult<RuntimeReleaseProjection> {
        if request.schema_version != RUNTIME_SCHEMA_VERSION {
            return Err(RuntimeError::invalid(
                "unsupported runtime schema version",
                "schemaVersion",
            ));
        }
        let Some((job, binding)) = self
            .registry
            .find_runtime_release_effect(&request.principal, &request.client_request_id)?
        else {
            return Err(RuntimeError::new(
                RuntimeErrorCode::JobNotFound,
                "Runtime Release effect not found",
                Some("clientRequestId"),
                false,
            ));
        };
        self.runtime_release_projection(&job.job_id, &binding)
    }

    fn runtime_release_projection(
        &self,
        job_id: &str,
        binding: &RuntimeReleaseEffectBinding,
    ) -> RuntimeResult<RuntimeReleaseProjection> {
        let snapshot = self.registry.job_snapshot(job_id)?;
        let receipt = inspect_runtime_release_receipt(binding, &snapshot)?;
        Ok(RuntimeReleaseProjection {
            contract: binding.contract,
            effect_id: binding.effect_id.clone(),
            client_request_id: snapshot.job.client_request_id,
            job_id: snapshot.job.job_id,
            workspace_id: binding.workspace_id.clone(),
            commit: binding.commit.clone(),
            candidate_manifest_digest: binding.candidate_manifest_digest.clone(),
            expected_tool_count: binding.expected_tool_count,
            effect_disposition: receipt.disposition,
            effect_terminal: receipt.terminal,
            receipt_available: receipt.available,
            receipt_digest: receipt.digest,
            deployed_tool_count: receipt.deployed_tool_count,
            tool_catalog_digest: receipt.tool_catalog_digest,
            rollback_status: receipt.rollback_status,
            reconciliation_issue: receipt.issue,
            attempt_state: snapshot.attempt.as_ref().map(|attempt| attempt.state),
            execution_terminal: snapshot.projection.execution_terminal,
            execution_disposition: snapshot.projection.execution_disposition,
            delivery_disposition: snapshot.projection.delivery_disposition,
            recovery_required: snapshot.projection.recovery_required,
            semantic_completion_evaluated: false,
        })
    }

}
