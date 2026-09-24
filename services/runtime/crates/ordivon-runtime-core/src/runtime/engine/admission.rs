impl Runtime {
    #[cfg(test)]
    pub(crate) fn run_job(&self, request: &JobRunRequest) -> RuntimeResult<JobObservation> {
        validate_run_request_structure(request)?;
        let request_identity_digest = super::operation_request_identity_digest(request)?;
        self.run_concrete_job(request, request_identity_digest)
    }


    /// Admit an Agent-authored proposal with exact immutable inputs. Proposal identity plus the
    /// canonical input bindings is fixed before current operator policy or authority roots are
    /// consulted, so replay preserves the same semantics as ordinary proposal admission.
    pub fn run_job_proposal_with_inputs(
        &self,
        proposal: &super::JobRunProposal,
        inputs: &[InputBindingRequest],
    ) -> RuntimeResult<JobObservation> {
        validate_run_proposal_structure(proposal)?;
        let inputs = canonical_input_binding_requests(inputs)?;
        let request_identity_digest =
            super::input_bound_proposal_request_identity_digest(proposal, &inputs)?;
        let job_id = {
            let _guard = self.lock_lifecycle()?;
            if let Some(existing) = self.registry.find_idempotent_job(
                &proposal.principal,
                &proposal.client_request_id,
                &request_identity_digest,
                None,
            )? {
                existing.job_id
            } else {
                let authority_contract =
                    super::authority_contract::AuthorityContract::immutable_inputs(proposal, &inputs)?;
                let request = self.resolve_proposal(proposal);
                validate_run_request_structure(&request)?;
                self.admit_new_job_with_inputs(
                    &request,
                    request_identity_digest,
                    &inputs,
                    &authority_contract,
                )?
            }
        };
        self.observe_admitted_job(
            &job_id,
            proposal.wait_ms,
            proposal.stdout_tail_bytes,
            proposal.stderr_tail_bytes,
        )
    }

    /// Admit an Agent-authored trusted-local Linux proposal with opaque named credentials.
    ///
    /// Proposal identity binds logical credential references, while Runtime snapshots the
    /// operator-owned bytes only after principal authorization. Existing Jobs replay before
    /// current credential authority state is consulted.
    pub fn run_job_proposal_with_credentials(
        &self,
        proposal: &super::JobRunProposal,
        credentials: &[CredentialBindingRequest],
    ) -> RuntimeResult<JobObservation> {
        validate_run_proposal_structure(proposal)?;
        if proposal.execution.execution_target != super::ExecutionTarget::LocalLinux {
            return Err(RuntimeError::invalid(
                "credential-bound execution currently supports local_linux only",
                "execution.executionTarget",
            ));
        }
        if proposal.execution.execution_profile != super::ExecutionProfile::TrustedLocal {
            return Err(RuntimeError::invalid(
                "credential-bound execution requires trusted_local",
                "execution.executionProfile",
            ));
        }
        for name in proposal.execution.env.keys() {
            if name.eq_ignore_ascii_case("CREDENTIALS_DIRECTORY") {
                return Err(RuntimeError::invalid(
                    "CREDENTIALS_DIRECTORY is owned by the credential delivery provider",
                    "execution.env.CREDENTIALS_DIRECTORY",
                ));
            }
        }
        for (index, step) in proposal.execution.steps.iter().enumerate() {
            for name in step.env.keys() {
                if name.eq_ignore_ascii_case("CREDENTIALS_DIRECTORY") {
                    return Err(RuntimeError::invalid(
                        "CREDENTIALS_DIRECTORY is owned by the credential delivery provider",
                        &format!("execution.steps[{index}].env.CREDENTIALS_DIRECTORY"),
                    ));
                }
            }
        }

        let credentials = canonical_credential_binding_requests(credentials)?;
        let request_identity_digest =
            super::credential_bound_proposal_request_identity_digest(proposal, &credentials)?;
        let job_id = {
            let _guard = self.lock_lifecycle()?;
            if let Some(existing) = self.registry.find_idempotent_job(
                &proposal.principal,
                &proposal.client_request_id,
                &request_identity_digest,
                None,
            )? {
                existing.job_id
            } else {
                let _authority_contract =
                    super::authority_contract::AuthorityContract::credential_bound_trusted(
                        proposal,
                        &credentials,
                    )?;
                let request = self.resolve_proposal(proposal);
                validate_run_request_structure(&request)?;
                self.admit_new_job_with_credentials(
                    &request,
                    request_identity_digest,
                    &credentials,
                )?
            }
        };
        self.observe_admitted_job(
            &job_id,
            proposal.wait_ms,
            proposal.stdout_tail_bytes,
            proposal.stderr_tail_bytes,
        )
    }

    fn admit_new_job_with_credentials(
        &self,
        request: &JobRunRequest,
        request_identity_digest: String,
        credentials: &[CredentialBindingRequest],
    ) -> RuntimeResult<String> {
        if request.execution.execution_target != super::ExecutionTarget::LocalLinux
            || request.execution.execution_profile != super::ExecutionProfile::TrustedLocal
        {
            return Err(RuntimeError::invalid(
                "credential-bound execution requires trusted_local local_linux",
                "execution.executionProfile",
            ));
        }
        validate_new_admission_policy(
            request,
            self.executor.max_runtime_ms,
            self.executor.max_output_bytes,
        )?;
        self.reconcile_recoverable_orphans()?;
        let _ = self.reconcile_workspace(&request.execution.workspace_id)?;
        let mut plan = self.resolve_plan(request)?;
        let admission_ids = self.registry.preallocate_admission_ids();
        let prepared = self.materialize_credential_bindings(
            request,
            &admission_ids.job_id,
            credentials,
        )?;
        plan.credential_set_id = Some(prepared.credential_set_id.clone());

        let submit = SubmitRequest {
            schema_version: RUNTIME_SCHEMA_VERSION,
            client_request_id: request.client_request_id.clone(),
            request_identity_digest: Some(request_identity_digest),
            execution_provider: Some(
                self.current_execution_provider_snapshot(request.execution.execution_target)?,
            ),
            runtime_release_effect: None,
            host_dependencies: Vec::new(),
            plan,
            global_limit: request.global_limit,
        };
        match self.registry.submit_preallocated(&submit, &admission_ids) {
            Ok(AdmissionOutcome::Created(created)) => {
                let job_id = created.job.job_id.clone();
                self.ensure_job_credential_ownership(&job_id)
                    .map_err(|error| error.with_operation_id(job_id.clone()))?;
                Ok(job_id)
            }
            Ok(AdmissionOutcome::Existing { job }) => {
                self.discard_prepared_credential_set(&prepared.prepared_root)?;
                Ok(job.job_id)
            }
            Err(error) => {
                self.discard_prepared_credential_set(&prepared.prepared_root)?;
                Err(error)
            }
        }
    }

    fn admit_new_job_with_inputs(
        &self,
        request: &JobRunRequest,
        request_identity_digest: String,
        inputs: &[InputBindingRequest],
        authority_contract: &super::authority_contract::AuthorityContract,
    ) -> RuntimeResult<String> {
        match request.execution.execution_target {
            super::ExecutionTarget::LocalLinux => {
                // Linux immutable inputs may be combined with either authority profile.
                // contained_local remains the reduced-authority default used by
                // workspace.execBound; trusted_local is reserved for an explicit
                // higher-authority public admission surface whose operation identity
                // still binds the exact input set.
            }
            super::ExecutionTarget::WindowsNative => {
                if request.execution.execution_profile != super::ExecutionProfile::TrustedLocal {
                    return Err(RuntimeError::invalid(
                        "windows_native immutable input bindings require trusted_local execution",
                        "execution.executionProfile",
                    ));
                }
                if request.execution.windows_authority != super::WindowsAuthority::Limited {
                    return Err(RuntimeError::invalid(
                        "windows_native immutable input bindings support limited authority only",
                        "execution.windowsAuthority",
                    ));
                }
                validate_windows_input_relative_paths(
                    inputs
                        .iter()
                        .map(|input| input.presentation_relative_path.as_str()),
                )?;
            }
        }
        validate_new_admission_policy(
            request,
            self.executor.max_runtime_ms,
            self.executor.max_output_bytes,
        )?;
        self.reconcile_recoverable_orphans()?;
        let _ = self.reconcile_workspace(&request.execution.workspace_id)?;
        let mut plan = self.resolve_plan(request)?;
        let admission_ids = self.registry.preallocate_admission_ids();
        let prepared = self.materialize_input_bindings(
            request,
            &request_identity_digest,
            &admission_ids.job_id,
            inputs,
        )?;
        plan.input_set_id = Some(prepared.input_set_id.clone());
        plan.effective_inputs = prepared.effective_inputs.clone();
        let input_root = match plan.execution_target {
            super::ExecutionTarget::LocalLinux => CONTAINED_INPUT_ROOT.to_string(),
            super::ExecutionTarget::WindowsNative => {
                windows_input_presentation_root(&plan, &prepared.input_set_id)?
            }
        };
        set_environment_value_case_insensitive(
            &mut plan.env,
            "ORDIVON_INPUT_ROOT",
            input_root.clone(),
        );
        for step in &mut plan.steps {
            set_environment_value_case_insensitive(
                &mut step.env,
                "ORDIVON_INPUT_ROOT",
                input_root.clone(),
            );
        }
        let provider =
            self.current_execution_provider_snapshot(request.execution.execution_target)?;
        let compiled = if authority_contract.is_immutable_input_reduced() {
            OperationCircuitCompiler::immutable_input_reduced(
                authority_contract,
                request,
                inputs,
                request_identity_digest,
                provider,
                plan,
            )
        } else {
            OperationCircuitCompiler::immutable_input_trusted(
                authority_contract,
                request,
                inputs,
                request_identity_digest,
                provider,
                plan,
            )
        };
        let submit = match compiled {
            Ok(circuit) => circuit.into_submit_request(),
            Err(error) => {
                self.discard_prepared_input_set(&prepared.prepared_root)?;
                return Err(error);
            }
        };
        match self.registry.submit_preallocated(&submit, &admission_ids) {
            Ok(AdmissionOutcome::Created(created)) => {
                let job_id = created.job.job_id.clone();
                self.ensure_job_input_ownership(&job_id)
                    .map_err(|error| error.with_operation_id(job_id.clone()))?;
                Ok(job_id)
            }
            Ok(AdmissionOutcome::Existing { job }) => {
                self.discard_prepared_input_set(&prepared.prepared_root)?;
                Ok(job.job_id)
            }
            Err(error) => {
                self.discard_prepared_input_set(&prepared.prepared_root)?;
                Err(error)
            }
        }
    }

    /// Admit an Agent-authored proposal whose proven mechanical execution limits may be omitted.
    /// Proposal identity is resolved before current operator policy so replay returns historical
    /// Runtime truth instead of re-adjudicating an already committed Job.
    pub fn run_job_proposal(
        &self,
        proposal: &super::JobRunProposal,
    ) -> RuntimeResult<JobObservation> {
        validate_run_proposal_structure(proposal)?;
        let request_identity_digest = super::proposal_request_identity_digest(proposal)?;
        let legacy_request_identity_digest =
            super::legacy_request_identity_digest_from_proposal(proposal)?;
        let (job_id, created) = {
            let _guard = self.lock_lifecycle()?;
            if let Some(existing) = self.registry.find_idempotent_job(
                &proposal.principal,
                &proposal.client_request_id,
                &request_identity_digest,
                legacy_request_identity_digest.as_deref(),
            )? {
                (existing.job_id, false)
            } else {
                let authority_contract =
                    super::authority_contract::AuthorityContract::ordinary(proposal)?;
                let request = self.resolve_proposal(proposal);
                validate_run_request_structure(&request)?;
                validate_new_admission_policy(
                    &request,
                    self.executor.max_runtime_ms,
                    self.executor.max_output_bytes,
                )?;
                (
                    self.admit_new_job(
                        &request,
                        request_identity_digest,
                        Some(&authority_contract),
                    )?,
                    true,
                )
            }
        };
        if created {
            self.ensure_newly_admitted_job_dispatched(&job_id)?;
        }
        self.observe_admitted_job(
            &job_id,
            proposal.wait_ms,
            proposal.stdout_tail_bytes,
            proposal.stderr_tail_bytes,
        )
    }

    #[cfg(test)]
    fn run_concrete_job(
        &self,
        request: &JobRunRequest,
        request_identity_digest: String,
    ) -> RuntimeResult<JobObservation> {
        let (job_id, created) = {
            let _guard = self.lock_lifecycle()?;
            if let Some(existing) = self.registry.find_idempotent_job(
                &request.principal,
                &request.client_request_id,
                &request_identity_digest,
                None,
            )? {
                (existing.job_id, false)
            } else {
                validate_new_admission_policy(
                    request,
                    self.executor.max_runtime_ms,
                    self.executor.max_output_bytes,
                )?;
                (self.admit_new_job(request, request_identity_digest, None)?, true)
            }
        };
        if created {
            self.ensure_newly_admitted_job_dispatched(&job_id)?;
        }
        self.observe_admitted_job(
            &job_id,
            request.wait_ms,
            request.stdout_tail_bytes,
            request.stderr_tail_bytes,
        )
    }

    fn admit_new_job(
        &self,
        request: &JobRunRequest,
        request_identity_digest: String,
        authority_contract: Option<&super::authority_contract::AuthorityContract>,
    ) -> RuntimeResult<String> {
        self.reconcile_recoverable_orphans()?;
        let _ = self.reconcile_workspace(&request.execution.workspace_id)?;
        let host_dependencies = self.validate_host_dependencies(request)?;
        let plan = self.resolve_plan(request)?;
        let provider =
            self.current_execution_provider_snapshot(request.execution.execution_target)?;
        let submit = match authority_contract {
            Some(authority_contract) => OperationCircuitCompiler::ordinary(
                authority_contract,
                request,
                request_identity_digest,
                provider,
                host_dependencies,
                plan,
            )?
            .into_submit_request(),
            None => SubmitRequest {
                schema_version: RUNTIME_SCHEMA_VERSION,
                client_request_id: request.client_request_id.clone(),
                request_identity_digest: Some(request_identity_digest),
                execution_provider: Some(provider),
                runtime_release_effect: None,
                host_dependencies,
                plan,
                global_limit: request.global_limit,
            },
        };
        match self.registry.submit(&submit)? {
            AdmissionOutcome::Created(created) => Ok(created.job.job_id.clone()),
            AdmissionOutcome::Existing { job } => Ok(job.job_id),
        }
    }

    fn observe_admitted_job(
        &self,
        job_id: &str,
        wait_ms: u64,
        stdout_tail_bytes: u64,
        stderr_tail_bytes: u64,
    ) -> RuntimeResult<JobObservation> {
        self.observe_job(&JobObserveRequest {
            schema_version: RUNTIME_SCHEMA_VERSION,
            job_id: job_id.to_string(),
            wait_ms,
            wait_until: JobObserveWaitUntil::Terminal,
            stdout_tail_bytes,
            stderr_tail_bytes,
            stdout_offset: None,
            stderr_offset: None,
        })
        .map_err(|error| error.with_operation_id(job_id.to_string()))
    }

    fn resolve_proposal(&self, proposal: &super::JobRunProposal) -> JobRunRequest {
        let timeout_ms = proposal
            .execution
            .timeout_ms
            .unwrap_or(self.default_runtime_ms);
        JobRunRequest {
            schema_version: proposal.schema_version,
            client_request_id: proposal.client_request_id.clone(),
            principal: proposal.principal.clone(),
            global_limit: proposal.global_limit,
            execution: super::UniversalExecutionRequest {
                workspace_id: proposal.execution.workspace_id.clone(),
                executable: proposal.execution.executable.clone(),
                args: proposal.execution.args.clone(),
                cwd_relative: proposal.execution.cwd_relative.clone(),
                env: proposal.execution.env.clone(),
                timeout_ms,
                stdout_limit_bytes: proposal
                    .execution
                    .stdout_limit_bytes
                    .unwrap_or(self.executor.max_output_bytes),
                stderr_limit_bytes: proposal
                    .execution
                    .stderr_limit_bytes
                    .unwrap_or(self.executor.max_output_bytes),
                steps: proposal
                    .execution
                    .steps
                    .iter()
                    .map(|step| super::UniversalExecutionStep {
                        id: step.id.clone(),
                        executable: step.executable.clone(),
                        args: step.args.clone(),
                        cwd_relative: step.cwd_relative.clone(),
                        env: step.env.clone(),
                        timeout_ms: step.timeout_ms.unwrap_or(timeout_ms),
                        continue_on_error: step.continue_on_error,
                    })
                    .collect(),
                budget: proposal.execution.budget.clone(),
                execution_profile: proposal.execution.execution_profile,
                execution_target: proposal.execution.execution_target,
                windows_authority: proposal.execution.windows_authority,
                windows_context: proposal.execution.windows_context,
                foreign_references: proposal.execution.foreign_references.clone(),
                host_dependencies: proposal.execution.host_dependencies.clone(),
            },
            wait_ms: proposal.wait_ms,
            stdout_tail_bytes: proposal.stdout_tail_bytes,
            stderr_tail_bytes: proposal.stderr_tail_bytes,
        }
    }

}
