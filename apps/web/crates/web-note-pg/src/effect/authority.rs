//! Cooperating owner-local writers. Security/WebAuthn verification remains
//! outside; these are atomic storage transitions, not authentication endpoints.
use super::domain::{db, one, valid_input};
use super::rows::{ApprovalRow, AuditRow, GrantRow};
use super::transaction::lock_identity;
use super::{
    EffectError, EffectOperation, EffectReceipt, EffectRequest, GrantFence, PendingApproval,
};
use crate::{PgNoteStore, domain::representable};
use serde::Serialize;
use tokio_postgres::Transaction;
use uuid::Uuid;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PendingOutcome {
    Registered(PendingApproval),
    AlreadyCommitted(EffectReceipt),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ApprovalWrite {
    pub effect_id: String,
    pub effect_digest: String,
    pub principal_id: String,
    pub credential_id: String,
    pub verified_at: i64,
    pub expires_at: i64,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GrantRevocation {
    pub grant_id: String,
    pub revision: i64,
    pub audit_id: Uuid,
}
fn text_ok(values: &[&str]) -> bool {
    values.iter().all(|s| !s.is_empty() && !s.contains('\0'))
}
fn safe(n: i64) -> bool {
    representable("", "", n)
}
fn deadline(now: i64, expires: i64) -> bool {
    safe(now) && safe(expires) && expires > now
}
fn unknown(
    operation: &'static str,
    coordinate: &str,
    source: tokio_postgres::Error,
) -> EffectError {
    EffectError::AuthorityCommitUnknown {
        operation,
        coordinate: coordinate.into(),
        source,
    }
}
async fn deferred(tx: &Transaction<'_>) -> Result<(), EffectError> {
    tx.batch_execute("SET CONSTRAINTS ALL IMMEDIATE")
        .await
        .map_err(|e| db("deferred authority fence", e))
}
async fn receipt(
    tx: &Transaction<'_>,
    effect_id: &str,
) -> Result<Option<EffectReceipt>, EffectError> {
    tx.query_opt(
        "SELECT * FROM agent_effects WHERE effect_id=$1",
        &[&effect_id],
    )
    .await
    .map_err(|e| db("authority receipt", e))?
    .as_ref()
    .map(EffectReceipt::read)
    .transpose()
}
async fn pending(
    tx: &Transaction<'_>,
    effect_id: &str,
) -> Result<Option<PendingApproval>, EffectError> {
    tx.query_opt(
        "SELECT * FROM pending_effect_approvals WHERE effect_id=$1 FOR UPDATE NOWAIT",
        &[&effect_id],
    )
    .await
    .map_err(|e| db("pending lock", e))?
    .as_ref()
    .map(PendingApproval::read)
    .transpose()
}
async fn grant(tx: &Transaction<'_>, grant_id: &str) -> Result<GrantRow, EffectError> {
    let row = tx
        .query_opt(
            "SELECT * FROM agent_grants WHERE grant_id=$1 FOR UPDATE NOWAIT",
            &[&grant_id],
        )
        .await
        .map_err(|e| db("authority grant lock", e))?
        .ok_or(EffectError::GrantChanged)?;
    GrantRow::read(&row)
}
impl PgNoteStore {
    /// Trusted STEP_UP caller, rechecks the mutable Grant and receipt in the
    /// same transaction as pending registration (no post-admission gap).
    pub async fn register_pending_approval(
        &self,
        g: &GrantFence,
        r: &EffectRequest,
        op: &EffectOperation,
        now: i64,
        expires: i64,
    ) -> Result<PendingOutcome, EffectError> {
        self.register_pending(g, r, op, now, expires, false).await
    }
    pub(crate) async fn register_selected_pending(
        &self,
        g: &GrantFence,
        r: &EffectRequest,
        op: &EffectOperation,
        now: i64,
        expires: i64,
    ) -> Result<PendingOutcome, EffectError> {
        self.register_pending(g, r, op, now, expires, true).await
    }
    async fn register_pending(
        &self,
        g: &GrantFence,
        r: &EffectRequest,
        op: &EffectOperation,
        now: i64,
        expires: i64,
        strict: bool,
    ) -> Result<PendingOutcome, EffectError> {
        if !valid_input(r, g, op, now) || !deadline(now, expires) {
            return Err(EffectError::Invalid);
        }
        self.owner_write(|e|unknown("pending",&r.effect_id,e),async |tx|{
            lock_identity(tx,&r.effect_id).await?;
            if let Some(receipt)=receipt(tx,&r.effect_id).await?{
                receipt.replay(r)?;return Ok(PendingOutcome::AlreadyCommitted(receipt));
            }
            if strict {super::grants::verify_unique_selection(tx,g,r,now).await?;}
            let current=grant(tx,&g.grant_id).await?;
            let (actions,prefixes)=current.checked()?;
            if !current.current(g,now){return Err(EffectError::GrantChanged)}
            if !current.binds(g,r,&actions,&prefixes)||!op.binds(r){return Err(EffectError::Binding)}
            let old=pending(tx,&r.effect_id).await?;
            if old.as_ref().is_some_and(|p|p.effect_digest!=r.effect_digest||p.principal_id!=g.principal_id){return Err(EffectError::PendingConflict)}
            let expected=PendingApproval{effect_id:r.effect_id.clone(),effect_digest:r.effect_digest.clone(),principal_id:g.principal_id.clone(),
                created_at:old.as_ref().map_or(now,|p|p.created_at),expires_at:expires};
            if !safe(expected.created_at){return Err(EffectError::Corrupt)}
            one(tx.execute("INSERT INTO pending_effect_approvals VALUES($1,$2,$3,$4,$5) ON CONFLICT(effect_id) DO UPDATE SET expires_at=excluded.expires_at WHERE pending_effect_approvals.effect_digest=excluded.effect_digest AND pending_effect_approvals.principal_id=excluded.principal_id",
              &[&expected.effect_id,&expected.effect_digest,&expected.principal_id,&expected.expires_at,&expected.created_at]).await.map_err(|e|db("pending write",e))?,"pending")?;
            deferred(tx).await?;
            if pending(tx,&r.effect_id).await?.as_ref()!=Some(&expected){return Err(EffectError::Mismatch("pending"))}
            if grant(tx,&g.grant_id).await?!=current{return Err(EffectError::Mismatch("pending grant"))}
            if receipt(tx,&r.effect_id).await?.is_some(){return Err(EffectError::Mismatch("pending terminal receipt"))}
            Ok(PendingOutcome::Registered(expected))
        }).await
    }
    /// Caller has completed WebAuthn verification for this exact Principal,
    /// credential and effect binding. Recheck live pending state atomically
    /// and never reopen a committed or consumed effect.
    pub async fn put_verified_approval(&self, input: &ApprovalWrite) -> Result<(), EffectError> {
        if !text_ok(&[
            &input.effect_id,
            &input.effect_digest,
            &input.principal_id,
            &input.credential_id,
        ]) || !deadline(input.verified_at, input.expires_at)
        {
            return Err(EffectError::Invalid);
        }
        self.owner_write(|e|unknown("approval",&input.effect_id,e),async |tx|{
            lock_identity(tx,&input.effect_id).await?;
            if receipt(tx,&input.effect_id).await?.is_some(){return Err(EffectError::ApprovalClosed)}
            let p=pending(tx,&input.effect_id).await?.ok_or(EffectError::PendingNotFound)?;
            if !safe(p.expires_at)||!safe(p.created_at){return Err(EffectError::Corrupt)}
            if p.principal_id!=input.principal_id||p.expires_at<=input.verified_at{return Err(EffectError::PendingNotFound)}
            if p.effect_digest!=input.effect_digest{return Err(EffectError::ApprovalBinding)}
            let row=tx.query_opt("SELECT principal_id FROM webauthn_credentials WHERE credential_id=$1 FOR SHARE NOWAIT",&[&input.credential_id]).await.map_err(|e|db("credential binding",e))?.ok_or(EffectError::ApprovalBinding)?;
            if row.get::<_,String>(0)!=input.principal_id{return Err(EffectError::ApprovalBinding)}
            let old=tx.query_opt("SELECT * FROM effect_approvals WHERE effect_id=$1 FOR UPDATE NOWAIT",&[&input.effect_id]).await.map_err(|e|db("approval write lock",e))?.as_ref().map(ApprovalRow::read).transpose()?;
            if old.as_ref().is_some_and(|a|a.consumed_at.is_some()||a.effect_digest!=input.effect_digest||a.principal_id!=input.principal_id){return Err(EffectError::ApprovalClosed)}
            let expected=ApprovalRow{effect_id:input.effect_id.clone(),effect_digest:input.effect_digest.clone(),principal_id:input.principal_id.clone(),credential_id:input.credential_id.clone(),verified_at:input.verified_at,expires_at:input.expires_at,consumed_at:None};
            one(tx.execute("INSERT INTO effect_approvals VALUES($1,$2,$3,$4,$5,$6,NULL) ON CONFLICT(effect_id) DO UPDATE SET credential_id=excluded.credential_id,verified_at=excluded.verified_at,expires_at=excluded.expires_at WHERE effect_approvals.consumed_at IS NULL AND effect_approvals.effect_digest=excluded.effect_digest AND effect_approvals.principal_id=excluded.principal_id",
                &[&expected.effect_id,&expected.effect_digest,&expected.principal_id,&expected.credential_id,&expected.verified_at,&expected.expires_at]).await.map_err(|e|db("approval write",e))?,"approval")?;
            deferred(tx).await?;
            let row=tx.query_opt("SELECT * FROM effect_approvals WHERE effect_id=$1",&[&input.effect_id]).await.map_err(|e|db("approval write readback",e))?.ok_or(EffectError::Mismatch("approval"))?;
            if ApprovalRow::read(&row)?!=expected{return Err(EffectError::Mismatch("approval"))}
            if pending(tx,&input.effect_id).await?.as_ref()!=Some(&p)||receipt(tx,&input.effect_id).await?.is_some(){return Err(EffectError::Mismatch("approval binding"))}
            Ok(())
        }).await
    }
    /// Caller owns a verified principal/digest decision and the audit
    /// identity. Grant-only row lock does not reverse Effect lock order.
    pub async fn revoke_grant(
        &self,
        principal: &str,
        grant_id: &str,
        digest: &str,
        audit_id: Uuid,
        now: i64,
    ) -> Result<GrantRevocation, EffectError> {
        if !text_ok(&[principal, grant_id, digest]) || !safe(now) {
            return Err(EffectError::Invalid);
        }
        let audit_coordinate = audit_id.to_string();
        self.owner_write(|e|unknown("grant-revocation",&audit_coordinate,e),async |tx|{
            let mut expected=grant(tx,grant_id).await?;
            expected.checked()?;
            if expected.principal_id!=principal{return Err(EffectError::GrantPrincipalMismatch)}
            if expected.grant_digest!=digest||!safe(expected.revision+1){return Err(EffectError::GrantChanged)}
            let revision=expected.revision;
            expected.active=0;expected.revision+=1;
            one(tx.execute("UPDATE agent_grants SET active=0,revision=revision+1 WHERE grant_id=$1 AND revision=$2",&[&grant_id,&revision]).await.map_err(|e|db("revoke grant",e))?,"grant revocation")?;
            #[derive(Serialize)]
            #[serde(rename_all="camelCase")]
            struct RevocationDetail<'a>{agent_id:&'a str}
            let audit=AuditRow{event_id:audit_coordinate.clone(),principal_id:Some(principal.into()),event_type:"agent.grant.revoked".into(),object_type:Some("agent-grant".into()),object_id:Some(grant_id.into()),detail_json:serde_json::to_string(&RevocationDetail{agent_id:&expected.agent_id}).map_err(|_|EffectError::Corrupt)?,created_at:now};
            one(tx.execute("INSERT INTO audit_events VALUES($1,$2,$3,$4,$5,$6,$7)",&[&audit.event_id,&audit.principal_id,&audit.event_type,&audit.object_type,&audit.object_id,&audit.detail_json,&audit.created_at]).await.map_err(|e|db("revoke audit",e))?,"revocation audit")?;
            deferred(tx).await?;
            if grant(tx,grant_id).await?!=expected{return Err(EffectError::Mismatch("revoked grant"))}
            let row=tx.query_opt("SELECT * FROM audit_events WHERE event_id=$1",&[&audit.event_id]).await.map_err(|e|db("revocation audit readback",e))?.ok_or(EffectError::Mismatch("revocation audit"))?;
            if AuditRow::read(&row)?!=audit{return Err(EffectError::Mismatch("revocation audit"))}
            Ok(GrantRevocation{grant_id:grant_id.into(),revision:expected.revision,audit_id})
        }).await
    }
}
