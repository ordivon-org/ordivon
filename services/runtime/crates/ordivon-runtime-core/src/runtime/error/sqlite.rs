//! Legacy SQLite-only Registry error translation.
use super::*;
use rusqlite::{Error as SqlError, ErrorCode as SqlErrorCode};

impl RuntimeError {
    pub(crate) fn from_sql(error: SqlError, context: &str) -> Self {
        let (code, retryable) = match &error {
            SqlError::SqliteFailure(failure, _) => match failure.code {
                SqlErrorCode::DatabaseBusy | SqlErrorCode::DatabaseLocked => {
                    (RuntimeErrorCode::RegistryBusy, true)
                }
                SqlErrorCode::DatabaseCorrupt | SqlErrorCode::NotADatabase => {
                    (RuntimeErrorCode::RegistryCorrupt, false)
                }
                _ => (RuntimeErrorCode::RegistryUnavailable, false),
            },
            _ => (RuntimeErrorCode::RegistryUnavailable, false),
        };
        Self::new(code, format!("{context}: {error}"), None, retryable)
    }
}
