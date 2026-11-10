//! Rust implementation of Host Attention over the existing PostgreSQL schema 13.
//! No inbox, event bus, second change log, or background scheduler is introduced.
//! Each public operation runs inside one transaction; read projections use one RR snapshot.
//!
//! The Python Host remains the production owner until MCP+PG consumer parity is qualified.
use chrono::{DateTime, FixedOffset, SecondsFormat, Utc};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;
use tokio_postgres::{types::Json, Client, IsolationLevel, Row, Transaction};

pub const MIN_COLLECTION_BYTES: usize = 16_384;
pub const MAX_COLLECTION_BYTES: usize = 4_194_304;
pub const DEFAULT_COLLECTION_BYTES: usize = 262_144;
const DELTA_SQL: &str = include_str!("attention_delta.sql");

const ATTENTION_BOUNDARY: &str =
    "rebuildable actor-scoped navigation over owner rows; not inbox truth, priority, assignment, or authority";
const REENTRY_BOUNDARY: &str =
    "rebuildable re-entry navigation only; no score, priority, assignment, scheduling, or foreign truth ownership";

#[derive(Debug, Error)]
pub enum AttentionError {
    #[error("INVALID_ARGUMENT: {0}")]
    Invalid(String),
    #[error("CONFLICT: {0}")]
    Conflict(String),
    #[error("NOT_FOUND: {0}")]
    NotFound(String),
    #[error("INTEGRITY_ERROR: {0}")]
    Integrity(String),
    #[error(transparent)]
    Database(#[from] tokio_postgres::Error),
}

pub type Result<T> = std::result::Result<T, AttentionError>;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum TargetKind {
    Work,
    Space,
    Topic,
}
impl TargetKind {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Work => "work",
            Self::Space => "space",
            Self::Topic => "topic",
        }
    }
    fn table(self) -> (&'static str, &'static str) {
        match self {
            Self::Work => ("works", "work_ref"),
            Self::Space => ("spaces", "space_ref"),
            Self::Topic => ("topics", "topic_ref"),
        }
    }
}

/// Use the same RFC 8785 serializer as the Work port. Check the I-JSON integer
/// domain first: serde_json_canonicalizer may round larger integers as f64.
pub(crate) fn canonical(value: &Value) -> Result<Vec<u8>> {
    fn check(value: &Value) -> Result<()> {
        const MAX_SAFE: i64 = 9_007_199_254_740_991;
        match value {
            Value::Number(n) => {
                if n.as_i64().is_some_and(|i| i.abs_diff(0) > MAX_SAFE as u64)
                    || n.as_u64().is_some_and(|i| i > MAX_SAFE as u64)
                {
                    return Err(AttentionError::Invalid(
                        "integer exceeds Python RFC 8785 safe integer domain".into(),
                    ));
                }
            }
            Value::Object(o) => {
                for v in o.values() {
                    check(v)?;
                }
            }
            Value::Array(a) => {
                for v in a {
                    check(v)?;
                }
            }
            _ => {}
        }
        Ok(())
    }
    check(value)?;
    serde_json_canonicalizer::to_vec(value)
        .map_err(|e| AttentionError::Invalid(format!("invalid canonical JSON: {e}")))
}

pub(crate) fn digest(value: &Value) -> Result<String> {
    Ok(format!(
        "sha256:{}",
        hex::encode(Sha256::digest(canonical(value)?))
    ))
}

pub(crate) fn exact_time(utc: DateTime<Utc>, offset_secs: i32) -> Result<String> {
    let offset = FixedOffset::east_opt(offset_secs)
        .ok_or_else(|| AttentionError::Integrity("invalid PG timezone offset".into()))?;
    let local = utc.with_timezone(&offset);
    Ok(local.to_rfc3339_opts(
        if local.timestamp_subsec_micros() == 0 {
            SecondsFormat::Secs
        } else {
            SecondsFormat::Micros
        },
        false,
    ))
}

