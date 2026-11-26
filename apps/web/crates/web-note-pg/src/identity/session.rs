//! Opaque token issuance, sliding idle expiry and cooperative revocation.
//! The trusted caller must have authenticated the user before issuance.
use super::{
    AuthenticatedSession, SessionView, audit, deferred, principal::lock_principal,
    rows::SessionRow, safe, unknown, valid_text, verify_audit, verify_unique_audit, write_audit,
};
use crate::{
    OwnerError, PgNoteStore,
    owner_audit::AuditRow,
    owner_error::{db, one},
};
use base64::{Engine, engine::general_purpose::URL_SAFE_NO_PAD};
use tokio_postgres::{IsolationLevel, Transaction};
use uuid::Uuid;

fn deadline(now: i64, ttl: i64) -> Result<i64, OwnerError> {
    if ttl <= 0 || !safe(now) {
        return Err(OwnerError::Invalid);
    }
    now.checked_add(ttl)
        .filter(|n| safe(*n))
        .ok_or(OwnerError::Invalid)
}
// No Debug or serialization of raw bearer secrets.
pub struct PreparedSession {
    token: String,
    pub(super) row: SessionRow,
    pub(super) audit: AuditRow,
}
impl PreparedSession {
    pub fn new(
        principal: &str,
        now: i64,
        idle: i64,
        absolute: i64,
        user_agent: Option<String>,
    ) -> Result<Self, OwnerError> {
        if !valid_text(principal) || user_agent.as_ref().is_some_and(|a| a.contains('\0')) {
            return Err(OwnerError::Invalid);
        }
        let idle_expires_at = deadline(now, idle)?;
        let absolute_expires_at = deadline(now, absolute)?;
        let mut bytes = [0u8; 32];
        getrandom::fill(&mut bytes).map_err(|_| OwnerError::Entropy)?;
        let token = URL_SAFE_NO_PAD.encode(bytes);
        let session_id = Uuid::new_v4().to_string();
        let row = SessionRow {
            session_id: session_id.clone(),
            token_hash: super::hash_text(&token),
            principal_id: principal.into(),
            created_at: now,
            authenticated_at: now,
            last_seen_at: now,
            idle_expires_at,
            absolute_expires_at,
            revoked_at: None,
            authn_method: "webauthn".into(),
            user_agent,
        };
        let audit = audit(
            Uuid::new_v4(),
            principal,
            "session.created",
            "session",
            &session_id,
            r#"{"authnMethod":"webauthn"}"#.into(),
            now,
        );
        Ok(Self { token, row, audit })
    }
    /// Trusted caller retains secret before await; release only on known success.
    pub fn token(&self) -> &str {
        &self.token
    }
    pub fn session_id(&self) -> &str {
        &self.row.session_id
    }
    pub fn audit_id(&self) -> &str {
        &self.audit.event_id
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SessionCreationObservation {
    Exact(Box<SessionView>),
    Unobserved,
    Mismatch,
}
pub(super) async fn row(
    tx: &Transaction<'_>,
    id: &str,
    lock: bool,
) -> Result<Option<SessionRow>, OwnerError> {
    let sql = if lock {
        "SELECT * FROM sessions WHERE session_id=$1 FOR UPDATE NOWAIT"
    } else {
        "SELECT * FROM sessions WHERE session_id=$1"
    };
    tx.query_opt(sql, &[&id])
        .await
        .map_err(|e| db("session row", e))?
        .as_ref()
        .map(SessionRow::read)
        .transpose()
}
async fn rows(tx: &Transaction<'_>, p: &str, lock: bool) -> Result<Vec<SessionRow>, OwnerError> {
    let sql = if lock {
        "SELECT * FROM sessions WHERE principal_id=$1 ORDER BY session_id FOR UPDATE NOWAIT"
    } else {
        "SELECT * FROM sessions WHERE principal_id=$1 ORDER BY session_id"
    };
    tx.query(sql, &[&p])
        .await
        .map_err(|e| db("session set", e))?
        .iter()
        .map(SessionRow::read)
        .collect()
}
pub(super) async fn verify_row(tx: &Transaction<'_>, r: &SessionRow) -> Result<(), OwnerError> {
    if row(tx, &r.session_id, false).await?.as_ref() != Some(r) {
        return Err(OwnerError::Mismatch("session"));
    }
    Ok(())
}
impl PgNoteStore {
    pub async fn issue_session(&self, p: &PreparedSession) -> Result<SessionView, OwnerError> {
        let r = &p.row;
        let a = &p.audit;
        self.owner_write(
            |e| unknown("session-create", &a.event_id, e),
            async |tx| {
                lock_principal(tx, &r.principal_id, false).await?.view()?;
                issue_in_tx(tx, p).await?;
                deferred(tx).await?;
                verify_row(tx, r).await?;
                verify_unique_audit(tx, a).await?;
                r.view()
            },
        )
        .await
    }
    /// Historical creation evidence, not current authentication.
    pub async fn observe_session_creation(
        &self,
        p: &PreparedSession,
    ) -> Result<SessionCreationObservation, OwnerError> {
        let mut lease = self.connect().await.map_err(OwnerError::Pool)?;
        let tx = lease
            .client()
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()
            .await
            .map_err(|e| db("session observe begin", e))?;
        let result = observe_creation_in_tx(&tx, p).await?;
        tx.rollback()
            .await
            .map_err(|e| db("session observe end", e))?;
        lease.reusable();
        Ok(result)
    }
    /// Token hash lookup only; after acquiring the principal/session locks,
    /// re-read the fresh row. No stale authentication after committed revoke.
    pub async fn authenticate_session(
        &self,
        token: &str,
        now: i64,
        idle: i64,
    ) -> Result<AuthenticatedSession, OwnerError> {
        let expires = deadline(now, idle)?;
        if token.is_empty() {
            return Err(OwnerError::SessionInvalid);
        }
        let hash = super::hash_text(token);
        self.owner_write(|e|unknown("session-touch","redacted",e),async |tx|{
   let found=tx.query_opt("SELECT session_id,principal_id FROM sessions WHERE token_hash=$1",&[&hash]).await.map_err(|e|db("session locate",e))?.ok_or(OwnerError::SessionInvalid)?;
   let id:String=found.get(0);let principal_id:String=found.get(1);
   let principal=lock_principal(tx,&principal_id,false).await?.view()?;
   let mut expected=row(tx,&id,true).await?.ok_or(OwnerError::SessionInvalid)?;
   expected.view()?;
   if expected.token_hash!=hash||expected.principal_id!=principal_id||expected.revoked_at.is_some()||expected.idle_expires_at<=now||expected.absolute_expires_at<=now{return Err(OwnerError::SessionInvalid)}
   if now<expected.last_seen_at{return Err(OwnerError::SessionStale)}
   expected.last_seen_at=now;expected.idle_expires_at=expires.min(expected.absolute_expires_at);
   one(tx.execute("UPDATE sessions SET last_seen_at=$2,idle_expires_at=$3 WHERE session_id=$1 AND revoked_at IS NULL",&[&id,&now,&expected.idle_expires_at]).await.map_err(|e|db("session touch",e))?,"session touch")?;
   deferred(tx).await?;verify_row(tx,&expected).await?;
   if lock_principal(tx,&principal_id,false).await?.view()?!=principal{return Err(OwnerError::Mismatch("session principal"))}
   Ok(AuthenticatedSession{token_hash:hash.clone(),principal,session:expected.view()?})
  }).await
    }
    pub async fn list_sessions(&self, p: &str) -> Result<Vec<SessionView>, OwnerError> {
        let mut lease = self.connect().await.map_err(OwnerError::Pool)?;
        let rows = lease
            .client()
            .query(
                "SELECT * FROM sessions WHERE principal_id=$1 ORDER BY created_at DESC,session_id",
                &[&p],
            )
            .await
            .map_err(|e| db("session list", e))?;
        let result = rows
            .iter()
            .map(|r| SessionRow::read(r)?.view())
            .collect::<Result<Vec<_>, _>>()?;
        lease.reusable();
        Ok(result)
    }
    pub async fn revoke_session(
        &self,
        p: &str,
        id: &str,
        audit_id: Uuid,
        now: i64,
    ) -> Result<bool, OwnerError> {
        if !safe(now) {
            return Err(OwnerError::Invalid);
        }
        let a = audit(
            audit_id,
            p,
            "session.revoked",
            "session",
            id,
            "{}".into(),
            now,
        );
        self.owner_write(|e|unknown("session-revoke",&a.event_id,e),async |tx|{
   lock_principal(tx,p,false).await?;
   // Principal-filtered lookup avoids locking a foreign session.
   let Some(r)=tx.query_opt("SELECT * FROM sessions WHERE session_id=$1 AND principal_id=$2 FOR UPDATE NOWAIT",&[&id,&p]).await.map_err(|e|db("session revoke lock",e))? else{return Ok(false)};
   let mut expected=SessionRow::read(&r)?;expected.view()?;
   if expected.revoked_at.is_some(){return Ok(false)}
   one(tx.execute("UPDATE sessions SET revoked_at=$2 WHERE session_id=$1 AND revoked_at IS NULL",&[&id,&now]).await.map_err(|e|db("session revoke",e))?,"session revoke")?;
   expected.revoked_at=Some(now);
   write_audit(tx,&a).await?;deferred(tx).await?;verify_row(tx,&expected).await?;verify_audit(tx,&a).await?;Ok(true)
  }).await
    }
    pub async fn revoke_all_sessions(
        &self,
        p: &str,
        audit_id: Uuid,
        now: i64,
    ) -> Result<u64, OwnerError> {
        if !safe(now) {
            return Err(OwnerError::Invalid);
        }
        let coordinate = audit_id.to_string();
        self.owner_write(|e|unknown("session-revoke-all",&coordinate,e),async |tx|{
   // Principal NO KEY UPDATE conflicts with SHARE used by every session
   // writer, but not unrelated foreign-key KEY SHARE users.
   lock_principal(tx,p,true).await?;
   let mut expected=rows(tx,p,true).await?;
   let mut count=0u64;
   for r in &mut expected{r.view()?;if r.revoked_at.is_none(){r.revoked_at=Some(now);count+=1}}
   let n=tx.execute("UPDATE sessions SET revoked_at=$2 WHERE principal_id=$1 AND revoked_at IS NULL",&[&p,&now]).await.map_err(|e|db("session bulk revoke",e))?;
   if n!=count{return Err(OwnerError::Write("session bulk revoke"))}
   let a=audit(audit_id,p,"session.revoked-all","principal",p,format!(r#"{{"count":{count}}}"#),now);
   write_audit(tx,&a).await?;deferred(tx).await?;
   if rows(tx,p,false).await?!=expected{return Err(OwnerError::Mismatch("session set"))}
   verify_audit(tx,&a).await?;Ok(count)
  }).await
    }
}

pub(super) async fn issue_in_tx(
    tx: &Transaction<'_>,
    p: &PreparedSession,
) -> Result<(), OwnerError> {
    let r = &p.row;
    let a = &p.audit;
    one(
        tx.execute(
            "INSERT INTO sessions VALUES($1,$2,$3,$4,$5,$6,$7,$8,NULL,$9,$10)",
            &[
                &r.session_id,
                &r.token_hash,
                &r.principal_id,
                &r.created_at,
                &r.authenticated_at,
                &r.last_seen_at,
                &r.idle_expires_at,
                &r.absolute_expires_at,
                &r.authn_method,
                &r.user_agent,
            ],
        )
        .await
        .map_err(|e| db("session insert", e))?,
        "session",
    )?;
    write_audit(tx, a).await?;
    Ok(())
}

pub(super) async fn observe_creation_in_tx(
    tx: &Transaction<'_>,
    p: &PreparedSession,
) -> Result<SessionCreationObservation, OwnerError> {
    let actual = row(tx, p.session_id(), false).await?;
    let audits=tx.query("SELECT * FROM audit_events WHERE event_id=$1 OR (event_type='session.created' AND object_type='session' AND object_id=$2) LIMIT 2",&[&p.audit_id(),&p.session_id()]).await.map_err(|e|db("session observe audit",e))?.iter().map(AuditRow::read).collect::<Result<Vec<_>,_>>()?;
    let result = match actual {
        None if audits.is_empty() => SessionCreationObservation::Unobserved,
        Some(r) if audits.as_slice() == [p.audit.clone()] => {
            let mut immutable = r.clone();
            immutable.last_seen_at = p.row.last_seen_at;
            immutable.idle_expires_at = p.row.idle_expires_at;
            immutable.revoked_at = p.row.revoked_at;
            match r.view() {
                Ok(v) if immutable == p.row => SessionCreationObservation::Exact(Box::new(v)),
                _ => SessionCreationObservation::Mismatch,
            }
        }
        _ => SessionCreationObservation::Mismatch,
    };
    Ok(result)
}
