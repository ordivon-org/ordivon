//! Explicit message-relation navigation over the existing Host PostgreSQL
//! authority. A relation is a source/target assertion, not verification of
//! opaque referenced objects, agreement, or permission.
use super::{exact_time, MessageRelationKind, MissingKind, Result, SocialError};
use crate::attention::canonical;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tokio_postgres::{Client, IsolationLevel};

const MIN_BYTES: usize = 16_384;
const MAX_BYTES: usize = 4_194_304;
const TRUTH: &str =
    "explicit collaboration relations only; opaque targets are references, not existence or authority proof";

#[derive(Clone, Copy, Debug, Eq, PartialEq, Deserialize, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum RelationDirection {
    Outgoing,
    Incoming,
    Both,
}
impl RelationDirection {
    fn as_str(self) -> &'static str {
        match self {
            Self::Outgoing => "outgoing",
            Self::Incoming => "incoming",
            Self::Both => "both",
        }
    }
}

#[derive(Clone, Debug)]
pub struct ListMessageRelations {
    pub message_ref: String,
    pub direction: RelationDirection,
    pub relation: Option<MessageRelationKind>,
    pub after_change_sequence: i64,
    pub limit: i64,
    pub max_bytes: usize,
}
impl ListMessageRelations {
    fn validate(&self) -> Result<()> {
        if self.after_change_sequence < 0 {
            return Err(SocialError::Invalid(
                "after_change_sequence must be non-negative".into(),
            ));
        }
        if self.after_change_sequence > 9_007_199_254_740_991 {
            return Err(SocialError::Invalid(
                "after_change_sequence exceeds RFC8785 exact integer range".into(),
            ));
        }
        if !(1..=500).contains(&self.limit) {
            return Err(SocialError::Invalid("limit must be in [1,500]".into()));
        }
        if !(MIN_BYTES..=MAX_BYTES).contains(&self.max_bytes) {
            return Err(SocialError::Invalid(format!(
                "max_bytes must be in [{MIN_BYTES},{MAX_BYTES}]"
            )));
        }
        Ok(())
    }
}
fn envelope(input: &ListMessageRelations, relations: Vec<Value>, has_more: bool) -> Value {
    let cursor = relations
        .last()
        .and_then(|r| r["changeSequence"].as_i64())
        .unwrap_or(input.after_change_sequence);
    json!({
        "schemaVersion":1,
        "kind":"ordivon.host-message-relation-list",
        "messageRef":input.message_ref,
        "direction":input.direction.as_str(),
        "relations":relations,
        "hasMore":has_more,
        "nextAfterChangeSequence":cursor,
        "rankingApplied":false,
        "truthBoundary":TRUTH
    })
}
/// Single repeatable-read snapshot. Native PG parameter binding, one ordered
/// query plus the source message existence check, no hand-coded event log.
/// Validates the byte budget against the *entire* canonical response, like the
/// original Python Host's bounded_prefix.
pub async fn list_message_relations(
    client: &mut Client,
    input: &ListMessageRelations,
) -> Result<Value> {
    input.validate()?;
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    if tx
        .query_opt(
            "SELECT 1 FROM messages WHERE message_ref=$1",
            &[&input.message_ref],
        )
        .await?
        .is_none()
    {
        return Err(SocialError::not_found(
            MissingKind::Message,
            &input.message_ref,
        ));
    }
    let relation = input.relation.map(MessageRelationKind::as_str);
    let direction = input.direction.as_str();
    let rows = tx
        .query(
            "SELECT change_sequence,source_message_ref,relation,target_ref,\
                    created_by_actor_ref,created_at,\
                    EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz \
             FROM message_relations WHERE change_sequence>$1 \
             AND ($2::text IS NULL OR relation=$2) \
             AND (($3 IN ('outgoing','both') AND source_message_ref=$4) \
                  OR ($3 IN ('incoming','both') AND target_ref=$4)) \
             ORDER BY change_sequence,source_message_ref,relation,target_ref LIMIT $5",
            &[
                &input.after_change_sequence,
                &relation,
                &direction,
                &input.message_ref.as_str(),
                &(input.limit + 1),
            ],
        )
        .await?;
    let sql_more = rows.len() > input.limit as usize;
    let mut candidates = Vec::new();
    for row in rows.iter().take(input.limit as usize) {
        candidates.push(json!({
            "changeSequence":row.get::<_,i64>("change_sequence"),
            "sourceMessageRef":row.get::<_,String>("source_message_ref"),
            "relation":row.get::<_,String>("relation"),
            "targetRef":row.get::<_,String>("target_ref"),
            "createdByActorRef":row.get::<_,String>("created_by_actor_ref"),
            "createdAt":exact_time(row.get("created_at"),row.get("created_tz"))?,
        }));
    }
    let mut page = Vec::new();
    let mut byte_more = false;
    for item in candidates {
        let mut prospective = page.clone();
        prospective.push(item.clone());
        if canonical(&envelope(input, prospective, true))?.len() > input.max_bytes {
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
    let result = envelope(input, page, sql_more || byte_more);
    tx.commit().await?;
    Ok(result)
}
