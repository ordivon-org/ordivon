//! Immutable message get/search via Schema 13 PostgreSQL owner indexes.
use super::{
    exact_time, message_digest_from_row, MissingKind, Result, SocialError, MESSAGE_FIELDS,
};
use crate::attention::canonical;
use serde_json::{json, Value};
use tokio_postgres::{types::ToSql, Client, IsolationLevel, Row};

const READ_BOUNDARY:&str="exact durable Host message projection only; message content remains collaboration evidence until interpreted by the owning domain";
const SEARCH_SUFFIX:&str=" ordered by message sequence, not relevance/priority; message claims require owner-native verification";
fn verified(row: &Row) -> Result<Value> {
    let claim: String = row.get("message_digest");
    if message_digest_from_row(row)? != claim {
        return Err(SocialError::Integrity(
            "Host message content digest differs from stored claim".into(),
        ));
    }
    Ok(json!({
        "sequence":row.get::<_,i64>("sequence"),
        "messageRef":row.get::<_,String>("message_ref"),
        "spaceRef":row.get::<_,String>("space_ref"),
        "topicRef":row.get::<_,String>("topic_ref"),
        "authorActorRef":row.get::<_,String>("author_actor_ref"),
        "messageKind":row.get::<_,String>("message_kind"),
        "body":row.get::<_,String>("body"),
        "messageDigest":claim,
        "recordedAtMs":row.get::<_,i64>("recorded_at_ms"),
        "createdAt":exact_time(row.get("created_at"),row.get("created_tz"))?,
    }))
}
pub async fn get_message(
    client: &mut Client,
    message_ref: &str,
    expected_digest: Option<&str>,
) -> Result<Value> {
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    let row = tx
        .query_opt(
            &format!("SELECT {MESSAGE_FIELDS} FROM messages WHERE message_ref=$1"),
            &[&message_ref],
        )
        .await?
        .ok_or_else(|| SocialError::not_found(MissingKind::Message, message_ref))?;
    let mut result = verified(&row)?;
    let stored = result["messageDigest"]
        .as_str()
        .ok_or_else(|| SocialError::Integrity("message digest is not string".into()))?;
    if let Some(expected) = expected_digest {
        if expected != stored {
            return Err(SocialError::Conflict(format!(
                "message digest mismatch: expected {expected}, actual {stored}"
            )));
        }
    }
    let obj = result
        .as_object_mut()
        .ok_or_else(|| SocialError::Integrity("message projection is not object".into()))?;
    obj.insert("schemaVersion".into(), json!(1));
    obj.insert("kind".into(), json!("ordivon.host-message-read"));
    obj.insert("truthBoundary".into(), json!(READ_BOUNDARY));
    tx.commit().await?;
    Ok(result)
}
#[derive(Clone, Debug)]
pub struct SearchMessages {
    pub query: String,
    pub space_ref: Option<String>,
    pub topic_ref: Option<String>,
    pub before_sequence: Option<i64>,
    pub limit: i64,
    pub max_bytes: usize,
}
impl SearchMessages {
    fn validate(&self) -> Result<()> {
        if self.query.trim_matches(super::python_whitespace).is_empty() {
            return Err(SocialError::Invalid("query must be non-empty".into()));
        }
        if !(1..=200).contains(&self.limit) {
            return Err(SocialError::Invalid("limit must be in [1,200]".into()));
        }
        if self.before_sequence.is_some_and(|s| s < 1) {
            return Err(SocialError::Invalid(
                "before_sequence must be positive".into(),
            ));
        }
        if !(131_072..=4_194_304).contains(&self.max_bytes) {
            return Err(SocialError::Invalid(
                "max_bytes must be in [131072,4194304]".into(),
            ));
        }
        Ok(())
    }
}
fn envelope(query: &str, boundary: &str, messages: Vec<Value>, has_more: bool) -> Value {
    let next = if has_more {
        messages.last().and_then(|v| v["sequence"].as_i64())
    } else {
        None
    };
    json!({"schemaVersion":1,"kind":"ordivon.host-message-search",
        "query":query,"messages":messages,"hasMore":has_more,
        "nextBeforeSequence":next,"rankingApplied":false,"ordering":"sequence_desc",
        "truthBoundary":format!("{boundary}{SEARCH_SUFFIX}")})
}
/// Three fixed PG pathways: indexed >=3-CJK ngrams + literal verification,
/// short literal CJK strpos, otherwise simple full-text websearch.
pub async fn search_messages(client: &mut Client, input: &SearchMessages) -> Result<Value> {
    input.validate()?;
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    if let Some(s) = input.space_ref.as_deref() {
        if tx
            .query_opt("SELECT 1 FROM spaces WHERE space_ref=$1", &[&s])
            .await?
            .is_none()
        {
            return Err(SocialError::not_found(MissingKind::Space, s));
        }
    }
    if let Some(t) = input.topic_ref.as_deref() {
        let row = tx
            .query_opt("SELECT space_ref FROM topics WHERE topic_ref=$1", &[&t])
            .await?
            .ok_or_else(|| SocialError::not_found(MissingKind::Topic, t))?;
        if input
            .space_ref
            .as_deref()
            .is_some_and(|s| s != row.get::<_, String>("space_ref"))
        {
            return Err(SocialError::Conflict(
                "topic does not belong to supplied space".into(),
            ));
        }
    }
    let count = input
        .query
        .chars()
        .filter(|ch| ('\u{3400}'..='\u{9fff}').contains(ch))
        .count();
    let literal = count > 0
        && !input
            .query
            .trim_matches(super::python_whitespace)
            .chars()
            .any(super::python_whitespace);
    let gram = literal && count >= 3;
    let (predicate, boundary, nargs) = if gram {
        (
            "host_unicode_ngrams3(body) @> host_unicode_ngrams3($1) AND strpos(body,$2)>0",
            "PostgreSQL CJK indexed Unicode-gram locator",
            2usize,
        )
    } else if literal {
        (
            "strpos(body,$1)>0",
            "PostgreSQL CJK literal substring locator",
            1usize,
        )
    } else {
        (
            "to_tsvector('simple',body) @@ websearch_to_tsquery('simple',$1)",
            "PostgreSQL full-text locator",
            1usize,
        )
    };
    let sp = format!("{}{}", '$', nargs + 1);
    let tp = format!("{}{}", '$', nargs + 2);
    let bp = format!("{}{}", '$', nargs + 3);
    let lp = format!("{}{}", '$', nargs + 4);
    let sql = format!(
        "SELECT {MESSAGE_FIELDS} FROM messages WHERE {predicate} \
        AND ({sp}::text IS NULL OR space_ref={sp}) \
        AND ({tp}::text IS NULL OR topic_ref={tp}) \
        AND ({bp}::bigint IS NULL OR sequence<{bp}) ORDER BY sequence DESC LIMIT {lp}"
    );
    let row_limit = input.limit + 1;
    let space = input.space_ref.as_deref();
    let topic = input.topic_ref.as_deref();
    let mut params: Vec<&(dyn ToSql + Sync)> = vec![&input.query];
    if gram {
        params.push(&input.query);
    }
    params.push(&space);
    params.push(&topic);
    params.push(&input.before_sequence);
    params.push(&row_limit);
    let rows = tx.query(&sql, &params).await?;
    let sql_more = rows.len() > input.limit as usize;
    let mut candidates = Vec::new();
    for row in rows.iter().take(input.limit as usize) {
        candidates.push(verified(row)?);
    }
    let mut messages = Vec::new();
    let mut byte_more = false;
    for item in candidates {
        let mut candidate = messages.clone();
        candidate.push(item.clone());
        if canonical(&envelope(&input.query, boundary, candidate, true))?.len() > input.max_bytes {
            if messages.is_empty() {
                return Err(SocialError::Invalid(
                    "max_bytes cannot fit one legal item plus response envelope".into(),
                ));
            }
            byte_more = true;
            break;
        }
        messages.push(item);
    }
    let result = envelope(&input.query, boundary, messages, sql_more || byte_more);
    tx.commit().await?;
    Ok(result)
}
