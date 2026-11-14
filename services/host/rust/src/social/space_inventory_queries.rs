//! Read-only Space, Participation, and Subject projections of existing Host PG18 Schema13.
use super::{exact_time, MissingKind, Result, SocialError};
use crate::attention::canonical;
use serde_json::{json, Value};
use tokio_postgres::{Client, IsolationLevel, Row};
const MIN_BYTES: usize = 16_384;
const MAX_BYTES: usize = 4_194_304;
fn budget(limit: i64, maximum: i64, bytes: usize) -> Result<()> {
    if !(1..=maximum).contains(&limit) {
        return Err(SocialError::Invalid(format!(
            "limit must be in [1,{maximum}]"
        )));
    }
    if !(MIN_BYTES..=MAX_BYTES).contains(&bytes) {
        return Err(SocialError::Invalid(format!(
            "max_bytes must be in [{MIN_BYTES},{MAX_BYTES}]"
        )));
    }
    Ok(())
}
fn prefix<T: Clone>(
    candidates: Vec<T>,
    max_bytes: usize,
    mut envelope: impl FnMut(Vec<T>, bool) -> Value,
) -> Result<(Vec<T>, bool)> {
    let mut page = Vec::new();
    for item in candidates {
        let mut proposed = page.clone();
        proposed.push(item);
        if canonical(&envelope(proposed.clone(), true))?.len() > max_bytes {
            if page.is_empty() {
                return Err(SocialError::Invalid(
                    "max_bytes cannot fit one legal item plus response envelope".into(),
                ));
            }
            return Ok((page, true));
        }
        page = proposed;
    }
    Ok((page, false))
}
async fn require_space(tx: &tokio_postgres::Transaction<'_>, space: &str) -> Result<()> {
    if tx
        .query_opt("SELECT 1 FROM spaces WHERE space_ref=$1", &[&space])
        .await?
        .is_none()
    {
        return Err(SocialError::not_found(MissingKind::Space, space));
    }
    Ok(())
}
/// Explicit Subject references are opaque navigation, never authority proofs.
pub async fn list_space_subjects(
    client: &mut Client,
    space_ref: &str,
    after_subject_ref: Option<&str>,
    limit: i64,
    max_bytes: usize,
) -> Result<Value> {
    budget(limit, 500, max_bytes)?;
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    require_space(&tx, space_ref).await?;
    let rows=tx.query(
        "SELECT subject_ref FROM space_subjects WHERE space_ref=$1 AND ($2::text IS NULL OR subject_ref>$2) ORDER BY subject_ref LIMIT $3",
        &[&space_ref,&after_subject_ref,&(limit+1)]
    ).await?;
    let more_sql = rows.len() > limit as usize;
    let items: Vec<String> = rows
        .iter()
        .take(limit as usize)
        .map(|r| r.get("subject_ref"))
        .collect();
    let envelope = |subjects: Vec<String>, more: bool| {
        let cursor = if more { subjects.last().cloned() } else { None };
        json!({"schemaVersion":1,"kind":"ordivon.host-space-subject-list",
              "spaceRef":space_ref,"subjectRefs":subjects,"hasMore":more,"nextAfterSubjectRef":cursor,
              "rankingApplied":false,
              "truthBoundary":"social subject navigation only; references do not transfer foreign authority"})
    };
    let (page, byte_more) = prefix(items, max_bytes, &envelope)?;
    let result = envelope(page, more_sql || byte_more);
    tx.commit().await?;
    Ok(result)
}
/// Current social standing only, not IAM, Work owner or historic event log.
pub async fn list_participations(
    client: &mut Client,
    space_ref: &str,
    after_actor_ref: Option<&str>,
    limit: i64,
    max_bytes: usize,
) -> Result<Value> {
    budget(limit, 500, max_bytes)?;
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    require_space(&tx, space_ref).await?;
    let rows=tx.query(
        "SELECT actor_ref,standing,updated_at,EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz FROM participations WHERE space_ref=$1 AND ($2::text IS NULL OR actor_ref>$2) ORDER BY actor_ref LIMIT $3",
        &[&space_ref,&after_actor_ref,&(limit+1)]
    ).await?;
    let more_sql = rows.len() > limit as usize;
    let items=rows.iter().take(limit as usize).map(|r|->Result<Value>{
        Ok(json!({"actorRef":r.get::<_,String>("actor_ref"),"standing":r.get::<_,String>("standing"),
            "updatedAt":exact_time(r.get("updated_at"),r.get("updated_tz"))?}))
    }).collect::<Result<Vec<_>>>()?;
    let envelope = |participants: Vec<Value>, more: bool| {
        let cursor = if more {
            participants
                .last()
                .and_then(|p| p["actorRef"].as_str())
                .map(str::to_owned)
        } else {
            None
        };
        json!({"schemaVersion":1,"kind":"ordivon.host-participation-list",
              "spaceRef":space_ref,"participants":participants,"hasMore":more,"nextAfterActorRef":cursor,
              "rankingApplied":false,
              "truthBoundary":"social participation only; not IAM, ownership, assignment, or authorization"})
    };
    let (page, byte_more) = prefix(items, max_bytes, &envelope)?;
    let result = envelope(page, more_sql || byte_more);
    tx.commit().await?;
    Ok(result)
}
#[derive(Clone, Debug)]
pub struct ListSpaces<'a> {
    pub actor_ref: Option<&'a str>,
    pub subject_ref: Option<&'a str>,
    pub limit: i64,
    pub before_created_at: Option<&'a str>,
    pub before_space_ref: Option<&'a str>,
    pub max_bytes: usize,
}
fn space_wire(row: &Row) -> Result<Value> {
    Ok(json!({"spaceRef":row.get::<_,String>("space_ref"),
        "purpose":row.get::<_,String>("purpose"),"openTopicCount":row.get::<_,i64>("open_topics"),
        "activeParticipantCount":row.get::<_,i64>("active_participants"),
        "createdAt":exact_time(row.get("created_at"),row.get("created_tz"))?}))
}
/// Stable descending composite timestamp+reference keyset; no secondary
/// index or separate storage. Only Space current projection, not Work lifecycle.
pub async fn list_spaces(client: &mut Client, input: &ListSpaces<'_>) -> Result<Value> {
    budget(input.limit, 200, input.max_bytes)?;
    if input.before_created_at.is_some() != input.before_space_ref.is_some() {
        return Err(SocialError::Invalid(
            "before_created_at and before_space_ref must be supplied together".into(),
        ));
    }
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    if let Some(actor) = input.actor_ref {
        if tx
            .query_opt("SELECT 1 FROM actor_refs WHERE actor_ref=$1", &[&actor])
            .await?
            .is_none()
        {
            return Err(SocialError::not_found(MissingKind::Actor, actor));
        }
    }
    let rows=tx.query(
        "SELECT s.space_ref,s.purpose,s.created_at,EXTRACT(TIMEZONE FROM s.created_at)::integer AS created_tz,\
         (SELECT count(*) FROM topics t WHERE t.space_ref=s.space_ref AND t.state='open') AS open_topics,\
         (SELECT count(*) FROM participations p WHERE p.space_ref=s.space_ref AND p.standing IN ('joined','observer')) AS active_participants \
         FROM spaces s WHERE \
         ($1::text IS NULL OR EXISTS(SELECT 1 FROM participations p WHERE p.space_ref=s.space_ref AND p.actor_ref=$1 AND p.standing IN ('joined','observer'))) \
         AND ($2::text IS NULL OR EXISTS(SELECT 1 FROM space_subjects ss WHERE ss.space_ref=s.space_ref AND ss.subject_ref=$2)) \
         AND ($3::text IS NULL OR (s.created_at,s.space_ref) < (($3::text)::timestamptz,$4::text)) \
         ORDER BY s.created_at DESC,s.space_ref DESC LIMIT $5",
        &[&input.actor_ref,&input.subject_ref,&input.before_created_at,&input.before_space_ref,&(input.limit+1)]
    ).await?;
    let more_sql = rows.len() > input.limit as usize;
    let items = rows
        .iter()
        .take(input.limit as usize)
        .map(space_wire)
        .collect::<Result<Vec<_>>>()?;
    let envelope = |spaces: Vec<Value>, more: bool| {
        let cursor = if more {
            spaces
                .last()
                .map(|s| json!({"beforeCreatedAt":s["createdAt"],"beforeSpaceRef":s["spaceRef"]}))
        } else {
            None
        };
        json!({"schemaVersion":1,"kind":"ordivon.host-space-list","spaces":spaces,"hasMore":more,
              "nextCursor":cursor,"rankingApplied":false,
              "truthBoundary":"compact social-space locator only; participation is not ownership, authority, or assignment"})
    };
    let (page, byte_more) = prefix(items, input.max_bytes, &envelope)?;
    let result = envelope(page, more_sql || byte_more);
    tx.commit().await?;
    Ok(result)
}
