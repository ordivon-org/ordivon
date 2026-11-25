//! Final exact business/evidence observations after the deferred fence.
use super::domain::db;
use super::rows::{ApprovalRow, AuditRow, GrantRow};
use super::{EffectError, EffectReceipt};
use crate::Note;
use crate::postgres::note_from_row;
use tokio_postgres::Transaction;
pub(super) async fn verify(
    tx: &Transaction<'_>,
    mut grant: GrantRow,
    approval: Option<&ApprovalRow>,
    note: &Note,
    receipt: &EffectReceipt,
    audit: &AuditRow,
) -> Result<(), EffectError> {
    grant.remaining_effects -= 1;
    grant.revision += 1;
    let row = tx
        .query_opt(
            "SELECT * FROM agent_grants WHERE grant_id=$1",
            &[&grant.grant_id],
        )
        .await
        .map_err(|e| db("grant readback", e))?
        .ok_or(EffectError::Mismatch("grant"))?;
    if GrantRow::read(&row)? != grant {
        return Err(EffectError::Mismatch("grant"));
    }
    let row = tx
        .query_opt(
            "SELECT * FROM canary_notes WHERE note_id=$1",
            &[&note.note_id],
        )
        .await
        .map_err(|e| db("note readback", e))?
        .ok_or(EffectError::Mismatch("note"))?;
    if note_from_row(&row).map_err(|_| EffectError::Corrupt)? != *note {
        return Err(EffectError::Mismatch("note"));
    }
    let row = tx
        .query_opt(
            "SELECT * FROM agent_effects WHERE effect_id=$1",
            &[&receipt.effect_id],
        )
        .await
        .map_err(|e| db("receipt readback", e))?
        .ok_or(EffectError::Mismatch("receipt"))?;
    if EffectReceipt::read(&row)? != *receipt {
        return Err(EffectError::Mismatch("receipt"));
    }
    let rows=tx.query("SELECT * FROM audit_events WHERE event_type='agent.effect.committed' AND object_type='effect' AND object_id=$1 LIMIT 2",&[&receipt.effect_id]).await.map_err(|e|db("audit readback",e))?;
    if rows.len() != 1 || AuditRow::read(&rows[0])? != *audit {
        return Err(EffectError::Mismatch("audit"));
    }
    if let Some(expected) = approval {
        let row = tx
            .query_opt(
                "SELECT * FROM effect_approvals WHERE effect_id=$1",
                &[&receipt.effect_id],
            )
            .await
            .map_err(|e| db("approval readback", e))?
            .ok_or(EffectError::Mismatch("approval"))?;
        if ApprovalRow::read(&row)? != *expected {
            return Err(EffectError::Mismatch("approval"));
        }
    }
    Ok(())
}
