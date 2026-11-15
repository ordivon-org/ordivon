//! Durable Work intake/claim/delivery/review through existing Host PG13 Work CAS.
//!
//! This is semantic accountability, not Runtime job assignment, agent identity,
//! process ownership, an Artifact blob store, or proof that a physical effect
//! happened. Every transition writes one immutable Work snapshot and receipt.
use chrono::{DateTime, Utc};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tokio_postgres::{types::Json, Client, IsolationLevel};

use super::{
    canonical_digest, claim_receipt, ensure_safe_json_numbers, get_work_in_tx, postgres_timestamp,
    record_receipt, validate_identifier, WorkError, WorkState,
};

const MAX_SAFE_JSON_INT: i64 = 9_007_199_254_740_991;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum Phase {
    Offered,
    Claimed,
    Submitted,
    Returned,
    Accepted,
    Cancelled,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ReviewDecision {
    Accepted,
    Returned,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Delivery {
    pub delivery_ref: String,
    pub summary: String,
    pub output_refs: Vec<String>,
    pub evidence_refs: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Review {
    pub decision: ReviewDecision,
    pub rationale: String,
    pub verification_refs: Vec<String>,
}

/// The contract lives inside the existing immutable work_snapshots.payload.
/// Historical snapshots preserve every offer, claim, returned delivery, etc.
/// Missing 'engagement' is the original pre-migration Work representation.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkEngagement {
    pub schema_version: u8,
    pub phase: Phase,
    pub requested_by_actor_ref: String,
    pub consumer_actor_ref: String,
    pub acceptance_criteria: Vec<String>,
    pub claim_epoch: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub assignee_actor_ref: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delivery: Option<Delivery>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub review: Option<Review>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_note: Option<String>,
}

/// One explicit accountability event, *not* a Runtime dispatch request.
/// Serde variant tagging is the sole command representation.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(
    tag = "type",
    rename_all = "snake_case",
    rename_all_fields = "camelCase"
)]
pub enum EngagementAction {
    Offer {
        consumer_actor_ref: String,
        acceptance_criteria: Vec<String>,
    },
    Claim,
    Release {
        reason: String,
    },
    Submit {
        claim_epoch: i64,
        delivery_ref: String,
        summary: String,
        output_refs: Vec<String>,
        evidence_refs: Vec<String>,
    },
    Review {
        claim_epoch: i64,
        decision: ReviewDecision,
        rationale: String,
        verification_refs: Vec<String>,
    },
    Cancel {
        reason: String,
    },
}

#[derive(Clone, Debug)]
pub struct AdvanceEngagement {
    pub work_ref: String,
    pub expected_revision: i64,
    pub actor_ref: String,
    pub action: EngagementAction,
    pub client_request_id: String,
}

fn actor_ref(reference: &str) -> Result<(), WorkError> {
    validate_identifier(reference, 3, 512)?;
    if !reference.contains(':') {
        return Err(WorkError::Invalid("actor_ref must be namespaced".into()));
    }
    Ok(())
}

fn nonempty_text(text: &str, max: usize, label: &str) -> Result<(), WorkError> {
    if text.is_empty() || text.chars().count() > max || text.trim() != text {
        return Err(WorkError::Invalid(format!(
            "{label} requires trimmed 1..={max} text"
        )));
    }
    Ok(())
}

fn refs(values: &[String], max: usize, label: &str) -> Result<(), WorkError> {
    if values.len() > max {
        return Err(WorkError::Invalid(format!("{label} exceeds {max} items")));
    }
    for reference in values {
        validate_identifier(reference, 3, 1024)?;
        if !reference.contains(':') {
            return Err(WorkError::Invalid(format!(
                "{label} requires opaque namespaced refs"
            )));
        }
    }
    Ok(())
}

