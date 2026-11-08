//! Reuse the production Access verifier at the PG transport boundary.
//! PG retains its configured static operator principal; credentials never enter SQL.
use crate::access_auth::{CloudflareAccessConfig, CloudflareAccessVerifier};
use axum::http::{header, HeaderMap};
use std::{fs, os::unix::fs::PermissionsExt, path::Path, sync::Arc};

#[derive(Clone)]
pub(crate) struct PgAuth {
    local: Arc<str>,
    remote: Option<Arc<str>>,
    access: Option<Arc<CloudflareAccessVerifier>>,
}

pub(crate) fn optional_env(key: &str) -> Result<Option<String>, Box<dyn std::error::Error>> {
    match std::env::var(key) {
        Ok(value) if !value.trim().is_empty() => Ok(Some(value)),
        Ok(_) => Err(format!("{key} must not be empty").into()),
        Err(std::env::VarError::NotPresent) => Ok(None),
        Err(error) => Err(error.into()),
    }
}

fn read_remote_token(path: &Path) -> Result<String, Box<dyn std::error::Error>> {
    let meta = fs::symlink_metadata(path)?;
    if !path.is_absolute()
        || !meta.file_type().is_file()
        || meta.permissions().mode() & 0o077 != 0
        || meta.len() > 16_384
    {
        return Err(
            "remote Bearer requires an absolute private regular file (max 16384 bytes)".into(),
        );
    }
    let raw = fs::read_to_string(path)?;
    let token = raw.trim();
    if token.len() < 32 || token.chars().any(char::is_whitespace) {
        return Err("remote Bearer requires one token of at least 32 characters".into());
    }
    Ok(token.to_string())
}

impl PgAuth {
    pub(crate) fn from_env(local: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let remote = optional_env("ORDIVON_REMOTE_BEARER_TOKEN_FILE")?
            .map(|path| read_remote_token(Path::new(&path)))
            .transpose()?;
        let enabled = match optional_env("ORDIVON_TRUST_CF_ACCESS")?.as_deref() {
            None | Some("false" | "0" | "no") => false,
            Some("true" | "1" | "yes") => true,
            _ => return Err("ORDIVON_TRUST_CF_ACCESS must be true or false".into()),
        };
        let access = if enabled {
            let required = |key: &str| -> Result<String, Box<dyn std::error::Error>> {
                optional_env(key)?.ok_or_else(|| format!("{key} required").into())
            };
            let issuer: String = required("ORDIVON_CF_ACCESS_ISSUER")?;
            let issuer = issuer.trim_end_matches('/').to_string();
            Some(CloudflareAccessConfig {
                jwks_url: optional_env("ORDIVON_CF_ACCESS_JWKS_URL")?
                    .unwrap_or_else(|| format!("{issuer}/cdn-cgi/access/certs")),
                issuer,
                audience: required("ORDIVON_CF_ACCESS_AUDIENCE")?,
            })
        } else {
            None
        };
        Self::new(local, remote.as_deref(), access)
    }

    fn new(
        local: &str,
        remote: Option<&str>,
        access: Option<CloudflareAccessConfig>,
    ) -> Result<Self, Box<dyn std::error::Error>> {
        if remote.is_some_and(|value| constant_time_eq(value.as_bytes(), local.as_bytes())) {
            return Err("remote Bearer must differ from the trusted-local Bearer".into());
        }
        Ok(Self {
            local: Arc::from(format!("Bearer {local}")),
            remote: remote.map(|value| Arc::from(format!("Bearer {value}"))),
            access: access
                .map(CloudflareAccessVerifier::new)
                .transpose()?
                .map(Arc::new),
        })
    }

    pub(crate) async fn authorized(&self, headers: &HeaderMap) -> bool {
        let supplied = headers
            .get(header::AUTHORIZATION)
            .and_then(|value| value.to_str().ok())
            .unwrap_or_default();
        if constant_time_eq(supplied.as_bytes(), self.local.as_bytes())
            || self
                .remote
                .as_deref()
                .is_some_and(|remote| constant_time_eq(supplied.as_bytes(), remote.as_bytes()))
        {
            return true;
        }
        match (
            self.access.as_deref(),
            headers
                .get("cf-access-jwt-assertion")
                .and_then(|value| value.to_str().ok()),
        ) {
            (Some(verifier), Some(token)) => verifier.verify_identity(token).await.is_some(),
            _ => false,
        }
    }
}

fn constant_time_eq(left: &[u8], right: &[u8]) -> bool {
    if left.len() != right.len() {
        return false;
    }
    left.iter()
        .zip(right)
        .fold(0_u8, |difference, (a, b)| difference | (a ^ b))
        == 0
}

#[cfg(test)]
mod tests {
    use super::*;
    #[tokio::test]
    async fn separate_bearers_work_without_access_network_and_invalid_headers_fail_closed() {
        let auth = PgAuth::new(
            &"l".repeat(32),
            Some(&"r".repeat(32)),
            Some(CloudflareAccessConfig {
                issuer: "https://example.cloudflareaccess.com".into(),
                audience: "test-audience".into(),
                jwks_url: "https://example.cloudflareaccess.com/cdn-cgi/access/certs".into(),
            }),
        )
        .unwrap();
        for (value, expected) in [
            (format!("Bearer {}", "l".repeat(32)), true),
            (format!("Bearer {}", "r".repeat(32)), true),
            (format!("Bearer {}", "x".repeat(32)), false),
        ] {
            let mut headers = HeaderMap::new();
            headers.insert(header::AUTHORIZATION, value.parse().unwrap());
            assert_eq!(auth.authorized(&headers).await, expected);
        }
        let mut headers = HeaderMap::new();
        assert!(!auth.authorized(&headers).await);
        headers.insert(
            "cf-access-jwt-assertion",
            "forged.header.signature".parse().unwrap(),
        );
        assert!(!auth.authorized(&headers).await);
    }
    #[test]
    fn shared_local_and_remote_secret_is_rejected() {
        assert!(PgAuth::new(&"l".repeat(32), Some(&"l".repeat(32)), None).is_err());
    }
    #[test]
    fn remote_token_file_must_be_private_and_not_a_symlink() {
        let path = std::env::temp_dir().join(format!("pg-auth-{}", uuid::Uuid::now_v7()));
        fs::write(&path, "r".repeat(32)).unwrap();
        fs::set_permissions(&path, fs::Permissions::from_mode(0o600)).unwrap();
        assert_eq!(read_remote_token(&path).unwrap(), "r".repeat(32));
        let link = path.with_extension("link");
        std::os::unix::fs::symlink(&path, &link).unwrap();
        assert!(read_remote_token(&link).is_err());
        fs::remove_file(link).unwrap();
        fs::set_permissions(&path, fs::Permissions::from_mode(0o644)).unwrap();
        assert!(read_remote_token(&path).is_err());
        fs::remove_file(&path).unwrap();
    }
}
