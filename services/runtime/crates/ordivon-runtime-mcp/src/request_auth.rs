//! HTTP authentication and principal mapping, isolated from Runtime business routing.
//!
//! The transport supplies verified identity; this module maps it to a principal.
//! No Job/Attempt, Workspace, Artifact, or release effect is implemented here.

use super::access_auth::CloudflareAccessVerifier;
use axum::http::{header, HeaderMap};
use sha2::{Digest, Sha256};
use std::sync::Arc;

#[derive(Clone)]
pub(super) struct HttpAuthConfig {
    pub(super) bearer: Arc<str>,
    pub(super) remote_bearer: Option<Arc<str>>,
    pub(super) principal_mode: PrincipalMode,
    pub(super) local_principal: Arc<str>,
    pub(super) remote_principal: Option<Arc<str>>,
    pub(super) cf_access: Option<Arc<CloudflareAccessVerifier>>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) enum PrincipalMode {
    Static,
    Factorized,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(super) struct AuthenticatedRequest {
    pub(super) source: AuthSource,
    pub(super) principal: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) enum AuthSource {
    None,
    LocalBearer,
    RemoteBearer,
    CloudflareAccess,
}

impl AuthSource {
    pub(super) fn as_str(self) -> &'static str {
        match self {
            Self::None => "none",
            Self::LocalBearer => "local_bearer",
            Self::RemoteBearer => "remote_bearer",
            Self::CloudflareAccess => "cloudflare_access",
        }
    }
}

pub(super) async fn authenticate_request(
    headers: &HeaderMap,
    state: &HttpAuthConfig,
) -> Option<AuthenticatedRequest> {
    let supplied = headers
        .get(header::AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
        .unwrap_or_default();
    if constant_time_eq(supplied.as_bytes(), state.bearer.as_bytes()) {
        return Some(AuthenticatedRequest {
            source: AuthSource::LocalBearer,
            principal: state.local_principal.to_string(),
        });
    }
    if state
        .remote_bearer
        .as_deref()
        .is_some_and(|remote| constant_time_eq(supplied.as_bytes(), remote.as_bytes()))
    {
        let principal = match state.principal_mode {
            PrincipalMode::Static => state.local_principal.to_string(),
            PrincipalMode::Factorized => state.remote_principal.as_deref()?.to_string(),
        };
        return Some(AuthenticatedRequest {
            source: AuthSource::RemoteBearer,
            principal,
        });
    }
    let verifier = state.cf_access.as_deref()?;
    let assertion = headers
        .get("cf-access-jwt-assertion")
        .and_then(|value| value.to_str().ok())?;
    let identity = verifier.verify_identity(assertion).await?;
    let principal = match state.principal_mode {
        PrincipalMode::Static => state.local_principal.to_string(),
        PrincipalMode::Factorized => {
            let subject = identity.subject.as_deref()?;
            cloudflare_access_principal(&identity.issuer, subject)
        }
    };
    Some(AuthenticatedRequest {
        source: AuthSource::CloudflareAccess,
        principal,
    })
}

pub(super) fn cloudflare_access_principal(issuer: &str, subject: &str) -> String {
    let mut digest = Sha256::new();
    digest.update(b"ordivon-runtime-cf-access-principal-v1\0");
    digest.update(issuer.as_bytes());
    digest.update(b"\0");
    digest.update(subject.as_bytes());
    format!("principal:cf-access:{}", hex::encode(digest.finalize()))
}

pub(super) fn constant_time_eq(left: &[u8], right: &[u8]) -> bool {
    if left.len() != right.len() {
        return false;
    }
    let mut difference = 0_u8;
    for (left, right) in left.iter().zip(right.iter()) {
        difference |= left ^ right;
    }
    difference == 0
}