impl WorkEngagement {
    fn validate(&self) -> Result<(), WorkError> {
        if self.schema_version != 1 {
            return Err(WorkError::Invalid(
                "unknown engagement schemaVersion".into(),
            ));
        }
        actor_ref(&self.requested_by_actor_ref)?;
        actor_ref(&self.consumer_actor_ref)?;
        if self.acceptance_criteria.is_empty() || self.acceptance_criteria.len() > 32 {
            return Err(WorkError::Invalid(
                "acceptanceCriteria must contain 1..=32 items".into(),
            ));
        }
        for criterion in &self.acceptance_criteria {
            nonempty_text(criterion, 2048, "acceptance criterion")?;
        }
        if !(0..=MAX_SAFE_JSON_INT).contains(&self.claim_epoch) {
            return Err(WorkError::Invalid(
                "claimEpoch exceeds safe monotonic domain".into(),
            ));
        }
        if let Some(owner) = &self.assignee_actor_ref {
            actor_ref(owner)?;
        }
        if let Some(note) = &self.transition_note {
            nonempty_text(note, 4096, "transitionNote")?;
        }
        if let Some(delivery) = &self.delivery {
            validate_identifier(&delivery.delivery_ref, 3, 1024)?;
            if !delivery.delivery_ref.contains(':') {
                return Err(WorkError::Invalid("deliveryRef requires namespace".into()));
            }
            nonempty_text(&delivery.summary, 4096, "delivery summary")?;
            refs(&delivery.output_refs, 64, "outputRefs")?;
            refs(&delivery.evidence_refs, 64, "evidenceRefs")?;
            if delivery.output_refs.is_empty() || delivery.evidence_refs.is_empty() {
                return Err(WorkError::Invalid(
                    "delivery requires output and evidence references".into(),
                ));
            }
        }
        if let Some(review) = &self.review {
            nonempty_text(&review.rationale, 4096, "review rationale")?;
            refs(&review.verification_refs, 64, "verificationRefs")?;
            if review.verification_refs.is_empty() {
                return Err(WorkError::Invalid(
                    "review requires consumer verification references".into(),
                ));
            }
        }
        match self.phase {
            Phase::Offered
                if self.assignee_actor_ref.is_none()
                    && self.delivery.is_none()
                    && self.review.is_none() => {}
            Phase::Claimed
                if self.claim_epoch > 0
                    && self.assignee_actor_ref.is_some()
                    && self.delivery.is_none()
                    && self.review.is_none() => {}
            Phase::Submitted
                if self.claim_epoch > 0
                    && self.assignee_actor_ref.is_some()
                    && self.delivery.is_some()
                    && self.review.is_none() => {}
            Phase::Returned | Phase::Accepted
                if self.claim_epoch > 0
                    && self.assignee_actor_ref.is_some()
                    && self.delivery.is_some()
                    && self.review.as_ref().is_some_and(|r| {
                        (self.phase == Phase::Accepted && r.decision == ReviewDecision::Accepted)
                            || (self.phase == Phase::Returned
                                && r.decision == ReviewDecision::Returned)
                    }) => {}
            Phase::Cancelled => {}
            _ => {
                return Err(WorkError::Invalid(
                    "inconsistent engagement phase and evidence".into(),
                ));
            }
        }
        Ok(())
    }
}

impl AdvanceEngagement {
    fn validate(&self) -> Result<(), WorkError> {
        validate_identifier(&self.work_ref, 3, 1024)?;
        actor_ref(&self.actor_ref)?;
        if !(1..MAX_SAFE_JSON_INT).contains(&self.expected_revision) {
            return Err(WorkError::Invalid(
                "expectedRevision must be positive safe predecessor".into(),
            ));
        }
        if self.client_request_id.is_empty()
            || self.client_request_id.trim() != self.client_request_id
        {
            return Err(WorkError::Invalid("invalid clientRequestId".into()));
        }
        Ok(())
    }
}

