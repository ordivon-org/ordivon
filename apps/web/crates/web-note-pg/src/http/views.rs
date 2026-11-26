use super::{ReadState, owner_problem};
use crate::identity::AuthenticatedSession;
use axum::{
    Extension, Json,
    extract::State,
    response::{IntoResponse, Response},
};
use serde::Serialize;
pub(super) async fn me(Extension(auth): Extension<AuthenticatedSession>) -> Response {
    Json(serde_json::json!({"principal":auth.principal,"session":auth.session})).into_response()
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct GrantObservation {
    principal_id: String,
    display_name: String,
    observed_at: i64,
    grants: Vec<crate::effect::GrantSnapshot>,
}
pub(super) async fn grants(
    State(state): State<ReadState>,
    Extension(auth): Extension<AuthenticatedSession>,
) -> Response {
    let observed_at = (state.clock)();
    match state.store.list_grants(&auth.principal.principal_id).await {
        Ok(grants) => Json(GrantObservation {
            principal_id: auth.principal.principal_id,
            display_name: auth.principal.display_name,
            observed_at,
            grants,
        })
        .into_response(),
        Err(e) => owner_problem(e),
    }
}

pub(super) async fn sessions(
    State(state): State<ReadState>,
    Extension(auth): Extension<AuthenticatedSession>,
) -> Response {
    match state
        .store
        .list_sessions(&auth.principal.principal_id)
        .await
    {
        Ok(sessions) => Json(
            serde_json::json!({"currentSessionId":auth.session.session_id,"sessions":sessions}),
        )
        .into_response(),
        Err(e) => owner_problem(e),
    }
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct PasskeyView {
    credential_id: String,
    device_type: String,
    backed_up: bool,
    transports: Vec<String>,
    created_at: i64,
    last_used_at: i64,
    revoked_at: Option<i64>,
}
pub(super) async fn passkeys(
    State(state): State<ReadState>,
    Extension(auth): Extension<AuthenticatedSession>,
) -> Response {
    match state
        .store
        .list_credentials(&auth.principal.principal_id)
        .await
    {
        Ok(credentials) => {
            let credentials: Vec<_> = credentials
                .into_iter()
                .map(|c| PasskeyView {
                    credential_id: c.credential_id,
                    device_type: c.device_type,
                    backed_up: c.backed_up,
                    transports: c.transports,
                    created_at: c.created_at,
                    last_used_at: c.last_used_at,
                    revoked_at: c.revoked_at,
                })
                .collect();
            Json(serde_json::json!({"credentials":credentials})).into_response()
        }
        Err(e) => owner_problem(e),
    }
}