fn validate_limit(limit: i64, max_bytes: usize) -> Result<()> {
    if !(1..=500).contains(&limit) {
        return Err(AttentionError::Invalid("limit must be in [1,500]".into()));
    }
    if !(MIN_COLLECTION_BYTES..=MAX_COLLECTION_BYTES).contains(&max_bytes) {
        return Err(AttentionError::Invalid(format!(
            "max_bytes must be in [{MIN_COLLECTION_BYTES},{MAX_COLLECTION_BYTES}]"
        )));
    }
    Ok(())
}
fn validate_cursor(cursor: i64, field: &str) -> Result<()> {
    if cursor < 0 {
        return Err(AttentionError::Invalid(format!(
            "{field} must be non-negative integer"
        )));
    }
    if cursor > 9_007_199_254_740_991 {
        return Err(AttentionError::Invalid(format!(
            "{field} exceeds RFC 8785 exact integer range"
        )));
    }
    Ok(())
}
pub(crate) async fn require_actor(tx: &Transaction<'_>, actor: &str) -> Result<()> {
    if tx
        .query_opt("SELECT 1 FROM actor_refs WHERE actor_ref=$1", &[&actor])
        .await?
        .is_none()
    {
        return Err(AttentionError::NotFound(format!("actor_ref {actor}")));
    }
    Ok(())
}
async fn require_target(tx: &Transaction<'_>, kind: TargetKind, target: &str) -> Result<()> {
    let (table, column) = kind.table();
    // Both SQL identifiers come from the closed enum, never from the caller.
    if tx
        .query_opt(
            &format!("SELECT 1 FROM {table} WHERE {column}=$1"),
            &[&target],
        )
        .await?
        .is_none()
    {
        return Err(AttentionError::NotFound(format!(
            "{} {target}",
            kind.as_str()
        )));
    }
    Ok(())
}

pub(crate) async fn claim_receipt(
    tx: &Transaction<'_>,
    request_id: &str,
    operation: &str,
    request_digest: &str,
) -> Result<Option<Value>> {
    let inserted = tx.query_opt(
        "INSERT INTO command_receipts(client_request_id,operation,request_digest,response) \
         VALUES ($1,$2,$3,NULL) ON CONFLICT (client_request_id) DO NOTHING RETURNING client_request_id",
        &[&request_id, &operation, &request_digest],
    ).await?;
    if inserted.is_some() {
        return Ok(None);
    }
    let row = tx.query_opt(
        "SELECT operation,request_digest,response FROM command_receipts WHERE client_request_id=$1",
        &[&request_id],
    ).await?.ok_or_else(|| AttentionError::Integrity("idempotency claim disappeared".into()))?;
    let prior_operation: String = row.get("operation");
    let prior_digest: String = row.get("request_digest");
    if prior_operation != operation || prior_digest != request_digest {
        return Err(AttentionError::Conflict(
            "client_request_id was already used for different content".into(),
        ));
    }
    let response: Option<Json<Value>> = row.try_get("response")?;
    let mut response = response
        .ok_or_else(|| {
            AttentionError::Integrity("committed idempotency claim is missing its response".into())
        })?
        .0;
    if !response.is_object() {
        return Err(AttentionError::Integrity(
            "idempotency response is not JSON object".into(),
        ));
    }
    response["admission"] = Value::String("existing".into());
    Ok(Some(response))
}
pub(crate) async fn record_receipt(
    tx: &Transaction<'_>,
    request_id: &str,
    operation: &str,
    request_digest: &str,
    response: &Value,
) -> Result<()> {
    if tx
        .query_opt(
            "UPDATE command_receipts SET response=$1 \
         WHERE client_request_id=$2 AND operation=$3 AND request_digest=$4 \
           AND response IS NULL RETURNING client_request_id",
            &[&Json(response), &request_id, &operation, &request_digest],
        )
        .await?
        .is_none()
    {
        return Err(AttentionError::Integrity(
            "idempotency claim could not be finalized".into(),
        ));
    }
    Ok(())
}