fn transition(
    old: Option<WorkEngagement>,
    action: &EngagementAction,
    caller: &str,
    creator: &str,
) -> Result<(WorkEngagement, WorkState), WorkError> {
    let conflict = |detail: &str| WorkError::Conflict(detail.into());
    let result = match (old, action) {
        (
            None,
            EngagementAction::Offer {
                consumer_actor_ref,
                acceptance_criteria,
            },
        ) => {
            if caller != creator {
                return Err(conflict(
                    "only creating ActorRef can offer pre-existing Work",
                ));
            }
            WorkEngagement {
                schema_version: 1,
                phase: Phase::Offered,
                requested_by_actor_ref: caller.to_string(),
                consumer_actor_ref: consumer_actor_ref.clone(),
                acceptance_criteria: acceptance_criteria.clone(),
                claim_epoch: 0,
                assignee_actor_ref: None,
                delivery: None,
                review: None,
                transition_note: None,
            }
        }
        (Some(mut previous), EngagementAction::Claim)
            if matches!(previous.phase, Phase::Offered | Phase::Returned) =>
        {
            previous.claim_epoch = previous
                .claim_epoch
                .checked_add(1)
                .filter(|v| *v <= MAX_SAFE_JSON_INT)
                .ok_or_else(|| conflict("claim epoch exhausted"))?;
            previous.phase = Phase::Claimed;
            previous.assignee_actor_ref = Some(caller.to_string());
            previous.delivery = None;
            previous.review = None;
            previous.transition_note = None;
            previous
        }
        (Some(mut previous), EngagementAction::Release { reason })
            if previous.phase == Phase::Claimed =>
        {
            if caller != previous.requested_by_actor_ref
                && previous.assignee_actor_ref.as_deref() != Some(caller)
            {
                return Err(conflict("only requester or claimed actor can release"));
            }
            previous.phase = Phase::Offered;
            previous.assignee_actor_ref = None;
            previous.delivery = None;
            previous.review = None;
            previous.transition_note = Some(reason.clone());
            previous
        }
        (
            Some(mut previous),
            EngagementAction::Submit {
                claim_epoch,
                delivery_ref,
                summary,
                output_refs,
                evidence_refs,
            },
        ) if previous.phase == Phase::Claimed => {
            if previous.assignee_actor_ref.as_deref() != Some(caller)
                || *claim_epoch != previous.claim_epoch
            {
                return Err(conflict("stale claim epoch or wrong submitting ActorRef"));
            }
            previous.phase = Phase::Submitted;
            previous.delivery = Some(Delivery {
                delivery_ref: delivery_ref.clone(),
                summary: summary.clone(),
                output_refs: output_refs.clone(),
                evidence_refs: evidence_refs.clone(),
            });
            previous.review = None;
            previous.transition_note = None;
            previous
        }
        (
            Some(mut previous),
            EngagementAction::Review {
                claim_epoch,
                decision,
                rationale,
                verification_refs,
            },
        ) if previous.phase == Phase::Submitted => {
            if caller != previous.consumer_actor_ref || *claim_epoch != previous.claim_epoch {
                return Err(conflict(
                    "review requires designated consumer and matching claim epoch",
                ));
            }
            previous.phase = if *decision == ReviewDecision::Accepted {
                Phase::Accepted
            } else {
                Phase::Returned
            };
            previous.review = Some(Review {
                decision: *decision,
                rationale: rationale.clone(),
                verification_refs: verification_refs.clone(),
            });
            previous.transition_note = None;
            previous
        }
        (Some(mut previous), EngagementAction::Cancel { reason })
            if !matches!(previous.phase, Phase::Accepted | Phase::Cancelled) =>
        {
            if caller != previous.requested_by_actor_ref {
                return Err(conflict("only requester can cancel active accountability"));
            }
            previous.phase = Phase::Cancelled;
            previous.transition_note = Some(reason.clone());
            previous
        }
        _ => return Err(conflict("invalid or stale Work engagement transition")),
    };
    result.validate()?;
    let work_state = match result.phase {
        Phase::Accepted => WorkState::Completed,
        Phase::Cancelled => WorkState::Abandoned,
        _ => WorkState::Open,
    };
    Ok((result, work_state))
}

/// A bounded read model over the existing immutable Work snapshots.
///
/// This deliberately makes no unproved promise that pagination across several
/// HTTP requests is one frozen MVCC snapshot: *each page* is one RR snapshot.
/// Offered/returned Work is discoverable without a duplicate task queue.
#[derive(Clone, Debug)]
pub struct ListEngagements {
    pub phase: Option<Phase>,
    pub assignee_actor_ref: Option<String>,
    pub consumer_actor_ref: Option<String>,
    pub limit: usize,
    pub max_bytes: usize,
    pub before_updated_at: Option<String>,
    pub before_work_ref: Option<String>,
}

impl Default for ListEngagements {
    fn default() -> Self {
        Self {
            phase: None,
            assignee_actor_ref: None,
            consumer_actor_ref: None,
            limit: 50,
            max_bytes: 262_144,
            before_updated_at: None,
            before_work_ref: None,
        }
    }
}

impl Phase {
    fn as_str(self) -> &'static str {
        match self {
            Self::Offered => "offered",
            Self::Claimed => "claimed",
            Self::Submitted => "submitted",
            Self::Returned => "returned",
            Self::Accepted => "accepted",
            Self::Cancelled => "cancelled",
        }
    }
}

