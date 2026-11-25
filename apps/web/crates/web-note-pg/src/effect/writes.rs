//! Native writes; transaction and admission remain owned by the caller.
use super::domain::{db, one};
use super::rows::{AuditRow, GrantRow};
use super::{EffectError, EffectOperation, EffectReceipt, EffectRequest};
use crate::postgres::note_from_row;
use crate::{Note, NoteState};
use serde::Serialize;
use tokio_postgres::Transaction;
pub(super) async fn write_note(
    tx: &Transaction<'_>,
    g: &GrantRow,
    op: &EffectOperation,
    now: i64,
) -> Result<Note, EffectError> {
    match op {
        EffectOperation::Create { note_id, content } => {
            let note = Note {
                note_id: note_id.to_string(),
                principal_id: g.principal_id.clone(),
                content: content.clone(),
                state: NoteState::Draft,
                created_at: now,
                published_at: None,
            };
            one(
                tx.execute(
                    "INSERT INTO canary_notes VALUES($1,$2,$3,'DRAFT',$4,NULL)",
                    &[&note.note_id, &note.principal_id, &note.content, &now],
                )
                .await
                .map_err(|e| db("create note", e))?,
                "note",
            )?;
            Ok(note)
        }
        EffectOperation::Publish { note_id } => {
            let row=tx.query_opt("SELECT * FROM canary_notes WHERE note_id=$1 AND principal_id=$2 FOR UPDATE NOWAIT",&[&note_id,&g.principal_id]).await.map_err(|e|db("note lock",e))?.ok_or(EffectError::NotPublishable)?;
            let mut note = note_from_row(&row).map_err(|_| EffectError::Corrupt)?;
            if note.state != NoteState::Draft {
                return Err(EffectError::NotPublishable);
            }
            one(tx.execute("UPDATE canary_notes SET state='PUBLISHED',published_at=$2 WHERE note_id=$1 AND state='DRAFT'",&[&note_id,&now]).await.map_err(|e|db("publish note",e))?,"note")?;
            note.state = NoteState::Published;
            note.published_at = Some(now);
            Ok(note)
        }
    }
}
#[derive(Serialize)]
struct ResultNote<'a> {
    note: &'a Note,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct AuditDetail<'a> {
    agent_id: &'a str,
    grant_id: &'a str,
    action: &'a str,
}
pub(super) async fn write_receipt(
    tx: &Transaction<'_>,
    g: &GrantRow,
    r: &EffectRequest,
    note: &Note,
    audit_id: uuid::Uuid,
    now: i64,
) -> Result<(EffectReceipt, AuditRow), EffectError> {
    let result_json =
        serde_json::to_string(&ResultNote { note }).map_err(|_| EffectError::Corrupt)?;
    let receipt = EffectReceipt {
        effect_id: r.effect_id.clone(),
        effect_digest: r.effect_digest.clone(),
        principal_id: g.principal_id.clone(),
        agent_id: r.agent_id.clone(),
        grant_id: g.grant_id.clone(),
        action: r.action.clone(),
        resource: r.resource.clone(),
        result_json,
        committed_at: now,
    };
    one(
        tx.execute(
            "INSERT INTO agent_effects VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)",
            &[
                &receipt.effect_id,
                &receipt.effect_digest,
                &receipt.principal_id,
                &receipt.agent_id,
                &receipt.grant_id,
                &receipt.action,
                &receipt.resource,
                &receipt.result_json,
                &receipt.committed_at,
            ],
        )
        .await
        .map_err(|e| db("receipt insert", e))?,
        "receipt",
    )?;
    let audit = AuditRow {
        event_id: audit_id.to_string(),
        principal_id: Some(g.principal_id.clone()),
        event_type: "agent.effect.committed".into(),
        object_type: Some("effect".into()),
        object_id: Some(r.effect_id.clone()),
        detail_json: serde_json::to_string(&AuditDetail {
            agent_id: &r.agent_id,
            grant_id: &g.grant_id,
            action: &r.action,
        })
        .map_err(|_| EffectError::Corrupt)?,
        created_at: now,
    };
    one(
        tx.execute(
            "INSERT INTO audit_events VALUES($1,$2,$3,$4,$5,$6,$7)",
            &[
                &audit.event_id,
                &audit.principal_id,
                &audit.event_type,
                &audit.object_type,
                &audit.object_id,
                &audit.detail_json,
                &audit.created_at,
            ],
        )
        .await
        .map_err(|e| db("audit insert", e))?,
        "audit",
    )?;
    Ok((receipt, audit))
}