pub async fn follow(
    client: &mut Client,
    actor_ref: &str,
    target_kind: TargetKind,
    target_ref: &str,
    _client_request_id: &str,
) -> Result<Value> {
    // Target-state semantics deliberately ignore request id. An OLD follow replay
    // after an intervening unfollow is a NEW desired-state follow, not a receipt replay.
    let tx = client.transaction().await?;
    require_actor(&tx, actor_ref).await?;
    require_target(&tx, target_kind, target_ref).await?;
    let row = tx
        .query_opt(
            "INSERT INTO subscriptions(actor_ref,target_kind,target_ref) VALUES ($1,$2,$3) \
         ON CONFLICT DO NOTHING RETURNING actor_ref,target_kind,target_ref,created_at,\
         EXTRACT(TIMEZONE FROM created_at)::integer AS tz,change_sequence",
            &[&actor_ref, &target_kind.as_str(), &target_ref],
        )
        .await?;
    let (row, admission) = match row {
        Some(row) => (row, "committed"),
        None => {
            let row = tx
                .query_opt(
                    "SELECT actor_ref,target_kind,target_ref,created_at,\
                 EXTRACT(TIMEZONE FROM created_at)::integer AS tz,change_sequence \
                 FROM subscriptions WHERE actor_ref=$1 AND target_kind=$2 AND target_ref=$3",
                    &[&actor_ref, &target_kind.as_str(), &target_ref],
                )
                .await?
                .ok_or_else(|| AttentionError::Integrity("subscription disappeared".into()))?;
            (row, "existing")
        }
    };
    let created_at: DateTime<Utc> = row.try_get("created_at")?;
    let tz: i32 = row.try_get("tz")?;
    let result = json!({
        "schemaVersion":1, "kind":"ordivon.host-subscription",
        "admission":admission, "actorRef":row.get::<_, String>("actor_ref"),
        "targetKind":row.get::<_, String>("target_kind"),
        "targetRef":row.get::<_, String>("target_ref"),
        "createdAt":exact_time(created_at,tz)?,
        "changeSequence":row.get::<_, i64>("change_sequence"),
        "truthBoundary":"attention routing preference only; not assignment, priority, ownership, or authorization"
    });
    tx.commit().await?;
    Ok(result)
}

pub async fn unfollow(
    client: &mut Client,
    actor_ref: &str,
    target_kind: TargetKind,
    target_ref: &str,
    _client_request_id: &str,
) -> Result<Value> {
    let tx = client.transaction().await?;
    require_actor(&tx, actor_ref).await?;
    let deleted = tx
        .query_opt(
            "DELETE FROM subscriptions WHERE actor_ref=$1 AND target_kind=$2 AND target_ref=$3 \
         RETURNING actor_ref",
            &[&actor_ref, &target_kind.as_str(), &target_ref],
        )
        .await?
        .is_some();
    tx.commit().await?;
    Ok(json!({
        "schemaVersion":1, "kind":"ordivon.host-subscription-unfollow",
        "admission": if deleted {"committed"} else {"existing"},
        "actorRef":actor_ref, "targetKind":target_kind.as_str(), "targetRef":target_ref,
        "truthBoundary":"attention routing preference only"
    }))
}

pub async fn ack(
    client: &mut Client,
    actor_ref: &str,
    cursor: i64,
    request_id: &str,
) -> Result<Value> {
    validate_cursor(cursor, "cursor")?;
    let request = json!({"operation":"attention.ack","actorRef":actor_ref,"cursor":cursor});
    let request_digest = digest(&request)?;
    let tx = client.transaction().await?;
    if let Some(replay) = claim_receipt(&tx, request_id, "attention.ack", &request_digest).await? {
        tx.commit().await?;
        return Ok(replay);
    }
    require_actor(&tx, actor_ref).await?;
    let row = tx
        .query_one("SELECT value FROM swf_change_clock WHERE singleton", &[])
        .await?;
    let high: i64 = row.get("value");
    if cursor > high {
        return Err(AttentionError::Conflict(
            "attention cursor cannot acknowledge beyond current change horizon".into(),
        ));
    }
    let current = tx
        .query_opt(
            "SELECT cursor FROM attention_cursors WHERE actor_ref=$1 FOR UPDATE",
            &[&actor_ref],
        )
        .await?;
    let previous: i64 = current.map(|r| r.get("cursor")).unwrap_or(0);
    if cursor < previous {
        return Err(AttentionError::Conflict(
            "attention cursor cannot move backwards".into(),
        ));
    }
    let updated = tx
        .query_opt(
            "INSERT INTO attention_cursors(actor_ref,cursor) VALUES ($1,$2) \
         ON CONFLICT (actor_ref) DO UPDATE SET cursor=EXCLUDED.cursor,updated_at=clock_timestamp() \
         WHERE attention_cursors.cursor <= EXCLUDED.cursor RETURNING cursor",
            &[&actor_ref, &cursor],
        )
        .await?;
    if updated.is_none() {
        return Err(AttentionError::Conflict(
            "attention cursor cannot move backwards".into(),
        ));
    }
    let result = json!({
        "schemaVersion":1, "kind":"ordivon.host-attention-ack",
        "actorRef":actor_ref, "previousCursor":previous, "cursor":cursor,
        "truthBoundary":"navigation acknowledgement only; not evidence that message content was semantically accepted"
    });
    record_receipt(&tx, request_id, "attention.ack", &request_digest, &result).await?;
    tx.commit().await?;
    Ok(result)
}

