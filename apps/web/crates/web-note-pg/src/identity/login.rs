//! Verified login persistence composition. Challenge is deliberately consumed
//! before the external verifier; only a trusted verified assertion may call
//! completion. Counter + session + two audits commit together.
use super::{
    ChallengeRecord, Credential, PreparedSession, SessionCreationObservation, SessionView,
    challenge::verify_consumed_login, credential, deferred, principal::lock_principal, safe,
    session, unknown, verify_unique_audit, write_audit,
};
use crate::{
    OwnerError, PgNoteStore,
    owner_audit::AuditRow,
    owner_error::{db, one},
};
use serde::Serialize;
use tokio_postgres::{IsolationLevel, Transaction};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LoginObservation {
    Exact(Box<SessionView>),
    Unobserved,
    Mismatch,
}
fn completion_audit(
    challenge: &ChallengeRecord,
    consumed: i64,
    prior: &Credential,
    new_counter: i64,
    session: &PreparedSession,
) -> Result<AuditRow, OwnerError> {
    let r = &session.row;
    if challenge.principal_id != prior.principal_id
        || r.principal_id != prior.principal_id
        || r.created_at < consumed
        || r.created_at >= challenge.expires_at
        || !safe(consumed)
        || !(0..=i64::from(u32::MAX)).contains(&new_counter)
    {
        return Err(OwnerError::ChallengeInvalid);
    }
    #[derive(Serialize)]
    #[serde(rename_all = "camelCase")]
    struct Detail<'a> {
        session_id: &'a str,
        credential_id: &'a str,
        challenge_payload_digest: &'a str,
        consumed_at: i64,
        prior_counter: i64,
        prior_last_used_at: i64,
        new_counter: i64,
    }
    let detail = Detail {
        session_id: &r.session_id,
        credential_id: &prior.credential_id,
        challenge_payload_digest: &challenge.payload_digest,
        consumed_at: consumed,
        prior_counter: prior.counter,
        prior_last_used_at: prior.last_used_at,
        new_counter,
    };
    Ok(AuditRow {
        event_id: format!("web-login:{}", challenge.challenge_id),
        principal_id: Some(prior.principal_id.clone()),
        event_type: "session.login-completed".into(),
        object_type: Some("webauthn-challenge".into()),
        object_id: Some(challenge.challenge_id.clone()),
        detail_json: serde_json::to_string(&detail).map_err(|_| OwnerError::Invalid)?,
        created_at: r.created_at,
    })
}
impl PgNoteStore {
    /// Trusted verifier has accepted this exact consumed challenge and
    /// credential pre-state. No raw WebAuthn assertion is verified here.
    pub async fn complete_verified_login(
        &self,
        challenge: &ChallengeRecord,
        consumed: i64,
        prior: &Credential,
        new_counter: i64,
        prepared: &PreparedSession,
    ) -> Result<SessionView, OwnerError> {
        let a = completion_audit(challenge, consumed, prior, new_counter, prepared)?;
        self.owner_write(
            |e| unknown("login-complete", &a.event_id, e),
            async |tx| {
                lock_principal(tx, &prior.principal_id, false)
                    .await?
                    .view()?;
                verify_consumed_login(tx, challenge, consumed, true).await?;
                match marker(tx,&challenge.challenge_id,true).await?{
                    Some((None,None))=>{},
                    Some((Some(_),Some(_)))=>return Err(OwnerError::LoginCompleted),
                    _=>return Err(OwnerError::ChallengeInvalid),
                }
                let expected =
                    credential::advance_in_tx(tx, prior, new_counter, prepared.row.created_at)
                        .await?;
                session::issue_in_tx(tx, prepared).await?;
                one(tx.execute("UPDATE webauthn_login_completions SET session_id=$2,completed_at=$3 WHERE challenge_id=$1 AND session_id IS NULL",&[&challenge.challenge_id,&prepared.row.session_id,&prepared.row.created_at]).await.map_err(|e|db("login complete marker",e))?,"login completion marker")?;
                write_audit(tx, &a).await?;
                deferred(tx).await?;
                if marker(tx,&challenge.challenge_id,false).await?!=Some((Some(prepared.row.session_id.clone()),Some(prepared.row.created_at))){return Err(OwnerError::Mismatch("login completion marker"))}
                verify_consumed_login(tx, challenge, consumed, false).await?;
                if credential::read(tx, &prior.credential_id).await? != expected {
                    return Err(OwnerError::Mismatch("login credential"));
                }
                session::verify_row(tx, &prepared.row).await?;
                verify_unique_audit(tx, &prepared.audit).await?;
                verify_unique_audit(tx, &a).await?;
                prepared.row.view()
            },
        )
        .await
    }
    /// Historical completion audit plus exact session issuance evidence.
    /// Current credential state may have advanced; this is NOT authentication.
    pub async fn observe_verified_login(
        &self,
        challenge: &ChallengeRecord,
        consumed: i64,
        prior: &Credential,
        new_counter: i64,
        prepared: &PreparedSession,
    ) -> Result<LoginObservation, OwnerError> {
        let expected = completion_audit(challenge, consumed, prior, new_counter, prepared)?;
        let mut lease = self.connect().await.map_err(OwnerError::Pool)?;
        let tx = lease
            .client()
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()
            .await
            .map_err(|e| db("login observe begin", e))?;
        let row = tx
            .query_opt(
                "SELECT * FROM audit_events WHERE event_id=$1",
                &[&expected.event_id],
            )
            .await
            .map_err(|e| db("login observe audit", e))?
            .as_ref()
            .map(AuditRow::read)
            .transpose()?;
        let state = marker(&tx, &challenge.challenge_id, false).await?;
        let result = match (row, state) {
            (None, None | Some((None, None))) => LoginObservation::Unobserved,
            (Some(a), Some((Some(id), Some(at))))
                if a == expected
                    && id == prepared.row.session_id
                    && at == prepared.row.created_at =>
            {
                match session::observe_creation_in_tx(&tx, prepared).await? {
                    SessionCreationObservation::Exact(v) => LoginObservation::Exact(v),
                    _ => LoginObservation::Mismatch,
                }
            }
            _ => LoginObservation::Mismatch,
        };
        tx.rollback()
            .await
            .map_err(|e| db("login observe end", e))?;
        lease.reusable();
        Ok(result)
    }
}

pub(super) async fn marker(
    tx: &Transaction<'_>,
    id: &str,
    lock: bool,
) -> Result<Option<(Option<String>, Option<i64>)>, OwnerError> {
    let sql = if lock {
        "SELECT session_id,completed_at FROM webauthn_login_completions WHERE challenge_id=$1 FOR UPDATE NOWAIT"
    } else {
        "SELECT session_id,completed_at FROM webauthn_login_completions WHERE challenge_id=$1"
    };
    let row = tx
        .query_opt(sql, &[&id])
        .await
        .map_err(|e| db("login marker", e))?;
    Ok(row.map(|r| (r.get(0), r.get(1))))
}
