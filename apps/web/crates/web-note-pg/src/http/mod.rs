//! Candidate browser HTTP consumers. Read and login routers are separate.
//! TLS, ingress/rate limiting and verifier integration remain deployment gates.
mod agent;
pub use agent::{AgentConfig, AgentState, agent_router};
mod boundary;
mod carrier;
mod login;
mod session_write;
pub use login::{LocalVerifier, LoginState, login_router};
pub use session_write::{SessionWriteState, session_write_router};
mod views;
use crate::{OwnerError, PgNoteStore};
use axum::{
    Json, Router,
    extract::{Request, State},
    http::{HeaderValue, StatusCode, header},
    middleware::{self, Next},
    response::{IntoResponse, Response},
    routing::get,
};
use std::sync::Arc;

#[derive(Clone)]
pub struct ReadState {
    store: Arc<PgNoteStore>,
    idle_seconds: i64,
    clock: Arc<dyn Fn() -> i64 + Send + Sync>,
}
impl ReadState {
    pub fn new(
        store: PgNoteStore,
        idle_seconds: i64,
        clock: impl Fn() -> i64 + Send + Sync + 'static,
    ) -> Result<Self, OwnerError> {
        if idle_seconds <= 0 {
            return Err(OwnerError::Invalid);
        }
        Ok(Self {
            store: Arc::new(store),
            idle_seconds,
            clock: Arc::new(clock),
        })
    }
}
/// Mount only behind an explicit opt-in candidate ingress. No fallback.
pub fn read_router(state: ReadState) -> Router {
    Router::new()
        .route("/api/me", get(views::me))
        .route("/api/security/sessions", get(views::sessions))
        .route("/api/security/passkeys", get(views::passkeys))
        .route("/api/security/agents/grants", get(views::grants))
        .route_layer(middleware::from_fn_with_state(state.clone(), authenticate))
        .layer(middleware::from_fn(response_boundary))
        .with_state(state)
}
async fn authenticate(State(s): State<ReadState>, mut req: Request, next: Next) -> Response {
    // GET-only: Axum's automatic HEAD handling must not touch session state.
    if req.method() != axum::http::Method::GET {
        return problem(StatusCode::METHOD_NOT_ALLOWED, "method-not-allowed");
    }
    let token = match boundary::session_token(req.headers()) {
        Ok(t) => t,
        Err((status, code)) => return problem(status, code),
    };
    match s
        .store
        .authenticate_session(token, (s.clock)(), s.idle_seconds)
        .await
    {
        Ok(auth) => {
            req.extensions_mut().insert(auth);
            next.run(req).await
        }
        Err(e) => owner_problem(e),
    }
}
async fn response_boundary(req: Request, next: Next) -> Response {
    let mut response = next.run(req).await;
    let h = response.headers_mut();
    h.insert(header::CACHE_CONTROL, HeaderValue::from_static("no-store"));
    h.insert(header::VARY, HeaderValue::from_static("Cookie"));
    h.insert(
        header::CONTENT_SECURITY_POLICY,
        HeaderValue::from_static("default-src 'none'; frame-ancestors 'none'; base-uri 'none'"),
    );
    h.insert(
        header::X_CONTENT_TYPE_OPTIONS,
        HeaderValue::from_static("nosniff"),
    );
    h.insert(
        header::REFERRER_POLICY,
        HeaderValue::from_static("no-referrer"),
    );
    response
}
fn problem(status: StatusCode, code: &'static str) -> Response {
    (status,[(header::CONTENT_TYPE,"application/problem+json")],Json(serde_json::json!({"status":status.as_u16(),"code":code,"title":status.canonical_reason().unwrap_or("Request rejected")}))).into_response()
}
fn owner_problem(e: OwnerError) -> Response {
    // Do not leak SQL errors, token hashes, conflict coordinates or carrier details.
    match e {
        OwnerError::SessionInvalid | OwnerError::PrincipalNotFound => {
            problem(StatusCode::UNAUTHORIZED, "session-invalid")
        }
        OwnerError::Busy
        | OwnerError::Pool(_)
        | OwnerError::SessionStale
        | OwnerError::AuthorityCommitUnknown { .. }
        | OwnerError::RollbackUnknown { .. } => {
            problem(StatusCode::SERVICE_UNAVAILABLE, "owner-unavailable")
        }
        _ => problem(StatusCode::INTERNAL_SERVER_ERROR, "owner-integrity-failure"),
    }
}
