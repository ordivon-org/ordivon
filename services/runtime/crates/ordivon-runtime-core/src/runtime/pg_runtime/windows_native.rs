//! Native Windows provider of the original PG Job lifecycle. No separate
//! registry, scheduler, authority, or terminal writer.
use super::*;
use crate::runtime::windows::{self, WindowsNativeRunSpec};

impl PgRuntime {
    pub(super) fn validate_native_windows_proposal(
        &self,
        proposal: &JobRunProposal,
    ) -> RuntimeResult<()> {
        let e = &proposal.execution;
        let context = e
            .windows_context
            .unwrap_or_else(|| e.windows_authority.canonical_context());
        // Only the configured desktop identity can receive an active-user
        // context; the existing native launcher still verifies SID/session.
        if !super::job::supports_native_pg_execution(e, true)
            || (context.identity == WindowsExecutionIdentity::ActiveUser
                && self.config.interactive_workspace_sid.is_none())
            || e.windows_context
                .is_some_and(|v| !v.compatible_with_legacy(e.windows_authority))
            || e.budget.scheduling.as_ref().is_some_and(|s| {
                s.workspace_access.read_only
                    || !s.workspace_access.read_paths.is_empty()
                    || !s.workspace_access.write_paths.is_empty()
            })
        {
            return Err(RuntimeError::invalid(
                "native Windows PG supports single-command service or operator-bound active_user trusted_local only",
                "execution",
            ));
        }
        self.config.windows.authorize_new_proposal(proposal)
    }

    pub(super) fn bind_native_windows_plan(
        &self,
        proposal: &JobRunProposal,
        plan: &mut RuntimeExecutionPlan,
    ) -> RuntimeResult<()> {
        windows::bind_pg_execution_context(&self.config.windows, proposal, plan)?;
        if plan.windows_authority == WindowsAuthority::ActiveUser {
            let context = plan
                .windows_execution_context
                .as_ref()
                .ok_or_else(|| error("native active-user context missing"))?;
            self.require_interactive_context(&context.token_user_sid, context.session_id)?;
        }
        let context = plan
            .windows_context
            .unwrap_or_else(|| plan.windows_authority.canonical_context());
        if context.privilege == WindowsPayloadPrivilege::Elevated {
            // A writable Workspace must not become the privileged process's
            // current-directory search root. The operator owns the profile's
            // executable and its installation directory.
            plan.cwd = Path::new(&plan.executable)
                .parent()
                .ok_or_else(|| error("elevated Windows executable directory missing"))?
                .to_str()
                .ok_or_else(|| error("non-UTF8 elevated Windows executable directory"))?
                .to_owned();
        }
        let (git_dir, work_tree) = self.qualified_git_environment(plan)?;
        windows::bind_pg_private_git_environment(&mut plan.env, &git_dir, &work_tree)?;
        Ok(())
    }

