use serde_json::Value;
use sqlx::{Postgres, Row, Transaction};

use super::{db_err, enum_str, PostgresKernelStore};
use crate::{verify_chain, verify_event, LedgerError, LedgerEvent, GENESIS_DIGEST};

impl PostgresKernelStore {
    pub async fn append_event(&self, event: &LedgerEvent) -> Result<(), LedgerError> {
        verify_event(event)?;
        let mut tx = self.pool.begin().await.map_err(db_err)?;
        sqlx::query("LOCK TABLE kernel_ledger_events IN EXCLUSIVE MODE")
            .execute(&mut *tx)
            .await
            .map_err(db_err)?;
        let current = sqlx::query(
            "SELECT event_seq, event_hash FROM kernel_ledger_events ORDER BY event_seq DESC LIMIT 1",
        )
        .fetch_optional(&mut *tx)
        .await
        .map_err(db_err)?;
        let (expected_seq, expected_prev) = if let Some(row) = current {
            (
                row.get::<i64, _>("event_seq") as u64 + 1,
                row.get::<String, _>("event_hash"),
            )
        } else {
            (1, GENESIS_DIGEST.to_string())
        };
        if event.event_seq != expected_seq {
            return Err(LedgerError::NonAppendSequence {
                expected: expected_seq,
                actual: event.event_seq,
            });
        }
        if event.prev_hash != expected_prev {
            return Err(LedgerError::PreviousHashMismatch {
                expected: expected_prev,
                actual: event.prev_hash.clone(),
            });
        }
        insert_ledger_event_tx(&mut tx, event).await?;
        tx.commit().await.map_err(db_err)?;
        Ok(())
    }

    pub async fn read_events(&self) -> Result<Vec<LedgerEvent>, LedgerError> {
        let rows = sqlx::query(
            "SELECT event_seq, event_id, event_type, origin, created_at, object_type, object_id,
                        payload, payload_hash, prev_hash, event_hash
                 FROM kernel_ledger_events ORDER BY event_seq ASC",
        )
        .fetch_all(&self.pool)
        .await
        .map_err(db_err)?;
        let mut events = Vec::new();
        for row in rows {
            let origin: String = row.get("origin");
            events.push(LedgerEvent {
                event_seq: row.get::<i64, _>("event_seq") as u64,
                event_id: row.get("event_id"),
                event_type: row.get("event_type"),
                origin: serde_json::from_value(Value::String(origin))
                    .map_err(|err| LedgerError::Json(err.to_string()))?,
                created_at: row.get("created_at"),
                object_type: row.get("object_type"),
                object_id: row.get("object_id"),
                payload: row.get::<sqlx::types::Json<Value>, _>("payload").0,
                payload_hash: row.get("payload_hash"),
                prev_hash: row.get("prev_hash"),
                event_hash: row.get("event_hash"),
            });
        }
        verify_chain(&events)?;
        Ok(events)
    }
}

pub(super) async fn insert_ledger_event_tx(
    tx: &mut Transaction<'_, Postgres>,
    event: &LedgerEvent,
) -> Result<(), LedgerError> {
    verify_event(event)?;
    sqlx::query("SELECT kernel_append_ledger_event($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)")
        .bind(event.event_seq as i64)
        .bind(&event.event_id)
        .bind(&event.event_type)
        .bind(enum_str(&event.origin))
        .bind(&event.created_at)
        .bind(&event.object_type)
        .bind(&event.object_id)
        .bind(sqlx::types::Json(&event.payload))
        .bind(&event.payload_hash)
        .bind(&event.prev_hash)
        .bind(&event.event_hash)
        .execute(&mut **tx)
        .await
        .map_err(db_err)?;
    Ok(())
}
