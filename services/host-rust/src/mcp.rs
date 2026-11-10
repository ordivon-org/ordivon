//! Real but incomplete Rust MCP migration staging surface.
//! Exposes only proved tools; never invents success for the 31-tool Python surface.
use std::sync::Arc;

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::{CallToolResult, ContentBlock, ServerCapabilities, ServerConfig};
use rmcp::{tool, tool_handler, tool_router, ServerHandler};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

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
                "STAGING ONLY: Rust Host migration; schema13, Work read/CAS, status summary.                 Not yet a production 31-tool parity replacement."
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
            vec!["host.status", "work.get", "work.snapshot.commit"]
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
