//! Effect identity -> receipt -> Grant -> Approval -> Note, one PG transaction.
//! No automatic retry. All future effect writers must cooperate on this order.
use super::domain::{db, one, valid_input};
use super::postconditions::verify;
use super::rows::{ApprovalRow, GrantRow};
use super::writes::{write_note, write_receipt};
use super::{
    EffectError, EffectOperation, EffectOutcome, EffectReceipt, EffectRequest, GrantFence,
};
use crate::PgNoteStore;
use tokio_postgres::Transaction;

impl PgNoteStore {
    /// Trusted caller must have verified the request and bound its content
    /// digest, selected Grant and policy decision. No transport exposure.
    pub async fn commit_effect(
        &self,
        g: &GrantFence,
        r: &EffectRequest,
        op: &EffectOperation,
        audit_id: uuid::Uuid,
        now: i64,
    ) -> Result<EffectOutcome, EffectError> {
        self.commit_with_selection(g, r, op, audit_id, now, false)
            .await
    }
    pub(crate) async fn commit_selected_effect(
        &self,
        g: &GrantFence,
        r: &EffectRequest,
        op: &EffectOperation,
        audit_id: uuid::Uuid,
        now: i64,
    ) -> Result<EffectOutcome, EffectError> {
        self.commit_with_selection(g, r, op, audit_id, now, true)
            .await
    }
    async fn commit_with_selection(
        &self,
        g: &GrantFence,
        r: &EffectRequest,
        op: &EffectOperation,
        audit_id: uuid::Uuid,
        now: i64,
        strict: bool,
    ) -> Result<EffectOutcome, EffectError> {
        if !valid_input(r, g, op, now) {
            return Err(EffectError::Invalid);
        }
        self.owner_write(
            |source| EffectError::CommitUnknown {
                effect_id: r.effect_id.clone(),
                source,
            },
            async |tx| execute(tx, g, r, op, audit_id, now, strict).await,
        )
        .await
    }

    /// Committed receipt observation only; absence is not proof of noncommit.
    /// Caller must be authenticated for the Agent in r.
    pub async fn observe_effect(
        &self,
        r: &EffectRequest,
    ) -> Result<Option<EffectReceipt>, EffectError> {
        if r.effect_id.contains('\0') {
            return Err(EffectError::Invalid);
        }
        let mut lease = self.connect().await.map_err(EffectError::Pool)?;
        let row = lease
            .client()
            .query_opt(
                "SELECT * FROM agent_effects WHERE effect_id=$1",
                &[&r.effect_id],
            )
            .await
            .map_err(|e| db("observe", e))?;
        let result = row.as_ref().map(EffectReceipt::read).transpose()?;
        if let Some(receipt) = &result {
            receipt.replay(r)?;
        }
        lease.reusable();
        Ok(result)
    }
}
async fn execute(
    tx: &Transaction<'_>,
    g: &GrantFence,
    r: &EffectRequest,
    op: &EffectOperation,
    audit_id: uuid::Uuid,
    now: i64,
    strict: bool,
) -> Result<EffectOutcome, EffectError> {
    lock_identity(tx, &r.effect_id).await?;
    if let Some(row) = tx
        .query_opt(
            "SELECT * FROM agent_effects WHERE effect_id=$1",
            &[&r.effect_id],
        )
        .await
        .map_err(|e| db("receipt", e))?
    {
        let receipt = EffectReceipt::read(&row)?;
        receipt.replay(r)?;
        return Ok(EffectOutcome {
            receipt,
            replayed: true,
        });
    }
    if strict {
        super::grants::verify_unique_selection(tx, g, r, now).await?;
    }
    let publish = matches!(op, EffectOperation::Publish { .. });
    let denied = || {
        if publish {
            EffectError::Fence
        } else {
            EffectError::GrantChanged
        }
    };
    let row = tx
        .query_opt(
            "SELECT * FROM agent_grants WHERE grant_id=$1 FOR UPDATE NOWAIT",
            &[&g.grant_id],
        )
        .await
        .map_err(|e| db("grant lock", e))?
        .ok_or_else(denied)?;
    let grant = GrantRow::read(&row)?;
    let (actions, prefixes) = grant.checked()?;
    if !grant.current(g, now) {
        return Err(denied());
    }
    let approval = if publish {
        let row=tx.query_opt("SELECT * FROM effect_approvals WHERE effect_id=$1 AND effect_digest=$2 AND principal_id=$3 AND consumed_at IS NULL AND expires_at>$4 FOR UPDATE NOWAIT",&[&r.effect_id,&r.effect_digest,&grant.principal_id,&now]).await.map_err(|e|db("approval lock",e))?.ok_or(EffectError::Fence)?;
        let mut a = ApprovalRow::read(&row)?;
        if !crate::domain::representable("", "", a.verified_at)
            || !crate::domain::representable("", "", a.expires_at)
        {
            return Err(EffectError::Corrupt);
        }
        a.consumed_at = Some(now);
        Some(a)
    } else {
        None
    };
    if !grant.binds(g, r, &actions, &prefixes) || !op.binds(r) {
        return Err(EffectError::Binding);
    }
    let note = write_note(tx, &grant, op, now).await?;
    if approval.is_some() {
        one(tx.execute("UPDATE effect_approvals SET consumed_at=$2 WHERE effect_id=$1 AND consumed_at IS NULL",&[&r.effect_id,&now]).await.map_err(|e|db("consume approval",e))?,"approval")?;
    }
    one(tx.execute("UPDATE agent_grants SET remaining_effects=remaining_effects-1,revision=revision+1 WHERE grant_id=$1 AND revision=$2",&[&grant.grant_id,&grant.revision]).await.map_err(|e|db("quota",e))?,"quota")?;
    let receipt = write_receipt(tx, &grant, r, &note, audit_id, now).await?;
    // Execute all deferred triggers before the last exact observations.
    tx.batch_execute("SET CONSTRAINTS ALL IMMEDIATE")
        .await
        .map_err(|e| db("deferred fence", e))?;
    verify(tx, grant, approval.as_ref(), &note, &receipt.0, &receipt.1).await?;
    Ok(EffectOutcome {
        receipt: receipt.0,
        replayed: false,
    })
}

pub(super) async fn lock_identity(
    tx: &Transaction<'_>,
    effect_id: &str,
) -> Result<(), EffectError> {
    let locked: bool = tx
        .query_one(
            "SELECT pg_try_advisory_xact_lock(hashtextextended('web-r1:'||$1,0))",
            &[&effect_id],
        )
        .await
        .map_err(|e| db("effect lock", e))?
        .get(0);
    if !locked {
        return Err(EffectError::Busy);
    }
    Ok(())
}
