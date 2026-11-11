//! Real but incomplete Rust MCP migration staging surface.
//! Exposes only proved tools; never invents success for the 31-tool Python surface.
use std::sync::Arc;

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::{CallToolResult, ContentBlock, ServerCapabilities, ServerConfig};
use rmcp::{tool, tool_handler, tool_router, ServerHandler};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use crate::attention::{self, TargetKind};
use crate::pg::{HostDbError, HostPg};
use crate::social::{self, AddMessageRelation, CreateSpace, CreateTopic, PostMessage};
use crate::work::{self, ActorDeclare, WorkSnapshot, WorkState};

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct SpaceCreateRequest {
    pub space_ref: String,
    pub purpose: String,
    pub actor_ref: String,
    // Python MCP's optional subjectRefs=None means [] at the Domain boundary.
    #[serde(default)]
    pub subject_refs: Option<Vec<String>>,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct SpaceGetRequest {
    pub space_ref: String,
    #[serde(default = "embedded_collection_limit")]
    pub participant_limit: i64,
    #[serde(default = "embedded_collection_limit")]
    pub topic_limit: i64,
    #[serde(default = "space_get_max_bytes")]
    pub max_bytes: usize,
}
const fn embedded_collection_limit() -> i64 {
    200
}
const fn space_get_max_bytes() -> usize {
    2_097_152
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct TopicCreateRequest {
    pub topic_ref: String,
    pub space_ref: String,
    pub title: String,
    pub actor_ref: String,
}

#[derive(Clone, Copy, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "lowercase")]
pub enum ParticipationStandingWire {
    Joined,
    Left,
    Observer,
}
impl ParticipationStandingWire {
    fn domain(self) -> social::ParticipationStanding {
        match self {
            Self::Joined => social::ParticipationStanding::Joined,
            Self::Left => social::ParticipationStanding::Left,
            Self::Observer => social::ParticipationStanding::Observer,
        }
    }
    fn as_str(self) -> &'static str {
        match self {
            Self::Joined => "joined",
            Self::Left => "left",
            Self::Observer => "observer",
        }
    }
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct SpaceParticipationSetRequest {
    pub space_ref: String,
    pub actor_ref: String,
    pub standing: ParticipationStandingWire,
}

#[derive(Clone, Copy, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "lowercase")]
pub enum ActorKindWire {
    Unknown,
    Human,
    Agent,
    Service,
    Organization,
}
impl ActorKindWire {
    fn domain(self) -> work::ActorKind {
        match self {
            Self::Unknown => work::ActorKind::Unknown,
            Self::Human => work::ActorKind::Human,
            Self::Agent => work::ActorKind::Agent,
            Self::Service => work::ActorKind::Service,
            Self::Organization => work::ActorKind::Organization,
        }
    }
    fn as_str(self) -> &'static str {
        match self {
            Self::Unknown => "unknown",
            Self::Human => "human",
            Self::Agent => "agent",
            Self::Service => "service",
            Self::Organization => "organization",
        }
    }
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct ActorDeclareRequest {
    pub actor_ref: String,
    pub actor_kind: ActorKindWire,
}

#[derive(Clone, Copy, Debug, Deserialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum HostStatusDetail {
    Summary,
    Integrity,
    History,
}

#[derive(Debug, Deserialize, JsonSchema)]
pub struct HostStatusRequest {
    #[serde(default = "summary_detail")]
    pub detail: HostStatusDetail,
}

const fn summary_detail() -> HostStatusDetail {
    HostStatusDetail::Summary
}
impl HostStatusDetail {
    const fn as_str(self) -> &'static str {
        match self {
            Self::Summary => "summary",
            Self::Integrity => "integrity",
            Self::History => "history",
        }
    }
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct WorkGetRequest {
    pub work_ref: String,
    #[serde(default)]
    pub revision: Option<i64>,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkSnapshotWire {
    pub objective: String,
    pub frontier: String,
    #[serde(default)]
    pub established: Vec<String>,
    #[serde(default)]
    pub unresolved: Vec<String>,
    #[serde(default)]
    pub rejected: Vec<String>,
    #[serde(default)]
    pub constraints: Vec<String>,
    #[serde(default, alias = "next_actions")]
    pub next_actions: Vec<String>,
    #[serde(default, alias = "reference_refs")]
    pub reference_refs: Vec<String>,
}

impl From<WorkSnapshotWire> for WorkSnapshot {
    fn from(wire: WorkSnapshotWire) -> Self {
        Self {
            objective: wire.objective,
            frontier: wire.frontier,
            established: wire.established,
            unresolved: wire.unresolved,
            rejected: wire.rejected,
            constraints: wire.constraints,
            next_actions: wire.next_actions,
            reference_refs: wire.reference_refs,
        }
    }
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct WorkCommitRequest {
    pub work_ref: String,
    pub expected_revision: i64,
    pub snapshot: WorkSnapshotWire,
    pub actor_ref: String,
    #[serde(default)]
    pub continuity_disposition: ContinuityDisposition,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct WorkCreateRequest {
    pub work_ref: String,
    pub work_kind: String,
    pub actor_ref: String,
    pub initial_snapshot: WorkSnapshotWire,
}

#[derive(Clone, Copy, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "lowercase")]
pub enum WorkListState {
    Open,
    Completed,
    Abandoned,
}

impl From<WorkListState> for WorkState {
    fn from(value: WorkListState) -> Self {
        match value {
            WorkListState::Open => WorkState::Open,
            WorkListState::Completed => WorkState::Completed,
            WorkListState::Abandoned => WorkState::Abandoned,
        }
    }
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct WorkListRequest {
    #[serde(default)]
    #[schemars(default)]
    pub state: Option<WorkListState>,
    #[serde(default = "work_list_limit")]
    pub limit: usize,
    #[serde(default)]
    pub before_updated_at: Option<String>,
    #[serde(default)]
    pub before_work_ref: Option<String>,
    #[serde(default = "work_list_max_bytes")]
    pub max_bytes: usize,
}

const fn work_list_limit() -> usize {
    50
}
const fn work_list_max_bytes() -> usize {
    262_144
}

/// Preserve Python mcp_work_tools.work_create's exact model_dump(mode="json")
/// request identity, including the snake_case nested Pydantic field names.
fn create_work_client_request_id(
    work_ref: &str,
    kind: &str,
    actor_ref: &str,
    snapshot: &WorkSnapshot,
) -> Result<String, work::WorkError> {
    snapshot.validate()?;
    let python_model_dump = json!({
        "work_ref": work_ref,
        "kind": kind,
        "actor_ref": actor_ref,
        "initial_snapshot": {
            "objective": snapshot.objective,
            "frontier": snapshot.frontier,
            "established": snapshot.established,
            "unresolved": snapshot.unresolved,
            "rejected": snapshot.rejected,
            "constraints": snapshot.constraints,
            "next_actions": snapshot.next_actions,
            "reference_refs": snapshot.reference_refs,
        }
    });
    let digest = work::canonical_digest(&python_model_dump)?;
    Ok(format!(
        "work-create:{}",
        digest.trim_start_matches("sha256:")
    ))
}

#[derive(Clone, Copy, Debug, Default, Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "lowercase")]
pub enum ContinuityDisposition {
    #[default]
    Continue,
    Complete,
    Abandon,
}

impl ContinuityDisposition {
    fn as_str(self) -> &'static str {
        match self {
            Self::Continue => "continue",
            Self::Complete => "complete",
            Self::Abandon => "abandon",
        }
    }
    fn state(self) -> WorkState {
        match self {
            Self::Continue => WorkState::Open,
            Self::Complete => WorkState::Completed,
            Self::Abandon => WorkState::Abandoned,
        }
    }
}

fn tool_error(error: impl std::fmt::Display) -> CallToolResult {
    CallToolResult::error(vec![ContentBlock::text(error.to_string())])
}

fn structured(value: Value) -> CallToolResult {
    CallToolResult::structured(value)
}
/// Only expected Host domain failures receive typed failure semantics.
/// Ambiguous PG/integrity errors never become business conflicts.
fn public_domain_error(
    name: &str,
    code: &str,
    detail: Option<&str>,
    resource: Option<(&str, &str)>,
    retryable: bool,
    suggested_action: &str,
) -> CallToolResult {
    let mut payload = json!({
        "schemaVersion": 1,
        "kind": "ordivon.host-domain-error",
        "code": code,
        "retryable": retryable,
        "suggestedAction": suggested_action
    });
    if let Some(detail) = detail {
        payload["detail"] = json!(detail);
    }
    if let Some((kind, reference)) = resource {
        payload["resourceKind"] = json!(kind);
        payload["resourceRef"] = json!(reference);
    }
    // The Gateway reads structuredContent.error. Preserve the legacy textual
    // error prefix for consumers that still recognize the Python envelope.
    let mut result = CallToolResult::structured_error(json!({"error": payload}));
    result.content = vec![ContentBlock::text(format!(
        "Error executing tool {name}: {}",
        payload
    ))];
    result
}

fn work_domain_tool_error(name: &str, error: work::WorkError) -> CallToolResult {
    match error {
        work::WorkError::Invalid(detail) => public_domain_error(
            name,
            "INVALID_ARGUMENT",
            Some(&detail),
            None,
            false,
            "correct-request",
        ),
        work::WorkError::Conflict(detail) => public_domain_error(
            name,
            "CONFLICT",
            Some(&detail),
            None,
            false,
            "reread-current-state-and-reconcile",
        ),
        work::WorkError::NotFound(reference) => public_domain_error(
            name,
            "NOT_FOUND",
            None,
            Some(("work", &reference)),
            false,
            "discover-before-create",
        ),
        work::WorkError::ActorNotFound(reference) => public_domain_error(
            name,
            "NOT_FOUND",
            None,
            Some(("actor", &reference)),
            false,
            "inspect-owner-inventory",
        ),
        work::WorkError::Integrity(_) | work::WorkError::Database(_) => tool_error(
            "Host integrity/availability failure; effect outcome UNKNOWN; reconcile before retry",
        ),
    }
}

fn attention_domain_tool_error(name: &str, error: attention::AttentionError) -> CallToolResult {
    match error {
        attention::AttentionError::Invalid(detail) => public_domain_error(
            name, "INVALID_ARGUMENT", Some(&detail), None, false, "correct-request",
        ),
        attention::AttentionError::Conflict(detail) => public_domain_error(
            name, "CONFLICT", Some(&detail), None, false,
            "reread-current-state-and-reconcile",
        ),
        // B's MissingResource carries exact kind/ref. Never reverse-engineer
        // these typed fields from a human-readable Display string.
        attention::AttentionError::NotFound(detail) => public_domain_error(
            name, "NOT_FOUND", Some(&detail),
            Some((detail.kind(), detail.reference())), false,
            "inspect-owner-inventory",
        ),
        attention::AttentionError::Integrity(_) | attention::AttentionError::Database(_) =>
            tool_error("Host integrity/availability failure; effect outcome UNKNOWN; reconcile before retry"),
    }
}

fn db_tool_error(name: &str, error: HostDbError) -> CallToolResult {
    match error {
        HostDbError::Work(error) => work_domain_tool_error(name, error),
        HostDbError::Attention(error) => attention_domain_tool_error(name, error),
        // Checkout timeout happens before a command acquires a database session.
        HostDbError::PoolCheckout(deadpool_postgres::PoolError::Timeout(_)) => public_domain_error(
            name,
            "DEADLINE_EXCEEDED",
            None,
            None,
            true,
            "retry-with-bounded-backoff",
        ),
        // Driver failures after a write could mean effect committed, response lost.
        _ => tool_error("Host PostgreSQL failure; effect outcome UNKNOWN; reconcile before retry"),
    }
}

#[derive(Clone, Copy, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "lowercase")]
pub enum TargetKindWire {
    Work,
    Space,
    Topic,
}

impl From<TargetKindWire> for TargetKind {
    fn from(value: TargetKindWire) -> Self {
        match value {
            TargetKindWire::Work => TargetKind::Work,
            TargetKindWire::Space => TargetKind::Space,
            TargetKindWire::Topic => TargetKind::Topic,
        }
    }
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct SubscriptionChangeRequest {
    pub actor_ref: String,
    pub target_kind: TargetKindWire,
    pub target_ref: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct SubscriptionListRequest {
    pub actor_ref: String,
    #[serde(default)]
    #[schemars(default)]
    pub target_kind: Option<TargetKindWire>,
    #[serde(default)]
    pub after_target_kind: Option<String>,
    #[serde(default)]
    pub after_target_ref: Option<String>,
    #[serde(default = "subscription_list_limit")]
    pub limit: i64,
    #[serde(default = "attention_max_bytes")]
    pub max_bytes: usize,
}

const fn subscription_list_limit() -> i64 {
    200
}
const fn attention_limit() -> i64 {
    100
}
const fn attention_max_bytes() -> usize {
    262_144
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AttentionGetRequest {
    pub actor_ref: String,
    #[serde(default = "attention_limit")]
    pub limit: i64,
    #[serde(default = "attention_max_bytes")]
    pub max_bytes: usize,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AttentionDeltaRequest {
    pub actor_ref: String,
    pub after_sequence: i64,
    #[serde(default = "attention_limit")]
    pub limit: i64,
    #[serde(default = "attention_max_bytes")]
    pub max_bytes: usize,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AttentionReentryRequest {
    pub actor_ref: String,
    #[serde(default)]
    pub after_sequence: Option<i64>,
    #[serde(default = "attention_limit")]
    pub limit: i64,
    #[serde(default = "attention_max_bytes")]
    pub max_bytes: usize,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AttentionAckRequest {
    pub actor_ref: String,
    pub cursor: i64,
}

fn attention_request_id(prefix: &str, payload: &Value) -> Result<String, work::WorkError> {
    let digest = work::canonical_digest(payload)?;
    Ok(format!("{prefix}:{}", digest.trim_start_matches("sha256:")))
}

// Native MCP inputs: retain the Python tool-level camelCase surface, while
// forwarding all state changes to B's domain implementation unchanged.
#[derive(Clone, Copy, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "lowercase")]
pub enum TopicStateWire {
    Open,
    Closed,
}
impl TopicStateWire {
    fn domain(self) -> social::TopicState {
        match self {
            Self::Open => social::TopicState::Open,
            Self::Closed => social::TopicState::Closed,
        }
    }
    fn as_str(self) -> &'static str {
        match self {
            Self::Open => "open",
            Self::Closed => "closed",
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum MessageKindWire {
    Note,
    Question,
    Proposal,
    Warning,
    Finding,
    Handoff,
}
impl MessageKindWire {
    fn domain(self) -> social::MessageKind {
        match self {
            Self::Note => social::MessageKind::Note,
            Self::Question => social::MessageKind::Question,
            Self::Proposal => social::MessageKind::Proposal,
            Self::Warning => social::MessageKind::Warning,
            Self::Finding => social::MessageKind::Finding,
            Self::Handoff => social::MessageKind::Handoff,
        }
    }
    fn as_str(self) -> &'static str {
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
const fn default_message_kind_wire() -> MessageKindWire {
    MessageKindWire::Note
}

#[derive(Clone, Copy, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum MessageRelationWire {
    ReplyTo,
    Mentions,
    References,
    Acknowledges,
    Supersedes,
    About,
}
impl MessageRelationWire {
    fn domain(self) -> social::MessageRelationKind {
        match self {
            Self::ReplyTo => social::MessageRelationKind::ReplyTo,
            Self::Mentions => social::MessageRelationKind::Mentions,
            Self::References => social::MessageRelationKind::References,
            Self::Acknowledges => social::MessageRelationKind::Acknowledges,
            Self::Supersedes => social::MessageRelationKind::Supersedes,
            Self::About => social::MessageRelationKind::About,
        }
    }
    fn as_str(self) -> &'static str {
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

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct TopicResumeRequest {
    pub topic_ref: String,
    #[serde(default)]
    pub after_sequence: i64,
    #[serde(default = "topic_resume_limit")]
    pub limit: i64,
    #[serde(default = "topic_resume_max_bytes")]
    pub max_bytes: usize,
}
const fn topic_resume_limit() -> i64 {
    50
}
const fn topic_resume_max_bytes() -> usize {
    524_288
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct TopicCursorGetRequest {
    pub actor_ref: String,
    pub topic_ref: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct TopicCursorAckRequest {
    pub actor_ref: String,
    pub topic_ref: String,
    pub cursor: i64,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct TopicStateSetRequest {
    pub topic_ref: String,
    pub actor_ref: String,
    pub state: TopicStateWire,
    pub expected_state: TopicStateWire,
    pub expected_high_sequence: i64,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct MessageGetRequest {
    pub message_ref: String,
    #[serde(default)]
    pub expected_digest: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct MessageSearchRequest {
    pub query: String,
    #[serde(default)]
    pub space_ref: Option<String>,
    #[serde(default)]
    pub topic_ref: Option<String>,
    #[serde(default)]
    pub before_sequence: Option<i64>,
    #[serde(default = "message_search_limit")]
    pub limit: i64,
    #[serde(default = "message_search_max_bytes")]
    pub max_bytes: usize,
}
const fn message_search_limit() -> i64 {
    50
}
const fn message_search_max_bytes() -> usize {
    524_288
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct MessagePostRequest {
    pub message_ref: String,
    pub space_ref: String,
    pub topic_ref: String,
    pub author_actor_ref: String,
    pub body: String,
    pub recorded_at_ms: i64,
    #[serde(default = "default_message_kind_wire")]
    pub message_kind: MessageKindWire,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct MessageRelationAddRequest {
    pub source_message_ref: String,
    pub relation: MessageRelationWire,
    pub target_ref: String,
    pub actor_ref: String,
}

#[derive(Clone)]
pub struct HostMcp {
    pg: Arc<HostPg>,
}

#[tool_router]
impl HostMcp {
    pub fn new(pg: HostPg) -> Self {
        Self { pg: Arc::new(pg) }
    }

    #[tool(
        name = "space.create",
        description = "Create one Social Space with immutable subjects, first-writer identity, and exact PostgreSQL receipt replay."
    )]
    async fn space_create(
        &self,
        Parameters(request): Parameters<SpaceCreateRequest>,
    ) -> CallToolResult {
        let subject_refs = request.subject_refs.unwrap_or_default();
        // Python SpaceInput.model_dump(mode="json") hashes snake_case Domain
        // fields and the original ordered subject_refs list (not sorted).
        let payload = json!({
            "space_ref":request.space_ref, "purpose":request.purpose,
            "actor_ref":request.actor_ref, "subject_refs":subject_refs
        });
        let id = match attention_request_id("space-create", &payload) {
            Ok(v) => v,
            Err(e) => return work_domain_tool_error("space.create", e),
        };
        let cmd = CreateSpace {
            space_ref: request.space_ref,
            purpose: request.purpose,
            actor_ref: request.actor_ref,
            subject_refs,
            client_request_id: id,
        };
        match self.pg.social_space_create(&cmd).await {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("space.create", e),
        }
    }

    #[tool(
        name = "space.get",
        description = "Read a bounded Space and embedded Topics/participants in one repeatable-read PostgreSQL snapshot."
    )]
    async fn space_get(&self, Parameters(request): Parameters<SpaceGetRequest>) -> CallToolResult {
        match self
            .pg
            .social_space_get(
                &request.space_ref,
                request.participant_limit,
                request.topic_limit,
                request.max_bytes,
            )
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("space.get", e),
        }
    }

    #[tool(
        name = "topic.create",
        description = "Create an asynchronous Topic under an existing Space with immutable first declaration and canonical command receipt."
    )]
    async fn topic_create(
        &self,
        Parameters(request): Parameters<TopicCreateRequest>,
    ) -> CallToolResult {
        let payload = json!({
            "topic_ref":request.topic_ref, "space_ref":request.space_ref,
            "title":request.title, "actor_ref":request.actor_ref,
        });
        let id = match attention_request_id("topic-create", &payload) {
            Ok(v) => v,
            Err(e) => return work_domain_tool_error("topic.create", e),
        };
        let cmd = CreateTopic {
            topic_ref: request.topic_ref,
            space_ref: request.space_ref,
            title: request.title,
            actor_ref: request.actor_ref,
            client_request_id: id,
        };
        match self.pg.social_topic_create(&cmd).await {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("topic.create", e),
        }
    }

    #[tool(
        name = "space.participation.set",
        description = "Set desired-state Social membership for an existing Space/Actor; not authentication or work assignment."
    )]
    async fn space_participation_set(
        &self,
        Parameters(request): Parameters<SpaceParticipationSetRequest>,
    ) -> CallToolResult {
        // Original Python MCP wrapper computes this identity but B's
        // desired-state native implementation intentionally ignores receipts.
        // Replaying joined->left->joined must not be defeated by old ids.
        let payload = json!({
            "spaceRef":request.space_ref, "actorRef":request.actor_ref,
            "standing":request.standing.as_str()
        });
        let id = match attention_request_id("space-participation-set", &payload) {
            Ok(v) => v,
            Err(e) => return work_domain_tool_error("space.participation.set", e),
        };
        match self
            .pg
            .social_participation_set(
                &request.space_ref,
                &request.actor_ref,
                request.standing.domain(),
                &id,
            )
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("space.participation.set", e),
        }
    }

    #[tool(
        name = "actor.declare",
        description = "Declare a stable Host ActorRef with immutable kind and an idempotent PG receipt; not authorization."
    )]
    async fn actor_declare(
        &self,
        Parameters(request): Parameters<ActorDeclareRequest>,
    ) -> CallToolResult {
        // Python ActorRefInput.model_dump(mode="json") hashes snake_case fields.
        let payload = json!({
            "actor_ref":request.actor_ref,"actor_kind":request.actor_kind.as_str()
        });
        let id = match attention_request_id("actor-declare", &payload) {
            Ok(v) => v,
            Err(e) => return work_domain_tool_error("actor.declare", e),
        };
        let cmd = ActorDeclare {
            actor_ref: request.actor_ref,
            actor_kind: request.actor_kind.domain(),
            client_request_id: id,
        };
        match self.pg.actor_declare(&cmd).await {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("actor.declare", e),
        }
    }

    #[tool(
        name = "host.status",
        description = "Read a coherent Host PostgreSQL authority snapshot, including native integrity/history Doctor diagnostics."
    )]
    async fn host_status(
        &self,
        Parameters(request): Parameters<HostStatusRequest>,
    ) -> CallToolResult {
        match self.pg.status(request.detail.as_str()).await {
            Ok(summary) => match serde_json::to_value(summary) {
                Ok(value) => structured(value),
                Err(error) => tool_error(error),
            },
            Err(error) => db_tool_error("host.status", error),
        }
    }

    #[tool(
        name = "subscription.follow",
        description = "Follow a Host Work, Space, or Topic as current desired state."
    )]
    async fn subscription_follow(
        &self,
        Parameters(request): Parameters<SubscriptionChangeRequest>,
    ) -> CallToolResult {
        let payload = json!({"actorRef":request.actor_ref,"targetKind":attention::TargetKind::from(request.target_kind).as_str(),"targetRef":request.target_ref});
        let id = match attention_request_id("subscription-follow", &payload) {
            Ok(id) => id,
            Err(e) => return work_domain_tool_error("subscription.follow", e),
        };
        match self
            .pg
            .subscription_follow(
                &request.actor_ref,
                request.target_kind.into(),
                &request.target_ref,
                &id,
            )
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("subscription.follow", e),
        }
    }

    #[tool(
        name = "subscription.unfollow",
        description = "Remove a current Host subscription without replaying an old desired state."
    )]
    async fn subscription_unfollow(
        &self,
        Parameters(request): Parameters<SubscriptionChangeRequest>,
    ) -> CallToolResult {
        let payload = json!({"actorRef":request.actor_ref,"targetKind":TargetKind::from(request.target_kind).as_str(),"targetRef":request.target_ref});
        let id = match attention_request_id("subscription-unfollow", &payload) {
            Ok(id) => id,
            Err(e) => return work_domain_tool_error("subscription.unfollow", e),
        };
        match self
            .pg
            .subscription_unfollow(
                &request.actor_ref,
                request.target_kind.into(),
                &request.target_ref,
                &id,
            )
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("subscription.unfollow", e),
        }
    }

    #[tool(
        name = "subscription.list",
        description = "Bounded read-only subscriptions with stable cursor pagination."
    )]
    async fn subscription_list(
        &self,
        Parameters(request): Parameters<SubscriptionListRequest>,
    ) -> CallToolResult {
        let after = match (
            request.after_target_kind.as_deref(),
            request.after_target_ref.as_deref(),
        ) {
            (None, None) => None,
            (Some(k), Some(r)) => Some((k, r)),
            _ => {
                return public_domain_error(
                    "subscription.list",
                    "INVALID_ARGUMENT",
                    Some("afterTargetKind and afterTargetRef must be supplied together"),
                    None,
                    false,
                    "correct-request",
                )
            }
        };
        match self
            .pg
            .subscription_list(
                &request.actor_ref,
                request.target_kind.map(TargetKind::from),
                after,
                request.limit,
                request.max_bytes,
            )
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("subscription.list", e),
        }
    }

    #[tool(
        name = "attention.get",
        description = "Read a bounded current-state Attention delta from this actor's acknowledged cursor."
    )]
    async fn attention_get(
        &self,
        Parameters(request): Parameters<AttentionGetRequest>,
    ) -> CallToolResult {
        match self
            .pg
            .attention_get(&request.actor_ref, request.limit, request.max_bytes)
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("attention.get", e),
        }
    }

    #[tool(
        name = "attention.delta",
        description = "Read an ordered bounded Attention delta from one snapshot."
    )]
    async fn attention_delta(
        &self,
        Parameters(request): Parameters<AttentionDeltaRequest>,
    ) -> CallToolResult {
        match self
            .pg
            .attention_delta(
                &request.actor_ref,
                request.after_sequence,
                request.limit,
                request.max_bytes,
            )
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("attention.delta", e),
        }
    }

    #[tool(
        name = "attention.reentry",
        description = "Read grouped navigation from a bounded Attention snapshot."
    )]
    async fn attention_reentry(
        &self,
        Parameters(request): Parameters<AttentionReentryRequest>,
    ) -> CallToolResult {
        match self
            .pg
            .attention_reentry(
                &request.actor_ref,
                request.after_sequence,
                request.limit,
                request.max_bytes,
            )
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("attention.reentry", e),
        }
    }

    #[tool(
        name = "attention.ack",
        description = "Acknowledge a monotone Attention cursor after the consumer has processed its page."
    )]
    async fn attention_ack(
        &self,
        Parameters(request): Parameters<AttentionAckRequest>,
    ) -> CallToolResult {
        let payload = json!({"actorRef":request.actor_ref,"cursor":request.cursor});
        let id = match attention_request_id("attention-ack", &payload) {
            Ok(id) => id,
            Err(e) => return work_domain_tool_error("attention.ack", e),
        };
        match self
            .pg
            .attention_ack(&request.actor_ref, request.cursor, &id)
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("attention.ack", e),
        }
    }

    #[tool(
        name = "topic.resume",
        description = "Resume an integrity-checked Topic page with a bounded cursor and byte budget."
    )]
    async fn topic_resume(
        &self,
        Parameters(request): Parameters<TopicResumeRequest>,
    ) -> CallToolResult {
        match self
            .pg
            .social_topic_resume(
                &request.topic_ref,
                request.after_sequence,
                request.limit,
                request.max_bytes,
            )
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("topic.resume", e),
        }
    }

    #[tool(
        name = "topic.cursor.get",
        description = "Read one actor's durable Topic-consumption cursor, distinct from Attention."
    )]
    async fn topic_cursor_get(
        &self,
        Parameters(request): Parameters<TopicCursorGetRequest>,
    ) -> CallToolResult {
        match self
            .pg
            .social_topic_cursor_get(&request.actor_ref, &request.topic_ref)
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("topic.cursor.get", e),
        }
    }

    #[tool(
        name = "topic.cursor.ack",
        description = "Acknowledge a monotone Topic-consumption cursor after reading the page."
    )]
    async fn topic_cursor_ack(
        &self,
        Parameters(request): Parameters<TopicCursorAckRequest>,
    ) -> CallToolResult {
        let payload = json!({"actorRef":request.actor_ref,"topicRef":request.topic_ref,"cursor":request.cursor});
        let id = match attention_request_id("topic-cursor-ack", &payload) {
            Ok(v) => v,
            Err(e) => return work_domain_tool_error("topic.cursor.ack", e),
        };
        match self
            .pg
            .social_topic_cursor_ack(&request.actor_ref, &request.topic_ref, request.cursor, &id)
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("topic.cursor.ack", e),
        }
    }

    #[tool(
        name = "topic.state.set",
        description = "Change Topic openness with expected state and message-high-sequence CAS."
    )]
    async fn topic_state_set(
        &self,
        Parameters(request): Parameters<TopicStateSetRequest>,
    ) -> CallToolResult {
        let payload = json!({
            "topicRef":request.topic_ref,"actorRef":request.actor_ref,
            "state":request.state.as_str(),"expectedState":request.expected_state.as_str(),
            "expectedHighSequence":request.expected_high_sequence
        });
        let id = match attention_request_id("topic-state-set", &payload) {
            Ok(v) => v,
            Err(e) => return work_domain_tool_error("topic.state.set", e),
        };
        match self
            .pg
            .social_topic_state_set(
                &request.topic_ref,
                &request.actor_ref,
                request.state.domain(),
                request.expected_state.domain(),
                request.expected_high_sequence,
                &id,
            )
            .await
        {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("topic.state.set", e),
        }
    }

    #[tool(
        name = "message.get",
        description = "Read and digest-check one exact durable Host Message, optionally enforcing an expected immutable digest."
    )]
    async fn message_get(
        &self,
        Parameters(request): Parameters<MessageGetRequest>,
    ) -> CallToolResult {
        match self
            .pg
            .social_message_get(&request.message_ref, request.expected_digest.as_deref())
            .await
        {
            Ok(value) => structured(value),
            Err(error) => db_tool_error("message.get", error),
        }
    }

    #[tool(
        name = "message.search",
        description = "Search integrity-checked Message rows with original PG CJK/full-text routes, bounded pagination, and no relevance ranking."
    )]
    async fn message_search(
        &self,
        Parameters(request): Parameters<MessageSearchRequest>,
    ) -> CallToolResult {
        let input = social::SearchMessages {
            query: request.query,
            space_ref: request.space_ref,
            topic_ref: request.topic_ref,
            before_sequence: request.before_sequence,
            limit: request.limit,
            max_bytes: request.max_bytes,
        };
        match self.pg.social_message_search(&input).await {
            Ok(value) => structured(value),
            Err(error) => db_tool_error("message.search", error),
        }
    }

    #[tool(
        name = "message.post",
        description = "Commit a durable Host collaboration Message with exact JCS request identity and receipt."
    )]
    async fn message_post(
        &self,
        Parameters(request): Parameters<MessagePostRequest>,
    ) -> CallToolResult {
        let payload = json!({
            "messageRef":request.message_ref,"spaceRef":request.space_ref,
            "topicRef":request.topic_ref,"authorActorRef":request.author_actor_ref,
            "body":request.body,"recordedAtMs":request.recorded_at_ms,
            "messageKind":request.message_kind.as_str()
        });
        let id = match attention_request_id("message-post", &payload) {
            Ok(v) => v,
            Err(e) => return work_domain_tool_error("message.post", e),
        };
        let value = PostMessage {
            message_ref: request.message_ref,
            client_request_id: id,
            space_ref: request.space_ref,
            topic_ref: request.topic_ref,
            author_actor_ref: request.author_actor_ref,
            body: request.body,
            recorded_at_ms: request.recorded_at_ms,
            message_kind: request.message_kind.domain(),
        };
        match self.pg.social_message_post(&value).await {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("message.post", e),
        }
    }

    #[tool(
        name = "message.relation.add",
        description = "Add a durable Message relation via the existing single-transaction Social domain."
    )]
    async fn message_relation_add(
        &self,
        Parameters(request): Parameters<MessageRelationAddRequest>,
    ) -> CallToolResult {
        // The original Python Pydantic MessageRelationInput.model_dump() uses
        // snake_case property names for the request identity.
        let payload = json!({
            "source_message_ref":request.source_message_ref,
            "relation":request.relation.as_str(),
            "target_ref":request.target_ref,"actor_ref":request.actor_ref
        });
        let id = match attention_request_id("message-relation-add", &payload) {
            Ok(v) => v,
            Err(e) => return work_domain_tool_error("message.relation.add", e),
        };
        let value = AddMessageRelation {
            source_message_ref: request.source_message_ref,
            relation: request.relation.domain(),
            target_ref: request.target_ref,
            actor_ref: request.actor_ref,
        };
        match self.pg.social_message_relation_add(&value, &id).await {
            Ok(value) => structured(value),
            Err(e) => db_tool_error("message.relation.add", e),
        }
    }

    #[tool(
        name = "work.get",
        description = "Read exact Work snapshot and revision from existing PostgreSQL schema13."
    )]
    async fn work_get(&self, Parameters(request): Parameters<WorkGetRequest>) -> CallToolResult {
        match self.pg.work_get(&request.work_ref, request.revision).await {
            Ok(value) => structured(value),
            Err(error) => db_tool_error("work.get", error),
        }
    }

    #[tool(
        name = "work.create",
        description = "Create one durable Work and immutable revision-one snapshot in PostgreSQL schema13."
    )]
    async fn work_create(
        &self,
        Parameters(request): Parameters<WorkCreateRequest>,
    ) -> CallToolResult {
        let snapshot: WorkSnapshot = request.initial_snapshot.into();
        let client_request_id = match create_work_client_request_id(
            &request.work_ref,
            &request.work_kind,
            &request.actor_ref,
            &snapshot,
        ) {
            Ok(identity) => identity,
            Err(error) => return work_domain_tool_error("work.create", error),
        };
        let command = work::CreateWork {
            work_ref: request.work_ref,
            kind: request.work_kind,
            actor_ref: request.actor_ref,
            initial_snapshot: snapshot,
            client_request_id,
        };
        match self.pg.work_create(&command).await {
            Ok(value) => structured(value),
            Err(error) => db_tool_error("work.create", error),
        }
    }

    #[tool(
        name = "work.list",
        description = "Read bounded PostgreSQL Work inventory with stable state and cursor filtering."
    )]
    async fn work_list(&self, Parameters(request): Parameters<WorkListRequest>) -> CallToolResult {
        let input = work::ListWorks {
            state: request.state.map(WorkState::from),
            limit: request.limit,
            before_updated_at: request.before_updated_at,
            before_work_ref: request.before_work_ref,
            max_bytes: request.max_bytes,
        };
        match self.pg.work_list(&input).await {
            Ok(value) => structured(value),
            Err(error) => db_tool_error("work.list", error),
        }
    }

    #[tool(
        name = "work.snapshot.commit",
        description = "Atomic Work compare-and-swap, immutable snapshot and idempotent receipt on PostgreSQL schema13."
    )]
    async fn work_snapshot_commit(
        &self,
        Parameters(request): Parameters<WorkCommitRequest>,
    ) -> CallToolResult {
        let snapshot: WorkSnapshot = request.snapshot.into();
        let payload = match serde_json::to_value(&snapshot) {
            Ok(value) => value,
            Err(error) => return tool_error(error),
        };
        // The caller-visible tool has no request ID; this MUST match Python's
        // mcp_tool_registration._request_id("work-snapshot-commit", payload).
        let identity = json!({
            "workRef": request.work_ref,
            "expectedRevision": request.expected_revision,
            "snapshot": payload,
            "actorRef": request.actor_ref,
            "continuityDisposition": request.continuity_disposition.as_str()
        });
        let digest = match work::canonical_digest(&identity) {
            Ok(value) => value,
            Err(error) => return work_domain_tool_error("work.snapshot.commit", error),
        };
        let command = work::CommitSnapshot {
            work_ref: request.work_ref,
            expected_revision: request.expected_revision,
            snapshot,
            actor_ref: request.actor_ref,
            state: request.continuity_disposition.state(),
            client_request_id: format!(
                "work-snapshot-commit:{}",
                digest.trim_start_matches("sha256:")
            ),
        };
        match self.pg.work_snapshot_commit(&command).await {
            Ok(value) => structured(value),
            Err(error) => db_tool_error("work.snapshot.commit", error),
        }
    }
}

