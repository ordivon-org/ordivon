//! Narrow browser mutation consumer: only current-session self-revocation.
//! The process-local CSRF key is not an authentication authority.
use super::{ReadState, boundary, owner_problem, problem, response_boundary};
use crate::{OwnerError, PgNoteStore};
use axum::{
    Json, Router,
    extract::State,
    http::{HeaderMap, StatusCode, header},
    middleware,
    response::{IntoResponse, Response},
    routing::{get, post},
};
use base64::{Engine, engine::general_purpose::URL_SAFE_NO_PAD};
use hmac::{Hmac, KeyInit, Mac};
use sha2::Sha256;
use std::sync::Arc;
use uuid::Uuid;

#[derive(Clone)]
pub struct SessionWriteState {
    read: ReadState,
    origin: Arc<str>,
    csrf_key: Arc<[u8; 32]>,
}
impl SessionWriteState {
    pub fn new(
        store: PgNoteStore,
        origin: &str,
        idle: i64,
        clock: impl Fn() -> i64 + Send + Sync + 'static,
    ) -> Result<Self, OwnerError> {
        if !boundary::valid_origin(origin) {
            return Err(OwnerError::Invalid);
        }
        let mut key = [0u8; 32];
        getrandom::fill(&mut key).map_err(|_| OwnerError::Entropy)?;
        Ok(Self {
            read: ReadState::new(store, idle, clock)?,
            origin: origin.into(),
            csrf_key: Arc::new(key),
        })
    }
    fn mac(&self, session: &str) -> Hmac<Sha256> {
        let mut mac = Hmac::<Sha256>::new_from_slice(self.csrf_key.as_ref()).expect("fixed key");
        mac.update(b"ordivon-web:csrf:session:v1\0");
        mac.update(session.as_bytes());
        mac
    }
    fn token(&self, session: &str) -> String {
        URL_SAFE_NO_PAD.encode(self.mac(session).finalize().into_bytes())
    }
    fn accepts(&self, headers: &HeaderMap, session: &str) -> bool {
        let mut values = headers.get_all("x-csrf-token").iter();
        let Some(value) = values.next().and_then(|v| v.to_str().ok()) else {
            return false;
        };
        if values.next().is_some() || value.len() != 43 {
            return false;
        }
        let Ok(decoded) = URL_SAFE_NO_PAD.decode(value) else {
            return false;
        };
        self.mac(session).verify_slice(&decoded).is_ok()
    }
}
pub fn session_write_router(state: SessionWriteState) -> Router {
    Router::new()
        .route("/api/session/csrf", get(csrf))
        .route("/api/session/logout", post(logout))
        .layer(middleware::from_fn(response_boundary))
        .with_state(state)
}
async fn csrf(
    State(s): State<SessionWriteState>,
    method: axum::http::Method,
    headers: HeaderMap,
) -> Response {
    if method != axum::http::Method::GET {
        return problem(StatusCode::METHOD_NOT_ALLOWED, "method-not-allowed");
    }
    let token = match boundary::session_token(&headers) {
        Ok(t) => t,
        Err((status, code)) => return problem(status, code),
    };
    if let Err(e) = s
        .read
        .store
        .authenticate_session(token, (s.read.clock)(), s.read.idle_seconds)
        .await
    {
        return owner_problem(e);
    }
    Json(serde_json::json!({"token":s.token(token)})).into_response()
}
async fn logout(State(s): State<SessionWriteState>, headers: HeaderMap) -> Response {
    if let Err((status, code)) = boundary::unsafe_origin(&headers, &s.origin) {
        return problem(status, code);
    }
    let token = match boundary::session_token(&headers) {
        Ok(t) => t,
        Err((status, code)) => return problem(status, code),
    };
    if !s.accepts(&headers, token) {
        return problem(StatusCode::FORBIDDEN, "csrf-rejected");
    }
    let now = (s.read.clock)();
    let auth = match s
        .read
        .store
        .authenticate_session(token, now, s.read.idle_seconds)
        .await
    {
        Ok(a) => a,
        Err(e) => return owner_problem(e),
    };
    // Only revoke the authenticated session itself. No arbitrary target, and
    // concurrent revocation cannot grant more authority. UNKNOWN never clears.
    match s
        .read
        .store
        .revoke_session(
            &auth.principal.principal_id,
            &auth.session.session_id,
            Uuid::new_v4(),
            now,
        )
        .await
    {
        Ok(true) => (
            [(
                header::SET_COOKIE,
                "__Host-session=; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=0",
            )],
            Json(serde_json::json!({"revoked":true})),
        )
            .into_response(),
        Ok(false) => problem(StatusCode::UNAUTHORIZED, "session-invalid"),
        Err(e) => owner_problem(e),
    }
}
