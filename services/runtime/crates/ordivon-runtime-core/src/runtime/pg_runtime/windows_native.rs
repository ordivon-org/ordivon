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
        // The Session1 presentation/ACL/private Git carrier is a distinct
        // mandatory qualification. Do not launch with incomplete authority.
        if e.execution_target != ExecutionTarget::WindowsNative
            || e.execution_profile != ExecutionProfile::TrustedLocal
            || context.identity != WindowsExecutionIdentity::Service
            || context.privilege != WindowsPayloadPrivilege::Limited
            || e.windows_authority != WindowsAuthority::Limited
            || e.windows_context
                .is_some_and(|v| !v.compatible_with_legacy(e.windows_authority))
            || !e.steps.is_empty()
            || !e.host_dependencies.is_empty()
            || e.budget.scheduling.as_ref().is_some_and(|s| {
                s.workspace_access.read_only
                    || !s.workspace_access.read_paths.is_empty()
                    || !s.workspace_access.write_paths.is_empty()
            })
        {
            return Err(RuntimeError::invalid(
                "native Windows PG candidate currently qualifies single-command service-limited trusted_local only",
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
        windows::bind_pg_execution_context(&self.config.windows, proposal, plan)
    }

    pub(in crate::runtime::pg_runtime) fn launch_native_windows_attempt(
        &self,
        a: &AttemptRecord,
        plan: &RuntimeExecutionPlan,
        request_digest: &str,
        expected_launcher_digest: &str,
    ) -> RuntimeResult<()> {
        if plan.execution_target != ExecutionTarget::WindowsNative
            || plan.windows_authority != WindowsAuthority::Limited
            || a.unit_name != format!("Ordivon.{}", a.attempt_id)
            || plan.windows_execution_context.is_none()
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
        let observed = windows::spawn_windows_native(&WindowsNativeRunSpec {
            config: &self.config.windows,
            bundle_path: Path::new(&a.bundle_path),
            job_id: &a.job_id,
            attempt_id: &a.attempt_id,
            launch_token_digest: &a.launch_token_digest,
            request_digest,
            authority: plan.windows_authority,
            payload_privilege: WindowsPayloadPrivilege::Limited,
            expected_privileged_broker_digest: None,
            expected_user_sid: None,
            expected_session_id: None,
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
