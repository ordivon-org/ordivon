enum BoundTaskRun {
    Legacy(TaskRunRequest),
    Proposal(TaskRunProposal),
}

impl BoundTaskRun {
    fn authority_shadow_candidate(&self) -> Result<AuthorityEffectCandidate, FabricContractError> {
        match self {
            Self::Legacy(request) => authority_shadow_candidate(
                &request.principal,
                &request.execution.workspace_id,
                request.execution.execution_profile,
                request.execution.execution_target,
                request.execution.windows_authority,
            ),
            Self::Proposal(request) => authority_shadow_candidate(
                &request.principal,
                &request.execution.workspace_id,
                request.execution.execution_profile,
                request.execution.execution_target,
                request.execution.windows_authority,
            ),
        }
    }
}

fn proposal_authority_shadow_candidate(
    request: &TaskRunProposal,
) -> Result<AuthorityEffectCandidate, FabricContractError> {
    authority_shadow_candidate(
        &request.principal,
        &request.execution.workspace_id,
        request.execution.execution_profile,
        request.execution.execution_target,
        request.execution.windows_authority,
    )
}

fn authority_shadow_candidate(
    principal: &str,
    workspace_id: &str,
    execution_profile: ExecutionProfile,
    execution_target: ExecutionTarget,
    windows_authority: WindowsAuthority,
) -> Result<AuthorityEffectCandidate, FabricContractError> {
    let capability_id = match execution_target {
        ExecutionTarget::LocalLinux => "capability/execution/local-linux",
        ExecutionTarget::WindowsNative => "capability/execution/windows-native",
    };
    let os_authority = match execution_target {
        ExecutionTarget::LocalLinux => match execution_profile {
            ExecutionProfile::TrustedLocal => "linux/trusted-local",
            ExecutionProfile::ContainedLocal => "linux/contained-local",
        },
        ExecutionTarget::WindowsNative => match windows_authority {
            WindowsAuthority::Limited => "windows/limited",
            WindowsAuthority::Elevated => "windows/elevated",
        },
    };
    Ok(AuthorityEffectCandidate {
        schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
        principal_id: FabricId::parse(principal.to_string())?,
        trust_domain: FabricId::parse("ordivon.local")?,
        resource_scope: FabricId::parse(format!("workspace/{workspace_id}"))?,
        capability_id: FabricId::parse(capability_id)?,
        os_authority: FabricId::parse(os_authority)?,
        mode: AuthorityMode::OpenControl,
        // Execution tools are effect-capable. R1 observes them conservatively as writers;
        // this is conflict telemetry only and does not serialize or deny execution.
        conflict_mode: ConflictMode::ExclusiveWrite,
    })
}

#[derive(Clone)]
pub struct ExecutionContext {
    pub principal: String,
    pub global_limit: u32,
}

impl ExecutionContext {
    fn with_principal(&self, principal: impl Into<String>) -> Self {
        Self {
            principal: principal.into(),
            global_limit: self.global_limit,
        }
    }

    fn bind_patch(&self, request: WorkspacePatchToolRequest) -> DurableWorkspacePatchRequest {
        DurableWorkspacePatchRequest {
            schema_version: request.schema_version,
            principal: self.principal.clone(),
            client_request_id: request.client_request_id,
            patch: WorkspacePatchRequest {
                schema_version: request.schema_version,
                workspace_id: request.workspace_id,
                files: request.files,
                max_diff_bytes: request.max_diff_bytes,
            },
        }
    }

    fn bind_patch_status(
        &self,
        request: WorkspacePatchStatusToolRequest,
    ) -> WorkspacePatchStatusRequest {
        WorkspacePatchStatusRequest {
            schema_version: request.schema_version,
            principal: self.principal.clone(),
            client_request_id: request.client_request_id,
        }
    }