#[tool_handler]
impl ServerHandler for HostMcp {
    fn get_info(&self) -> ServerConfig {
        ServerConfig::new(ServerCapabilities::builder().enable_tools().build())
            .with_instructions(
                "STAGING ONLY: Rust Host migration; schema13, Work/Social/Attention and full integrity/history Doctor. Not yet a production 31-tool parity replacement."
            )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn python_outer_extra_ignore_but_nested_snapshot_is_strict() {
        let host: HostStatusRequest =
            serde_json::from_value(json!({"detail":"summary","unknownExtra":"ignored"}))
                .expect("Python MCP tool parameters ignore extra top-level fields");
        assert_eq!(host.detail, HostStatusDetail::Summary);
        let get: WorkGetRequest =
            serde_json::from_value(json!({"workRef":"work:test:extra","unknownExtra":1}))
                .expect("tool-level extra parameters ignored");
        assert_eq!(get.work_ref, "work:test:extra");
        assert!(serde_json::from_value::<WorkSnapshotWire>(json!({
            "objective":"x","frontier":"y","unknownExtra":1
        }))
        .is_err());
    }

    #[test]
    fn structured_domain_errors_preserve_gateway_recovery_contract() {
        let result = attention_domain_tool_error(
            "attention.delta",
            attention::AttentionError::Conflict(
                "after_sequence cannot exceed current change horizon".into(),
            ),
        );
        assert_eq!(result.is_error, Some(true));
        let value = result.structured_content.expect("structured error");
        assert_eq!(value["error"]["kind"], "ordivon.host-domain-error");
        assert_eq!(value["error"]["code"], "CONFLICT");
        assert_eq!(value["error"]["retryable"], false);
        assert_eq!(
            value["error"]["suggestedAction"],
            "reread-current-state-and-reconcile"
        );
        let result = work_domain_tool_error(
            "work.get",
            work::WorkError::NotFound("work:test:missing".into()),
        );
        let value = result.structured_content.unwrap();
        assert_eq!(value["error"]["code"], "NOT_FOUND");
        assert_eq!(value["error"]["resourceKind"], "work");
        assert_eq!(value["error"]["resourceRef"], "work:test:missing");
        let internal = db_tool_error(
            "work.snapshot.commit",
            HostDbError::Pool("invalid config".into()),
        );
        assert_eq!(internal.is_error, Some(true));
        assert!(internal.structured_content.is_none());
    }

    #[test]
    fn incomplete_surface_is_explicit() {
        let names: Vec<_> = HostMcp::tool_router()
            .list_all()
            .iter()
            .map(|tool| tool.name.to_string())
            .collect();
        assert_eq!(
            names,
            vec![
                "actor.declare",
                "attention.ack",
                "attention.delta",
                "attention.get",
                "attention.reentry",
                "host.status",
                "message.get",
                "message.post",
                "message.relation.add",
                "message.search",
                "space.create",
                "space.get",
                "space.participation.set",
                "subscription.follow",
                "subscription.list",
                "subscription.unfollow",
                "topic.create",
                "topic.cursor.ack",
                "topic.cursor.get",
                "topic.resume",
                "topic.state.set",
                "work.create",
                "work.get",
                "work.list",
                "work.snapshot.commit"
            ]
        );
    }

    #[test]
    fn work_create_request_identity_matches_original_python_mcp() {
        let snapshot: WorkSnapshot = serde_json::from_value(json!({
            "objective": "中文 🌍",
            "frontier": "review",
        }))
        .unwrap();
        assert_eq!(
            create_work_client_request_id(
                "work:test:rust-wire-create",
                "demo",
                "actor:test:rust-wire",
                &snapshot
            )
            .unwrap(),
            "work-create:b53c3e1e3fb341efee31eb82e915ea45424cc76b9729e374939782ab97bc47b7"
        );
    }

    #[test]
    fn request_identity_is_based_on_canonical_payload_not_tool_transport() {
        let value = serde_json::from_value::<WorkCommitRequest>(json!({
            "workRef": "work:test:a",
            "expectedRevision": 1,
            "snapshot": {"objective": "中文 🌍", "frontier": "review"},
            "actorRef": "actor:test:a"
        }))
        .expect("tool request should decode");
        assert_eq!(value.continuity_disposition.as_str(), "continue");
        let snapshot: WorkSnapshot = value.snapshot.into();
        let wire = serde_json::to_value(&snapshot).expect("serialize");
        assert!(wire.get("nextActions").is_some());
        assert!(wire.get("next_actions").is_none());
    }
}
