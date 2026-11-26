//! Read-only recovery projections. Historical evidence and mutable state
//! are deliberately different types, never convert missing to noncommit.
use super::domain::db;
use super::rows::{ApprovalRow, AuditRow, GrantRow};
use super::{
    EffectError, EffectReceipt, EffectRequest, GrantFence, GrantSnapshot, PendingApproval,
};
use crate::{PgNoteStore, domain::representable};
use serde::Serialize;
use tokio_postgres::IsolationLevel;
use uuid::Uuid;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RevocationObservation {
    // Exact operation audit and currently inactive bound Grant. Not a
    // reconstruction of the revision at the historical revocation instant.
    Exact(Box<GrantSnapshot>),
    Unobserved,
    Mismatch,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ApprovalView {
    pub effect_id: String,
    pub effect_digest: String,
    pub principal_id: String,
    pub credential_id: String,
    pub verified_at: i64,
    pub expires_at: i64,
    pub consumed_at: Option<i64>,
}
impl ApprovalRow {
    fn view(self) -> Result<ApprovalView, EffectError> {
        if !representable("", "", self.verified_at)
            || !representable("", "", self.expires_at)
            || self.consumed_at.is_some_and(|n| !representable("", "", n))
        {
            return Err(EffectError::Corrupt);
        }
        Ok(ApprovalView {
            effect_id: self.effect_id,
            effect_digest: self.effect_digest,
            principal_id: self.principal_id,
            credential_id: self.credential_id,
            verified_at: self.verified_at,
            expires_at: self.expires_at,
            consumed_at: self.consumed_at,
        })
    }
}
/// Current coherent facts, NOT proof that a particular pending/approval
/// write committed. A later refresh can replace these mutable fields.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AuthorityObservation {
    pub pending: Option<PendingApproval>,
    pub approval: Option<ApprovalView>,
    pub receipt: Option<EffectReceipt>,
}
impl PgNoteStore {
    /// Caller retains the selected Grant binding, audit identity and time.
    /// This is an internal storage observation, not an authentication check.
    pub async fn observe_grant_revocation(
        &self,
        g: &GrantFence,
        audit_id: Uuid,
        now: i64,
    ) -> Result<RevocationObservation, EffectError> {
        if !representable("", "", now) || !representable("", "", g.revision) || g.revision < 1 {
            return Err(EffectError::Invalid);
        }
        let mut lease = self.connect().await.map_err(EffectError::Pool)?;
        let tx = lease
            .client()
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()
            .await
            .map_err(|e| db("observe revoke begin", e))?;
        let audit = tx
            .query_opt(
                "SELECT * FROM audit_events WHERE event_id=$1",
                &[&audit_id.to_string()],
            )
            .await
            .map_err(|e| db("observe revoke audit", e))?
            .as_ref()
            .map(AuditRow::read)
            .transpose()?;
        let result = if let Some(audit) = audit {
            #[derive(Serialize)]
            #[serde(rename_all = "camelCase")]
            struct Detail<'a> {
                agent_id: &'a str,
            }
            let expected = AuditRow {
                event_id: audit_id.to_string(),
                principal_id: Some(g.principal_id.clone()),
                event_type: "agent.grant.revoked".into(),
                object_type: Some("agent-grant".into()),
                object_id: Some(g.grant_id.clone()),
                detail_json: serde_json::to_string(&Detail {
                    agent_id: &g.agent_id,
                })
                .map_err(|_| EffectError::Invalid)?,
                created_at: now,
            };
            let row = tx
                .query_opt(
                    "SELECT * FROM agent_grants WHERE grant_id=$1",
                    &[&g.grant_id],
                )
                .await
                .map_err(|e| db("observe revoked grant", e))?
                .as_ref()
                .map(GrantRow::read)
                .transpose()?;
            match row {
                Some(row)
                    if audit == expected
                        && row.grant_digest == g.grant_digest
                        && row.principal_id == g.principal_id
                        && row.agent_id == g.agent_id
                        && row.active == 0
                        && row.revision > g.revision =>
                {
                    match row.snapshot() {
                        Ok(snapshot) => RevocationObservation::Exact(Box::new(snapshot)),
                        Err(_) => RevocationObservation::Mismatch,
                    }
                }
                _ => RevocationObservation::Mismatch,
            }
        } else {
            RevocationObservation::Unobserved
        };
        tx.rollback()
            .await
            .map_err(|e| db("observe revoke end", e))?;
        lease.reusable();
        Ok(result)
    }
    /// Authenticated trusted caller owns principal + request binding.
    /// Read all three facts under one native MVCC snapshot.
    pub async fn observe_authority(
        &self,
        principal: &str,
        r: &EffectRequest,
    ) -> Result<AuthorityObservation, EffectError> {
        let mut lease = self.connect().await.map_err(EffectError::Pool)?;
        let tx = lease
            .client()
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()
            .await
            .map_err(|e| db("observe authority begin", e))?;
        let pending = tx
            .query_opt(
                "SELECT * FROM pending_effect_approvals WHERE effect_id=$1",
                &[&r.effect_id],
            )
            .await
            .map_err(|e| db("observe pending", e))?
            .as_ref()
            .map(PendingApproval::read)
            .transpose()?;
        if let Some(p) = &pending {
            if p.principal_id != principal || p.effect_digest != r.effect_digest {
                return Err(EffectError::ApprovalBinding);
            }
            if !representable("", "", p.created_at) || !representable("", "", p.expires_at) {
                return Err(EffectError::Corrupt);
            }
        }
        let approval = tx
            .query_opt(
                "SELECT * FROM effect_approvals WHERE effect_id=$1",
                &[&r.effect_id],
            )
            .await
            .map_err(|e| db("observe approval", e))?
            .as_ref()
            .map(ApprovalRow::read)
            .transpose()?
            .map(ApprovalRow::view)
            .transpose()?;
        if approval
            .as_ref()
            .is_some_and(|a| a.principal_id != principal || a.effect_digest != r.effect_digest)
        {
            return Err(EffectError::ApprovalBinding);
        }
        let receipt = tx
            .query_opt(
                "SELECT * FROM agent_effects WHERE effect_id=$1",
                &[&r.effect_id],
            )
            .await
            .map_err(|e| db("observe authority receipt", e))?
            .as_ref()
            .map(EffectReceipt::read)
            .transpose()?;
        if let Some(receipt) = &receipt {
            if receipt.principal_id != principal {
                return Err(EffectError::ApprovalBinding);
            }
            receipt.replay(r)?;
        }
        tx.rollback()
            .await
            .map_err(|e| db("observe authority end", e))?;
        lease.reusable();
        Ok(AuthorityObservation {
            pending,
            approval,
            receipt,
        })
    }
}