    fn bind(&self, request: WorkspaceExecRequest) -> BoundTaskRun {
        let legacy_compatible = request.execution.timeout_ms.is_some()
            && request.execution.stdout_limit_bytes.is_some()
            && request.execution.stderr_limit_bytes.is_some()
            && request
                .execution
                .steps
                .iter()
                .all(|step| step.timeout_ms.is_some());
        if legacy_compatible {
            BoundTaskRun::Legacy(TaskRunRequest {
                schema_version: request.schema_version,
                client_request_id: request.client_request_id,
                principal: self.principal.clone(),
                global_limit: self.global_limit,
                execution: UniversalExecutionRequest {
                    workspace_id: request.execution.workspace_id,
                    executable: request.execution.executable,
                    args: request.execution.args,
                    cwd_relative: request.execution.cwd_relative,
                    env: request.execution.env,
                    timeout_ms: request.execution.timeout_ms.expect("checked explicit"),
                    stdout_limit_bytes: request
                        .execution
                        .stdout_limit_bytes
                        .expect("checked explicit"),
                    stderr_limit_bytes: request
                        .execution
                        .stderr_limit_bytes
                        .expect("checked explicit"),
                    steps: request
                        .execution
                        .steps
                        .into_iter()
                        .map(|step| UniversalExecutionStep {
                            id: step.id,
                            executable: step.executable,
                            args: step.args,
                            cwd_relative: step.cwd_relative,
                            env: step.env,
                            timeout_ms: step.timeout_ms.expect("checked explicit"),
                            continue_on_error: step.continue_on_error,
                        })
                        .collect(),
                    budget: request.execution.budget,
                    execution_profile: request.execution.execution_profile,
                    execution_target: request.execution.execution_target,
                    windows_authority: request.execution.windows_authority,
                    foreign_references: request.execution.foreign_references,
                    host_dependencies: request.execution.host_dependencies,
                },
                wait_ms: request.wait_ms,
                stdout_tail_bytes: request.stdout_tail_bytes,
                stderr_tail_bytes: request.stderr_tail_bytes,
            })
        } else {
            BoundTaskRun::Proposal(TaskRunProposal {
                schema_version: request.schema_version,
                client_request_id: request.client_request_id,
                principal: self.principal.clone(),
                global_limit: self.global_limit,
                execution: request.execution,
                wait_ms: request.wait_ms,
                stdout_tail_bytes: request.stdout_tail_bytes,
                stderr_tail_bytes: request.stderr_tail_bytes,
            })
        }
    }

    fn bind_bound(
        &self,
        request: WorkspaceExecBoundRequest,
    ) -> (TaskRunProposal, Vec<InputBindingRequest>) {
        let execution = request.execution;
        (
            TaskRunProposal {
                schema_version: request.schema_version,
                client_request_id: request.client_request_id,
                principal: self.principal.clone(),
                global_limit: self.global_limit,
                execution: ExecutionProposal {
                    workspace_id: execution.workspace_id,
                    executable: execution.executable,
                    args: execution.args,
                    cwd_relative: execution.cwd_relative,
                    env: execution.env,
                    timeout_ms: execution.timeout_ms,
                    stdout_limit_bytes: execution.stdout_limit_bytes,
                    stderr_limit_bytes: execution.stderr_limit_bytes,
                    steps: execution.steps,
                    budget: execution.budget,
                    execution_profile: match execution.execution_target {
                        ExecutionTarget::LocalLinux => ExecutionProfile::ContainedLocal,
                        ExecutionTarget::WindowsNative => ExecutionProfile::TrustedLocal,
                    },
                    execution_target: execution.execution_target,
                    windows_authority: execution.windows_authority,
                    foreign_references: execution.foreign_references,
                    host_dependencies: Vec::new(),
                },
                wait_ms: request.wait_ms,
                stdout_tail_bytes: request.stdout_tail_bytes,
                stderr_tail_bytes: request.stderr_tail_bytes,
            },
            request.inputs,
        )
    }

    fn bind_bound_trusted(
        &self,
        request: WorkspaceExecBoundRequest,
    ) -> Result<(TaskRunProposal, Vec<InputBindingRequest>), ToolError> {
        if request.execution.execution_target != ExecutionTarget::LocalLinux {
            return Err(ToolError::invalid(
                "workspace.execBoundTrusted supports local_linux only",
                "execution.executionTarget",
            ));
        }
        if request.execution.windows_authority != WindowsAuthority::Limited {
            return Err(ToolError::invalid(
                "workspace.execBoundTrusted does not accept Windows authority selection",
                "execution.windowsAuthority",
            ));
        }
        let execution = request.execution;
        Ok((
            TaskRunProposal {
                schema_version: request.schema_version,
                client_request_id: request.client_request_id,
                principal: self.principal.clone(),
                global_limit: self.global_limit,
                execution: ExecutionProposal {
                    workspace_id: execution.workspace_id,
                    executable: execution.executable,
                    args: execution.args,
                    cwd_relative: execution.cwd_relative,
                    env: execution.env,
                    timeout_ms: execution.timeout_ms,
                    stdout_limit_bytes: execution.stdout_limit_bytes,
                    stderr_limit_bytes: execution.stderr_limit_bytes,
                    steps: execution.steps,
                    budget: execution.budget,
                    execution_profile: ExecutionProfile::TrustedLocal,
                    execution_target: ExecutionTarget::LocalLinux,
                    windows_authority: WindowsAuthority::Limited,
                    foreign_references: execution.foreign_references,
                    host_dependencies: Vec::new(),
                },
                wait_ms: request.wait_ms,
                stdout_tail_bytes: request.stdout_tail_bytes,
                stderr_tail_bytes: request.stderr_tail_bytes,
            },
            request.inputs,
        ))
    }

