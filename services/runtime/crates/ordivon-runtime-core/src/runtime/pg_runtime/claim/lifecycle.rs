//! Existing physical Claim read/release, not a Domain output-finalizer or authority grant.
use super::contract::{validate_key, WorkspaceClaimKeyRequest, WorkspaceClaimProjection};
use super::persistence::query_claim;
use super::{
    io, now, workspace_effect_commit, PgRuntime, RuntimeError, RuntimeErrorCode, RuntimeResult,
};

impl PgRuntime {
    /// Exact principal+request key is the recovery coordinate for lost
    /// COMMIT/MCP replies; never submit a different claim when result UNKNOWN.
    pub fn get_workspace_claim(
        &self,
        principal: &str,
        request: &WorkspaceClaimKeyRequest,
    ) -> RuntimeResult<WorkspaceClaimProjection> {
        validate_key(
            request.schema_version,
            principal,
            &request.client_request_id,
        )?;
        let store_root = self
            .config
            .executor
            .canonical_store_root()
            .map_err(io)?
            .to_string_lossy()
            .into_owned();
        let mut db = self.store()?;
        query_claim(&mut db.client, principal, &request.client_request_id, false)?
            .filter(|claim| claim.store_root == store_root)
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::WorkspaceNotFound,
                    "no matching Runtime-owned Workspace Claim",
                    Some("clientRequestId"),
                    false,
                )
            })
    }

    /// This is a caller's consumer-release assertion, NOT an output finalizer.
    /// Source and ignored deliverables remain independent NativeClose gates.
    pub fn release_workspace_claim(
        &self,
        principal: &str,
        request: &WorkspaceClaimKeyRequest,
    ) -> RuntimeResult<WorkspaceClaimProjection> {
        validate_key(
            request.schema_version,
            principal,
            &request.client_request_id,
        )?;
        let store_root = self
            .config
            .executor
            .canonical_store_root()
            .map_err(io)?
            .to_string_lossy()
            .into_owned();
        let mut db = self.store()?;
        let mut tx = self.begin_workspace_effect_tx(&mut db)?;
        let mut existing = query_claim(&mut tx, principal, &request.client_request_id, true)?
            .filter(|claim| claim.store_root == store_root)
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::WorkspaceNotFound,
                    "no matching Runtime-owned Workspace Claim to release",
                    Some("clientRequestId"),
                    false,
                )
            })?;
        if existing.state == "held" {
            let time = now()?;
            tx.execute(
                "UPDATE workspace_consumer_claims
                 SET state='released', updated_at_ms=$2
                 WHERE claim_id=$1 AND state='held'",
                &[&existing.claim_id, &time],
            )
            .map_err(io)?;
            existing.state = "released".to_string();
            existing.updated_at_ms = time;
        }
        workspace_effect_commit(tx.commit(), "workspace.claim.release")?;
        Ok(existing)
    }
}
