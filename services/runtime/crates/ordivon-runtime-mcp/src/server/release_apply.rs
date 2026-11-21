//! Existing Runtime release.apply execution orchestration, separate from public MCP Tool registration.
use super::release_invocation::{build_release_deployer_args, build_release_effect_proposal};
use super::{
    runtime_release_owner_commit, runtime_release_source_identity, EffectivePrincipal,
    RuntimeReleaseAdmission, RuntimeReleaseApplyToolRequest, RuntimeReleaseRequest, RuntimeServer,
    RuntimeWorkspaceGetRequest, ToolError, ToolOutcome, RUNTIME_SCHEMA_VERSION,
};
use sha2::{Digest, Sha256};

impl RuntimeServer {
    pub(super) async fn execute_structured_release(
        &self,
        principal: EffectivePrincipal,
        request: RuntimeReleaseApplyToolRequest,
    ) -> ToolOutcome<RuntimeReleaseAdmission> {
        let runtime = self.state.runtime.clone();
        let release_config = self.state.release.clone();
        let execution = self.state.execution.with_principal(principal.principal);
        let principal = execution.principal.clone();
        let global_limit = execution.global_limit;
        self.run_core("release.apply", move || {
            let release_request = RuntimeReleaseRequest {
                schema_version: request.schema_version,
                client_request_id: request.client_request_id.clone(),
                principal: principal.clone(),
                workspace_id: request.workspace_id.clone(),
                commit: request.commit.clone(),
                candidate_manifest_digest: request.candidate_manifest_digest.clone(),
                expected_tool_count: request.expected_tool_count,
            };

            // Exact replay is intentionally resolved before current operator/world state.
            if let Some(replay) = runtime
                .find_runtime_release_for_apply(&release_request)
                .map_err(ToolError::from)?
            {
                return Ok(replay);
            }

            let release = release_config.ok_or_else(|| {
                ToolError::invalid(
                    "structured Runtime release is not configured on this node",
                    "release",
                )
            })?;
            let workspace = runtime
                .get_workspace(&RuntimeWorkspaceGetRequest {
                    schema_version: RUNTIME_SCHEMA_VERSION,
                    workspace_id: request.workspace_id.clone(),
                })
                .map_err(ToolError::from)?;
            let source_identity =
                runtime_release_source_identity(&release.source_repo).map_err(|error| {
                    ToolError::invalid(
                        format!("configured Runtime release source is invalid: {error}"),
                        "release.sourceRepo",
                    )
                })?;
            let workspace_source =
                std::fs::canonicalize(&workspace.source_repo).map_err(|error| {
                    ToolError::invalid(
                        format!("Workspace source repository is unavailable: {error}"),
                        "workspaceId",
                    )
                })?;
            if workspace_source != source_identity.git_root {
                return Err(ToolError::invalid(
                    "Workspace Git root does not match operator-owned Runtime release source",
                    "workspaceId",
                ));
            }
            let owner_commit = runtime_release_owner_commit(
                &source_identity.owner_root,
                &workspace.current_head_revision,
            )
            .map_err(|error| {
                ToolError::invalid(
                    format!("cannot resolve Runtime owner revision from Workspace: {error}"),
                    "commit",
                )
            })?;
            if owner_commit != request.commit {
                return Err(ToolError::invalid(
                    "requested commit does not match the Runtime owner revision at Workspace HEAD",
                    "commit",
                ));
            }
            let configured_source = source_identity.owner_root;
            if workspace.dirty {
                return Err(ToolError::invalid(
                    "Runtime release Workspace must be clean",
                    "workspaceId",
                ));
            }

            let candidate_dir = release.candidate_dir(&request.commit);
            let candidate_manifest = candidate_dir.join("ordivon-deployment-manifest.json");
            let candidate_deployer = release.candidate_deployer(&request.commit);
            let manifest_metadata =
                std::fs::symlink_metadata(&candidate_manifest).map_err(|error| {
                    ToolError::invalid(
                        format!("Runtime release candidate manifest is unavailable: {error}"),
                        "candidateManifestDigest",
                    )
                })?;
            if manifest_metadata.file_type().is_symlink() || !manifest_metadata.is_file() {
                return Err(ToolError::invalid(
                    "Runtime release candidate manifest must be a regular non-symlink file",
                    "candidateManifestDigest",
                ));
            }
            if manifest_metadata.len() > 4 * 1024 * 1024 {
                return Err(ToolError::invalid(
                    "Runtime release candidate manifest is too large",
                    "candidateManifestDigest",
                ));
            }
            let manifest_bytes = std::fs::read(&candidate_manifest).map_err(|error| {
                ToolError::invalid(
                    format!("cannot read Runtime release candidate manifest: {error}"),
                    "candidateManifestDigest",
                )
            })?;
            let manifest_digest =
                format!("sha256:{}", hex::encode(Sha256::digest(&manifest_bytes)));
            if manifest_digest != request.candidate_manifest_digest {
                return Err(ToolError::invalid(
                    "Runtime release candidate manifest digest does not match current bytes",
                    "candidateManifestDigest",
                ));
            }
            let deployer_metadata =
                std::fs::symlink_metadata(&candidate_deployer).map_err(|error| {
                    ToolError::invalid(
                        format!("Runtime release candidate deployer is unavailable: {error}"),
                        "commit",
                    )
                })?;
            if deployer_metadata.file_type().is_symlink() || !deployer_metadata.is_file() {
                return Err(ToolError::invalid(
                    "Runtime release candidate deployer must be a regular non-symlink file",
                    "commit",
                ));
            }

            let effect_id = ordivon_runtime_core::runtime_release_effect_id(&release_request);
            let request_digest =
                ordivon_runtime_core::runtime_release_request_identity_digest(&release_request)
                    .map_err(ToolError::from)?;
            let receipt_path = release.receipt_root.join(format!("effect-{effect_id}"));
            let args = build_release_deployer_args(
                &release,
                &request,
                &configured_source,
                &candidate_dir,
                &candidate_manifest,
                &effect_id,
                &request_digest,
            );
            let proposal = build_release_effect_proposal(
                &release,
                &request,
                &principal,
                global_limit,
                &candidate_deployer,
                &effect_id,
                args,
            );
            runtime
                .admit_runtime_release_effect(&release_request, &proposal, &receipt_path)
                .map_err(ToolError::from)
        })
        .await
    }
}
