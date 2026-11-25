use crate::domain::{Audit, Note, NoteState, representable};
use crate::pool::{Lease, local_pool};
use crate::{NoteError, NoteObservation, PoolLimits, PreparedNote};
use std::path::Path;
use tokio_postgres::{IsolationLevel, Row, Transaction};

#[derive(Clone)]
pub struct PgNoteStore {
    pool: deadpool_postgres::Pool,
}
fn db(phase: &'static str, source: tokio_postgres::Error) -> NoteError {
    NoteError::Database { phase, source }
}
fn note_from_row(row: &Row) -> Result<Note, NoteError> {
    let decode = |e| db("decode-note", e);
    let state: String = row.try_get("state").map_err(decode)?;
    let note = Note {
        note_id: row.try_get("note_id").map_err(decode)?,
        principal_id: row.try_get("principal_id").map_err(decode)?,
        content: row.try_get("content").map_err(decode)?,
        state: match state.as_str() {
            "DRAFT" => NoteState::Draft,
            "PUBLISHED" => NoteState::Published,
            _ => return Err(NoteError::BusinessMismatch),
        },
        created_at: row.try_get("created_at").map_err(decode)?,
        published_at: row.try_get("published_at").map_err(decode)?,
    };
    if !representable(&note.principal_id, &note.content, note.created_at)
        || note.published_at.is_some_and(|t| !representable("", "", t))
    {
        return Err(NoteError::BusinessMismatch);
    }
    Ok(note)
}
fn audit_from_row(row: &Row) -> Result<Audit, tokio_postgres::Error> {
    Ok(Audit {
        event_id: row.try_get("event_id")?,
        principal_id: row.try_get("principal_id")?,
        event_type: row.try_get("event_type")?,
        object_type: row.try_get("object_type")?,
        object_id: row.try_get("object_id")?,
        detail_json: row.try_get("detail_json")?,
        created_at: row.try_get("created_at")?,
    })
}
fn one(count: u64) -> Result<(), NoteError> {
    if count == 1 {
        Ok(())
    } else {
        Err(NoteError::WriteNotApplied)
    }
}

impl PgNoteStore {
    /// Trusted local socket and installed schema; never a public admission boundary.
    pub fn local(socket: &Path, port: u16, user: &str, database: &str) -> Result<Self, NoteError> {
        Self::local_bounded(socket, port, user, database, PoolLimits::default())
    }

    pub fn local_bounded(
        socket: &Path,
        port: u16,
        user: &str,
        database: &str,
        limits: PoolLimits,
    ) -> Result<Self, NoteError> {
        Ok(Self {
            pool: local_pool(socket, port, user, database, limits)?,
        })
    }

    async fn connect(&self) -> Result<Lease, NoteError> {
        Ok(Lease::new(self.pool.get().await.map_err(NoteError::Pool)?))
    }

    /// No implicit retries, no upsert, no replay on duplicate identity.
    pub async fn execute(&self, operation: &PreparedNote) -> Result<Note, NoteError> {
        let note = &operation.note;
        let audit = &operation.audit;
        let mut lease = self.connect().await?;
        let tx = lease
            .client()
            .build_transaction()
            .isolation_level(IsolationLevel::ReadCommitted)
            .start()
            .await
            .map_err(|e| db("begin", e))?;
        if let Err(cause) = write(&tx, note, audit).await {
            return match tx.rollback().await {
                Ok(()) => {
                    lease.reusable();
                    Err(cause)
                }
                Err(rollback) => Err(NoteError::RollbackUnknown {
                    cause: Box::new(cause),
                    rollback,
                }),
            };
        }
        tx.commit()
            .await
            .map_err(|source| NoteError::CommitUnknown {
                note_id: note.note_id.clone(),
                source,
            })?;
        lease.reusable();
        Ok(note.clone())
    }