    fn bind_plan(&self, request: WorkspaceExecPlanRequest) -> Result<BoundTaskRun, ToolError> {
        let first = request.execution.steps.first().cloned().ok_or_else(|| {
            ToolError::invalid("steps must contain at least one item", "execution.steps")
        })?;
        let all_step_timeouts_explicit = request
            .execution
            .steps
            .iter()
            .all(|step| step.timeout_ms.is_some());
        let legacy_compatible = request.execution.timeout_ms.is_none()
            && all_step_timeouts_explicit
            && request.execution.stdout_limit_bytes.is_some()
            && request.execution.stderr_limit_bytes.is_some();
        if legacy_compatible {
            // Compatibility only: v1 execPlan identity historically derived its overall timeout
            // from the explicit step sum. This arithmetic is not a Runtime execution law.
            let timeout_ms = request
                .execution
                .steps
                .iter()
                .try_fold(0_u64, |total, step| {
                    total.checked_add(step.timeout_ms.expect("checked explicit"))
                })
                .ok_or_else(|| {
                    ToolError::invalid("step timeout sum overflowed", "execution.steps")
                })?;
            return Ok(BoundTaskRun::Legacy(TaskRunRequest {
                schema_version: request.schema_version,
                client_request_id: request.client_request_id,
                principal: self.principal.clone(),
                global_limit: self.global_limit,
                execution: UniversalExecutionRequest {
                    workspace_id: request.execution.workspace_id,
                    executable: first.executable.clone(),
                    args: first.args.clone(),
                    cwd_relative: first.cwd_relative.clone(),
                    env: first.env.clone(),
                    timeout_ms,
                    stdout_limit_bytes: request
                        .execution
                        .stdout_limit_bytes
                        .expect("checked explicit"),
                    stderr_limit_bytes: request
                        .execution
                        .stderr_limit_bytes
                        .expect("checked explicit"),
                    steps: request
                        .execution
                        .steps
                        .into_iter()
                        .map(|step| UniversalExecutionStep {
                            id: step.id,
                            executable: step.executable,
                            args: step.args,
                            cwd_relative: step.cwd_relative,
                            env: step.env,
                            timeout_ms: step.timeout_ms.expect("checked explicit"),
                            continue_on_error: step.continue_on_error,
                        })
                        .collect(),
                    budget: request.execution.budget,
                    execution_profile: request.execution.execution_profile,
                    execution_target: request.execution.execution_target,
                    windows_authority: request.execution.windows_authority,
                    foreign_references: request.execution.foreign_references,
                    host_dependencies: request.execution.host_dependencies,
                },
                wait_ms: request.wait_ms,
                stdout_tail_bytes: request.stdout_tail_bytes,
                stderr_tail_bytes: request.stderr_tail_bytes,
            }));
        }

        Ok(BoundTaskRun::Proposal(TaskRunProposal {
            schema_version: request.schema_version,
            client_request_id: request.client_request_id,
            principal: self.principal.clone(),
            global_limit: self.global_limit,
            execution: ExecutionProposal {
                workspace_id: request.execution.workspace_id,
                executable: first.executable,
                args: first.args,
                cwd_relative: first.cwd_relative,
                env: first.env,
                timeout_ms: request.execution.timeout_ms,
                stdout_limit_bytes: request.execution.stdout_limit_bytes,
                stderr_limit_bytes: request.execution.stderr_limit_bytes,
                steps: request.execution.steps,
                budget: request.execution.budget,
                execution_profile: request.execution.execution_profile,
                execution_target: request.execution.execution_target,
                windows_authority: request.execution.windows_authority,
                foreign_references: request.execution.foreign_references,
                host_dependencies: request.execution.host_dependencies,
            },
            wait_ms: request.wait_ms,
            stdout_tail_bytes: request.stdout_tail_bytes,
            stderr_tail_bytes: request.stderr_tail_bytes,
        }))
    }
}

fn default_patch_diff_bytes() -> u64 {
    MAX_WORKSPACE_IO_BYTES
}

fn default_exec_wait_ms() -> u64 {
    // Public MCP admission should return quickly once durable Job identity exists.
    // Callers that deliberately want a longer synchronous observation may still
    // request any wait up to Core's MAX_TASK_WAIT_MS.
    2_000
}

fn default_exec_tail_bytes() -> u64 {
    4096
}