fn reasons(row: &Row) -> Vec<&'static str> {
    let columns = [
        "followed_work",
        "followed_space",
        "followed_topic",
        "mentioned",
        "replied_to_me",
        "own_participation",
        "own_coordination_intent",
    ];
    let mut result: Vec<&str> = columns
        .iter()
        .copied()
        .filter(|column| row.get::<_, bool>(*column))
        .collect();
    result.sort_unstable();
    result
}
fn event_json(row: &Row) -> Value {
    json!({
        "changeSequence":row.get::<_, i64>("change_sequence"),
        "eventKind":row.get::<_, String>("event_kind"),
        "sourceRef":row.get::<_, String>("source_ref"),
        "contextRef":row.get::<_, String>("context_ref"),
        "reasons":reasons(row),
        "navigationKind":row.get::<_, String>("navigation_kind"),
        "navigationRef":row.get::<_, String>("navigation_ref")
    })
}
fn delta_envelope(actor: &str, after: i64, high: i64, events: Vec<Value>, has_more: bool) -> Value {
    let next = if has_more {
        events
            .last()
            .and_then(|v| v["changeSequence"].as_i64())
            .unwrap_or(after)
    } else {
        high
    };
    json!({
        "schemaVersion":1, "kind":"ordivon.host-attention-delta-r1",
        "actorRef":actor,"afterSequence":after,"snapshotHighSequence":high,
        "events":events,"hasMore":has_more,"nextAfterSequence":next,
        "rankingApplied":false,"truthBoundary":ATTENTION_BOUNDARY
    })
}
async fn delta_in_tx(
    tx: &Transaction<'_>,
    actor: &str,
    after: i64,
    limit: i64,
    max_bytes: usize,
) -> Result<Value> {
    let high: i64 = tx
        .query_one("SELECT value FROM swf_change_clock WHERE singleton", &[])
        .await?
        .get("value");
    if after > high {
        return Err(AttentionError::Conflict(
            "after_sequence cannot exceed current change horizon".into(),
        ));
    }
    if after == high {
        return Ok(delta_envelope(actor, after, high, vec![], false));
    }
    let raw = tx
        .query(DELTA_SQL, &[&actor, &after, &high, &(limit + 1)])
        .await?;
    let sql_more = raw.len() > limit as usize;
    let candidates: Vec<Value> = raw.iter().take(limit as usize).map(event_json).collect();
    let mut events = Vec::with_capacity(candidates.len());
    let mut byte_more = false;
    for event in candidates {
        let mut candidate = events.clone();
        candidate.push(event.clone());
        let wire = delta_envelope(actor, after, high, candidate, true);
        if canonical(&wire)?.len() > max_bytes {
            if events.is_empty() {
                return Err(AttentionError::Invalid(
                    "max_bytes cannot fit one legal item plus response envelope".into(),
                ));
            }
            byte_more = true;
            break;
        }
        events.push(event);
    }
    Ok(delta_envelope(
        actor,
        after,
        high,
        events,
        sql_more || byte_more,
    ))
}

pub async fn delta(
    client: &mut Client,
    actor: &str,
    after: i64,
    limit: i64,
    max_bytes: usize,
) -> Result<Value> {
    validate_cursor(after, "after_sequence")?;
    validate_limit(limit, max_bytes)?;
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    require_actor(&tx, actor).await?;
    let result = delta_in_tx(&tx, actor, after, limit, max_bytes).await?;
    tx.commit().await?;
    Ok(result)
}