impl ListEngagements {
    fn validate(&self) -> Result<(), WorkError> {
        if !(1..=200).contains(&self.limit) {
            return Err(WorkError::Invalid("limit must be in 1..=200".into()));
        }
        if !(16_384..=4_194_304).contains(&self.max_bytes) {
            return Err(WorkError::Invalid(
                "maxBytes must be in 16384..=4194304".into(),
            ));
        }
        if self.before_updated_at.is_some() != self.before_work_ref.is_some() {
            return Err(WorkError::Invalid(
                "beforeUpdatedAt and beforeWorkRef are a required pair".into(),
            ));
        }
        if let Some(timestamp) = &self.before_updated_at {
            DateTime::parse_from_rfc3339(timestamp).map_err(|_| {
                WorkError::Invalid("beforeUpdatedAt must be an RFC3339 timestamp".into())
            })?;
        }
        if let Some(reference) = &self.before_work_ref {
            validate_identifier(reference, 3, 1024)?;
        }
        if let Some(reference) = &self.assignee_actor_ref {
            actor_ref(reference)?;
        }
        if let Some(reference) = &self.consumer_actor_ref {
            actor_ref(reference)?;
        }
        Ok(())
    }
}

fn engagement_list_envelope(items: &[Value], more: bool) -> Value {
    let next = if more {
        items.last().map(|last| {
            json!({
                "beforeUpdatedAt":last["updatedAt"],
                "beforeWorkRef":last["workRef"],
            })
        })
    } else {
        None
    };
    json!({
        "schemaVersion":1,
        "kind":"ordivon.host-work-engagement-list",
        "engagements":items,
        "hasMore":more,
        "nextCursor":next,
        "rankingApplied":false,
        "truthBoundary":"Host declared Work accountability; not Runtime dispatch, actor authentication, Artifact verification, priority, or a cross-page frozen snapshot",
    })
}

/// Existing indexes: works_state_updated_idx and work_snapshots PK. No new DDL.
/// Query cost must be benchmarked before promising high-volume task discovery.
pub async fn list_engagements(
    client: &mut Client,
    input: &ListEngagements,
) -> Result<Value, WorkError> {
    input.validate()?;
    let phase = input.phase.map(Phase::as_str);
    let consumer = input.consumer_actor_ref.as_deref();
    let assignee = input.assignee_actor_ref.as_deref();
    let before_at = input.before_updated_at.as_deref();
    let before_ref = input.before_work_ref.as_deref();
    let limit_plus_one =
        i64::try_from(input.limit + 1).map_err(|_| WorkError::Invalid("limit overflow".into()))?;
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    let rows = tx
        .query(
            "SELECT w.work_ref,w.kind,w.state,w.current_revision,w.current_snapshot_digest, \
         w.updated_at,EXTRACT(TIMEZONE FROM w.updated_at)::integer AS updated_tz,s.payload \
         FROM works w JOIN work_snapshots s ON s.work_ref=w.work_ref \
         AND s.revision=w.current_revision \
         WHERE s.payload ? 'engagement' \
         AND ($1::text IS NULL OR s.payload #>> '{engagement,phase}'=$1) \
         AND ($2::text IS NULL OR s.payload #>> '{engagement,consumerActorRef}'=$2) \
         AND ($3::text IS NULL OR s.payload #>> '{engagement,assigneeActorRef}'=$3) \
         AND ($4::text::timestamptz IS NULL OR \
              (w.updated_at,w.work_ref)<($4::text::timestamptz,$5)) \
         ORDER BY w.updated_at DESC,w.work_ref DESC LIMIT $6",
            &[
                &phase,
                &consumer,
                &assignee,
                &before_at,
                &before_ref,
                &limit_plus_one,
            ],
        )
        .await?;
    let sql_more = rows.len() > input.limit;
    let mut page: Vec<Value> = Vec::new();
    let mut byte_more = false;
    for row in rows.iter().take(input.limit) {
        let Json(payload): Json<Value> = row.try_get("payload")?;
        let digest: String = row.try_get("current_snapshot_digest")?;
        if canonical_digest(&payload)? != digest {
            return Err(WorkError::Integrity(
                "current engaged Work digest is invalid".into(),
            ));
        }
        let engagement: WorkEngagement = serde_json::from_value(
            payload
                .get("engagement")
                .cloned()
                .ok_or_else(|| WorkError::Integrity("engagement JSON disappeared".into()))?,
        )
        .map_err(|err| WorkError::Integrity(format!("invalid engagement JSON: {err}")))?;
        engagement.validate().map_err(|err| {
            WorkError::Integrity(format!("corrupt Work engagement standing: {err}"))
        })?;
        let observed_state: String = row.try_get("state")?;
        let expected_state = match engagement.phase {
            Phase::Accepted => "completed",
            Phase::Cancelled => "abandoned",
            _ => "open",
        };
        if observed_state != expected_state {
            return Err(WorkError::Integrity(
                "Work state contradicts engagement phase".into(),
            ));
        }
        let timestamp: DateTime<Utc> = row.try_get("updated_at")?;
        let tz: i32 = row.try_get("updated_tz")?;
        let item = json!({
            "workRef":row.try_get::<_, String>("work_ref")?,
            "workKind":row.try_get::<_, String>("kind")?,
            "state":observed_state,
            "revision":row.try_get::<_, i64>("current_revision")?,
            "snapshotDigest":digest,
            "updatedAt":postgres_timestamp(timestamp,tz)?,
            "engagement":engagement,
        });
        page.push(item);
        let candidate = engagement_list_envelope(&page, true);
        ensure_safe_json_numbers(&candidate)?;
        let length = serde_json_canonicalizer::to_vec(&candidate)
            .map_err(|err| WorkError::Invalid(err.to_string()))?
            .len();
        if length > input.max_bytes {
            page.pop();
            if page.is_empty() {
                return Err(WorkError::Invalid(
                    "maxBytes cannot fit one Work engagement and response envelope".into(),
                ));
            }
            byte_more = true;
            break;
        }
    }
    tx.commit().await?;
    Ok(engagement_list_envelope(&page, sql_more || byte_more))
}

