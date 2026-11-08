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
