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
use crate::pg::HostPg;
use crate::work::{self, WorkSnapshot, WorkState};

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct HostStatusRequest {
    #[serde(default = "summary_detail")]
    pub detail: String,
}

fn summary_detail() -> String {
    "summary".to_string()
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
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
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkCommitRequest {
    pub work_ref: String,
    pub expected_revision: i64,
    pub snapshot: WorkSnapshotWire,
    pub actor_ref: String,
    #[serde(default)]
    pub continuity_disposition: ContinuityDisposition,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
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
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkListRequest {
    #[serde(default)]
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
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SubscriptionChangeRequest {
    pub actor_ref: String,
    pub target_kind: TargetKindWire,
    pub target_ref: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SubscriptionListRequest {
    pub actor_ref: String,
    #[serde(default)]
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
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct AttentionGetRequest {
    pub actor_ref: String,
    #[serde(default = "attention_limit")]
    pub limit: i64,
    #[serde(default = "attention_max_bytes")]
    pub max_bytes: usize,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct AttentionDeltaRequest {
    pub actor_ref: String,
    pub after_sequence: i64,
    #[serde(default = "attention_limit")]
    pub limit: i64,
    #[serde(default = "attention_max_bytes")]
    pub max_bytes: usize,
}

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
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
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct AttentionAckRequest {
    pub actor_ref: String,
    pub cursor: i64,
}

fn attention_request_id(prefix: &str, payload: &Value) -> Result<String, work::WorkError> {
    let digest = work::canonical_digest(payload)?;
    Ok(format!("{prefix}:{}", digest.trim_start_matches("sha256:")))
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
        name = "host.status",
        description = "Read actual PostgreSQL-backed Host status; staging Rust currently supports detail=summary only."
    )]
    async fn host_status(
        &self,
        Parameters(request): Parameters<HostStatusRequest>,
    ) -> CallToolResult {
        if request.detail != "summary" {
            return tool_error(
                "Rust candidate supports detail=summary only; history/integrity still Python-owned",
            );
        }
        match self.pg.summary().await {
            Ok(summary) => match serde_json::to_value(summary) {
                Ok(value) => structured(value),
                Err(error) => tool_error(error),
            },
            Err(error) => tool_error(error),
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
            Err(e) => return tool_error(e),
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
            Err(e) => tool_error(e),
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
            Err(e) => return tool_error(e),
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
            Err(e) => tool_error(e),
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
            _ => return tool_error("afterTargetKind and afterTargetRef must be supplied together"),
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
            Err(e) => tool_error(e),
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
            Err(e) => tool_error(e),
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
            Err(e) => tool_error(e),
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
            Err(e) => tool_error(e),
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
            Err(e) => return tool_error(e),
        };
        match self
            .pg
            .attention_ack(&request.actor_ref, request.cursor, &id)
            .await
        {
            Ok(value) => structured(value),
            Err(e) => tool_error(e),
        }
    }

    #[tool(
        name = "work.get",
        description = "Read exact Work snapshot and revision from existing PostgreSQL schema13."
    )]
    async fn work_get(&self, Parameters(request): Parameters<WorkGetRequest>) -> CallToolResult {
        match self.pg.work_get(&request.work_ref, request.revision).await {
            Ok(value) => structured(value),
            Err(error) => tool_error(error),
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
            Err(error) => return tool_error(error),
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
            Err(error) => tool_error(error),
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
            Err(error) => tool_error(error),
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
            Err(error) => return tool_error(error),
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
            Err(error) => tool_error(error),
        }
    }
}

#[tool_handler]
impl ServerHandler for HostMcp {
    fn get_info(&self) -> ServerConfig {
        ServerConfig::new(ServerCapabilities::builder().enable_tools().build())
            .with_instructions(
                "STAGING ONLY: Rust Host migration; schema13, Work create/get/list/CAS, status summary.                 Not yet a production 31-tool parity replacement."
            )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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
                "attention.ack",
                "attention.delta",
                "attention.get",
                "attention.reentry",
                "host.status",
                "subscription.follow",
                "subscription.list",
                "subscription.unfollow",
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
