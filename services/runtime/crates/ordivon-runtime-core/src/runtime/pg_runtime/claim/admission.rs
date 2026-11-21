//! Original PG atomic Claim reserve with Workspace lifecycle and exact Source binding.
use super::contract::{validate_key, WorkspaceClaimProjection, WorkspaceClaimReserveRequest};
use super::persistence::query_claim;
use super::{
    io, now, universal, workspace_effect_commit, PgRuntime, RuntimeError, RuntimeErrorCode,
    RuntimeResult,
};
use uuid::Uuid;

impl PgRuntime {
    /// A HELD claim is a durable physical pin. The Run remains semantic truth
    /// in Harness's independent DB: this method does not grant Tool execution.
    /// The same Runtime PG admission lock protects this insert AND NativeClose.
    pub fn reserve_workspace_claim(
        &self,
        principal: &str,
        request: &WorkspaceClaimReserveRequest,
    ) -> RuntimeResult<WorkspaceClaimProjection> {
        validate_key(
            request.schema_version,
            principal,
            &request.client_request_id,
        )?;
        crate::runtime::types::validate_logical_id(&request.run_ref, "runRef")?;
        universal::validate_id(&request.workspace_id, "workspaceId").map_err(io)?;
        if !request.expected_source_state_digest.starts_with("sha256:")
            || request.expected_source_state_digest.len() != 71
            || !request.expected_source_state_digest[7..]
                .bytes()
                .all(|x| x.is_ascii_hexdigit())
        {
            return Err(RuntimeError::invalid(
                "exact sha256 sourceStateDigest required",
                "expectedSourceStateDigest",
            ));
        }
        let store_root = self
            .config
            .executor
            .canonical_store_root()
            .map_err(io)?
            .to_string_lossy()
            .into_owned();
        let mut db = self.store()?;
        let mut tx = self.begin_workspace_effect_tx(&mut db)?;
        if let Some(existing) = query_claim(&mut tx, principal, &request.client_request_id, true)? {
            if existing.workspace_id != request.workspace_id
                || existing.store_root != store_root
                || existing.run_ref != request.run_ref
                || existing.source_state_digest_at_reserve != request.expected_source_state_digest
            {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::IdempotencyConflict,
                    "clientRequestId already binds a different physical Workspace/Run",
                    Some("clientRequestId"),
                    false,
                ));
            }
            tx.commit().map_err(io)?;
            return Ok(existing);
        }
        // This read MUST follow Runtime's own PG lock, NOT a cached Harness
        // preflight. A Closed/Opening record, missing Git directory, or stale
        // source identity must refuse claim creation, including after a crash
        // between Git removal and closed tombstone.
        let record = universal::load_workspace_record(&self.config.executor, &request.workspace_id)
            .map_err(crate::runtime::error::map_universal_error)?;
        let physical_digest =
            universal::workspace_source_state_digest(&self.config.executor, &request.workspace_id)
                .map_err(io)?;
        if physical_digest != request.expected_source_state_digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RevisionMismatch,
                "Workspace source changed before Runtime-owned claim admission",
                Some("expectedSourceStateDigest"),
                false,
            ));
        }
        let id = format!("wclaim-{}", Uuid::now_v7());
        let time = now()?;
        tx.execute(
            "INSERT INTO workspace_consumer_claims
             (claim_id,principal,client_request_id,store_root,workspace_id,run_ref,source_repo,
              source_revision,source_state_digest,state,created_at_ms,updated_at_ms)
             VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,'held',$10,$10)",
            &[
                &id,
                &principal.to_owned(),
                &request.client_request_id,
                &store_root,
                &request.workspace_id,
                &request.run_ref,
                &record.source_repo,
                &record.source_revision,
                &physical_digest,
                &time,
            ],
        )
        .map_err(io)?;
        workspace_effect_commit(tx.commit(), "workspace.claim.reserve")?;
        Ok(WorkspaceClaimProjection {
            schema_version: 1,
            claim_id: id,
            workspace_id: request.workspace_id.clone(),
            client_request_id: request.client_request_id.clone(),
            run_ref: request.run_ref.clone(),
            store_root,
            source_repo: record.source_repo,
            source_revision: record.source_revision,
            source_state_digest_at_reserve: physical_digest,
            state: "held".to_string(),
            created_at_ms: time,
            updated_at_ms: time,
        })
    }
}
