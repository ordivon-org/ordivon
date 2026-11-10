//! A real (but deliberately incomplete) MCP staging surface.
//! Only fully implemented tools are exposed; never claim 31-tool parity from a manifest.
use std::sync::Arc;

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::{CallToolResult, ServerCapabilities, ServerConfig};
use rmcp::{tool, tool_handler, tool_router, ServerHandler};
use schemars::JsonSchema;
use serde::Deserialize;

use crate::pg::HostPg;

#[derive(Debug, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct HostStatusRequest {
    #[serde(default = "summary_detail")]
    pub detail: String,
}

fn summary_detail() -> String {
    "summary".to_string()
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
        description = "Read the actual PostgreSQL-backed Host summary. This Rust migration candidate currently supports detail=summary only."
    )]
    async fn host_status(
        &self,
        Parameters(request): Parameters<HostStatusRequest>,
    ) -> CallToolResult {
        if request.detail != "summary" {
            return CallToolResult::error(vec![rmcp::model::ContentBlock::text(
                "Rust migration candidate only supports detail=summary; integrity/history remain Python-owned until parity"
            )]);
        }
        match self.pg.summary().await {
            Ok(summary) => match serde_json::to_value(summary) {
                Ok(value) => CallToolResult::structured(value),
                Err(error) => CallToolResult::error(vec![rmcp::model::ContentBlock::text(
                    format!("Host summary serialization error: {error}"),
                )]),
            },
            Err(error) => CallToolResult::error(vec![rmcp::model::ContentBlock::text(format!(
                "Host unavailable: {error}"
            ))]),
        }
    }
}

#[tool_handler]
impl ServerHandler for HostMcp {
    fn get_info(&self) -> ServerConfig {
        ServerConfig::new(ServerCapabilities::builder().enable_tools().build())
            .with_instructions(
                "STAGING ONLY: Rust Host migration slice, schema 13 read-only summary;                  not a production-ready replacement for 31-tool Python Host."
            )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn incomplete_surface_does_not_pretend_to_expose_other_tools() {
        let names: Vec<_> = HostMcp::tool_router()
            .list_all()
            .iter()
            .map(|t| t.name.to_string())
            .collect();
        assert_eq!(names, vec!["host.status"]);
    }
}