/// Transactional CAS: exactly one state + immutable snapshot + receipt.
/// An expired/unresponsive Agent does not prove physical side effects undone.
/// claimEpoch only fences *Host accountability* updates, not Runtime effects.
pub async fn advance_engagement(
    client: &mut Client,
    command: &AdvanceEngagement,
) -> Result<Value, WorkError> {
    command.validate()?;
    const OP: &str = "work.engagement.advance";
    let request = json!({
        "operation": OP,
        "workRef": command.work_ref,
        "expectedRevision": command.expected_revision,
        "actorRef": command.actor_ref,
        "action": command.action,
    });
    let digest = canonical_digest(&request)?;
    let tx = client.transaction().await?;
    if let Some(previous) = claim_receipt(&tx, &command.client_request_id, OP, &digest).await? {
        tx.commit().await?;
        return Ok(previous);
    }
    if tx
        .query_opt(
            "SELECT 1 FROM actor_refs WHERE actor_ref=$1",
            &[&command.actor_ref],
        )
        .await?
        .is_none()
    {
        return Err(WorkError::ActorNotFound(command.actor_ref.clone()));
    }
    let work = tx
        .query_opt(
            "SELECT state,current_revision,current_snapshot_digest,created_by_actor_ref \
          FROM works WHERE work_ref=$1 FOR UPDATE",
            &[&command.work_ref],
        )
        .await?
        .ok_or_else(|| WorkError::NotFound(command.work_ref.clone()))?;
    let state: String = work.try_get("state")?;
    let revision: i64 = work.try_get("current_revision")?;
    let creator: String = work.try_get("created_by_actor_ref")?;
    let digest_before: String = work.try_get("current_snapshot_digest")?;
    if state != "open" || revision != command.expected_revision {
        return Err(WorkError::Conflict(
            "Work is terminal or expectedRevision lost CAS race".into(),
        ));
    }
    let row = tx
        .query_opt(
            "SELECT payload FROM work_snapshots WHERE work_ref=$1 AND revision=$2",
            &[&command.work_ref, &revision],
        )
        .await?
        .ok_or_else(|| WorkError::Integrity("current Work snapshot missing".into()))?;
    let Json(mut payload): Json<Value> = row.try_get("payload")?;
    if canonical_digest(&payload)? != digest_before {
        return Err(WorkError::Integrity(
            "current Work snapshot digest mismatches authority".into(),
        ));
    }
    let object = payload.as_object_mut().ok_or_else(|| {
        WorkError::Integrity("Work snapshot JSON payload is not an object".into())
    })?;
    let old: Option<WorkEngagement> = match object.get("engagement") {
        Some(value) => Some(serde_json::from_value(value.clone()).map_err(|e| {
            WorkError::Integrity(format!("existing engagement contract invalid: {e}"))
        })?),
        None => None,
    };
    let (new, next_state) = transition(old, &command.action, &command.actor_ref, &creator)?;
    // No external resolution of these references: presence, not validity,
    // is recorded. Verification belongs to the designated consumer.
    if matches!(&command.action, EngagementAction::Offer { .. })
        && tx
            .query_opt(
                "SELECT 1 FROM actor_refs WHERE actor_ref=$1",
                &[&new.consumer_actor_ref],
            )
            .await?
            .is_none()
    {
        return Err(WorkError::ActorNotFound(new.consumer_actor_ref.clone()));
    }
    // An old returned delivery remains in the immutable history. Never
    // publish the same deliveryRef as a fresh claim-epoch attempt.
    if let EngagementAction::Submit { delivery_ref, .. } = &command.action {
        if tx
            .query_opt(
                "SELECT 1 FROM work_snapshots WHERE work_ref=$1 \
              AND payload #>> '{engagement,delivery,deliveryRef}'=$2 LIMIT 1",
                &[&command.work_ref, delivery_ref],
            )
            .await?
            .is_some()
        {
            return Err(WorkError::Conflict(
                "deliveryRef already exists in Work history".into(),
            ));
        }
    }
    object.insert(
        "engagement".into(),
        serde_json::to_value(&new)
            .map_err(|e| WorkError::Invalid(format!("engagement JSON invalid: {e}")))?,
    );
    let new_digest = canonical_digest(&payload)?;
    let new_revision = revision
        .checked_add(1)
        .ok_or_else(|| WorkError::Conflict("Work revision exhausted".into()))?;
    let updated = tx
        .execute(
            "UPDATE works SET state=$1,current_revision=$2,current_snapshot_digest=$3, \
          updated_at=clock_timestamp() WHERE work_ref=$4 AND current_revision=$5 AND state='open'",
            &[
                &next_state.as_str(),
                &new_revision,
                &new_digest,
                &command.work_ref,
                &revision,
            ],
        )
        .await?;
    if updated != 1 {
        return Err(WorkError::Conflict(
            "engagement CAS lost authoritative update".into(),
        ));
    }
    tx.execute(
        "INSERT INTO work_snapshots(work_ref,revision,snapshot_digest,payload,writer_actor_ref) \
          VALUES ($1,$2,$3,$4,$5)",
        &[
            &command.work_ref,
            &new_revision,
            &new_digest,
            &Json(&payload),
            &command.actor_ref,
        ],
    )
    .await?;
    let mut response = get_work_in_tx(&tx, &command.work_ref, Some(new_revision)).await?;
    response["admission"] = json!("committed");
    record_receipt(&tx, &command.client_request_id, OP, &digest, &response).await?;
    tx.commit().await?;
    Ok(response)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn action(type_: &str) -> EngagementAction {
        match type_ {
            "offer" => EngagementAction::Offer {
                consumer_actor_ref: "actor:consumer".into(),
                acceptance_criteria: vec!["Consumer verifies a referenced artifact".into()],
            },
            "claim" => EngagementAction::Claim,
            _ => unreachable!(),
        }
    }
    #[test]
    fn claim_epoch_and_acceptance_are_not_execution_or_authorization() {
        let (offered, state) =
            transition(None, &action("offer"), "actor:creator", "actor:creator").unwrap();
        assert_eq!(state, WorkState::Open);
        assert_eq!(offered.claim_epoch, 0);
        let (claimed, state) = transition(
            Some(offered),
            &action("claim"),
            "actor:agent",
            "actor:creator",
        )
        .unwrap();
        assert_eq!(state, WorkState::Open);
        assert_eq!(claimed.claim_epoch, 1);
        assert_eq!(claimed.assignee_actor_ref.as_deref(), Some("actor:agent"));
        let wrong = transition(
            Some(claimed.clone()),
            &EngagementAction::Submit {
                claim_epoch: 0,
                delivery_ref: "delivery:stale".into(),
                summary: "done".into(),
                output_refs: vec!["artifact:1".into()],
                evidence_refs: vec!["receipt:1".into()],
            },
            "actor:agent",
            "actor:creator",
        );
        assert!(matches!(wrong, Err(WorkError::Conflict(_))));
    }

    #[test]
    fn no_criteria_or_no_verification_is_not_a_success() {
        assert!(matches!(
            transition(
                None,
                &EngagementAction::Offer {
                    consumer_actor_ref: "actor:consumer".into(),
                    acceptance_criteria: vec![],
                },
                "actor:creator",
                "actor:creator"
            ),
            Err(WorkError::Invalid(_))
        ));
    }
}
