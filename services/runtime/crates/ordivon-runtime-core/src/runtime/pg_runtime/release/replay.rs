// Original PG ReleaseEffect same principal+client key idempotent effect reuse.
use super::{
    io, pg, runtime_release_request_identity_digest, PgAdmissionError, PgRuntime,
    RuntimeReleaseAdmission, RuntimeReleaseGetRequest, RuntimeReleaseRequest, RuntimeResult,
};
use crate::runtime::artifact_release_state::ReleaseStateContract;

impl PgRuntime {
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
}
