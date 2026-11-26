//! PG-native read-only ReleaseEffect projection.
//!
//! PostgreSQL is the only admission authority for this Runtime. The SQLite
//! Runtime's release *reader* is reusable only at the type/receipt-contract
//! level; its release storage and migration hooks are not PG authority.
//! This module does not admit, dispatch, or install any release.
use super::*;
use crate::runtime::artifact_release_state::ReleaseStateContract;

fn corrupt(message: &'static str) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::RegistryCorrupt,
        message,
        Some("runtimeReleaseEffect"),
        false,
    )
}

/// Read exact committed PG release side truth and externally attested receipt.
/// Does not reconcile or dispatch Jobs. In particular, a terminal Job without
/// a qualified installer receipt is NOT a deployed Runtime.
impl PgRuntime {
    pub fn get_runtime_release_effect(
        &self,
        request: &RuntimeReleaseGetRequest,
    ) -> RuntimeResult<RuntimeReleaseProjection> {
        if request.schema_version != RUNTIME_SCHEMA_VERSION {
            return Err(RuntimeError::invalid(
                "unsupported Runtime release schema version",
                "schemaVersion",
            ));
        }
        super::types::validate_client_request_id(&request.client_request_id, "clientRequestId")?;
        let mut db = self.store()?;
        // Principal is bound by the native MCP authenticated execution context,
        // NEVER caller-supplied JSON; the SQL lookup is scoped before any
        // receipt path or release metadata becomes visible.
        let row = db
            .client
            .query_opt(
                "SELECT j.job_id,j.request_digest,j.workspace_id,j.workspace_snapshot_json,\
             r.effect_id,r.contract,r.request_digest,r.workspace_id,r.commit_revision,\
             r.candidate_manifest_digest,r.expected_tool_count,r.receipt_path,r.binding_digest \
             FROM jobs j JOIN job_runtime_release_effects r ON r.job_id=j.job_id \
             WHERE j.principal=$1 AND j.client_request_id=$2",
                &[&request.principal, &request.client_request_id],
            )
            .map_err(io)?
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::JobNotFound,
                    "Runtime Release effect not found for principal",
                    Some("clientRequestId"),
                    false,
                )
            })?;
        let job_id: String = row.get(0);
        let contract: String = row.get(5);
        if contract != "runtime_release_v1" {
            return Err(corrupt("unsupported committed Runtime Release contract"));
        }
        let count: i32 = row.get(10);
        let expected_tool_count = u32::try_from(count)
            .map_err(|_| corrupt("invalid committed Runtime Release Tool count"))?;
        let binding = RuntimeReleaseEffectBinding {
            contract: RuntimeReleaseContract::RuntimeReleaseV1,
            effect_id: row.get(4),
            request_digest: row.get(6),
            workspace_id: row.get(7),
            commit: row.get(8),
            candidate_manifest_digest: row.get(9),
            expected_tool_count,
            receipt_path: row.get(11),
        };
        let source = RuntimeReleaseRequest {
            schema_version: 1,
            client_request_id: request.client_request_id.clone(),
            principal: request.principal.clone(),
            workspace_id: binding.workspace_id.clone(),
            commit: binding.commit.clone(),
            candidate_manifest_digest: binding.candidate_manifest_digest.clone(),
            expected_tool_count: binding.expected_tool_count,
        };
        ReleaseStateContract::validate_request(&source)
            .map_err(|_| corrupt("invalid committed Runtime Release identity"))?;
        ReleaseStateContract::validate_binding_matches_request(&binding, &source)?;
        if row.get::<_, String>(1) != binding.request_digest
            || row.get::<_, String>(2) != binding.workspace_id
        {
            return Err(corrupt("Runtime Release and Job identity disagree"));
        }
        let expected_digest = universal::sha256_bytes(encode(&binding)?.as_bytes());
        let snapshot: serde_json::Value = decode(&row.get::<_, String>(3))?;
        if row.get::<_, String>(12) != expected_digest
            || snapshot
                .get("runtimeReleaseEffectDigest")
                .and_then(serde_json::Value::as_str)
                != Some(expected_digest.as_str())
        {
            return Err(corrupt(
                "Runtime Release binding digest is not committed by Job",
            ));
        }

        let observation = self.project(
            &mut db,
            &JobObserveRequest {
                schema_version: 1,
                job_id: job_id.clone(),
                wait_ms: 0,
                wait_until: JobObserveWaitUntil::Terminal,
                stdout_tail_bytes: 0,
                stderr_tail_bytes: 0,
                stdout_offset: None,
                stderr_offset: None,
            },
        )?;
        let receipt = ReleaseStateContract::inspect_receipt(
            &binding,
            observation.execution_disposition,
            observation.attempt_state,
        )?;
        Ok(RuntimeReleaseProjection {
            contract: binding.contract,
            effect_id: binding.effect_id,
            client_request_id: request.client_request_id.clone(),
            job_id,
            workspace_id: binding.workspace_id,
            commit: binding.commit,
            candidate_manifest_digest: binding.candidate_manifest_digest,
            expected_tool_count: binding.expected_tool_count,
            effect_disposition: receipt.disposition,
            effect_terminal: receipt.terminal,
            receipt_available: receipt.available,
            receipt_digest: receipt.digest,
            deployed_tool_count: receipt.deployed_tool_count,
            tool_catalog_digest: receipt.tool_catalog_digest,
            rollback_status: receipt.rollback_status,
            reconciliation_issue: receipt.issue,
            attempt_state: observation.attempt_state,
            execution_terminal: observation.execution_terminal,
            execution_disposition: observation.execution_disposition,
            delivery_disposition: observation.delivery_disposition,
            recovery_required: observation.recovery_required,
            semantic_completion_evaluated: false,
        })
    }
}