pub async fn get(client: &mut Client, actor: &str, limit: i64, max_bytes: usize) -> Result<Value> {
    validate_limit(limit, max_bytes)?;
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    require_actor(&tx, actor).await?;
    let current = tx
        .query_opt(
            "SELECT cursor FROM attention_cursors WHERE actor_ref=$1",
            &[&actor],
        )
        .await?
        .map(|r| r.get::<_, i64>("cursor"))
        .unwrap_or(0);
    let result = delta_in_tx(&tx, actor, current, limit, max_bytes).await?;
    tx.commit().await?;
    Ok(result)
}

#[derive(Clone, Copy)]
struct ReentryWindow<'a> {
    actor: &'a str,
    after: i64,
    high: i64,
    delta_more: bool,
    delta_next: i64,
}
fn group_reentry(
    window: ReentryWindow<'_>,
    events: &[Value],
    count: usize,
    cursors: &BTreeMap<String, i64>,
) -> Value {
    let prefix = &events[..count];
    let mut keys: Vec<(String, String)> = Vec::new();
    let mut groups: Vec<Value> = Vec::new();
    for event in prefix {
        let key = (
            event["navigationKind"]
                .as_str()
                .unwrap_or_default()
                .to_string(),
            event["navigationRef"]
                .as_str()
                .unwrap_or_default()
                .to_string(),
        );
        let pos = keys.iter().position(|k| *k == key);
        let index = match pos {
            Some(i) => i,
            None => {
                let mut item = json!({
                    "navigationKind":key.0,"navigationRef":key.1,
                    "latestChangeSequence":event["changeSequence"],"eventKinds":[],
                    "reasons":[],"eventCount":0
                });
                if key.0 == "topic" {
                    item["resumeAfterSequence"] = json!(cursors.get(&key.1).copied().unwrap_or(0));
                }
                keys.push(key);
                groups.push(item);
                groups.len() - 1
            }
        };
        let item = &mut groups[index];
        let current = item["latestChangeSequence"].as_i64().unwrap_or(0);
        let sequence = event["changeSequence"].as_i64().unwrap_or(0);
        item["latestChangeSequence"] = json!(current.max(sequence));
        item["eventCount"] = json!(item["eventCount"].as_i64().unwrap_or(0) + 1);
        {
            let field = "eventKinds";
            let value = &event["eventKind"];
            let mut unique: BTreeSet<String> = item[field]
                .as_array()
                .into_iter()
                .flatten()
                .filter_map(Value::as_str)
                .map(str::to_owned)
                .collect();
            if let Some(s) = value.as_str() {
                unique.insert(s.to_string());
            }
            item[field] = json!(unique.into_iter().collect::<Vec<_>>());
        }
        let mut unique: BTreeSet<String> = item["reasons"]
            .as_array()
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
            .map(str::to_owned)
            .collect();
        for reason in event["reasons"].as_array().into_iter().flatten() {
            if let Some(s) = reason.as_str() {
                unique.insert(s.to_string());
            }
        }
        item["reasons"] = json!(unique.into_iter().collect::<Vec<_>>());
    }
    let trimmed = count < events.len();
    let has_more = trimmed || window.delta_more;
    let next = if trimmed {
        prefix
            .last()
            .and_then(|v| v["changeSequence"].as_i64())
            .unwrap_or(window.after)
    } else {
        window.delta_next
    };
    json!({
        "schemaVersion":1,"kind":"ordivon.host-attention-reentry-r1",
        "actorRef":window.actor,"afterSequence":window.after,"snapshotHighSequence":window.high,
        "items":groups,"rawEventCount":count,"hasMore":has_more,
        "nextAfterSequence":next,"rankingApplied":false,"truthBoundary":REENTRY_BOUNDARY
    })
}

