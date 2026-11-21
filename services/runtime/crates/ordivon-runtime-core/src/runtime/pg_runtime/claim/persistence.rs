//! Original PostgreSQL Claim row projection and exact principal/request-key readback.
use super::*;

pub(super) fn query_claim<C: postgres::GenericClient>(
    client: &mut C,
    principal: &str,
    client_request_id: &str,
    lock: bool,
) -> RuntimeResult<Option<WorkspaceClaimProjection>> {
    let query = if lock {
        "SELECT claim_id, workspace_id, client_request_id, run_ref, store_root, source_repo,
                 source_revision, source_state_digest, state, created_at_ms, updated_at_ms
           FROM workspace_consumer_claims
          WHERE principal=$1 AND client_request_id=$2 FOR UPDATE"
    } else {
        "SELECT claim_id, workspace_id, client_request_id, run_ref, store_root, source_repo,
                 source_revision, source_state_digest, state, created_at_ms, updated_at_ms
           FROM workspace_consumer_claims
          WHERE principal=$1 AND client_request_id=$2"
    };
    client
        .query_opt(query, &[&principal, &client_request_id])
        .map_err(io)
        .map(|row| {
            row.map(|r| WorkspaceClaimProjection {
                schema_version: 1,
                claim_id: r.get(0),
                workspace_id: r.get(1),
                client_request_id: r.get(2),
                run_ref: r.get(3),
                store_root: r.get(4),
                source_repo: r.get(5),
                source_revision: r.get(6),
                source_state_digest_at_reserve: r.get(7),
                state: r.get(8),
                created_at_ms: r.get(9),
                updated_at_ms: r.get(10),
            })
        })
}