/// A PG-native release is a distinct durable Effect, not a generic Runner Job.
/// Only admit after the MCP adapter independently verifies the configured
/// operator/service, exact Git owner revision and immutable candidate manifest.
/// The independent installed systemd operator, not Runtime's generic scheduler,
/// consumes the accepted side row and attests installed bytes and live MCP.
impl PgRuntime {
    /// Release advertisement needs independently qualified durable authority.
    /// Querying the app role cannot grant the qualification itself.
    pub fn release_qualified(&self) -> RuntimeResult<bool> {
        let mut db = self.store()?;
        let row=db.client.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='release'",
            &[],
        ).map_err(io)?;
        Ok(row.is_some_and(|row| {
            row.get::<_, String>(0) == "QUALIFIED_RELEASE"
                && row.get::<_, String>(1) == self.config.source_sha256
                && row.get::<_, bool>(2)
        }))
    }

    /// Resolve the exact committed release identity before considering new
    /// operator configuration or mutable candidate bytes.
    pub fn find_runtime_release_for_apply(
        &self,
        request: &RuntimeReleaseRequest,
    ) -> RuntimeResult<Option<RuntimeReleaseAdmission>> {
        ReleaseStateContract::validate_request(request)?;
        let identity = runtime_release_request_identity_digest(request)?;
        let mut db = self.store()?;
        let existing = db
            .client
            .query_opt(
                "SELECT request_digest FROM jobs WHERE principal=$1 AND client_request_id=$2",
                &[&request.principal, &request.client_request_id],
            )
            .map_err(io)?;
        let Some(existing) = existing else {
            return Ok(None);
        };
        if existing.get::<_, String>(0) != identity {
            return Err(pg(PgAdmissionError::IdempotencyConflict));
        }
        Ok(Some(RuntimeReleaseAdmission {
            replayed: true,
            release: self.get_runtime_release_effect(&RuntimeReleaseGetRequest {
                schema_version: 1,
                principal: request.principal.clone(),
                client_request_id: request.client_request_id.clone(),
            })?,
        }))
    }

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
            .map_err(super::super::error::map_universal_error)?;
        let (head, _, dirty) =
            universal::workspace_head_and_dirty_at(Path::new(&record.workspace_path))
                .map_err(super::super::error::map_universal_error)?;
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
