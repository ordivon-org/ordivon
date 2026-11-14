#[cfg(unix)]
use std::fs::{self, File};
use std::io;
#[cfg(unix)]
use std::io::Read;
use std::path::Path;
use std::sync::Arc;

use axum::extract::{Request, State};
use axum::http::{header, HeaderValue, StatusCode};
use axum::middleware::Next;
use axum::response::{IntoResponse, Response};
use hmac::{Hmac, KeyInit, Mac};
use sha2::Sha256;

/// Authenticates one service-to-service Owner caller. It does NOT authenticate an ActorRef.
#[derive(Clone)]
pub struct OwnerBearer {
    token: Arc<str>,
}

fn denied(reason: &'static str) -> io::Error {
    io::Error::new(io::ErrorKind::PermissionDenied, reason)
}

impl OwnerBearer {
    #[cfg(unix)]
    pub fn read_file(path: &Path) -> io::Result<Self> {
        if !path.is_absolute() {
            return Err(denied(
                "Host HTTP Owner credential requires an absolute path",
            ));
        }
        let lstat = fs::symlink_metadata(path)?;
        if !lstat.file_type().is_file() || lstat.len() > 16_384 {
            return Err(denied(
                "Host HTTP Owner credential must be a bounded regular file",
            ));
        }
        let file = File::open(path)?;
        let meta = file.metadata()?;
        if !meta.file_type().is_file() || meta.len() > 16_384 {
            return Err(denied("Host HTTP Owner credential file identity changed"));
        }
        #[cfg(unix)]
        {
            use std::os::unix::fs::{MetadataExt, PermissionsExt};
            if (lstat.dev(), lstat.ino()) != (meta.dev(), meta.ino()) {
                return Err(denied(
                    "Host HTTP Owner credential path changed during open",
                ));
            }
            let mode = meta.permissions().mode() & 0o777;
            let systemd_credential = std::env::var_os("CREDENTIALS_DIRECTORY")
                .map(|path_text| {
                    let directory = Path::new(&path_text);
                    directory.is_absolute()
                        && path.parent() == Some(directory)
                        && fs::symlink_metadata(directory)
                            .is_ok_and(|meta| meta.file_type().is_dir())
                })
                .unwrap_or(false);
            if (systemd_credential && mode & 0o037 != 0)
                || (!systemd_credential && mode & 0o077 != 0)
            {
                return Err(denied(
                    "Host HTTP Owner credential file permissions too broad",
                ));
            }
        }
        let mut bytes = Vec::new();
        file.take(16_385).read_to_end(&mut bytes)?;
        if bytes.len() > 16_384 {
            return Err(denied("Host HTTP Owner credential exceeds bounded size"));
        }
        let text = String::from_utf8(bytes)
            .map_err(|_| denied("Host HTTP Owner credential must be UTF-8"))?;
        let token = text.trim();
        if token.len() < 32 || token.chars().any(|c| c.is_control() || c.is_whitespace()) {
            return Err(denied("Host HTTP Owner credential has invalid format"));
        }
        Ok(Self {
            token: Arc::from(token),
        })
    }

    #[cfg(not(unix))]
    pub fn read_file(_path: &Path) -> io::Result<Self> {
        // Never treat POSIX file modes as Windows ACL validation.
        Err(denied(
            "Owner credential reader needs Windows ACL verification",
        ))
    }

    fn matches(&self, candidate: Option<&str>) -> bool {
        let Some(candidate) = candidate else {
            return false;
        };
        if candidate.is_empty() || candidate.len() > 16_384 {
            return false;
        }
        type MacSha256 = Hmac<Sha256>;
        const CONTEXT: &[u8] = b"ordivon.host.http-owner-service-auth.v1";
        let mut expected = MacSha256::new_from_slice(self.token.as_bytes()).unwrap();
        expected.update(CONTEXT);
        let mut actual = MacSha256::new_from_slice(candidate.as_bytes()).unwrap();
        actual.update(CONTEXT);
        expected
            .verify_slice(actual.finalize().into_bytes().as_ref())
            .is_ok()
    }
}

pub async fn require_owner_bearer(
    State(owner): State<Arc<OwnerBearer>>,
    request: Request,
    next: Next,
) -> Response {
    let supplied = request
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|header| header.to_str().ok())
        .and_then(|value| value.strip_prefix("Bearer "));
    if !owner.matches(supplied) {
        let mut denied = StatusCode::UNAUTHORIZED.into_response();
        denied
            .headers_mut()
            .insert(header::WWW_AUTHENTICATE, HeaderValue::from_static("Bearer"));
        return denied;
    }
    next.run(request).await
}

#[cfg(all(test, unix))]
mod tests {
    use super::*;
    use std::io::Write;
    use std::os::unix::fs::PermissionsExt;

    #[test]
    fn bearer_authenticates_owner_not_work_actor_and_denies_public_secret() {
        // A generated fixture must exercise the *real* credential reader.
        // Never embed a reusable cryptographic secret in tracked test source.
        let mut secret_bytes = [0u8; 32];
        getrandom::fill(&mut secret_bytes).expect("OS random source for test credentials");
        let token = hex::encode(secret_bytes);
        let mut path_nonce = [0u8; 16];
        getrandom::fill(&mut path_nonce).expect("OS random source for test path");
        let path = std::env::temp_dir().join(format!(
            "host-owner-test-{}-{:?}-{}",
            std::process::id(),
            std::thread::current().id(),
            hex::encode(path_nonce),
        ));
        let mut f = fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&path)
            .unwrap();
        f.set_permissions(fs::Permissions::from_mode(0o600))
            .unwrap();
        f.write_all(token.as_bytes()).unwrap();
        f.write_all(b"\n").unwrap();
        f.sync_all().unwrap();
        drop(f);
        let auth = OwnerBearer::read_file(&path).unwrap();
        assert!(auth.matches(Some(&token)));
        assert!(!auth.matches(None));
        let mut wrong_bytes = token.as_bytes().to_vec();
        wrong_bytes[0] = if wrong_bytes[0] == b'0' { b'1' } else { b'0' };
        let wrong_token = String::from_utf8(wrong_bytes).unwrap();
        assert!(!auth.matches(Some(&wrong_token)));
        fs::set_permissions(&path, fs::Permissions::from_mode(0o644)).unwrap();
        assert!(OwnerBearer::read_file(&path).is_err());
        fs::set_permissions(&path, fs::Permissions::from_mode(0o600)).unwrap();
        let symlink = path.with_extension("link");
        let _ = fs::remove_file(&symlink);
        std::os::unix::fs::symlink(&path, &symlink).unwrap();
        assert!(OwnerBearer::read_file(&symlink).is_err());
        fs::remove_file(&symlink).unwrap();
        fs::remove_file(&path).unwrap();
    }
}