/// Cursor, delta, and topic resume positions must be read from ONE MVCC snapshot.
/// Pagination across separate MCP calls has no persistent snapshot lease.
pub async fn reentry(
    client: &mut Client,
    actor: &str,
    after: Option<i64>,
    limit: i64,
    max_bytes: usize,
) -> Result<Value> {
    validate_limit(limit, max_bytes)?;
    if let Some(cursor) = after {
        validate_cursor(cursor, "after_sequence")?;
    }
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    require_actor(&tx, actor).await?;
    let effective_after = match after {
        Some(v) => v,
        None => tx
            .query_opt(
                "SELECT cursor FROM attention_cursors WHERE actor_ref=$1",
                &[&actor],
            )
            .await?
            .map(|r| r.get::<_, i64>("cursor"))
            .unwrap_or(0),
    };
    let delta = delta_in_tx(&tx, actor, effective_after, limit, max_bytes).await?;
    let events = delta["events"]
        .as_array()
        .ok_or_else(|| AttentionError::Integrity("delta events are not an array".into()))?;
    let topic_refs: Vec<String> = events
        .iter()
        .filter(|v| v["navigationKind"] == "topic")
        .filter_map(|v| v["navigationRef"].as_str().map(str::to_owned))
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let mut cursors = BTreeMap::new();
    if !topic_refs.is_empty() {
        for row in tx
            .query(
                "SELECT topic_ref,cursor FROM topic_consumption_cursors \
             WHERE actor_ref=$1 AND topic_ref=ANY($2)",
                &[&actor, &topic_refs],
            )
            .await?
        {
            cursors.insert(
                row.get::<_, String>("topic_ref"),
                row.get::<_, i64>("cursor"),
            );
        }
    }
    let high = delta["snapshotHighSequence"]
        .as_i64()
        .unwrap_or(effective_after);
    let more = delta["hasMore"].as_bool().unwrap_or(false);
    let next = delta["nextAfterSequence"].as_i64().unwrap_or(high);
    let window = ReentryWindow {
        actor,
        after: effective_after,
        high,
        delta_more: more,
        delta_next: next,
    };
    let all = group_reentry(window, events, events.len(), &cursors);
    let result = if canonical(&all)?.len() <= max_bytes {
        all
    } else {
        // A monotone prefix-size search; no second Attention SQL execution.
        let mut lo = 1usize;
        let mut hi = events.len().saturating_sub(1);
        let mut best = None;
        while lo <= hi {
            let mid = lo + (hi - lo) / 2;
            let candidate = group_reentry(window, events, mid, &cursors);
            if canonical(&candidate)?.len() <= max_bytes {
                best = Some(candidate);
                lo = mid + 1;
            } else {
                hi = mid.saturating_sub(1);
            }
        }
        best.ok_or_else(|| {
            AttentionError::Invalid("max_bytes cannot fit one re-entry navigation item".into())
        })?
    };
    tx.commit().await?;
    Ok(result)
}

