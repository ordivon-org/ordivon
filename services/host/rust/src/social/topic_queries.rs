//! Topic inventory projection is read-only, bounded, and distinct from Work
//! lifecycle or Message content. PostgreSQL Schema13 is the only authority.
use super::{exact_time, MissingKind, Result, SocialError};
use crate::attention::canonical;
use serde_json::{json, Value};
use tokio_postgres::{Client, IsolationLevel};

const TRUTH: &str = "conversation-axis inventory only; not Work lifecycle or priority";

fn envelope(space_ref: &str, topics: Vec<Value>, has_more: bool) -> Value {
    let cursor = if has_more {
        topics
            .last()
            .and_then(|row| row["topicRef"].as_str())
            .map(str::to_owned)
    } else {
        None
    };
    json!({
        "schemaVersion":1,
        "kind":"ordivon.host-topic-list",
        "spaceRef":space_ref,
        "topics":topics,
        "hasMore":has_more,
        "nextAfterTopicRef":cursor,
        "rankingApplied":false,
        "truthBoundary":TRUTH,
    })
}
/// Paginated, lexicographically ordered, consistent Topic inventory. Unlike
/// Work list this does not imply execution, assignment, or current message
/// history. Read-only single RR snapshot; cross-call snapshots do not persist.
pub async fn list_topics(
    client: &mut Client,
    space_ref: &str,
    after_topic_ref: Option<&str>,
    limit: i64,
    max_bytes: usize,
) -> Result<Value> {
    if !(1..=500).contains(&limit) {
        return Err(SocialError::Invalid("limit must be in [1,500]".into()));
    }
    if !(16_384..=4_194_304).contains(&max_bytes) {
        return Err(SocialError::Invalid(
            "max_bytes must be in [16384,4194304]".into(),
        ));
    }
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    if tx
        .query_opt("SELECT 1 FROM spaces WHERE space_ref=$1", &[&space_ref])
        .await?
        .is_none()
    {
        return Err(SocialError::not_found(MissingKind::Space, space_ref));
    }
    let rows = tx
        .query(
            "SELECT topic_ref,title,state,created_by_actor_ref,created_at,updated_at,\
                EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz,\
                EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz \
             FROM topics WHERE space_ref=$1 AND ($2::text IS NULL OR topic_ref>$2) \
             ORDER BY topic_ref LIMIT $3",
            &[&space_ref, &after_topic_ref, &(limit + 1)],
        )
        .await?;
    let sql_more = rows.len() > limit as usize;
    let mut candidates = Vec::new();
    for row in rows.iter().take(limit as usize) {
        candidates.push(json!({
            "topicRef":row.get::<_,String>("topic_ref"),
            "title":row.get::<_,String>("title"),
            "state":row.get::<_,String>("state"),
            "createdByActorRef":row.get::<_,String>("created_by_actor_ref"),
            "createdAt":exact_time(row.get("created_at"),row.get("created_tz"))?,
            "updatedAt":exact_time(row.get("updated_at"),row.get("updated_tz"))?,
        }));
    }
    let mut page = Vec::new();
    let mut byte_more = false;
    for item in candidates {
        let mut prospective = page.clone();
        prospective.push(item.clone());
        if canonical(&envelope(space_ref, prospective, true))?.len() > max_bytes {
            if page.is_empty() {
                return Err(SocialError::Invalid(
                    "max_bytes cannot fit one legal item plus response envelope".into(),
                ));
            }
            byte_more = true;
            break;
        }
        page.push(item);
    }
    let result = envelope(space_ref, page, sql_more || byte_more);
    tx.commit().await?;
    Ok(result)
}
