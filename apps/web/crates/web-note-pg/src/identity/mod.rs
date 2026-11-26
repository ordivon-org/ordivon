//! Trusted owner persistence, NOT a WebAuthn verifier or session HTTP layer.
mod challenge;
mod credential;
mod dpop;
mod login;
mod principal;
mod rows;
mod session;
use crate::{
    OwnerError,
    owner_audit::AuditRow,
    owner_error::{db, one},
};
pub use rows::{AuthenticatedSession, Credential, Principal, SessionView};
pub use session::{PreparedSession, SessionCreationObservation};
use tokio_postgres::Transaction;
use uuid::Uuid;
pub(super) fn valid_text(s: &str) -> bool {
    !s.is_empty() && !s.contains('\0')
}
pub(super) fn safe(n: i64) -> bool {
    crate::domain::representable("", "", n)
}
pub(super) fn unknown(
    operation: &'static str,
    coordinate: &str,
    source: tokio_postgres::Error,
) -> OwnerError {
    OwnerError::AuthorityCommitUnknown {
        operation,
        coordinate: coordinate.into(),
        source,
    }
}
pub(super) async fn deferred(tx: &Transaction<'_>) -> Result<(), OwnerError> {
    tx.batch_execute("SET CONSTRAINTS ALL IMMEDIATE")
        .await
        .map_err(|e| db("identity deferred fence", e))
}
pub(super) fn audit(
    id: Uuid,
    principal: &str,
    event: &str,
    object: &str,
    target: &str,
    detail: String,
    now: i64,
) -> AuditRow {
    AuditRow {
        event_id: id.to_string(),
        principal_id: Some(principal.into()),
        event_type: event.into(),
        object_type: Some(object.into()),
        object_id: Some(target.into()),
        detail_json: detail,
        created_at: now,
    }
}
pub(super) async fn write_audit(tx: &Transaction<'_>, a: &AuditRow) -> Result<(), OwnerError> {
    one(
        tx.execute(
            "INSERT INTO audit_events VALUES($1,$2,$3,$4,$5,$6,$7)",
            &[
                &a.event_id,
                &a.principal_id,
                &a.event_type,
                &a.object_type,
                &a.object_id,
                &a.detail_json,
                &a.created_at,
            ],
        )
        .await
        .map_err(|e| db("identity audit", e))?,
        "identity audit",
    )
}
pub(super) async fn verify_audit(tx: &Transaction<'_>, a: &AuditRow) -> Result<(), OwnerError> {
    let row = tx
        .query_opt(
            "SELECT * FROM audit_events WHERE event_id=$1",
            &[&a.event_id],
        )
        .await
        .map_err(|e| db("identity audit readback", e))?
        .ok_or(OwnerError::Mismatch("identity audit"))?;
    if AuditRow::read(&row)? != *a {
        return Err(OwnerError::Mismatch("identity audit"));
    }
    Ok(())
}

pub use challenge::{ChallengeObservation, ChallengePurpose, ChallengeRecord, PreparedChallenge};
use sha2::{Digest, Sha256};
pub(super) fn hash_text(token: &str) -> String {
    use std::fmt::Write as _;
    let mut hash = String::with_capacity(64);
    for b in Sha256::digest(token.as_bytes()) {
        write!(&mut hash, "{b:02x}").expect("String write")
    }
    hash
}

pub use login::LoginObservation;

pub(super) async fn verify_unique_audit(
    tx: &Transaction<'_>,
    a: &AuditRow,
) -> Result<(), OwnerError> {
    let rows=tx.query("SELECT * FROM audit_events WHERE event_id=$1 OR (event_type=$2 AND object_type=$3 AND object_id=$4) LIMIT 2",&[&a.event_id,&a.event_type,&a.object_type,&a.object_id]).await.map_err(|e|db("unique identity audit",e))?;
    if rows.len() != 1 || AuditRow::read(&rows[0])? != *a {
        return Err(OwnerError::Mismatch("identity audit"));
    }
    Ok(())
}
