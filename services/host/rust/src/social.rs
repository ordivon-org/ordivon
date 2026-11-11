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
use crate::attention::{
    claim_receipt, digest, exact_time, record_receipt, require_actor, MissingKind,
};
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
        return Err(SocialError::not_found(MissingKind::Space, &value.space_ref));
    }
    // FOR NO KEY UPDATE prevents post/close overtaking while FK KEY SHARE stays legal.
    let topic = tx
        .query_opt(
            "SELECT space_ref,state FROM topics WHERE topic_ref=$1 FOR NO KEY UPDATE",
            &[&value.topic_ref],
        )
        .await?
        .ok_or_else(|| SocialError::not_found(MissingKind::Topic, &value.topic_ref))?;
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
        .ok_or_else(|| SocialError::not_found(MissingKind::Topic, topic_ref))?;
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
        return Err(SocialError::not_found(MissingKind::Topic, topic_ref));
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
        .ok_or_else(|| SocialError::not_found(MissingKind::Message, &value.source_message_ref))?;
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
                .ok_or_else(|| SocialError::not_found(MissingKind::Message, &value.target_ref))?;
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

/// Bounded, integrity-checked Topic resume using a single repeatable-read
/// PostgreSQL snapshot. This is the same pagination/byte-budget contract as
/// Python SocialTopicReadQueries.resume_topic, not a synthetic event stream.
pub async fn resume_topic(
    client: &mut Client,
    topic_ref: &str,
    after_sequence: i64,
    limit: i64,
    max_bytes: usize,
) -> Result<Value> {
    const MIN_MESSAGE_BYTES: usize = 131_072;
    const MAX_BYTES: usize = 4_194_304;
    if !(1..=500).contains(&limit) {
        return Err(SocialError::Invalid("limit must be in [1,500]".into()));
    }
    if after_sequence < 0 {
        return Err(SocialError::Invalid(
            "after_sequence must be non-negative".into(),
        ));
    }
    if !(MIN_MESSAGE_BYTES..=MAX_BYTES).contains(&max_bytes) {
        return Err(SocialError::Invalid(format!(
            "max_bytes must be in [{MIN_MESSAGE_BYTES},{MAX_BYTES}]"
        )));
    }
    let tx = client
        .build_transaction()
        .isolation_level(tokio_postgres::IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    let topic = tx
        .query_opt(
            "SELECT topic_ref,space_ref,title,state FROM topics WHERE topic_ref=$1",
            &[&topic_ref],
        )
        .await?
        .ok_or_else(|| SocialError::not_found(MissingKind::Topic, topic_ref))?;
    let topic_wire = json!({
        "topicRef":topic.get::<_,String>("topic_ref"),
        "spaceRef":topic.get::<_,String>("space_ref"),
        "title":topic.get::<_,String>("title"),
        "state":topic.get::<_,String>("state"),
    });
    let rows = tx
        .query(
            &format!(
                "SELECT {MESSAGE_FIELDS} FROM messages \
                 WHERE topic_ref=$1 AND sequence>$2 ORDER BY sequence LIMIT $3"
            ),
            &[&topic_ref, &after_sequence, &(limit + 1)],
        )
        .await?;
    let sql_more = rows.len() > limit as usize;
    // Python verifies the digests of ALL SQL candidates before byte trimming.
    // Checking only the emitted prefix would hide corruption in a fetched row
    // that does not fit in this response's max_bytes envelope.
    let mut candidates = Vec::new();
    for row in rows.iter().take(limit as usize) {
        let stored: String = row.get("message_digest");
        if message_digest_from_row(row)? != stored {
            return Err(SocialError::Integrity(
                "durable message content digest differs".into(),
            ));
        }
        let msg = json!({
            "sequence":row.get::<_,i64>("sequence"),
            "messageRef":row.get::<_,String>("message_ref"),
            "authorActorRef":row.get::<_,String>("author_actor_ref"),
            "messageKind":row.get::<_,String>("message_kind"),
            "body":row.get::<_,String>("body"),
            "messageDigest":stored,
            "recordedAtMs":row.get::<_,i64>("recorded_at_ms"),
            "createdAt":exact_time(row.get("created_at"),row.get("created_tz"))?,
        });
        candidates.push(msg);
    }
    let mut messages = Vec::new();
    let mut byte_more = false;
    for msg in candidates {
        let mut candidate = messages.clone();
        candidate.push(msg.clone());
        if crate::attention::canonical(&resume_envelope(
            &topic_wire,
            after_sequence,
            candidate,
            true,
        ))?
        .len()
            > max_bytes
        {
            if messages.is_empty() {
                return Err(SocialError::Invalid(
                    "max_bytes cannot fit one legal item plus response envelope".into(),
                ));
            }
            byte_more = true;
            break;
        }
        messages.push(msg);
    }
    let result = resume_envelope(&topic_wire, after_sequence, messages, sql_more || byte_more);
    tx.commit().await?;
    Ok(result)
}

fn resume_envelope(
    topic: &Value,
    after_sequence: i64,
    messages: Vec<Value>,
    has_more: bool,
) -> Value {
    let next = messages
        .last()
        .and_then(|message| message["sequence"].as_i64())
        .unwrap_or(after_sequence);
    json!({
        "schemaVersion":1,
        "kind":"ordivon.host-topic-resume",
        "topic":topic,
        "messages":messages,
        "hasMore":has_more,
        "nextAfterSequence":next,
        "truthBoundary":"bounded topic conversation only; message claims require owner-native verification",
    })
}

/// The topic consumption cursor is distinct from Attention's global change
/// cursor. It does not certify semantic acceptance of the message contents.
pub async fn get_topic_cursor(
    client: &mut Client,
    actor_ref: &str,
    topic_ref: &str,
) -> Result<Value> {
    let tx = client
        .build_transaction()
        .isolation_level(tokio_postgres::IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    require_actor(&tx, actor_ref).await?;
    if tx
        .query_opt("SELECT 1 FROM topics WHERE topic_ref=$1", &[&topic_ref])
        .await?
        .is_none()
    {
        return Err(SocialError::not_found(MissingKind::Topic, topic_ref));
    }
    let current = tx
        .query_opt(
            "SELECT cursor FROM topic_consumption_cursors \
             WHERE actor_ref=$1 AND topic_ref=$2",
            &[&actor_ref, &topic_ref],
        )
        .await?
        .map(|r| r.get::<_, i64>("cursor"))
        .unwrap_or(0);
    let high: i64 = tx
        .query_one(
            "SELECT COALESCE(MAX(sequence),0) AS high FROM messages WHERE topic_ref=$1",
            &[&topic_ref],
        )
        .await?
        .get("high");
    tx.commit().await?;
    Ok(json!({
        "schemaVersion":1,"kind":"ordivon.host-topic-cursor",
        "actorRef":actor_ref,"topicRef":topic_ref,
        "cursor":current,"topicHighSequence":high,
        "truthBoundary":"topic navigation cursor only; not evidence of semantic acceptance"
    }))
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CreateTopic {
    pub topic_ref: String,
    pub space_ref: String,
    pub title: String,
    pub actor_ref: String,
    pub client_request_id: String,
}

impl CreateTopic {
    fn validate(&self) -> Result<()> {
        validate_ref(&self.topic_ref, 3, 1024, "topic_ref")?;
        validate_ref(&self.space_ref, 3, 1024, "space_ref")?;
        validate_ref(&self.title, 1, 512, "title")?;
        validate_ref(&self.actor_ref, 3, 512, "actor_ref")?;
        validate_ref(&self.client_request_id, 1, 1024, "client_request_id")
    }
}

const TOPIC_FIELDS: &str = "topic_ref,space_ref,title,state,created_by_actor_ref,\
created_at,updated_at,EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz,\
EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz";

fn topic_created_response(row: &Row, admission: &str) -> Result<Value> {
    Ok(json!({
        "schemaVersion":1, "kind":"ordivon.host-topic", "admission":admission,
        "topicRef":row.get::<_,String>("topic_ref"),
        "spaceRef":row.get::<_,String>("space_ref"),
        "title":row.get::<_,String>("title"),
        "state":row.get::<_,String>("state"),
        "createdByActorRef":row.get::<_,String>("created_by_actor_ref"),
        "createdAt":exact_time(row.get("created_at"),row.get("created_tz"))?,
        "updatedAt":exact_time(row.get("updated_at"),row.get("updated_tz"))?,
        "truthBoundary":"named asynchronous conversation axis only; not Work lifecycle or authority",
    }))
}

/// PostgreSQL unique topic_ref linearizes first creators; a replayed command
/// receipt is immutable even if the Topic has since changed state.
pub async fn create_topic(client: &mut Client, command: &CreateTopic) -> Result<Value> {
    command.validate()?;
    // Python TopicInput.model_dump(mode="json"): snake_case domain field names.
    let request_digest = digest(&json!({
        "operation":"topic.create",
        "topic_ref":command.topic_ref,
        "space_ref":command.space_ref,
        "title":command.title,
        "actor_ref":command.actor_ref,
    }))?;
    let tx = client.transaction().await?;
    if let Some(existing) = claim_receipt(
        &tx,
        &command.client_request_id,
        "topic.create",
        &request_digest,
    )
    .await?
    {
        tx.commit().await?;
        return Ok(existing);
    }
    if tx
        .query_opt(
            "SELECT 1 FROM spaces WHERE space_ref=$1",
            &[&command.space_ref],
        )
        .await?
        .is_none()
    {
        return Err(SocialError::not_found(
            MissingKind::Space,
            &command.space_ref,
        ));
    }
    require_actor(&tx, &command.actor_ref).await?;
    let inserted = tx
        .query_opt(
            &format!(
                "INSERT INTO topics(topic_ref,space_ref,title,state,created_by_actor_ref) \
             VALUES($1,$2,$3,'open',$4) ON CONFLICT (topic_ref) DO NOTHING \
             RETURNING {TOPIC_FIELDS}"
            ),
            &[
                &command.topic_ref,
                &command.space_ref,
                &command.title,
                &command.actor_ref,
            ],
        )
        .await?;
    let (row, admission) = if let Some(row) = inserted {
        (row, "committed")
    } else {
        let row = tx
            .query_opt(
                &format!("SELECT {TOPIC_FIELDS} FROM topics WHERE topic_ref=$1"),
                &[&command.topic_ref],
            )
            .await?
            .ok_or_else(|| SocialError::Integrity("topic declaration disappeared".into()))?;
        if row.get::<_, String>("space_ref") != command.space_ref
            || row.get::<_, String>("title") != command.title
            || row.get::<_, String>("created_by_actor_ref") != command.actor_ref
        {
            return Err(SocialError::Conflict(
                "topic_ref already exists with different initial semantics".into(),
            ));
        }
        (row, "existing")
    };
    let result = topic_created_response(&row, admission)?;
    record_receipt(
        &tx,
        &command.client_request_id,
        "topic.create",
        &request_digest,
        &result,
    )
    .await?;
    tx.commit().await?;
    Ok(result)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ParticipationStanding {
    Joined,
    Left,
    Observer,
}
impl ParticipationStanding {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Joined => "joined",
            Self::Left => "left",
            Self::Observer => "observer",
        }
    }
}

/// Current desired-state participation; no command receipt. A historical
/// joined request must not prevent a later left -> joined transition.
pub async fn set_participation(
    client: &mut Client,
    space_ref: &str,
    actor_ref: &str,
    standing: ParticipationStanding,
    _client_request_id: &str,
) -> Result<Value> {
    let tx = client.transaction().await?;
    if tx
        .query_opt("SELECT 1 FROM spaces WHERE space_ref=$1", &[&space_ref])
        .await?
        .is_none()
    {
        return Err(SocialError::not_found(MissingKind::Space, space_ref));
    }
    require_actor(&tx, actor_ref).await?;
    let inserted = tx
        .query_opt(
            "INSERT INTO participations(space_ref,actor_ref,standing) VALUES($1,$2,$3) \
         ON CONFLICT (space_ref,actor_ref) DO UPDATE \
         SET standing=EXCLUDED.standing,updated_at=clock_timestamp(),\
             change_sequence=swf_next_change_sequence() \
         WHERE participations.standing IS DISTINCT FROM EXCLUDED.standing \
         RETURNING space_ref,actor_ref,standing,updated_at,\
                   EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz",
            &[&space_ref, &actor_ref, &standing.as_str()],
        )
        .await?;
    let row = if let Some(row) = inserted {
        row
    } else {
        tx.query_opt(
            "SELECT space_ref,actor_ref,standing,updated_at,\
                    EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz \
             FROM participations WHERE space_ref=$1 AND actor_ref=$2",
            &[&space_ref, &actor_ref],
        )
        .await?
        .ok_or_else(|| SocialError::Integrity("participation update disappeared".into()))?
    };
    let result = json!({
        "schemaVersion":1,"kind":"ordivon.host-participation",
        "spaceRef":row.get::<_,String>("space_ref"),
        "actorRef":row.get::<_,String>("actor_ref"),
        "standing":row.get::<_,String>("standing"),
        "updatedAt":exact_time(row.get("updated_at"),row.get("updated_tz"))?,
        "truthBoundary":"social participation only; not ownership, authentication, authorization, assignment, or EffectAuthority",
    });
    tx.commit().await?;
    Ok(result)
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CreateSpace {
    pub space_ref: String,
    pub purpose: String,
    pub actor_ref: String,
    #[serde(default)]
    pub subject_refs: Vec<String>,
    pub client_request_id: String,
}

fn python_whitespace(ch: char) -> bool {
    ch.is_whitespace() || ('\u{001c}'..='\u{001f}').contains(&ch)
}
fn validate_printable_space_text(value: &str, min: usize, max: usize, field: &str) -> Result<()> {
    validate_ref(value, min, max, field)?;
    if value.trim_matches(python_whitespace) != value || value.chars().any(|ch| (ch as u32) < 0x20)
    {
        return Err(SocialError::Invalid(
            "space fields must be trimmed printable text".into(),
        ));
    }
    Ok(())
}
impl CreateSpace {
    fn validate(&self) -> Result<()> {
        validate_printable_space_text(&self.space_ref, 3, 1024, "space_ref")?;
        validate_printable_space_text(&self.purpose, 1, 4096, "purpose")?;
        validate_printable_space_text(&self.actor_ref, 3, 512, "actor_ref")?;
        validate_ref(&self.client_request_id, 1, 1024, "client_request_id")?;
        if self.subject_refs.len() > 256 {
            return Err(SocialError::Invalid(
                "subject_refs must contain at most 256 entries".into(),
            ));
        }
        let mut seen = std::collections::BTreeSet::new();
        for reference in &self.subject_refs {
            if !seen.insert(reference) {
                return Err(SocialError::Invalid("subject_refs must be unique".into()));
            }
            if reference.is_empty() || reference.trim_matches(python_whitespace) != reference {
                return Err(SocialError::Invalid(
                    "subject refs must be non-empty trimmed text".into(),
                ));
            }
            if reference.chars().count() > 2048 {
                return Err(SocialError::Invalid(
                    "subject refs must be at most 2048 characters".into(),
                ));
            }
        }
        Ok(())
    }
}

fn space_projection_row_time(row: &Row, field: &str, tz: &str) -> Result<String> {
    exact_time(row.get(field), row.get(tz))
}

/// Same bounded embedded projection as Python's _get_space_in_tx. The row
/// counts and returned prefix are from a SINGLE caller-owned PG transaction.
/// Social participation does not prove IAM, Work ownership or delegation.
async fn space_projection_in_tx(
    tx: &tokio_postgres::Transaction<'_>,
    space_ref: &str,
    participant_limit: i64,
    topic_limit: i64,
    max_bytes: usize,
) -> Result<Value> {
    if !(1..=200).contains(&participant_limit) || !(1..=200).contains(&topic_limit) {
        return Err(SocialError::Invalid(
            "embedded participant/topic limits must be in [1,200]".into(),
        ));
    }
    if !(1_048_576..=4_194_304).contains(&max_bytes) {
        return Err(SocialError::Invalid(
            "max_bytes must be in [1048576,4194304]".into(),
        ));
    }
    let space = tx
        .query_opt(
            "SELECT space_ref,purpose,created_by_actor_ref,created_at,\
                EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz \
         FROM spaces WHERE space_ref=$1",
            &[&space_ref],
        )
        .await?
        .ok_or_else(|| SocialError::not_found(MissingKind::Space, space_ref))?;
    let subject_count: i64 = tx
        .query_one(
            "SELECT count(*) FROM space_subjects WHERE space_ref=$1",
            &[&space_ref],
        )
        .await?
        .get(0);
    let participant_count: i64 = tx
        .query_one(
            "SELECT count(*) FROM participations WHERE space_ref=$1",
            &[&space_ref],
        )
        .await?
        .get(0);
    let topic_count: i64 = tx
        .query_one(
            "SELECT count(*) FROM topics WHERE space_ref=$1",
            &[&space_ref],
        )
        .await?
        .get(0);
    let subject_rows = tx
        .query(
            "SELECT subject_ref FROM space_subjects WHERE space_ref=$1 \
         ORDER BY subject_ref LIMIT 129",
            &[&space_ref],
        )
        .await?;
    let participant_rows = tx
        .query(
            "SELECT actor_ref,standing,updated_at,\
         EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz \
         FROM participations WHERE space_ref=$1 ORDER BY actor_ref LIMIT $2",
            &[&space_ref, &(participant_limit + 1)],
        )
        .await?;
    let topic_rows = tx
        .query(
            "SELECT topic_ref,title,state,created_by_actor_ref,created_at,updated_at,\
         EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz,\
         EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz \
         FROM topics WHERE space_ref=$1 ORDER BY topic_ref LIMIT $2",
            &[&space_ref, &(topic_limit + 1)],
        )
        .await?;
    let mut subjects = subject_rows
        .iter()
        .take(128)
        .map(|r| r.get::<_, String>("subject_ref"))
        .collect::<Vec<_>>();
    let mut participants = participant_rows
        .iter()
        .take(participant_limit as usize)
        .map(|r| -> Result<Value> {
            Ok(json!({
                "actorRef":r.get::<_,String>("actor_ref"),
                "standing":r.get::<_,String>("standing"),
                "updatedAt":space_projection_row_time(r,"updated_at","updated_tz")?,
            }))
        })
        .collect::<Result<Vec<_>>>()?;
    let mut topics = topic_rows
        .iter()
        .take(topic_limit as usize)
        .map(|r| -> Result<Value> {
            Ok(json!({
                "topicRef":r.get::<_,String>("topic_ref"),
                "title":r.get::<_,String>("title"),
                "state":r.get::<_,String>("state"),
                "createdByActorRef":r.get::<_,String>("created_by_actor_ref"),
                "createdAt":space_projection_row_time(r,"created_at","created_tz")?,
                "updatedAt":space_projection_row_time(r,"updated_at","updated_tz")?,
            }))
        })
        .collect::<Result<Vec<_>>>()?;
    let space_ref = space.get::<_, String>("space_ref");
    let purpose = space.get::<_, String>("purpose");
    let actor_ref = space.get::<_, String>("created_by_actor_ref");
    let created_at = space_projection_row_time(&space, "created_at", "created_tz")?;
    loop {
        let result = json!({
            "schemaVersion":1,"kind":"ordivon.host-space",
            "spaceRef":space_ref,"purpose":purpose,
            "createdByActorRef":actor_ref,"createdAt":created_at,
            "subjectRefs":subjects,"subjectCount":subject_count,
            "subjectHasMore":subjects.len() < subject_count as usize,
            "participants":participants,"participantCount":participant_count,
            "participantHasMore":participants.len() < participant_count as usize,
            "topics":topics,"topicCount":topic_count,
            "topicHasMore":topics.len() < topic_count as usize,
            "truthBoundary":"social organization record only; participation does not imply identity, authority, ownership, or assignment",
        });
        if crate::attention::canonical(&result)?.len() <= max_bytes {
            return Ok(result);
        }
        // Python trims topics first, then participation, then subject refs.
        if !topics.is_empty() {
            topics.pop();
        } else if !participants.is_empty() {
            participants.pop();
        } else if !subjects.is_empty() {
            subjects.pop();
        } else {
            return Err(SocialError::Invalid(
                "max_bytes cannot fit the Space response envelope".into(),
            ));
        }
    }
}

/// The unique space_ref plus transactionally bound Subjects and Receipt
/// preserve Python Host's create semantics and response-loss idempotency.
pub async fn create_space(client: &mut Client, command: &CreateSpace) -> Result<Value> {
    command.validate()?;
    let request_digest = digest(&json!({
        "operation":"space.create","space_ref":command.space_ref,
        "purpose":command.purpose,"actor_ref":command.actor_ref,
        "subject_refs":command.subject_refs,
    }))?;
    let tx = client.transaction().await?;
    if let Some(existing) = claim_receipt(
        &tx,
        &command.client_request_id,
        "space.create",
        &request_digest,
    )
    .await?
    {
        tx.commit().await?;
        return Ok(existing);
    }
    require_actor(&tx, &command.actor_ref).await?;
    let inserted = tx
        .query_opt(
            "INSERT INTO spaces(space_ref,purpose,created_by_actor_ref) VALUES($1,$2,$3) \
         ON CONFLICT (space_ref) DO NOTHING RETURNING space_ref",
            &[&command.space_ref, &command.purpose, &command.actor_ref],
        )
        .await?;
    let admission =
        if inserted.is_some() {
            let mut subjects = command.subject_refs.clone();
            subjects.sort();
            for subject in &subjects {
                tx.execute(
                    "INSERT INTO space_subjects(space_ref,subject_ref) VALUES($1,$2)",
                    &[&command.space_ref, subject],
                )
                .await?;
            }
            "committed"
        } else {
            let row = tx
                .query_opt(
                    "SELECT space_ref,purpose,created_by_actor_ref FROM spaces \
             WHERE space_ref=$1 FOR UPDATE",
                    &[&command.space_ref],
                )
                .await?
                .ok_or_else(|| {
                    SocialError::Integrity("space_ref disappeared after insert conflict".into())
                })?;
            let subjects = tx.query(
            "SELECT subject_ref FROM space_subjects WHERE space_ref=$1 ORDER BY subject_ref",
            &[&command.space_ref]
        ).await?.into_iter().map(
            |r| r.get::<_,String>("subject_ref")
        ).collect::<Vec<_>>();
            let mut requested = command.subject_refs.clone();
            requested.sort();
            if row.get::<_, String>("purpose") != command.purpose
                || row.get::<_, String>("created_by_actor_ref") != command.actor_ref
                || subjects != requested
            {
                return Err(SocialError::Conflict(
                    "space_ref already exists with different initial semantics".into(),
                ));
            }
            "existing"
        };
    let mut result = space_projection_in_tx(&tx, &command.space_ref, 200, 200, 2_097_152).await?;
    result["admission"] = json!(admission);
    record_receipt(
        &tx,
        &command.client_request_id,
        "space.create",
        &request_digest,
        &result,
    )
    .await?;
    tx.commit().await?;
    Ok(result)
}

/// Read-only Space projection via one repeatable-read database snapshot.
pub async fn get_space(
    client: &mut Client,
    space_ref: &str,
    participant_limit: i64,
    topic_limit: i64,
    max_bytes: usize,
) -> Result<Value> {
    let tx = client
        .build_transaction()
        .isolation_level(tokio_postgres::IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    let result =
        space_projection_in_tx(&tx, space_ref, participant_limit, topic_limit, max_bytes).await?;
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

mod message_queries;
pub use message_queries::{get_message, search_messages, SearchMessages};

mod relation_queries;
pub use relation_queries::{list_message_relations, ListMessageRelations, RelationDirection};

mod topic_queries;
pub use topic_queries::list_topics;
