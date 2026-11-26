//! Read-side migration adapter. The existing caller owns the transaction.
//! No schema activation, compact writer or alternate persistence authority.
use super::{canonical_digest, try_claim_receipt, validate_receipt_replay, WorkError};
use serde_json::Value;
use tokio_postgres::{types::Json, Transaction};

pub(super) enum Request<'a> {
    Create {
        work_ref: &'a str,
        work_kind: &'a str,
    },
    Commit {
        work_ref: &'a str,
        revision: i64,
        snapshot_digest: &'a str,
        actor_ref: &'a str,
        state: &'a str,
    },
}

fn invalid(message: &str) -> WorkError {
    WorkError::Integrity(message.into())
}

impl Request<'_> {
    fn work_ref(&self) -> &str {
        match self {
            Self::Create { work_ref, .. } | Self::Commit { work_ref, .. } => work_ref,
        }
    }

    fn matches(&self, envelope: &Value, revision: i64) -> bool {
        match self {
            Self::Create { work_kind, .. } => envelope["workKind"].as_str() == Some(work_kind),
            Self::Commit {
                revision: expected,
                snapshot_digest,
                actor_ref,
                state,
                ..
            } => {
                *expected == revision
                    && envelope["snapshotDigest"].as_str() == Some(snapshot_digest)
                    && envelope["writerActorRef"].as_str() == Some(actor_ref)
                    && envelope["state"].as_str() == Some(state)
            }
        }
    }
}

pub(super) async fn claim(
    tx: &Transaction<'_>,
    client_request_id: &str,
    operation: &str,
    request_digest: &str,
    request: Request<'_>,
) -> Result<Option<Value>, WorkError> {
    if try_claim_receipt(tx, client_request_id, operation, request_digest).await? {
        return Ok(None);
    }
    // Whole-row projection preserves the older-schema rollback reader.
    let row = tx.query_opt(
        "SELECT r.*, (SELECT schema_version FROM host_v2_schema WHERE singleton) AS receipt_schema \
         FROM command_receipts r WHERE r.client_request_id=$1",
        &[&client_request_id],
    ).await?.ok_or_else(|| invalid("idempotency claim disappeared"))?;
    let replay = validate_receipt_replay(&row, operation, request_digest)?;
    let schema: i32 = row.try_get("receipt_schema")?;
    let has_ref = row
        .columns()
        .iter()
        .any(|column| column.name() == "receipt_work_ref");
    let has_revision = row
        .columns()
        .iter()
        .any(|column| column.name() == "receipt_work_revision");
    if (schema >= 17 && !(has_ref && has_revision)) || (schema < 17 && (has_ref || has_revision)) {
        return Err(invalid("native Work receipt root schema differs"));
    }
    let (native_ref, native_revision): (Option<String>, Option<i64>) = if schema >= 17 {
        (
            row.try_get("receipt_work_ref")?,
            row.try_get("receipt_work_revision")?,
        )
    } else {
        (None, None)
    };
    if replay["kind"] == "ordivon.host-work" {
        if native_ref.is_some() || native_revision.is_some() {
            return Err(invalid(
                "invalid native Work receipt root for legacy response",
            ));
        }
        return Ok(Some(replay));
    }
    let (Some(native_ref), Some(revision)) = (native_ref, native_revision) else {
        return Err(invalid("native Work receipt root reference missing"));
    };
    if native_ref != request.work_ref() || replay["kind"] != "ordivon.host-work-receipt-ref-v1" {
        return Err(invalid(
            "native Work receipt root reference differs from request",
        ));
    }
    let envelope = &replay["envelope"];
    if !envelope.is_object()
        || envelope["kind"] != "ordivon.host-work"
        || envelope["schemaVersion"].as_i64() != Some(1)
        || envelope["workRef"].as_str() != Some(native_ref.as_str())
        || envelope["revision"].as_i64() != Some(revision)
        || !(1..=9_007_199_254_740_991).contains(&revision)
        || envelope["snapshotDigest"].as_str().is_none()
        || envelope["writerActorRef"].as_str().is_none()
        || envelope["admission"] != "existing"
        || envelope.get("snapshot").is_some()
        || !request.matches(envelope, revision)
    {
        return Err(invalid(
            "Work receipt reference differs from committed request",
        ));
    }
    let target = tx
        .query_opt(
            "SELECT snapshot_digest,payload,writer_actor_ref FROM work_snapshots \
         WHERE work_ref=$1 AND revision=$2",
            &[&native_ref, &revision],
        )
        .await?
        .ok_or_else(|| invalid("committed Work receipt target is missing"))?;
    let digest: String = target.try_get("snapshot_digest")?;
    let writer: String = target.try_get("writer_actor_ref")?;
    let payload: Value = target.try_get::<_, Json<Value>>("payload")?.0;
    if envelope["snapshotDigest"].as_str() != Some(digest.as_str())
        || envelope["writerActorRef"].as_str() != Some(writer.as_str())
        || !payload.is_object()
        || canonical_digest(&payload)? != digest
    {
        return Err(invalid(
            "committed Work receipt target is missing or changed",
        ));
    }
    let mut result = envelope.clone();
    result["snapshot"] = payload;
    if replay["responseDigest"].as_str() != Some(canonical_digest(&result)?.as_str()) {
        return Err(invalid("committed Work receipt response digest differs"));
    }
    Ok(Some(result))
}
