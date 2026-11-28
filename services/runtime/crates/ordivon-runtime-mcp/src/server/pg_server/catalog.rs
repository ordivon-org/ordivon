//! Existing native PG Tool catalog, operator timer readiness and agent-visible projections.
use super::{
    CLAIM_ONLY_TOOL_NAMES, PgRuntimeServer, Tool, json, pg_portable_tool_catalog,
    pg_workspace_claim_catalog, qualify_pg_scheduling_output_schema,
    restrict_new_effect_catalog,
};

impl PgRuntimeServer {
    pub(super) fn release_ready(&self) -> bool {
        let Some(config)=&self.release else { return false; };
        if !config.source_repo.is_dir()
            || !config.operator_executable.is_file()
            || !config.receipt_root.is_absolute()
            || !config.dispatcher_timer.starts_with("ordivon-")
            || !config.dispatcher_timer.ends_with(".timer")
            || !config.dispatcher_timer.bytes().all(|b|b.is_ascii_alphanumeric()||matches!(b,b'-'|b'.'))
        { return false; }
        // Synchronous postgres starts its own Tokio runtime when establishing
        // a connection. Tool catalogs are read both from async MCP handlers
        // and from the Tokio-driven PG binary startup path. Do not connect on
        // a Tokio worker: one shared boundary covers all those consumers.
        let qualified = if tokio::runtime::Handle::try_current().is_ok() {
            let runtime = self.runtime.clone();
            std::thread::spawn(move || runtime.release_qualified().unwrap_or(false))
                .join()
                .unwrap_or(false)
        } else {
            self.runtime.release_qualified().unwrap_or(false)
        };
        if !qualified { return false; }
        std::process::Command::new("/usr/bin/systemctl")
            .args(["is-active","--quiet",&config.dispatcher_timer])
            .status().is_ok_and(|status| status.success())
    }
    pub(super) fn catalog_for(&self) -> Vec<Tool> {
        let mut tools =
            Self::catalog_for_route(self.release_ready(), self.claim_release_ingress.may_release());
        if self.claim_release_ingress.claim_only() {
            tools.retain(|tool| CLAIM_ONLY_TOOL_NAMES.contains(&tool.name.as_ref()));
        }
        restrict_new_effect_catalog(&mut tools, self.required_new_execution_profile);
        tools
    }
    // Protect the Agent-visible catalog as well as raw tools/call: an ordinary
    // executor should not plan a domain-finalizer effect it cannot invoke.
    // The raw call guard remains authoritative against a hand-written request.
    pub(super) fn catalog_for_route(release_ready: bool, release_allowed: bool) -> Vec<Tool> {
        let mut tools = Self::catalog_enabled(release_ready);
        if !release_allowed {
            tools.retain(|tool| tool.name.as_ref() != "workspace.claim.release");
        }
        tools
    }
    pub fn configured_tool_count(&self) -> usize {
        self.catalog_for().len()
    }
    pub fn catalog() -> Vec<Tool> {
        Self::catalog_for_route(false, false)
    }
    pub(super) fn catalog_enabled(release_ready: bool) -> Vec<Tool> {
        pg_portable_tool_catalog().into_iter()
            .chain(pg_workspace_claim_catalog())
            .filter_map(|mut t| {
            let description = match t.name.as_ref() {
                "runtime.describe" => "Describe only the executable PostgreSQL Runtime capabilities and native Linux runner provider.",
                "job.list" => "Principal-scoped, newest-first PostgreSQL Job listing with exact cursor and no historical SQLite IDs.",
                "workspace.get" => "Read exact current Git source identity and PG-bound active Job identities for one fresh-epoch Workspace. dirty and sourceStateDigest exclude ignored output; dirty=false does not establish close eligibility.",
                "workspace.list" => "List fresh-epoch Git Workspaces in stable creation-time order, without SQLite history. dirty excludes ignored output and does not establish close eligibility.",
                "workspace.diff" => "Read bounded Git diff with mature Workspace source authority; no SQLite state.",
                "workspace.changes" => "Page exact changed Workspace paths using the existing bounded Workspace diff implementation.",
                "workspace.file" => "Project a digest-verified bounded Workspace binary file into a native MCP resource.",
                "workspace.content" => "Project an exact digest-bound PNG or JPEG Workspace image using the mature native Workspace reader.",
                "artifact.content" => "Read an exact digest-verified PostgreSQL Artifact as a native MCP embedded binary resource.",
                "workspace.close" => "Close a fresh-epoch Git Workspace only after the PostgreSQL Job and Runtime-owned logical Run Claim fences find no held consumer. Non-force close rejects tracked changes and untracked paths including ignored output; source-clean is not close-safe.",
                "workspace.claim.reserve" => "Atomically pin a verified OPEN physical Workspace in the Runtime PostgreSQL database. This is not a Harness Run READY or Tool grant; exact clientRequestId supports lost-response readback.",
                "workspace.claim.get" => "Read only this principal's exact Runtime-owned Workspace claim by the original clientRequestId.",
                "workspace.claim.release" => "Explicitly release this principal's Runtime-owned Workspace pin; this is not artifact delivery or source finalization.",
                "workspace.mutate" => "Apply the mature atomic Workspace mutation contract, serialized against active PostgreSQL Job admission.",
                "workspace.read" => "Read bounded UTF-8 files from an isolated fresh-epoch Workspace using the native Workspace path authority.",
                "workspace.open" => "Create a fresh Git Workspace using the native Workspace contract. A caller-owned stable workspaceId is REQUIRED; on response loss use workspace.get with that exact ID before any replay. Agent notice: PG Workspaces are ephemeral, and the lifecycle timer may be disabled; if enabled its cadence is operator-defined. Four hours after the latest Job activity is only a minimum quiet period, not a guaranteed reclamation deadline. Commit/publish deliverables to Git or Artifact; never use Workspace files as durable evidence. The successful open response includes retentionNotice.",
                "workspace.execPlan" => "Run an ordered plan with the mature native Runner; PG commits the exact immutable step plan before physical launch. No input or credential bindings.",
                "workspace.exec" => "Fresh PostgreSQL execution vertical: one trusted_local local_linux command. Host Dependencies are admitted as exact file commitments and rechecked before native launch; foreignReferences and Windows context are rejected. PostgreSQL commits admission and dispatch intent before the existing systemd runner launches. A starting Attempt is dispatch intent, not proof of a running process. Ambiguous launches are never automatically reissued. Use job.observe to reconcile native runner evidence.",
                "release.apply" if release_ready => "Admit an exact qualified PG Runtime ReleaseEffect atomically. An independent running native systemd dispatcher consumes it and verifies actual installed Runtime bytes and MCP readback; connection loss requires release.get reconciliation, not another deployment.",
                "release.get" => "Read an authenticated principal-owned, durably bound PostgreSQL ReleaseEffect and validate its immutable operator receipt. Never dispatches, retries, or claims a release merely because the Runtime Job terminated.",
                "job.get" => "Read a PostgreSQL Job projection without dispatch or reconciliation. migrationVersion=0 identifies the fresh PG schema rather than SQLite migrations.",
                "job.observe" => "Observe and reconcile a principal-owned PostgreSQL Job using native runner evidence; may dispatch an accepted Job once. Supports terminal and change_or_terminal waiting with bounded output offsets. Does not claim domain semantic completion.",
                "job.cancel" => "Persist PostgreSQL cancellation intent before requesting the native systemd cgroup stop. A stop submission never proves terminal execution. Pending work cancels before dispatch; issued work requires native terminal evidence.",
                "artifact.read" => "Read a bounded verified UTF-8 range of a PostgreSQL-registered Artifact. Revalidates retained bytes against their digest and length.",
                _ => return None,
            };
            if t.name.as_ref()=="runtime.describe"{
                t.output_schema=Some(std::sync::Arc::new(json!({"type":"object","properties":{"globalExecutionLimit":{"type":["integer","null"],"description":"Null: native allocations are resource governed, not Job-count governed."},"scheduling":{"type":"object"},"node":{"type":"object"}},"additionalProperties":true}).as_object().unwrap().clone()));
            }
            qualify_pg_scheduling_output_schema(&mut t);
            t.description=Some(description.into());
            Some(t)
        }).collect()
    }

}
