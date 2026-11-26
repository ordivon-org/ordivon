//! Candidate Agent rail: actual Security verification, OPA decision, native
//! replay and owner commit. No browser session authority or production ingress.
mod admission;
mod auth;
mod routes;
use super::{boundary, carrier::JsonCarrier, response_boundary};
use crate::{OwnerError, PgNoteStore};
use axum::{Router, extract::DefaultBodyLimit, middleware, routing::post};
use std::{path::Path, sync::Arc, time::Duration};
#[derive(Clone)]
pub struct AgentState {
    store: Arc<PgNoteStore>,
    verifier: JsonCarrier,
    admission: JsonCarrier,
    origin: Arc<str>,
    issuer: Arc<str>,
    allow_insecure: bool,
    clock: Arc<dyn Fn() -> i64 + Send + Sync>,
}
/// Trusted installation configuration. Insecure issuer explicitly limited to
/// loopback for disposable integration fixtures; never selected by requests.
pub struct AgentConfig<'a> {
    pub origin: &'a str,
    pub issuer: &'a str,
    pub allow_loopback_http: bool,
    pub node: &'a Path,
    pub verifier_script: &'a Path,
    pub python: &'a Path,
    pub admission_script: &'a Path,
    pub opa_dir: &'a Path,
    pub max_parallel: usize,
    pub deadline: Duration,
}
impl AgentState {
    pub fn new(
        store: PgNoteStore,
        c: AgentConfig<'_>,
        clock: impl Fn() -> i64 + Send + Sync + 'static,
    ) -> Result<Self, OwnerError> {
        let uri = c
            .issuer
            .parse::<axum::http::Uri>()
            .map_err(|_| OwnerError::Invalid)?;
        let auth = uri.authority().ok_or(OwnerError::Invalid)?;
        let insecure = uri.scheme_str() == Some("http")
            && c.allow_loopback_http
            && matches!(auth.host(), "127.0.0.1" | "[::1]");
        if !boundary::valid_origin(c.origin)
            || !(uri.scheme_str() == Some("https") || insecure)
            || auth.as_str().contains('@')
            || uri.query().is_some()
            || !c.opa_dir.join("opa").is_file()
        {
            return Err(OwnerError::Invalid);
        }
        let verifier = JsonCarrier::new(c.node, c.verifier_script, c.max_parallel, c.deadline)
            .map_err(|_| OwnerError::Invalid)?;
        let admission = JsonCarrier::new(c.python, c.admission_script, c.max_parallel, c.deadline)
            .and_then(|x| x.with_path(c.opa_dir))
            .map_err(|_| OwnerError::Invalid)?;
        Ok(Self {
            store: Arc::new(store),
            verifier,
            admission,
            origin: c.origin.into(),
            issuer: c.issuer.into(),
            allow_insecure: insecure,
            clock: Arc::new(clock),
        })
    }
}
pub fn agent_router(s: AgentState) -> Router {
    Router::new()
        .route("/api/agent/canary/notes", post(routes::create))
        .route(
            "/api/agent/canary/notes/{note_id}/publish",
            post(routes::publish),
        )
        .layer(DefaultBodyLimit::max(16384))
        .layer(middleware::from_fn(response_boundary))
        .with_state(s)
}
