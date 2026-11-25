//! Operator-owned fixture credentials. No grants, issuer or production secret store.
//! The containing directory must be trusted by the operator. POSIX-only refinement.

use std::path::Path;

const MAX_BYTES: u64 = 16_384;

// No Debug or Display of token/path/OS error. The caller projects only a fixed reason.
pub fn read_fixture_bearer(path: &Path) -> Result<String, ()> {
    #[cfg(unix)]
    {
        use std::{
            fs::OpenOptions,
            io::Read,
            os::unix::fs::{MetadataExt, OpenOptionsExt},
        };
        if !path.is_absolute() {
            return Err(());
        }
        let mut file = OpenOptions::new()
            .read(true)
            .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK | libc::O_CLOEXEC)
            .open(path)
            .map_err(|_| ())?;
        let before = file.metadata().map_err(|_| ())?;
        if !before.is_file() || before.mode() & 0o077 != 0 || before.len() > MAX_BYTES {
            return Err(());
        }
        let mut bytes = Vec::new();
        (&mut file)
            .take(MAX_BYTES + 1)
            .read_to_end(&mut bytes)
            .map_err(|_| ())?;
        let after = file.metadata().map_err(|_| ())?;
        let identity = |m: &std::fs::Metadata| {
            (
                m.dev(),
                m.ino(),
                m.mode(),
                m.len(),
                m.mtime(),
                m.mtime_nsec(),
                m.ctime(),
                m.ctime_nsec(),
            )
        };
        if bytes.len() as u64 > MAX_BYTES || identity(&before) != identity(&after) {
            return Err(());
        }
        // RFC6750 b64token: ASCII alnum or -._~+/ with optional trailing '='.
        let raw = std::str::from_utf8(&bytes).map_err(|_| ())?;
        let token = raw.trim_matches(|c: char| c.is_ascii_whitespace());
        let core = token.trim_end_matches('=');
        if core.is_empty()
            || !core
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b"-._~+/".contains(&b))
        {
            return Err(());
        }
        Ok(token.to_owned())
    }
    #[cfg(not(unix))]
    {
        let _ = path;
        Err(())
    }
}
