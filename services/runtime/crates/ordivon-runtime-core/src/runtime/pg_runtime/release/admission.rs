// Original PG ReleaseEffect exact immutable candidate snapshot admission, no OS spawn.
use super::{
    encode, io, json, now, pg, runtime_release_effect_id, runtime_release_request_identity_digest,
    universal, ExecutionBudget, ExecutionProfile, ExecutionTarget, JobIdentityContract,
    OperationIdentityBindings, Path, PgAdmissionInput, PgAdmissionOutcome, PgRuntime, RuntimeError,
    RuntimeExecutionPlan, RuntimeReleaseAdmission, RuntimeReleaseContract,
    RuntimeReleaseEffectBinding, RuntimeReleaseGetRequest, RuntimeReleaseRequest, RuntimeResult,
    Uuid, WindowsAuthority,
};
use crate::runtime::artifact_release_state::ReleaseStateContract;

impl PgRuntime {
    pub fn admit_runtime_release_effect(
        &self,
        request: &RuntimeReleaseRequest,
        operator_executable: &Path,
        receipt_root: &Path,
    ) -> RuntimeResult<RuntimeReleaseAdmission> {
        ReleaseStateContract::validate_request(request)?;
        if let Some(replay) = self.find_runtime_release_for_apply(request)? {
            return Ok(replay);
        }
        let identity = runtime_release_request_identity_digest(request)?;
        let mut db = self.store()?;
        if !receipt_root.is_absolute()
            || !operator_executable.is_absolute()
            || !operator_executable.is_file()
        {
            return Err(RuntimeError::invalid(
                "qualified PG release operator and absolute receiptRoot required",
                "release",
            ));
        }
        let operator_digest = universal::sha256_file(operator_executable).map_err(io)?;
        let record = universal::load_workspace_record(&self.config.executor, &request.workspace_id)
            .map_err(crate::runtime::error::map_universal_error)?;
        let (head, _, dirty) =
            universal::workspace_head_and_dirty_at(Path::new(&record.workspace_path))
                .map_err(crate::runtime::error::map_universal_error)?;
        if dirty || head.len() != 40 {
            return Err(RuntimeError::invalid(
                "Release Workspace must have an exact clean Git HEAD",
                "workspaceId",
            ));
        }
        let effect_id = runtime_release_effect_id(request);
        let receipt_path = receipt_root.join(format!("effect-{effect_id}"));
        let binding = RuntimeReleaseEffectBinding {
            contract: RuntimeReleaseContract::RuntimeReleaseV1,
            effect_id: effect_id.clone(),
            request_digest: identity.clone(),
            workspace_id: request.workspace_id.clone(),
            commit: request.commit.clone(),
            candidate_manifest_digest: request.candidate_manifest_digest.clone(),
            expected_tool_count: request.expected_tool_count,
            receipt_path: receipt_path.to_string_lossy().into_owned(),
        };
        let binding_digest = universal::sha256_bytes(encode(&binding)?.as_bytes());
        let snapshot = json!({
            "workspace":record,
            "runtimeReleaseEffectDigest":binding_digest,
            "executionProvider":{
                "contract":"pg_release_operator_v1",
                "executableDigest":operator_digest
            }
        });
        // Avoid accidental later mutation of the identity-bound snapshot.
        let snapshot_json = encode(&snapshot)?;
        let plan = RuntimeExecutionPlan {
            schema_version: 1,
            workspace_id: request.workspace_id.clone(),
            workspace_path: record.workspace_path.clone(),
            source_revision: head,
            workspace_source_digest: None,
            workspace_git_common_dir: None,
            executable: operator_executable.to_string_lossy().into_owned(),
            executable_digest: operator_digest.clone(),
            args: vec!["apply".into(), "--effect-id".into(), effect_id],
            cwd: record.workspace_path.clone(),
            env: Default::default(),
            timeout_ms: self.config.executor.max_runtime_ms,
            stdout_limit_bytes: self.config.executor.max_output_bytes,
            stderr_limit_bytes: self.config.executor.max_output_bytes,
            steps: Vec::new(),
            budget: ExecutionBudget::default(),
            execution_profile: ExecutionProfile::TrustedLocal,
            execution_target: ExecutionTarget::LocalLinux,
            windows_authority: WindowsAuthority::Limited,
            windows_context: None,
            windows_execution_context: None,
            foreign_references: Vec::new(),
            host_dependencies: Vec::new(),
            input_set_id: None,
            effective_inputs: Vec::new(),
            credential_set_id: None,
            principal: request.principal.clone(),
        };
        let plan_json = encode(&plan)?;
        let plan_digest = universal::sha256_bytes(plan_json.as_bytes());
        let operation_digest = JobIdentityContract::operation_digest(
            &identity,
            &plan_digest,
            OperationIdentityBindings::Provider {
                provider_digest: &operator_digest,
            },
        );
        let attempt = format!("attempt-{}", Uuid::now_v7());
        let token = universal::sha256_bytes(
            format!("runtime-release-launch-v1\0{attempt}\0{operation_digest}").as_bytes(),
        );
        let input = PgAdmissionInput {
            job_id: format!("job-{}", Uuid::now_v7()),
            attempt_id: attempt.clone(),
            reservation_id: format!("reservation-{}", Uuid::now_v7()),
            principal: request.principal.clone(),
            client_request_id: request.client_request_id.clone(),
            request_digest: identity,
            operation_digest,
            workspace_id: request.workspace_id.clone(),
            workspace_snapshot_json: snapshot_json,
            execution_plan_json: plan_json,
            execution_plan_digest: plan_digest,
            launch_token_digest: universal::sha256_bytes(token.as_bytes()),
            bundle_path: self
                .config
                .executor
                .store_root
                .join("pg-attempts")
                .join(&attempt)
                .to_string_lossy()
                .into_owned(),
            unit_name: format!("ordivon-pg-{attempt}.service"),
            global_limit: 0,
            created_at_ms: now()?,
            expected_source_sha256: self.config.source_sha256.clone(),
        };
        let replayed = match db
            .admit_release_effect(&input, request, &receipt_path)
            .map_err(pg)?
        {
            PgAdmissionOutcome::Existing(_) => true,
            PgAdmissionOutcome::Created(_) => false,
        };
        // Admission intentionally NEVER starts a generic Runner or the
        // independently privileged operator. PG is durable intent authority.
        let release = self.get_runtime_release_effect(&RuntimeReleaseGetRequest {
            schema_version: 1,
            principal: request.principal.clone(),
            client_request_id: request.client_request_id.clone(),
        })?;
        Ok(RuntimeReleaseAdmission { replayed, release })
    }
}
