//! Shared exact audit row projection; no authorization authority.
use crate::{OwnerError, owner_error::db};
use tokio_postgres::Row;
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct AuditRow {
    pub event_id: String,
    pub principal_id: Option<String>,
    pub event_type: String,
    pub object_type: Option<String>,
    pub object_id: Option<String>,
    pub detail_json: String,
    pub created_at: i64,
}
impl AuditRow {
    pub(crate) fn read(r: &Row) -> Result<Self, OwnerError> {
        macro_rules! f {
            ($field:literal) => {
                r.try_get($field)
                    .map_err(|e| db("audit row projection", e))?
            };
        }
        Ok(Self {
            event_id: f!("event_id"),
            principal_id: f!("principal_id"),
            event_type: f!("event_type"),
            object_type: f!("object_type"),
            object_id: f!("object_id"),
            detail_json: f!("detail_json"),
            created_at: f!("created_at"),
        })
    }
}
