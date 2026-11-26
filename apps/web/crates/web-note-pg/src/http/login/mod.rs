//! Real WebAuthn login consumer. Trusted executable configuration is not request input.
mod verifier;
use super::{ReadState, owner_problem, problem, response_boundary};
use crate::{
    OwnerError, PgNoteStore,
    identity::{ChallengePurpose, PreparedChallenge, PreparedSession},
};
use axum::{
    Json, Router,
    extract::{DefaultBodyLimit, Request, State},
    http::{HeaderMap, HeaderValue, StatusCode, header},
    middleware::{self, Next},
    response::{IntoResponse, Response},
    routing::post,
};
use serde::Deserialize;
use serde_json::{Value, json};
use std::sync::Arc;
pub use verifier::LocalVerifier;
use verifier::Reply;
#[derive(Clone)]
pub struct LoginState {
    read: ReadState,
    verifier: LocalVerifier,
    origin: Arc<str>,
    rp_id: Arc<str>,
    absolute: i64,
}
impl LoginState {
    pub fn new(
        store: PgNoteStore,
        verifier: LocalVerifier,
        origin: &str,
        rp_id: &str,
        idle: i64,
        absolute: i64,
        clock: impl Fn() -> i64 + Send + Sync + 'static,
    ) -> Result<Self, OwnerError> {
        if !super::boundary::valid_origin(origin)
            || rp_id.is_empty()
            || absolute < idle
            || absolute > 604800
        {
            return Err(OwnerError::Invalid);
        }
        Ok(Self {
            read: ReadState::new(store, idle, clock)?,
            verifier,
            origin: origin.into(),
            rp_id: rp_id.into(),
            absolute,
        })
    }
}
pub fn login_router(state: LoginState) -> Router {
    Router::new()
        .route("/api/auth/login/options", post(options))
        .route("/api/auth/login/verify", post(verify))
        .route_layer(middleware::from_fn_with_state(state.clone(), origin_guard))
        .layer(DefaultBodyLimit::max(65536))
        .layer(middleware::from_fn(response_boundary))
        .with_state(state)
}
async fn origin_guard(State(s): State<LoginState>, req: Request, next: Next) -> Response {
    if let Err((status, code)) = super::boundary::unsafe_origin(req.headers(), &s.origin) {
        return problem(status, code);
    }
    next.run(req).await
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct OptionsInput {
    user_name: String,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct VerifyInput {
    challenge_id: String,
    response: Value,
}
fn denied() -> Response {
    problem(StatusCode::UNAUTHORIZED, "webauthn-login-failed")
}
fn unavailable() -> Response {
    problem(StatusCode::SERVICE_UNAVAILABLE, "verifier-unavailable")
}
fn login_error(e: OwnerError) -> Response {
    match e {
        OwnerError::ChallengeInvalid
        | OwnerError::CredentialNotFound
        | OwnerError::PrincipalNotFound
        | OwnerError::CredentialConflict
        | OwnerError::LoginCompleted => denied(),
        _ => owner_problem(e),
    }
}
fn text(s: &str, max: usize) -> bool {
    !s.is_empty() && s.len() <= max && !s.contains('\0')
}
async fn options(State(s): State<LoginState>, Json(input): Json<OptionsInput>) -> Response {
    if !text(&input.user_name, 256) {
        return problem(StatusCode::UNPROCESSABLE_ENTITY, "invalid-input");
    }
    let p = match s.read.store.find_principal(&input.user_name).await {
        Ok(p) => p,
        Err(e) => return login_error(e),
    };
    let credentials = match s.read.store.list_credentials(&p.principal_id).await {
        Ok(v) => v,
        Err(e) => return login_error(e),
    };
    let allow: Vec<_> = credentials
        .iter()
        .filter(|c| c.revoked_at.is_none())
        .map(|c| json!({"id":c.credential_id,"transports":c.transports}))
        .collect();
    if allow.is_empty() {
        return denied();
    }
    let result = s
        .verifier
        .call(json!({"op":"options","rpID":s.rp_id.as_ref(),"credentials":allow}))
        .await;
    let Ok(Reply::Options { options }) = result else {
        return unavailable();
    };
    let Some(challenge) = options["challenge"].as_str().filter(|v| text(v, 256)) else {
        return unavailable();
    };
    if options["rpId"] != s.rp_id.as_ref() || options["userVerification"] != "required" {
        return unavailable();
    }
    let p = match PreparedChallenge::new(
        ChallengePurpose::Login,
        &p.principal_id,
        challenge,
        "{}".into(),
        (s.read.clock)(),
        120,
    ) {
        Ok(p) => p,
        Err(e) => return login_error(e),
    };
    if let Err(e) = s.read.store.issue_challenge(&p).await {
        return login_error(e);
    }
    Json(json!({"challengeId":p.record().challenge_id,"options":options})).into_response()
}
async fn verify(
    State(s): State<LoginState>,
    headers: HeaderMap,
    Json(input): Json<VerifyInput>,
) -> Response {
    if !text(&input.challenge_id, 256) {
        return denied();
    }
    let Some(id) = input.response["id"].as_str().filter(|v| text(v, 2048)) else {
        return denied();
    };
    let credential = match s.read.store.get_active_credential(id).await {
        Ok(c) => c,
        Err(e) => return login_error(e),
    };
    let consumed = (s.read.clock)();
    let challenge = match s
        .read
        .store
        .consume_challenge(
            &input.challenge_id,
            ChallengePurpose::Login,
            &credential.principal_id,
            consumed,
        )
        .await
    {
        Ok(c) => c,
        Err(e) => return login_error(e),
    };
    let reply=s.verifier.call(json!({"op":"verify","rpID":s.rp_id.as_ref(),"origin":s.origin.as_ref(),"challenge":challenge.challenge,"response":input.response,"credential":{"id":credential.credential_id,"publicKey":credential.public_key,"counter":credential.counter,"transports":credential.transports}})).await;
    let counter = match reply {
        Ok(Reply::Verified { counter }) => counter,
        Ok(Reply::Denied) => return denied(),
        _ => return unavailable(),
    };
    let now = (s.read.clock)();
    let agent = headers
        .get(header::USER_AGENT)
        .and_then(|v| v.to_str().ok())
        .filter(|v| text(v, 1024))
        .map(str::to_owned);
    let prepared = match PreparedSession::new(
        &credential.principal_id,
        now,
        s.read.idle_seconds,
        s.absolute,
        agent,
    ) {
        Ok(p) => p,
        Err(e) => return login_error(e),
    };
    let principal = match s.read.store.get_principal(&credential.principal_id).await {
        Ok(p) => p,
        Err(e) => return login_error(e),
    };
    let session = match s
        .read
        .store
        .complete_verified_login(
            &challenge,
            consumed,
            &credential,
            i64::from(counter),
            &prepared,
        )
        .await
    {
        Ok(v) => v,
        Err(e) => return login_error(e),
    };
    let cookie = HeaderValue::from_str(&format!(
        "__Host-session={}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age={}; Priority=High",
        prepared.token(),
        s.absolute
    ))
    .expect("generated cookie");
    (
        [(header::SET_COOKIE, cookie)],
        Json(json!({"principal":principal,"session":session})),
    )
        .into_response()
}