pub async fn list_subscriptions(
    client: &mut Client,
    actor: &str,
    target_kind: Option<TargetKind>,
    after: Option<(&str, &str)>,
    limit: i64,
    max_bytes: usize,
) -> Result<Value> {
    validate_limit(limit, max_bytes)?;
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    require_actor(&tx, actor).await?;
    let target = target_kind.map(TargetKind::as_str);
    let (after_kind, after_ref) = after.map_or((None, None), |(k, v)| (Some(k), Some(v)));
    let rows = tx
        .query(
            "SELECT target_kind,target_ref,created_at, \
         EXTRACT(TIMEZONE FROM created_at)::integer AS tz,change_sequence \
         FROM subscriptions WHERE actor_ref=$1 \
         AND ($2::text IS NULL OR target_kind=$2) \
         AND ($3::text IS NULL OR (target_kind,target_ref)>($3,$4)) \
         ORDER BY target_kind,target_ref LIMIT $5",
            &[&actor, &target, &after_kind, &after_ref, &(limit + 1)],
        )
        .await?;
    let sql_more = rows.len() > limit as usize;
    let mut candidates = Vec::new();
    for row in rows.iter().take(limit as usize) {
        candidates.push(json!({
            "targetKind":row.get::<_,String>("target_kind"),
            "targetRef":row.get::<_,String>("target_ref"),
            "createdAt":exact_time(row.get("created_at"),row.get("tz"))?,
            "changeSequence":row.get::<_,i64>("change_sequence")
        }));
    }
    let envelope = |page: Vec<Value>, more: bool| {
        let next_kind = if more {
            page.last().and_then(|v| v["targetKind"].as_str())
        } else {
            None
        };
        let next_ref = if more {
            page.last().and_then(|v| v["targetRef"].as_str())
        } else {
            None
        };
        json!({
            "schemaVersion":1,"kind":"ordivon.host-subscription-list",
            "actorRef":actor,"subscriptions":page,"hasMore":more,"truncated":more,
            "nextAfterTargetKind":next_kind,"nextAfterTargetRef":next_ref,
            "rankingApplied":false,
            "truthBoundary":"actor attention-routing preferences only; not assignment, priority, ownership, or authorization"
        })
    };
    let mut page: Vec<Value> = Vec::new();
    let mut byte_more = false;
    for item in candidates {
        let mut candidate = page.clone();
        candidate.push(item.clone());
        if canonical(&envelope(candidate, true))?.len() > max_bytes {
            if page.is_empty() {
                return Err(AttentionError::Invalid(
                    "max_bytes cannot fit one legal item plus response envelope".into(),
                ));
            }
            byte_more = true;
            break;
        }
        page.push(item);
    }
    let result = envelope(page, sql_more || byte_more);
    tx.commit().await?;
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn safe_cursor_and_budgets_are_checked_before_pg_effects() {
        assert!(validate_cursor(-1, "cursor").is_err());
        assert!(validate_cursor(9_007_199_254_740_992, "cursor").is_err());
        assert!(validate_limit(0, MIN_COLLECTION_BYTES).is_err());
        assert!(validate_limit(501, MIN_COLLECTION_BYTES).is_err());
        assert!(validate_limit(1, MIN_COLLECTION_BYTES - 1).is_err());
        assert!(validate_limit(1, MAX_COLLECTION_BYTES + 1).is_err());
        assert!(validate_limit(1, DEFAULT_COLLECTION_BYTES).is_ok());
    }
    #[test]
    fn canonical_i_json_bounds_are_exact() {
        assert!(canonical(&json!({"cursor":9_007_199_254_740_991i64})).is_ok());
        assert!(canonical(&json!({"cursor":9_007_199_254_740_992i64})).is_err());
        assert!(canonical(&json!({"cursor":-9_007_199_254_740_992i64})).is_err());
    }
    #[test]
    fn reentry_preserves_first_navigation_order_and_sorted_reasons() {
        let events = vec![
            json!({"navigationKind":"topic","navigationRef":"z","changeSequence":4,
                "eventKind":"message","reasons":["followed_topic"]}),
            json!({"navigationKind":"space","navigationRef":"a","changeSequence":5,
                "eventKind":"participation_change","reasons":["own_participation"]}),
            json!({"navigationKind":"topic","navigationRef":"z","changeSequence":6,
                "eventKind":"message_relation","reasons":["mentioned","followed_topic"]}),
        ];
        let got = group_reentry(
            ReentryWindow {
                actor: "actor",
                after: 0,
                high: 9,
                delta_more: false,
                delta_next: 9,
            },
            &events,
            events.len(),
            &BTreeMap::from([("z".into(), 3)]),
        );
        assert_eq!(got["items"][0]["navigationRef"], "z");
        assert_eq!(got["items"][0]["eventCount"], 2);
        assert_eq!(got["items"][0]["latestChangeSequence"], 6);
        assert_eq!(got["items"][0]["resumeAfterSequence"], 3);
        assert_eq!(
            got["items"][0]["eventKinds"],
            json!(["message", "message_relation"])
        );
        assert_eq!(
            got["items"][0]["reasons"],
            json!(["followed_topic", "mentioned"])
        );
        assert_eq!(got["items"][1]["navigationRef"], "a");
    }
    #[test]
    fn python_rfc8785_ack_digest_is_equal() {
        assert_eq!(
            digest(&json!({"operation":"attention.ack",
            "actorRef":"actor:host-rust-b:social-flow","cursor":25}))
            .unwrap(),
            "sha256:3bb49fcde9034e76b6e80ef7e19b11618d415d98557834c36396d4d2393e44a6"
        );
    }
    #[test]
    fn current_state_projection_is_not_full_event_log() {
        // After a mutable topic row advances 4 -> 7, the old 4 cannot
        // be reproduced from the new row. This is NOT a promised event log.
        let e = delta_envelope("actor", 4, 7, vec![], false);
        assert_eq!(e["nextAfterSequence"], 7);
        assert_eq!(e["hasMore"], false);
    }
}
