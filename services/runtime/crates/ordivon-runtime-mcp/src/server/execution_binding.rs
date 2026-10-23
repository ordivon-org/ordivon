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

    fn bind(&self, request: WorkspaceExecRequest) -> JobRunProposal {
        JobRunProposal {
            schema_version: request.schema_version,
            client_request_id: request.client_request_id,
            principal: self.principal.clone(),
            global_limit: self.global_limit,
            execution: request.execution,
            wait_ms: request.wait_ms,
            stdout_tail_bytes: request.stdout_tail_bytes,
            stderr_tail_bytes: request.stderr_tail_bytes,
        }
    }

    fn bind_bound(
        &self,
        request: WorkspaceExecBoundRequest,
    ) -> (JobRunProposal, Vec<InputBindingRequest>) {
        let execution = request.execution;
        (
            JobRunProposal {
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
                    windows_context: None,
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
    ) -> Result<(JobRunProposal, Vec<InputBindingRequest>), ToolError> {
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
            JobRunProposal {
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
                    windows_context: None,
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

    fn bind_credential_bound_trusted(
        &self,
        request: WorkspaceExecCredentialBoundRequest,
    ) -> Result<(JobRunProposal, Vec<CredentialBindingRequest>), ToolError> {
        if request.execution.execution_target != ExecutionTarget::LocalLinux {
            return Err(ToolError::invalid(
                "workspace.execCredentialBoundTrusted supports local_linux only",
                "execution.executionTarget",
            ));
        }
        if request.execution.windows_authority != WindowsAuthority::Limited {
            return Err(ToolError::invalid(
                "workspace.execCredentialBoundTrusted does not accept Windows authority selection",
                "execution.windowsAuthority",
            ));
        }
        let execution = request.execution;
        Ok((
            JobRunProposal {
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
                    windows_context: None,
                    foreign_references: execution.foreign_references,
                    host_dependencies: Vec::new(),
                },
                wait_ms: request.wait_ms,
                stdout_tail_bytes: request.stdout_tail_bytes,
                stderr_tail_bytes: request.stderr_tail_bytes,
            },
            request.credentials,
        ))
    }

    fn bind_plan(&self, request: WorkspaceExecPlanRequest) -> Result<JobRunProposal, ToolError> {
        let first = request.execution.steps.first().cloned().ok_or_else(|| {
            ToolError::invalid("steps must contain at least one item", "execution.steps")
        })?;
        let all_step_timeouts_explicit = request
            .execution
            .steps
            .iter()
            .all(|step| step.timeout_ms.is_some());
        let legacy_shape = request.execution.timeout_ms.is_none()
            && all_step_timeouts_explicit
            && request.execution.stdout_limit_bytes.is_some()
            && request.execution.stderr_limit_bytes.is_some();
        let timeout_ms = if legacy_shape {
            // Read/replay compatibility only: historical v1 execPlan identity derived its
            // overall timeout from the explicit step sum. Preserve that execution meaning
            // while all new admissions use the v2 proposal identity.
            Some(
                request
                    .execution
                    .steps
                    .iter()
                    .try_fold(0_u64, |total, step| {
                        total.checked_add(step.timeout_ms.expect("checked explicit"))
                    })
                    .ok_or_else(|| {
                        ToolError::invalid("step timeout sum overflowed", "execution.steps")
                    })?,
            )
        } else {
            request.execution.timeout_ms
        };

        Ok(JobRunProposal {
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
                timeout_ms,
                stdout_limit_bytes: request.execution.stdout_limit_bytes,
                stderr_limit_bytes: request.execution.stderr_limit_bytes,
                steps: request.execution.steps,
                budget: request.execution.budget,
                execution_profile: request.execution.execution_profile,
                execution_target: request.execution.execution_target,
                windows_authority: request.execution.windows_authority,
                windows_context: request.execution.windows_context,
                foreign_references: request.execution.foreign_references,
                host_dependencies: request.execution.host_dependencies,
            },
            wait_ms: request.wait_ms,
            stdout_tail_bytes: request.stdout_tail_bytes,
            stderr_tail_bytes: request.stderr_tail_bytes,
        })
    }

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