    pub async fn list(&self, principal: &str) -> Result<Vec<Note>, NoteError> {
        if principal.contains('\0') {
            return Err(NoteError::Unrepresentable);
        }
        let mut lease = self.connect().await?;
        let rows=lease.client().query(
            "SELECT note_id,principal_id,content,state,created_at,published_at FROM canary_notes WHERE principal_id=$1 ORDER BY created_at DESC,note_id ASC",
            &[&principal],
        ).await.map_err(|e|db("list",e))?;
        let result = rows.iter().map(note_from_row).collect();
        lease.reusable();
        result
    }

    /// A coherent, read-only snapshot of both operation coordinates.
    /// Missing rows are never translated into a failure or permission to retry.
    pub async fn observe(&self, operation: &PreparedNote) -> Result<NoteObservation, NoteError> {
        let mut lease = self.connect().await?;
        let tx = lease
            .client()
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()
            .await
            .map_err(|e| db("observe-begin", e))?;
        let row=tx.query_opt("SELECT note_id,principal_id,content,state,created_at,published_at FROM canary_notes WHERE note_id=$1",
            &[&operation.note.note_id]).await.map_err(|e|db("observe-note",e))?;
        let audits=tx.query("SELECT event_id,principal_id,event_type,object_type,object_id,detail_json,created_at FROM audit_events WHERE event_id=$1 OR (event_type='canary.note.created' AND object_type='canary-note' AND object_id=$2) LIMIT 2",
            &[&operation.audit.event_id,&operation.note.note_id]).await.map_err(|e|db("observe-audit",e))?;
        let result = if row.is_none() && audits.is_empty() {
            NoteObservation::Unobserved
        } else if row.as_ref().map(note_from_row).transpose()?.as_ref() == Some(&operation.note)
            && audits.len() == 1
            && audit_from_row(&audits[0]).map_err(|e| db("observe-decode", e))? == operation.audit
        {
            NoteObservation::Exact(operation.note.clone())
        } else {
            NoteObservation::Mismatch
        };
        tx.rollback().await.map_err(|e| db("observe-close", e))?;
        lease.reusable();
        Ok(result)
    }
}

async fn write(tx: &Transaction<'_>, note: &Note, audit: &Audit) -> Result<(), NoteError> {
    one(tx.execute(
        "INSERT INTO canary_notes(note_id,principal_id,content,state,created_at,published_at) VALUES ($1,$2,$3,'DRAFT',$4,NULL)",
        &[&note.note_id,&note.principal_id,&note.content,&note.created_at],
    ).await.map_err(|e| db("write-note",e))?)?;
    one(tx.execute(
        "INSERT INTO audit_events(event_id,principal_id,event_type,object_type,object_id,detail_json,created_at) VALUES ($1,$2,$3,$4,$5,$6,$7)",
        &[&audit.event_id,&audit.principal_id,&audit.event_type,&audit.object_type,&audit.object_id,&audit.detail_json,&audit.created_at],
    ).await.map_err(|e| db("write-audit",e))?)?;
    // Force deferred constraint triggers before the last exact readback.
    tx.batch_execute("SET CONSTRAINTS ALL IMMEDIATE")
        .await
        .map_err(|e| db("deferred-constraints", e))?;
    let rows=tx.query(
        "SELECT event_id,principal_id,event_type,object_type,object_id,detail_json,created_at FROM audit_events WHERE event_type='canary.note.created' AND object_type='canary-note' AND object_id=$1 LIMIT 2",
        &[&note.note_id],
    ).await.map_err(|e| db("read-audit",e))?;
    if rows.len() != 1 || audit_from_row(&rows[0]).map_err(|e| db("decode-audit", e))? != *audit {
        return Err(NoteError::AuditMismatch);
    }
    let row=tx.query_opt(
        "SELECT note_id,principal_id,content,state,created_at,published_at FROM canary_notes WHERE note_id=$1 AND principal_id=$2",
        &[&note.note_id,&note.principal_id],
    ).await.map_err(|e| db("read-note",e))?;
    if row.as_ref().map(note_from_row).transpose()?.as_ref() != Some(note) {
        return Err(NoteError::BusinessMismatch);
    }
    Ok(())
}