    pub(in crate::runtime::pg_runtime) fn require_interactive_context(
        &self,
        sid: &str,
        session: Option<u32>,
    ) -> RuntimeResult<()> {
        if self.config.interactive_workspace_sid.as_deref() != Some(sid)
            || session.is_none_or(|v| v == 0)
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                "active desktop token does not match operator-bound interactive account/session",
                Some("windowsContext"),
                false,
            ));
        }
        Ok(())
    }

    fn interactive_workspace_leaves(&self, id: &str) -> RuntimeResult<(PathBuf, PathBuf)> {
        let root = self
            .config
            .executor
            .workspace_root
            .as_ref()
            .ok_or_else(|| error("operator Workspace root absent"))?;
        let _root = universal::open_directory_nofollow(root).map_err(io)?;
        let root = fs::canonicalize(root).map_err(io)?;
        let leaf = |p: PathBuf| -> RuntimeResult<PathBuf> {
            let _directory = universal::open_directory_nofollow(&p).map_err(io)?;
            let physical = fs::canonicalize(p).map_err(io)?;
            if physical.parent() != Some(root.as_path()) {
                return Err(error(
                    "interactive carrier escaped its exact presentation root",
                ));
            }
            Ok(physical)
        };
        Ok((
            leaf(self.config.executor.workspace_path(id))?,
            leaf(self.config.executor.workspace_private_git_path(id))?,
        ))
    }

    fn qualified_git_environment(
        &self,
        plan: &RuntimeExecutionPlan,
    ) -> RuntimeResult<(String, String)> {
        let (worktree, private) = self.interactive_workspace_leaves(&plan.workspace_id)?;
        if worktree != Path::new(&plan.workspace_path) || worktree == private {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "Windows PG private Git carrier differs from admitted Workspace",
                Some("execution.workspaceId"),
                false,
            ));
        }
        let visible = |path: &Path| -> RuntimeResult<String> {
            use std::path::{Component, Prefix};
            let carrier = universal::git_cli_path(path);
            if !matches!(carrier.components().next(), Some(Component::Prefix(p)) if matches!(p.kind(), Prefix::Disk(_)))
            {
                return Err(RuntimeError::invalid(
                    "Windows PG Git carrier has no ordinary drive-path projection",
                    "execution.workspaceId",
                ));
            }
            carrier
                .to_str()
                .map(str::to_owned)
                .ok_or_else(|| error("non-UTF8 Git carrier"))
        };
        Ok((visible(&private)?, visible(&worktree)?))
    }

    pub(in crate::runtime::pg_runtime) fn prepare_interactive_workspace_leaves(
        &self,
        id: &str,
        sid: &str,
    ) -> RuntimeResult<()> {
        let (worktree, private) = self.interactive_workspace_leaves(id)?;
        // Grant private Git first, then worktree. No grant to parent, source,
        // journal or secret. Only fresh open calls this under the PG lock.
        crate::windows_security::protect_interactive_workspace_leaf(&private, sid).map_err(io)?;
        crate::windows_security::protect_interactive_workspace_leaf(&worktree, sid).map_err(io)?;
        Ok(())
    }

    pub(in crate::runtime::pg_runtime) fn launch_native_windows_attempt(
        &self,
        a: &AttemptRecord,
        plan: &RuntimeExecutionPlan,
        request_digest: &str,
        expected_launcher_digest: &str,
    ) -> RuntimeResult<()> {
        let payload = plan
            .windows_context
            .unwrap_or_else(|| plan.windows_authority.canonical_context());
        if plan.execution_target != ExecutionTarget::WindowsNative
            || payload.transport_authority() != plan.windows_authority
            || a.unit_name != format!("Ordivon.{}", a.attempt_id)
        {
            return Err(error("invalid frozen Windows native provider identity")
                .with_operation_id(&a.job_id));
        }
        let launcher_digest =
            universal::sha256_file(&self.config.windows.launcher_path).map_err(io)?;
        if launcher_digest != expected_launcher_digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ProviderStateMismatch,
                "native Windows launcher changed after admission",
                Some("executionProvider"),
                false,
            )
            .with_operation_id(&a.job_id));
        }
        let context = plan
            .windows_execution_context
            .as_ref()
            .ok_or_else(|| error("frozen native context absent"))?;
        let active_user = payload.identity == WindowsExecutionIdentity::ActiveUser;
        if active_user {
            self.require_interactive_context(&context.token_user_sid, context.session_id)?;
        }
        let (git_dir, work_tree) = self.qualified_git_environment(plan)?;
        for (key, value) in [("GIT_DIR", git_dir), ("GIT_WORK_TREE", work_tree)] {
            if plan.env.get(key) != Some(&value) {
                return Err(
                    error("frozen native PG Git carrier changed").with_operation_id(&a.job_id)
                );
            }
        }
        let observed = windows::spawn_windows_native(&WindowsNativeRunSpec {
            config: &self.config.windows,
            bundle_path: Path::new(&a.bundle_path),
            job_id: &a.job_id,
            attempt_id: &a.attempt_id,
            launch_token_digest: &a.launch_token_digest,
            request_digest,
            authority: plan.windows_authority,
            payload_privilege: payload.privilege,
            expected_privileged_broker_digest: context.privileged_broker_digest.as_deref(),
            expected_user_sid: active_user.then_some(context.token_user_sid.as_str()),
            expected_session_id: if active_user {
                context.session_id
            } else {
                None
            },
            executable: Path::new(&plan.executable),
            args: &plan.args,
            cwd: Path::new(&plan.cwd),
            environment: &plan.env,
            input_source_root: None,
            input_set_id: None,
            input_presentation_root: None,
            input_bindings_digest: None,
            budget: &plan.budget,
            timeout_ms: plan.timeout_ms,
            stdout_limit_bytes: plan.stdout_limit_bytes,
            stderr_limit_bytes: plan.stderr_limit_bytes,
            pg_terminal_peer_pid: Some(std::process::id()),
        })
        .map_err(|e| {
            RuntimeError::new(
                RuntimeErrorCode::DispatchOutcomeUnknown,
                format!("native Windows dispatch after durable issue: {}", e.message),
                Some("jobId"),
                false,
            )
            .with_operation_id(&a.job_id)
        })?;
        // Parent's actual native process handle is the sole source of identity.
        universal::write_json_atomic(
            &Path::new(&a.bundle_path).join("windows-launcher-start.json"),
            &json!({"schemaVersion":1,"jobId":a.job_id,"attemptId":a.attempt_id,
                "launchTokenDigest":a.launch_token_digest,"requestDigest":request_digest,
                "jobName":a.unit_name,"launcherProcessId":observed.launcher_process_id,
                "launcherProcessCreationTimeFileTime":observed.launcher_process_creation_time_file_time,
                "launcherImageDigest":launcher_digest,"observedUnixMs":now()?}),
        ).map_err(|e| RuntimeError::new(RuntimeErrorCode::DispatchOutcomeUnknown,
            format!("Windows launcher may already be running: {e}"), Some("jobId"), false)
            .with_operation_id(&a.job_id))?;
        Ok(())
    }

    pub(in crate::runtime::pg_runtime) fn publish_native_windows_stop(
        &self,
        a: &AttemptRecord,
    ) -> RuntimeResult<()> {
        if a.unit_name != format!("Ordivon.{}", a.attempt_id) {
            return Err(error("Windows native stop identity mismatch").with_operation_id(&a.job_id));
        }
        universal::write_json_atomic(
            &Path::new(&a.bundle_path).join("cancel-requested.json"),
            &json!({"schemaVersion":1,"jobId":a.job_id,"attemptId":a.attempt_id}),
        )
        .map_err(io)
    }

    pub(in crate::runtime::pg_runtime) fn reconcile_native_windows_attempt(
        &self,
        db: &mut PgAdmissionStore,
        a: &AttemptRecord,
        plan: &RuntimeExecutionPlan,
    ) -> RuntimeResult<()> {
        if a.state.is_terminal() {
            return Ok(());
        }
        if a.termination_intent == AttemptTerminationIntent::StopRequested {
            self.publish_native_windows_stop(a)?;
        }
        if a.state == AttemptState::Starting
            && a.termination_intent == AttemptTerminationIntent::Natural
        {
            crate::pg_windows_evidence::reconcile_admitted_windows_pg_running(
                db,
                &self.config.source_sha256,
                &plan.principal,
                &a.job_id,
                &self.config.executor.store_root,
            )
            .map_err(|e| {
                RuntimeError::new(
                    RuntimeErrorCode::ReconciliationRequired,
                    e,
                    Some("jobId"),
                    false,
                )
                .with_operation_id(&a.job_id)
            })?;
        }
        // Terminal reconciliation rebinds the PG row after RUNNER_BOUND.
        crate::pg_windows_evidence::reconcile_admitted_windows_pg_terminal(
            db,
            &self.config.source_sha256,
            &plan.principal,
            &a.job_id,
            &self.config.executor.store_root,
        )
        .map_err(|e| {
            RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                e,
                Some("jobId"),
                false,
            )
            .with_operation_id(&a.job_id)
        })?;
        Ok(())
    }
}
