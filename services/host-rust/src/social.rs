//! Rust Social commands against the existing Host PostgreSQL schema 13.
//!
//! Message identity and receipts share a single transaction. Topic state CAS
//! locks the exact same Topic row as message.post before its IDENTITY sequence
//! is allocated. The Python Host remains production writer until cutover.
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tokio_postgres::{Client, Row};

pub use crate::attention::AttentionError as SocialError;
use crate::attention::{claim_receipt, digest, exact_time, record_receipt, require_actor};
type Result<T> = std::result::Result<T, SocialError>;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum TopicState {
    Open,
    Closed,
}
impl TopicState {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Open => "open",
            Self::Closed => "closed",
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MessageKind {
    Note,
    Question,
    Proposal,
    Warning,
    Finding,
    Handoff,
}
impl MessageKind {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Note => "note",
            Self::Question => "question",
            Self::Proposal => "proposal",
            Self::Warning => "warning",
            Self::Finding => "finding",
            Self::Handoff => "handoff",
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MessageRelationKind {
    ReplyTo,
    Mentions,
    References,
    Acknowledges,
    Supersedes,
    About,
}
impl MessageRelationKind {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::ReplyTo => "reply_to",
            Self::Mentions => "mentions",
            Self::References => "references",
            Self::Acknowledges => "acknowledges",
            Self::Supersedes => "supersedes",
            Self::About => "about",
        }
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PostMessage {
    pub message_ref: String,
    pub client_request_id: String,
    pub space_ref: String,
    pub topic_ref: String,
    pub author_actor_ref: String,
    #[serde(default = "default_message_kind")]
    pub message_kind: MessageKind,
    pub body: String,
    pub recorded_at_ms: i64,
}
fn default_message_kind() -> MessageKind {
    MessageKind::Note
}
fn validate_ref(value: &str, min: usize, max: usize, name: &str) -> Result<()> {
    // Python MessageInput/MessageRelationInput apply Field length bounds only.
    // Do NOT silently strengthen this with SpaceInput's trim/control validator.
    if !(min..=max).contains(&value.chars().count()) {
        return Err(SocialError::Invalid(format!(
            "{name} must have {min}..={max} Unicode codepoints"
        )));
    }
    Ok(())
}
impl PostMessage {
    fn validate(&self) -> Result<()> {
        validate_ref(&self.message_ref, 3, 1024, "message_ref")?;
        validate_ref(&self.space_ref, 3, 1024, "space_ref")?;
        validate_ref(&self.topic_ref, 3, 1024, "topic_ref")?;
        validate_ref(&self.author_actor_ref, 3, 512, "author_actor_ref")?;
        if self.client_request_id.is_empty() || self.client_request_id.chars().count() > 1024 {
            return Err(SocialError::Invalid(
                "client_request_id must have 1..=1024 codepoints".into(),
            ));
        }
        // Pydantic Field(min_length=1,max_length=65536) validates Unicode codepoints.
        if !(1..=65536).contains(&self.body.chars().count()) {
            return Err(SocialError::Invalid(
                "body must have 1..=65536 codepoints".into(),
            ));
        }
        if self.recorded_at_ms < 0 || self.recorded_at_ms > 9_007_199_254_740_991 {
            return Err(SocialError::Invalid(
                "recorded_at_ms is outside RFC8785 safe integer domain".into(),
            ));
        }
        Ok(())
    }
    fn request_digest(&self) -> Result<String> {
        let mut v = serde_json::to_value(self).map_err(|e| SocialError::Invalid(e.to_string()))?;
        v.as_object_mut()
            .expect("serde struct maps to object")
            .insert("operation".into(), json!("message.post"));
        digest(&v)
    }
    fn message_digest(&self) -> Result<String> {
        digest(&json!({
            "messageRef":self.message_ref,"spaceRef":self.space_ref,
            "topicRef":self.topic_ref,"authorActorRef":self.author_actor_ref,
            "messageKind":self.message_kind.as_str(),"body":self.body,
            "recordedAtMs":self.recorded_at_ms
        }))
    }
}

fn message_digest_from_row(row: &Row) -> Result<String> {
    digest(&json!({
        "messageRef":row.get::<_,String>("message_ref"),
        "spaceRef":row.get::<_,String>("space_ref"),
        "topicRef":row.get::<_,String>("topic_ref"),
        "authorActorRef":row.get::<_,String>("author_actor_ref"),
        "messageKind":row.get::<_,String>("message_kind"),
        "body":row.get::<_,String>("body"),
        "recordedAtMs":row.get::<_,i64>("recorded_at_ms")
    }))
}
fn message_response(row: &Row, admission: &str) -> Result<Value> {
    let expected_digest: String = row.get("message_digest");
    if message_digest_from_row(row)? != expected_digest {
        return Err(SocialError::Integrity(
            "durable message content digest differs".into(),
        ));
    }
    let time: DateTime<Utc> = row.get("created_at");
    let offset: i32 = row.get("created_tz");
    Ok(json!({
        "schemaVersion":1,"kind":"ordivon.host-message","admission":admission,
        "sequence":row.get::<_,i64>("sequence"),
        "messageRef":row.get::<_,String>("message_ref"),
        "spaceRef":row.get::<_,String>("space_ref"),
        "topicRef":row.get::<_,String>("topic_ref"),
        "authorActorRef":row.get::<_,String>("author_actor_ref"),
        "messageKind":row.get::<_,String>("message_kind"),
        "body":row.get::<_,String>("body"),
        "messageDigest":expected_digest,
        "recordedAtMs":row.get::<_,i64>("recorded_at_ms"),
        "createdAt":exact_time(time,offset)?,
        "truthBoundary":"durable collaboration message only; participation is not authorization and message content is not Work/domain truth"
    }))
}

const MESSAGE_FIELDS:&str="sequence,message_ref,space_ref,topic_ref,author_actor_ref,message_kind,body,message_digest,recorded_at_ms,created_at,EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz";

/// The IDENTITY allocation must follow the per-topic row lock, matching Python.
/// Receipt stores an immutable *reference* rather than duplicating the body.
pub async fn post_message(client: &mut Client, value: &PostMessage) -> Result<Value> {
    value.validate()?;
    let request_digest = value.request_digest()?;
    let message_digest = value.message_digest()?;
    let tx = client.transaction().await?;
    if let Some(replay) = claim_receipt(
        &tx,
        &value.client_request_id,
        "message.post",
        &request_digest,
    )
    .await?
    {
        if replay["kind"] == "ordivon.host-message-post-receipt-ref" {
            if replay["messageRef"] != value.message_ref
                || replay["messageDigest"] != message_digest
            {
                return Err(SocialError::Integrity(
                    "message receipt reference differs from committed request".into(),
                ));
            }
            let row = tx
                .query_opt(
                    &format!("SELECT {MESSAGE_FIELDS} FROM messages WHERE message_ref=$1"),
                    &[&value.message_ref],
                )
                .await?
                .ok_or_else(|| {
                    SocialError::Integrity("committed message receipt target is missing".into())
                })?;
            let response = message_response(&row, "existing")?;
            tx.commit().await?;
            return Ok(response);
        }
        tx.commit().await?;
        return Ok(replay);
    }
    require_actor(&tx, &value.author_actor_ref).await?;
    if tx
        .query_opt(
            "SELECT 1 FROM spaces WHERE space_ref=$1",
            &[&value.space_ref],
        )
        .await?
        .is_none()
    {
        return Err(SocialError::NotFound(format!("space {}", value.space_ref)));
    }
    // FOR NO KEY UPDATE prevents post/close overtaking while FK KEY SHARE stays legal.
    let topic = tx
        .query_opt(
            "SELECT space_ref,state FROM topics WHERE topic_ref=$1 FOR NO KEY UPDATE",
            &[&value.topic_ref],
        )
        .await?
        .ok_or_else(|| SocialError::NotFound(format!("topic {}", value.topic_ref)))?;
    if topic.get::<_, String>("space_ref") != value.space_ref {
        return Err(SocialError::Conflict(
            "topic does not belong to supplied space".into(),
        ));
    }
    if topic.get::<_, String>("state") != "open" {
        return Err(SocialError::Conflict(
            "closed topic does not accept new messages".into(),
        ));
    }
    let row=tx.query_opt(
        &format!("INSERT INTO messages(message_ref,client_request_id,space_ref,topic_ref,author_actor_ref,\
          message_kind,body,message_digest,recorded_at_ms) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9) \
          ON CONFLICT (message_ref) DO NOTHING RETURNING {MESSAGE_FIELDS}"),
        &[&value.message_ref,&value.client_request_id,&value.space_ref,&value.topic_ref,
          &value.author_actor_ref,&value.message_kind.as_str(),&value.body,&message_digest,
          &value.recorded_at_ms],
    ).await?;
    let (row, admission) = if let Some(r) = row {
        (r, "committed")
    } else {
        let row = tx
            .query_opt(
                &format!("SELECT {MESSAGE_FIELDS} FROM messages WHERE message_ref=$1"),
                &[&value.message_ref],
            )
            .await?
            .ok_or_else(|| SocialError::Integrity("message disappeared".into()))?;
        if row.get::<_, String>("message_digest") != message_digest {
            return Err(SocialError::Conflict(
                "message_ref already exists with different content".into(),
            ));
        }
        (row, "existing")
    };
    let result = message_response(&row, admission)?;
    let marker = json!({
        "schemaVersion":1,"kind":"ordivon.host-message-post-receipt-ref",
        "messageRef":value.message_ref,"messageDigest":message_digest
    });
    record_receipt(
        &tx,
        &value.client_request_id,
        "message.post",
        &request_digest,
        &marker,
    )
    .await?;
    tx.commit().await?;
    Ok(result)
}

/// Compare-and-set the topic's state *and* current maximum message sequence.
pub async fn set_topic_state(
    client: &mut Client,
    topic_ref: &str,
    actor_ref: &str,
    state: TopicState,
    expected_state: TopicState,
    expected_high_sequence: i64,
    request_id: &str,
) -> Result<Value> {
    if expected_high_sequence < 0 {
        return Err(SocialError::Invalid(
            "expected_high_sequence must be non-negative integer".into(),
        ));
    }
    let request_digest = digest(&json!({
        "operation":"topic.state.set","topicRef":topic_ref,"actorRef":actor_ref,
        "state":state.as_str(),"expectedState":expected_state.as_str(),
        "expectedHighSequence":expected_high_sequence
    }))?;
    let tx = client.transaction().await?;
    if let Some(replay) = claim_receipt(&tx, request_id, "topic.state.set", &request_digest).await?
    {
        tx.commit().await?;
        return Ok(replay);
    }
    require_actor(&tx, actor_ref).await?;
    let topic = tx
        .query_opt(
            "SELECT topic_ref,space_ref,title,state,created_by_actor_ref,created_at,updated_at,\
        EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz,\
        EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz \
        FROM topics WHERE topic_ref=$1 FOR NO KEY UPDATE",
            &[&topic_ref],
        )
        .await?
        .ok_or_else(|| SocialError::NotFound(format!("topic {topic_ref}")))?;
    let high: i64 = tx
        .query_one(
            "SELECT COALESCE(MAX(sequence),0) AS high FROM messages WHERE topic_ref=$1",
            &[&topic_ref],
        )
        .await?
        .get("high");
    if topic.get::<_, String>("state") != expected_state.as_str() {
        return Err(SocialError::Conflict(
            "topic state changed since expected state".into(),
        ));
    }
    if high != expected_high_sequence {
        return Err(SocialError::Conflict(
            "topic messages changed since expected high sequence".into(),
        ));
    }
    let admission = if state == expected_state {
        "existing"
    } else {
        "committed"
    };
    let result_row = if state != expected_state {
        tx.query_one(
            "UPDATE topics SET state=$1,updated_at=clock_timestamp(),\
             change_sequence=swf_next_change_sequence() WHERE topic_ref=$2 \
             RETURNING topic_ref,space_ref,title,state,created_by_actor_ref,created_at,updated_at,\
             EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz,\
             EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz",
            &[&state.as_str(), &topic_ref],
        )
        .await?
    } else {
        topic
    };
    let result = json!({
        "schemaVersion":1,"kind":"ordivon.host-topic","admission":admission,
        "topicRef":result_row.get::<_,String>("topic_ref"),
        "spaceRef":result_row.get::<_,String>("space_ref"),
        "title":result_row.get::<_,String>("title"),
        "state":result_row.get::<_,String>("state"),
        "createdByActorRef":result_row.get::<_,String>("created_by_actor_ref"),
        "createdAt":exact_time(result_row.get("created_at"),result_row.get("created_tz"))?,
        "updatedAt":exact_time(result_row.get("updated_at"),result_row.get("updated_tz"))?,
        "truthBoundary":"topic openness only; no message deletion, consumer-release proof, or authority transfer"
    });
    record_receipt(&tx, request_id, "topic.state.set", &request_digest, &result).await?;
    tx.commit().await?;
    Ok(result)
}

/// ACK proves only a monotone durable navigation cursor; the consumer must
/// actually read/process the page before issuing this command.
pub async fn ack_topic_cursor(
    client: &mut Client,
    actor_ref: &str,
    topic_ref: &str,
    cursor: i64,
    request_id: &str,
) -> Result<Value> {
    if !(0..=9_007_199_254_740_991).contains(&cursor) {
        return Err(SocialError::Invalid(
            "cursor must be non-negative exact integer".into(),
        ));
    }
    let request_digest = digest(&json!({
        "operation":"topic.cursor.ack","actorRef":actor_ref,
        "topicRef":topic_ref,"cursor":cursor
    }))?;
    let tx = client.transaction().await?;
    if let Some(replay) =
        claim_receipt(&tx, request_id, "topic.cursor.ack", &request_digest).await?
    {
        tx.commit().await?;
        return Ok(replay);
    }
    require_actor(&tx, actor_ref).await?;
    if tx
        .query_opt("SELECT 1 FROM topics WHERE topic_ref=$1", &[&topic_ref])
        .await?
        .is_none()
    {
        return Err(SocialError::NotFound(format!("topic {topic_ref}")));
    }
    let high: i64 = tx
        .query_one(
            "SELECT COALESCE(MAX(sequence),0) AS high FROM messages WHERE topic_ref=$1",
            &[&topic_ref],
        )
        .await?
        .get("high");
    if cursor > high {
        return Err(SocialError::Conflict(
            "topic cursor cannot acknowledge beyond current topic horizon".into(),
        ));
    }
    let previous=tx.query_opt(
        "SELECT cursor FROM topic_consumption_cursors WHERE actor_ref=$1 AND topic_ref=$2 FOR UPDATE",
        &[&actor_ref,&topic_ref]
    ).await?.map(|r|r.get::<_,i64>("cursor")).unwrap_or(0);
    if cursor < previous {
        return Err(SocialError::Conflict(
            "topic cursor cannot move backwards".into(),
        ));
    }
    if tx.query_opt(
        "INSERT INTO topic_consumption_cursors(actor_ref,topic_ref,cursor) VALUES($1,$2,$3)\
         ON CONFLICT(actor_ref,topic_ref) DO UPDATE SET cursor=EXCLUDED.cursor,updated_at=clock_timestamp()\
         WHERE topic_consumption_cursors.cursor<=EXCLUDED.cursor RETURNING cursor",
        &[&actor_ref,&topic_ref,&cursor]
    ).await?.is_none(){
        return Err(SocialError::Conflict("topic cursor cannot move backwards".into()));
    }
    let result = json!({
        "schemaVersion":1,"kind":"ordivon.host-topic-cursor-ack",
        "actorRef":actor_ref,"topicRef":topic_ref,"previousCursor":previous,
        "cursor":cursor,"topicHighSequence":high,
        "truthBoundary":"topic navigation acknowledgement only; not semantic acceptance"
    });
    record_receipt(
        &tx,
        request_id,
        "topic.cursor.ack",
        &request_digest,
        &result,
    )
    .await?;
    tx.commit().await?;
    Ok(result)
}

#[derive(Clone, Copy)]
pub struct RelationEndpoint<'a> {
    pub sequence: i64,
    pub space: &'a str,
    pub topic: &'a str,
}
pub fn validate_message_relation(
    relation: MessageRelationKind,
    source: RelationEndpoint<'_>,
    target: Option<RelationEndpoint<'_>>,
    same_message: bool,
) -> Result<()> {
    match relation {
        MessageRelationKind::ReplyTo
        | MessageRelationKind::Acknowledges
        | MessageRelationKind::Supersedes => {
            if target.map(|t| t.space) != Some(source.space) {
                return Err(SocialError::Conflict(format!(
                    "{} cannot cross spaces",
                    relation.as_str()
                )));
            }
            if relation == MessageRelationKind::ReplyTo {
                if target.map(|t| t.topic) != Some(source.topic) {
                    return Err(SocialError::Conflict("reply_to cannot cross topics".into()));
                }
                if !target.is_some_and(|t| t.sequence < source.sequence) {
                    return Err(SocialError::Conflict(
                        "reply_to must target an earlier message".into(),
                    ));
                }
            }
            if relation == MessageRelationKind::Supersedes && same_message {
                return Err(SocialError::Conflict(
                    "message cannot supersede itself".into(),
                ));
            }
        }
        _ => {}
    }
    Ok(())
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AddMessageRelation {
    pub source_message_ref: String,
    pub relation: MessageRelationKind,
    pub target_ref: String,
    pub actor_ref: String,
}
impl AddMessageRelation {
    fn validate(&self) -> Result<()> {
        validate_ref(&self.source_message_ref, 3, 1024, "source_message_ref")?;
        validate_ref(&self.actor_ref, 3, 512, "actor_ref")?;
        validate_ref(&self.target_ref, 1, 2048, "target_ref")?;
        Ok(())
    }
}
/// One transaction with the existing Python Host's receipt semantics.
/// Opaque references and about do not establish foreign object existence.
pub async fn add_message_relation(
    client: &mut Client,
    value: &AddMessageRelation,
    request_id: &str,
) -> Result<Value> {
    value.validate()?;
    let mut command =
        serde_json::to_value(value).map_err(|e| SocialError::Invalid(e.to_string()))?;
    command["operation"] = json!("message.relation.add");
    let request_digest = digest(&command)?;
    let tx = client.transaction().await?;
    if let Some(replay) =
        claim_receipt(&tx, request_id, "message.relation.add", &request_digest).await?
    {
        tx.commit().await?;
        return Ok(replay);
    }
    require_actor(&tx, &value.actor_ref).await?;
    let source = tx
        .query_opt(
            "SELECT sequence,space_ref,topic_ref FROM messages WHERE message_ref=$1",
            &[&value.source_message_ref],
        )
        .await?
        .ok_or_else(|| SocialError::NotFound(format!("message {}", value.source_message_ref)))?;
    match value.relation {
        MessageRelationKind::ReplyTo
        | MessageRelationKind::Acknowledges
        | MessageRelationKind::Supersedes => {
            let target = tx
                .query_opt(
                    "SELECT sequence,space_ref,topic_ref FROM messages WHERE message_ref=$1",
                    &[&value.target_ref],
                )
                .await?
                .ok_or_else(|| SocialError::NotFound(format!("message {}", value.target_ref)))?;
            let ss: String = source.get("space_ref");
            let st: String = source.get("topic_ref");
            let ts: String = target.get("space_ref");
            let tt: String = target.get("topic_ref");
            validate_message_relation(
                value.relation,
                RelationEndpoint {
                    sequence: source.get("sequence"),
                    space: &ss,
                    topic: &st,
                },
                Some(RelationEndpoint {
                    sequence: target.get("sequence"),
                    space: &ts,
                    topic: &tt,
                }),
                value.source_message_ref == value.target_ref,
            )?;
        }
        MessageRelationKind::Mentions => require_actor(&tx, &value.target_ref).await?,
        MessageRelationKind::References | MessageRelationKind::About => {}
    }
    let inserted=tx.query_opt(
        "INSERT INTO message_relations(source_message_ref,relation,target_ref,created_by_actor_ref) \
         VALUES($1,$2,$3,$4) ON CONFLICT DO NOTHING RETURNING created_at",
        &[&value.source_message_ref,&value.relation.as_str(),&value.target_ref,&value.actor_ref],
    ).await?.is_some();
    let row = tx
        .query_opt(
            "SELECT source_message_ref,relation,target_ref,created_by_actor_ref,created_at,\
         EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz \
         FROM message_relations WHERE source_message_ref=$1 AND relation=$2 AND target_ref=$3",
            &[
                &value.source_message_ref,
                &value.relation.as_str(),
                &value.target_ref,
            ],
        )
        .await?
        .ok_or_else(|| SocialError::Integrity("message relation disappeared".into()))?;
    let result = json!({
        "schemaVersion":1,"kind":"ordivon.host-message-relation",
        "admission":if inserted {"committed"} else {"existing"},
        "sourceMessageRef":row.get::<_,String>("source_message_ref"),
        "relation":row.get::<_,String>("relation"),
        "targetRef":row.get::<_,String>("target_ref"),
        "createdByActorRef":row.get::<_,String>("created_by_actor_ref"),
        "createdAt":exact_time(row.get("created_at"),row.get("created_tz"))?,
        "truthBoundary":"collaboration relation only; acknowledgement is not vote/acceptance and mention is not assignment"
    });
    record_receipt(
        &tx,
        request_id,
        "message.relation.add",
        &request_digest,
        &result,
    )
    .await?;
    tx.commit().await?;
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    fn endpoint<'a>(sequence: i64, space: &'a str, topic: &'a str) -> RelationEndpoint<'a> {
        RelationEndpoint {
            sequence,
            space,
            topic,
        }
    }
    #[test]
    fn reply_to_is_strictly_descending_and_topic_scoped() {
        let rel = MessageRelationKind::ReplyTo;
        let src = endpoint(10, "s", "t");
        assert!(validate_message_relation(rel, src, Some(endpoint(9, "s", "t")), false).is_ok());
        assert!(validate_message_relation(rel, src, Some(endpoint(10, "s", "t")), false).is_err());
        assert!(
            validate_message_relation(rel, src, Some(endpoint(8, "s", "other")), false).is_err()
        );
        assert!(
            validate_message_relation(rel, src, Some(endpoint(8, "other", "t")), false).is_err()
        );
        assert!(validate_message_relation(
            rel,
            endpoint(i64::MAX, "s", "t"),
            Some(endpoint(i64::MIN, "s", "t")),
            false
        )
        .is_ok());
    }
    #[test]
    fn message_input_enforces_python_bounds_without_float_conversion() {
        let good = PostMessage {
            message_ref: "msg".into(),
            client_request_id: "req".into(),
            space_ref: "spc".into(),
            topic_ref: "top".into(),
            author_actor_ref: "actor".into(),
            message_kind: MessageKind::Note,
            body: "中国🧩".into(),
            recorded_at_ms: 1,
        };
        assert!(good.validate().is_ok());
        assert!(good.message_digest().unwrap().starts_with("sha256:"));
        let mut bad = good.clone();
        bad.recorded_at_ms = 9_007_199_254_740_992;
        assert!(bad.validate().is_err());
        bad = good;
        bad.body = String::new();
        assert!(bad.validate().is_err());
    }
    #[test]
    fn supersedes_rejects_self_and_opaque_references_are_allowed() {
        assert!(validate_message_relation(
            MessageRelationKind::Supersedes,
            endpoint(10, "s", "t"),
            Some(endpoint(1, "s", "t")),
            true
        )
        .is_err());
        assert!(validate_message_relation(
            MessageRelationKind::References,
            endpoint(10, "s", "t"),
            None,
            false
        )
        .is_ok());
    }
}
