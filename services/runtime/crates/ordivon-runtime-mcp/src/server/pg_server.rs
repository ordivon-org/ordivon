/// Independently launched fresh-PG MCP adapter. The SQLite Engine is never constructed.
/// Operator-owned release configuration; never supplied in MCP request JSON.
#[derive(Clone, Debug)]
pub struct PgReleaseOperatorConfig {
    pub source_repo: PathBuf,
    pub operator_executable: PathBuf,
    pub receipt_root: PathBuf,
    /// The independent systemd timer is a durable consumer of accepted effects.
    pub dispatcher_timer: String,
}

// A private in-process ingress classification, NOT a caller-supplied
// permission. Only pg_main's separately authenticated Harness route may
// select DedicatedFinalizer. The ordinary tool transport must never infer
// release authority from an ordinary bearer or the absence of a finalizer.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum ClaimReleaseIngress {
    Ordinary,
    // Original same-PG Harness Issuer remains able to admit Job requests.
    DedicatedFinalizer,
    // Separate original Run resource ownership from source-current Job issuance.
    // The minimal port needs no foreign Harness tables in Runtime PostgreSQL.
    DedicatedClaimOnly,
}

impl ClaimReleaseIngress {
    const fn may_release(self) -> bool {
        matches!(self, Self::DedicatedFinalizer | Self::DedicatedClaimOnly)
    }

    const fn claim_only(self) -> bool {
        matches!(self, Self::DedicatedClaimOnly)
    }
}

const CLAIM_ONLY_TOOL_NAMES: &[&str] = &[
    "workspace.get",
    "workspace.claim.reserve",
    "workspace.claim.get",
    "workspace.claim.release",
];

fn claim_only_route_guard(ingress: ClaimReleaseIngress, name: &str) -> Result<(), McpError> {
    if ingress.claim_only() && !CLAIM_ONLY_TOOL_NAMES.contains(&name) {
        return Err(McpError::invalid_params(
            "Claim Finalizer ingress does not grant Job execution or Runtime administration",
            None,
        ));
    }
    Ok(())
}

/// A caller-supplied key is a recovery coordinate, never release authority.
/// Keep the real raw-dispatch check testable without constructing a PG client.
fn claim_release_route_guard(allowed: bool, name: &str) -> Result<(), McpError> {
    if name == "workspace.claim.release" && !allowed {
        return Err(McpError::invalid_params(
            "workspace.claim.release requires the authenticated Run finalizer route",
            None,
        ));
    }
    Ok(())
}

/// Advertise only profiles accepted for NEW effects by the authenticated
/// transport, rather than exposing a caller-selected privileged alternative.
fn project_ingress_execution_profiles(
    description: &mut serde_json::Value,
    required: Option<ExecutionProfile>,
) {
    let Some(required) = required else { return; };
    if let Some(targets) = description.get_mut("targets").and_then(serde_json::Value::as_array_mut) {
        for target in targets {
            if target.get("target").and_then(serde_json::Value::as_str) == Some("local_linux") {
                target["executionProfiles"] = json!([required.as_str()]);
            }
        }
    }
}

/// Restrict advertised new effects for an authenticated contained-only Agent.
/// A manually authored raw tools/call is independently checked by Core after
/// committed replay; tools/list filtering is never the authorization gate.
fn restrict_new_effect_catalog(
    tools: &mut Vec<Tool>,
    required: Option<ExecutionProfile>,
) {
    if required == Some(ExecutionProfile::ContainedLocal) {
        tools.retain(|tool| tool.name.as_ref() != "release.apply");
        for tool in tools {
            if matches!(tool.name.as_ref(), "workspace.exec" | "workspace.execPlan") {
                tool.description = Some(
                    "Authenticated contained_local-only Job admission. Caller-selected trusted_local is DENIED for new effects; exact previously committed Job recovery remains allowed.".into()
                );
            }
        }
    }
}

/// A direct MCP caller may omit executionProfile because the original
/// public Tool schema defaults to trusted_local. Historical committed Jobs
/// must be observed through that ORIGINAL identity first, even after the
/// authenticated ordinary ingress is restricted to contained_local.
///
/// Only a qualified native precommit profile denial or exact PG-key conflict
/// permits one alternate contained admission. The PG Store rechecks the
/// principal and full immutable request digest; the MCP layer is not a new
/// permission authority or retry ledger.
fn run_pg_direct_implicit_profile(
    runtime: &ordivon_runtime_core::PgRuntime,
    mut bound: JobRunProposal,
    required: Option<ExecutionProfile>,
    caller_omitted_profile: bool,
) -> Result<JobObservation, RuntimeError> {
    let initial = runtime.run_with_execution_profile_policy(&bound, required);
    let can_reenter_contained = caller_omitted_profile
        && required == Some(ExecutionProfile::ContainedLocal)
        && bound.execution.execution_profile == ExecutionProfile::TrustedLocal
        && initial.as_ref().err().is_some_and(|error| {
            !error.retryable
                && error.operation_id.is_none()
                && match error.code {
                    ordivon_runtime_core::RuntimeErrorCode::AuthorizationDenied => {
                        error.field.as_deref() == Some("execution.executionProfile")
                    }
                    ordivon_runtime_core::RuntimeErrorCode::IdempotencyConflict => {
                        error.field.is_none()
                    }
                    _ => false,
                }
        });
    if can_reenter_contained {
        bound.execution.execution_profile = ExecutionProfile::ContainedLocal;
        runtime.run_with_execution_profile_policy(&bound, required)
    } else {
        initial
    }
}

fn profile_omitted_from_raw_tool_arguments(arguments: &serde_json::Value) -> bool {
    arguments.get("execution")
        .and_then(serde_json::Value::as_object)
        .is_some_and(|execution| !execution.contains_key("executionProfile"))
}

#[derive(Clone)]
pub struct PgRuntimeServer {
    runtime: ordivon_runtime_core::PgRuntime,
    execution: ExecutionContext,
    release: Option<PgReleaseOperatorConfig>,
    // The ordinary execution bearer is not authority to relinquish another
    // domain's still-held Workspace. The protected Harness/Finalizer route
    // alone may expose the original principal-scoped release operation.
    claim_release_ingress: ClaimReleaseIngress,
    // Authentication-bound NEW-Job policy, never a tools/call argument.
    // Core performs historical exact-key recovery before this check.
    required_new_execution_profile: Option<ExecutionProfile>,
}

impl PgRuntimeServer {
    pub fn new(runtime: ordivon_runtime_core::PgRuntime, execution: ExecutionContext) -> Self {
        Self {
            runtime,
            execution,
            release: None,
            claim_release_ingress: ClaimReleaseIngress::Ordinary,
            required_new_execution_profile: None,
        }
    }
    pub fn with_release(
        runtime: ordivon_runtime_core::PgRuntime,
        execution: ExecutionContext,
        release: Option<PgReleaseOperatorConfig>,
    ) -> Self {
        Self {
            runtime,
            execution,
            release,
            claim_release_ingress: ClaimReleaseIngress::Ordinary,
            required_new_execution_profile: None,
        }
    }
    /// This is ONLY called for the separately authenticated dedicated
    /// Harness ingress selected by the operator at service startup. The
    /// ordinary route remains deny-by-default even with no dedicated profile.
    /// A distinct principal cannot silently inherit a prior principal's HELD
    /// claim: legacy Claim migration needs original-consumer qualification.
    pub fn for_authenticated_harness_finalizer(mut self) -> Self {
        self.claim_release_ingress = ClaimReleaseIngress::DedicatedFinalizer;
        self
    }

    /// A separately authenticated Claim owner cannot execute, cancel, release
    /// Runtime binaries, or close Workspaces. Original recipient/OS verification
    /// is still the external Harness Finalizer's responsibility.
    pub fn for_authenticated_claim_only_finalizer(mut self) -> Self {
        self.claim_release_ingress = ClaimReleaseIngress::DedicatedClaimOnly;
        self
    }

    /// Operator-selected ordinary Agent ingress. An authenticated caller
    /// cannot upgrade a new contained Job by supplying trusted_local in JSON.
    /// The old trusted operator ingress remains the default until cutover.
    pub fn restrict_ordinary_jobs_to_contained(mut self) -> Self {
        self.required_new_execution_profile = Some(ExecutionProfile::ContainedLocal);
        self
    }

    fn require_claim_release_authority(&self, name: &str) -> Result<(), McpError> {
        claim_release_route_guard(self.claim_release_ingress.may_release(), name)
    }

    fn release_ready(&self) -> bool {
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
    fn catalog_for(&self) -> Vec<Tool> {
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
    fn catalog_for_route(release_ready: bool, release_allowed: bool) -> Vec<Tool> {
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
        Self::catalog_enabled(false)
    }
    fn catalog_enabled(release_ready: bool) -> Vec<Tool> {
        pg_portable_tool_catalog().into_iter()
            .chain(pg_workspace_claim_catalog())
            .filter_map(|mut t| {
            let description = match t.name.as_ref() {
                "runtime.describe" => "Describe only the executable PostgreSQL Runtime capabilities and native Linux runner provider.",
                "job.list" => "Principal-scoped, newest-first PostgreSQL Job listing with exact cursor and no historical SQLite IDs.",
                "workspace.get" => "Read exact current Git source identity and PG-bound active Job identities for one fresh-epoch Workspace.",
                "workspace.list" => "List fresh-epoch Git Workspaces in stable creation-time order, without SQLite history.",
                "workspace.diff" => "Read bounded Git diff with mature Workspace source authority; no SQLite state.",
                "workspace.changes" => "Page exact changed Workspace paths using the existing bounded Workspace diff implementation.",
                "workspace.file" => "Project a digest-verified bounded Workspace binary file into a native MCP resource.",
                "workspace.content" => "Project an exact digest-bound PNG or JPEG Workspace image using the mature native Workspace reader.",
                "artifact.content" => "Read an exact digest-verified PostgreSQL Artifact as a native MCP embedded binary resource.",
                "workspace.close" => "Close a fresh-epoch Git Workspace only after the PostgreSQL Job and Runtime-owned logical Run Claim fences find no held consumer.",
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
    /// Shared by the MCP handler and protocol consumer tests; performs real Core calls.
    pub async fn call(&self, name: String, arguments: serde_json::Value) -> Result<CallToolResult, McpError> {
        // Enforce before the PG transaction and before any Release readiness
        // side query. A caller who knows the exact idempotency key still
        // cannot invoke the physical relinquishment through ordinary /mcp.
        self.require_claim_release_authority(&name)?;
        claim_only_route_guard(self.claim_release_ingress, &name)?;
        let release_ready=self.release_ready();
        if !Self::catalog_enabled(release_ready).iter().any(|t|t.name.as_ref()==name) {
            return Err(McpError::invalid_params("Tool is not implemented by the PG vertical", None));
        }
        // Native MCP media surfaces intentionally return ContentBlock resources,
        // not text/base64 stuffed into a JSON observation projection.
        if name=="workspace.file" {
            let request:WorkspaceFileToolRequest=serde_json::from_value(arguments)
                .map_err(|e|McpError::invalid_params(e.to_string(),None))?;
            let (media,standing)=match request.media_type.as_deref() {
                Some(m) if !m.is_empty() && m.len()<=256 && m.bytes().all(|b|b.is_ascii_graphic())
                    =>(m.to_string(),"CALLER_DECLARED_UNVERIFIED".to_string()),
                None =>("application/octet-stream".to_string(),"DEFAULT_BINARY".to_string()),
                _ =>return Err(McpError::invalid_params("invalid mediaType",None))
            };
            let core=ordivon_runtime_core::WorkspaceFileRequest{
                schema_version:request.schema_version,workspace_id:request.workspace_id,
                relative_path:request.relative_path,expected_digest:request.expected_digest,
                max_bytes:request.max_bytes
            };
            let config=self.runtime.executor_config();
            let result=tokio::task::spawn_blocking(move||ordivon_runtime_core::read_workspace_file(&config,&core))
                .await.map_err(|e|McpError::internal_error(e.to_string(),None))?;
            return workspace_file_call_result(match result{
                Ok(v)=>ToolOutcome::Success(v),
                Err(e)=>ToolOutcome::Error(ToolError::from(e))
            },media,standing);
        }
        if name=="workspace.content" {
            let request:ordivon_runtime_core::WorkspaceContentRequest=serde_json::from_value(arguments)
                .map_err(|e|McpError::invalid_params(e.to_string(),None))?;
            let config=self.runtime.executor_config();
            let result=tokio::task::spawn_blocking(move||ordivon_runtime_core::read_workspace_content(&config,&request))
                .await.map_err(|e|McpError::internal_error(e.to_string(),None))?;
            return workspace_content_call_result(match result {
                Ok(v)=>ToolOutcome::Success(v),Err(e)=>ToolOutcome::Error(ToolError::from(e))
            });
        }
        if name=="artifact.content" {
            let request:ordivon_runtime_core::ArtifactContentRequest=serde_json::from_value(arguments)
                .map_err(|e|McpError::invalid_params(e.to_string(),None))?;
            let runtime=self.runtime.clone();
            let principal=self.execution.principal.clone();
            let result=tokio::task::spawn_blocking(move||runtime.read_artifact_content(&principal,&request))
                .await.map_err(|e|McpError::internal_error(e.to_string(),None))?;
            return artifact_content_call_result(match result {
                Ok(v)=>ToolOutcome::Success(v),Err(e)=>ToolOutcome::Error(ToolError::from(e))
            });
        }
        let runtime=self.runtime.clone();
        let execution=self.execution.clone();
        let release=self.release.clone();
        let annotation_runtime=runtime.clone();
        let required_new_execution_profile=self.required_new_execution_profile;
        // A Job ID alone must not cause a schema-invalid response. Reuse the
        // exact qualified MCP output-schema tool set from pg_output_contract.
        let annotate_job_scheduling = pg_scheduling_success_definition(&name).is_some();
        let result=tokio::task::spawn_blocking(move || -> Result<serde_json::Value, ToolError> {
            fn parse<T: serde::de::DeserializeOwned>(v: serde_json::Value) -> Result<T,ToolError> {
                serde_json::from_value(v).map_err(|e|ToolError::invalid(e.to_string(),"arguments"))
            }
            fn value<T: serde::Serialize>(r: Result<T,RuntimeError>) -> Result<serde_json::Value,ToolError> {
                serde_json::to_value(r.map_err(ToolError::from)?).map_err(|e|ToolError::internal(e.to_string()))
            }
            match name.as_str() {
                "runtime.describe" => {
                    // Reuse the SAME Serde/JSON Schema input contract as
                    // the legacy MCP router; do not maintain a second parser.
                    let request: RuntimeDescribeRequest = parse(arguments)?;
                    if request.schema_version != RUNTIME_SCHEMA_VERSION {
                        return Err(ToolError::invalid("schemaVersion must be 1", "schemaVersion"));
                    }
                    let mut description=runtime.describe().map_err(ToolError::from)?;
                    project_ingress_execution_profiles(&mut description, required_new_execution_profile);
                    description["structuredReleaseConfigured"]=json!(
                        release_ready && required_new_execution_profile.is_none()
                    );
                    Ok(description)
                },
                "release.apply" => {
                    let request:RuntimeReleaseApplyToolRequest=parse(arguments)?;
                    let configured=release.as_ref().ok_or_else(||
                        ToolError::invalid("independent PG Release operator is unavailable","release")
                    )?;
                    let req=RuntimeReleaseRequest {
                        schema_version:request.schema_version,
                        client_request_id:request.client_request_id,
                        principal:execution.principal.clone(),
                        workspace_id:request.workspace_id,
                        commit:request.commit,
                        candidate_manifest_digest:request.candidate_manifest_digest,
                        expected_tool_count:request.expected_tool_count,
                    };
                    // Historical exact replay MUST precede changed candidate,
                    // current authorization, worktree or timer state.
                    if let Some(replay)=runtime.find_runtime_release_for_apply(&req)
                        .map_err(ToolError::from)?
                    {
                        return serde_json::to_value(replay)
                            .map_err(|e|ToolError::internal(e.to_string()));
                    }
                    if required_new_execution_profile == Some(ExecutionProfile::ContainedLocal) {
                        return Err(ToolError::from(RuntimeError::new(
                            ordivon_runtime_core::RuntimeErrorCode::AuthorizationDenied,
                            "ordinary contained ingress cannot admit new operator ReleaseEffects",
                            Some("release"), false
                        )));
                    }
                    if !release_ready {
                        return Err(ToolError::invalid(
                            "qualified independent PG Release dispatcher is not running",
                            "release",
                        ));
                    }
                    let workspace=runtime.get_workspace(&RuntimeWorkspaceGetRequest {
                        schema_version:1,workspace_id:req.workspace_id.clone(),
                    }).map_err(ToolError::from)?;
                    let configured_source=runtime_release_source_identity(&configured.source_repo)
                        .map_err(|e|ToolError::invalid(e,"release.sourceRepo"))?;
                    let actual_source=std::fs::canonicalize(
                        workspace["sourceRepo"].as_str().ok_or_else(||
                            ToolError::invalid("Workspace sourceRepo missing","workspaceId")
                        )?
                    ).map_err(|e|ToolError::invalid(e.to_string(),"workspaceId"))?;
                    if actual_source!=configured_source.git_root
                        || workspace["dirty"]!=false
                    {
                        return Err(ToolError::invalid(
                            "Release Workspace must be clean and match the operator Git root",
                            "workspaceId",
                        ));
                    }
                    let head=workspace["currentHeadRevision"].as_str().ok_or_else(||
                        ToolError::invalid("Release Workspace Git HEAD missing","workspaceId")
                    )?;
                    let owner=runtime_release_owner_commit(&configured_source.owner_root,head)
                        .map_err(|e|ToolError::invalid(e,"commit"))?;
                    if owner!=req.commit {
                        return Err(ToolError::invalid(
                            "Release commit differs from the actual Workspace owner revision",
                            "commit",
                        ));
                    }
                    let candidate=configured.source_repo.join("target")
                        .join("ordivon-release-candidates")
                        .join(&req.commit).join("release")
                        .join("ordivon-deployment-manifest.json");
                    let manifest=std::fs::symlink_metadata(&candidate)
                        .map_err(|e|ToolError::invalid(e.to_string(),"candidateManifestDigest"))?;
                    if !manifest.is_file() || manifest.file_type().is_symlink()
                        || manifest.len()>4*1024*1024
                    {
                        return Err(ToolError::invalid(
                            "exact regular candidate manifest missing","candidateManifestDigest",
                        ));
                    }
                    let bytes=std::fs::read(&candidate)
                        .map_err(|e|ToolError::invalid(e.to_string(),"candidateManifestDigest"))?;
                    let digest=format!("sha256:{}",hex::encode(Sha256::digest(&bytes)));
                    if digest!=req.candidate_manifest_digest {
                        return Err(ToolError::invalid(
                            "candidate Manifest digest differs from committed proposal",
                            "candidateManifestDigest",
                        ));
                    }
                    value(runtime.admit_runtime_release_effect(
                        &req,&configured.operator_executable,&configured.receipt_root,
                    ))
                },
                "release.get" => {
                    let request: RuntimeReleaseGetToolRequest = parse(arguments)?;
                    value(runtime.get_runtime_release_effect(&RuntimeReleaseGetRequest {
                        schema_version: request.schema_version,
                        client_request_id: request.client_request_id,
                        principal: execution.principal.clone(),
                    }))
                },
                "job.list" => value(runtime.list(&execution.principal,&parse::<RuntimeJobListRequest>(arguments)?)),
                "workspace.get" => value(runtime.get_workspace(&parse::<RuntimeWorkspaceGetRequest>(arguments)?)),
                "workspace.list" => value(runtime.list_workspaces(&parse::<RuntimeWorkspaceListRequest>(arguments)?)),
                "workspace.diff" => {
                    let request:WorkspaceDiffRequest=parse(arguments)?;
                    let config=runtime.executor_config();
                    let result=workspace_diff_compact(&config,&ExecWorkspaceDiffRequest {
                        schema_version:request.schema_version,workspace_id:request.workspace_id,max_bytes:request.max_bytes
                    }).map_err(ToolError::from)?;
                    serde_json::to_value(result).map_err(|e|ToolError::internal(e.to_string()))
                },
                "workspace.changes" => {
                    let request:WorkspaceChangesRequest=parse(arguments)?;
                    let config=runtime.executor_config();
                    let result=workspace_changes_page(&config,&ExecWorkspaceChangePageRequest {
                        schema_version:request.schema_version,workspace_id:request.workspace_id,limit:request.limit,
                        max_bytes:request.max_bytes,cursor:request.cursor
                    }).map_err(ToolError::from)?;
                    serde_json::to_value(result).map_err(|e|ToolError::internal(e.to_string()))
                },
                "workspace.close" => value(runtime.close_workspace(&parse::<WorkspaceCloseRequest>(arguments)?)),
                "workspace.claim.reserve" => value(runtime.reserve_workspace_claim(
                    &execution.principal,
                    &parse::<ordivon_runtime_core::WorkspaceClaimReserveRequest>(arguments)?
                )),
                "workspace.claim.get" => value(runtime.get_workspace_claim(
                    &execution.principal,
                    &parse::<ordivon_runtime_core::WorkspaceClaimKeyRequest>(arguments)?
                )),
                "workspace.claim.release" => value(runtime.release_workspace_claim(
                    &execution.principal,
                    &parse::<ordivon_runtime_core::WorkspaceClaimKeyRequest>(arguments)?
                )),
                "workspace.mutate" => value(runtime.mutate_workspace(&parse::<WorkspaceMutateRequest>(arguments)?)),
                "workspace.read" => {
                    let request:WorkspaceReadRequest=parse(arguments)?;
                    let config=runtime.executor_config();
                    match request.mode {
                        WorkspaceReadMode::Full => {
                            if request.offset!=0 {return Err(ToolError::invalid("FULL offset must be zero","offset"));}
                            let result=read_workspace_text_compact(&config,&ExecWorkspaceReadRequest {
                                schema_version:request.schema_version,workspace_id:request.workspace_id,
                                relative_path:request.relative_path,max_bytes:request.max_bytes
                            }).map_err(ToolError::from)?;
                            value::<serde_json::Value>(Ok(json!({"content":result.content,"digest":result.digest})))
                        },
                        WorkspaceReadMode::Slice => {
                            let result=read_workspace_slice_compact(&config,&WorkspaceReadSliceRequest {
                                schema_version:request.schema_version,workspace_id:request.workspace_id,
                                relative_path:request.relative_path,max_bytes:request.max_bytes,offset:request.offset
                            }).map_err(ToolError::from)?;
                            value::<serde_json::Value>(Ok(json!({"content":result.content,"digest":result.file_digest,"fileByteLength":result.file_byte_length,"eof":result.eof})))
                        }
                    }
                },
                "workspace.open" => value(runtime.open_workspace(&parse::<WorkspaceOpenRequest>(arguments)?.bind())),
                "workspace.execPlan" => {
                    let omitted=profile_omitted_from_raw_tool_arguments(&arguments);
                    let request:WorkspaceExecPlanRequest=parse(arguments)?;
                    let bound=execution.bind_plan(request)?;
                    value(run_pg_direct_implicit_profile(
                        &runtime,bound,required_new_execution_profile,omitted
                    ))
                },
                "workspace.exec" => {
                    let omitted=profile_omitted_from_raw_tool_arguments(&arguments);
                    let bound=execution.bind(parse(arguments)?);
                    value(run_pg_direct_implicit_profile(
                        &runtime,bound,required_new_execution_profile,omitted
                    ))
                },
                "job.get" => {let r:JobGetRequest=parse(arguments)?; if r.schema_version!=1 {return Err(ToolError::invalid("schemaVersion must be 1","schemaVersion"));} value(runtime.get(&execution.principal,&r.job_id,r.event_limit))},
                "job.observe" => value(runtime.observe(&execution.principal,&parse(arguments)?)),
                "job.cancel" => value(runtime.cancel(&execution.principal,&parse(arguments)?)),
                "artifact.read" => value(runtime.read_artifact(&execution.principal,&parse(arguments)?)),
                _ => unreachable!(),
            }
        }).await.map_err(|e|McpError::internal_error(e.to_string(),None))?;
        match result {
            Ok(value) => {
                let value=if annotate_job_scheduling {
                    let runtime=annotation_runtime;
                    tokio::task::spawn_blocking(move||runtime.annotate_scheduling(value)).await
                        .map_err(|e|McpError::internal_error(e.to_string(),None))?
                        .map_err(|e|McpError::internal_error(e.to_string(),None))?
                } else {
                    value
                };
                Ok(CallToolResult::structured(value))
            },
            Err(e) => Ok(CallToolResult::structured_error(json!({"error":e}))),
        }
    }
}

impl ServerHandler for PgRuntimeServer {
    fn get_info(&self) -> rmcp::model::ServerConfig {
        rmcp::model::ServerConfig::new(ServerCapabilities::builder().enable_tools().build())
            .with_server_info(Implementation::new("ordivon-runtime-pg",env!("CARGO_PKG_VERSION")))
            .with_instructions("Fresh PostgreSQL Runtime, scoped execution vertical. Only listed tools are implemented. SQL starting is dispatch intent, not OS execution. No SQLite history. Local trusted principal only.")
    }
    fn supported_protocol_versions(&self) -> Cow<'static,[ProtocolVersion]> {
        Cow::Borrowed(&[ProtocolVersion::V_2026_07_28,ProtocolVersion::V_2025_11_25,ProtocolVersion::V_2025_06_18])
    }
    async fn list_tools(&self, _: Option<PaginatedRequestParams>, _: RequestContext<RoleServer>) -> Result<ListToolsResult,McpError> {
        Ok(ListToolsResult::with_all_items(self.catalog_for()).with_ttl_ms(0).with_cache_scope(CacheScope::Private))
    }
    fn get_tool(&self,name:&str) -> Option<Tool> {self.catalog_for().into_iter().find(|t|t.name.as_ref()==name)}
    async fn call_tool(&self, request:CallToolRequestParams, _:RequestContext<RoleServer>) -> Result<CallToolResponse,McpError> {
        self.call(request.name.to_string(),serde_json::Value::Object(request.arguments.unwrap_or_default())).await.map(CallToolResponse::Complete)
    }
    async fn discover(&self,_:RequestContext<RoleServer>) -> Result<DiscoverResult,McpError> {
        let mut result=DiscoverResult::from_server_info(self.supported_protocol_versions().into_owned(),self.get_info());
        let mut catalog=self.catalog_for(); catalog.sort_by(|a,b|a.name.cmp(&b.name));
        let digest=format!("sha256:{}",hex::encode(Sha256::digest(serde_json::to_vec(&catalog).expect("serializable Tool catalog"))));
        result.meta.get_or_insert_default().0.insert("com.ordivon/runtime/toolCatalogDigest".into(),json!(digest));
        Ok(result)
    }
}

#[cfg(test)]
mod pg_catalog_consumer_tests {
    use super::PgRuntimeServer;

    #[test]
    fn job_observe_discovery_describes_the_real_gateway_wait_mode() {
        // The actual Gateway consumer calls change_or_terminal; the PG19
        // native HTTP MCP integration test executes that exact mode.
        let tool = PgRuntimeServer::catalog()
            .into_iter()
            .find(|item| item.name.as_ref() == "job.observe")
            .expect("PG must expose the consumed observation tool");
        let description = tool.description.expect("Agent-visible behavior contract");
        assert!(description.contains("change_or_terminal"), "{description}");
        assert!(!description.contains("not supported"), "{description}");
    }
}


#[cfg(test)]
mod claim_release_route_authority_tests {
    use super::*;

    #[test]
    fn standalone_claim_finalizer_cannot_admit_jobs_or_close_workspaces() {
        assert!(ClaimReleaseIngress::DedicatedClaimOnly.may_release());
        assert!(!ClaimReleaseIngress::Ordinary.may_release());
        for name in CLAIM_ONLY_TOOL_NAMES {
            assert!(claim_only_route_guard(ClaimReleaseIngress::DedicatedClaimOnly, name).is_ok());
        }
        for forbidden in [
            "workspace.exec", "workspace.execPlan", "workspace.open",
            "workspace.close", "workspace.mutate", "job.cancel", "job.observe",
            "release.apply", "release.get", "artifact.content",
        ] {
            assert!(claim_only_route_guard(
                ClaimReleaseIngress::DedicatedClaimOnly, forbidden
            ).is_err(), "{forbidden}");
            assert!(claim_only_route_guard(
                ClaimReleaseIngress::DedicatedFinalizer, forbidden
            ).is_ok(), "existing same-PG Harness issuer mode must retain {forbidden}");
        }
        assert!(claim_release_route_guard(
            ClaimReleaseIngress::Ordinary.may_release(), "workspace.claim.release"
        ).is_err());
    }

    #[test]
    fn ordinary_ingress_must_never_inherit_finalizer_release_capability() {
        // Production may boot with no dedicated Harness profile at all. The
        // ordinary /mcp constructor must not silently permit raw Claim release.
        assert!(!ClaimReleaseIngress::Ordinary.may_release());
        assert!(ClaimReleaseIngress::DedicatedFinalizer.may_release());
        assert!(claim_release_route_guard(
            ClaimReleaseIngress::Ordinary.may_release(),
            "workspace.claim.release"
        ).is_err());
        for (route, expected) in [
            (ClaimReleaseIngress::Ordinary, false),
            (ClaimReleaseIngress::DedicatedFinalizer, true),
        ] {
            let catalog = PgRuntimeServer::catalog_for_route(false, route.may_release());
            assert_eq!(
                catalog.iter().any(|tool| tool.name.as_ref() == "workspace.claim.release"),
                expected,
            );
            assert_eq!(
                claim_release_route_guard(route.may_release(), "workspace.claim.release").is_ok(),
                expected,
            );
        }
    }

    #[test]
    fn raw_tool_dispatch_blocks_normal_known_key_but_not_claim_readback() {
        assert!(claim_release_route_guard(false, "workspace.claim.release").is_err());
        assert!(claim_release_route_guard(true, "workspace.claim.release").is_ok());
        assert!(claim_release_route_guard(false, "workspace.claim.get").is_ok());
        assert!(claim_release_route_guard(false, "workspace.claim.reserve").is_ok());
        // Tool-name obfuscation cannot become an alternate release API.
        assert!(PgRuntimeServer::catalog().iter().any(|t|
            t.name.as_ref() == "workspace.claim.release"));
        assert!(!PgRuntimeServer::catalog().iter().any(|t|
            t.name.as_ref() == "workspace.claim.release.legacy"));
        let isolated = PgRuntimeServer::catalog_for_route(false, false);
        let dedicated = PgRuntimeServer::catalog_for_route(false, true);
        assert!(dedicated.iter().any(|t| t.name.as_ref() == "workspace.claim.release"));
        assert!(!isolated.iter().any(|t| t.name.as_ref() == "workspace.claim.release"));
        assert_eq!(dedicated.len(), isolated.len() + 1);
        assert!(isolated.iter().any(|t| t.name.as_ref() == "workspace.claim.reserve"));
        assert!(isolated.iter().any(|t| t.name.as_ref() == "workspace.claim.get"));
    }
}

#[cfg(test)]
mod authenticated_execution_profile_projection_tests {
    use super::*;

    #[test]
    fn only_bound_contained_profile_is_advertised_to_normal_agents() {
        let mut description=json!({
            "targets":[
                {"target":"local_linux","executionProfiles":["trusted_local","contained_local"]},
                {"target":"windows_native","executionProfiles":["trusted_local"]}
            ]
        });
        project_ingress_execution_profiles(&mut description,Some(ExecutionProfile::ContainedLocal));
        assert_eq!(description["targets"][0]["executionProfiles"],json!(["contained_local"]));
        assert_eq!(description["targets"][1]["executionProfiles"],json!(["trusted_local"]));
        let unchanged=description.clone();
        project_ingress_execution_profiles(&mut description,None);
        assert_eq!(description,unchanged);
    }

    #[test]
    fn root_release_qualified_catalog_count_differs_from_no_root_fixture() {
        // R62 real production release rolled back before acceptance because
        // the disposable/no-Root integration profile advertised 22 tools but
        // Root-qualified ordinary /mcp advertised 23 (release.apply added).
        // Keep these exact *route/identity/config* contracts distinct.
        let ordinary_without_release = PgRuntimeServer::catalog_for_route(false, false);
        let ordinary_with_release = PgRuntimeServer::catalog_for_route(true, false);
        assert_eq!(ordinary_without_release.len(), 22);
        assert_eq!(ordinary_with_release.len(), 23);
        assert!(!ordinary_without_release.iter().any(|t| t.name.as_ref() == "release.apply"));
        assert!(ordinary_with_release.iter().any(|t| t.name.as_ref() == "release.apply"));
        assert!(!ordinary_with_release
            .iter()
            .any(|t| t.name.as_ref() == "workspace.claim.release"));
        assert!(ordinary_with_release
            .iter()
            .any(|t| t.name.as_ref() == "release.get"));

        let dedicated_finalizer = PgRuntimeServer::catalog_for_route(true, true);
        assert_eq!(dedicated_finalizer.len(), 24);
        assert!(dedicated_finalizer
            .iter()
            .any(|t| t.name.as_ref() == "workspace.claim.release"));

        // An authenticated ordinary contained-only profile cannot admit a
        // new Root release even when the operator's timer is configured.
        let mut ordinary_contained = ordinary_with_release;
        restrict_new_effect_catalog(
            &mut ordinary_contained,
            Some(ExecutionProfile::ContainedLocal),
        );
        assert_eq!(ordinary_contained.len(), 22);
        assert!(!ordinary_contained
            .iter()
            .any(|t| t.name.as_ref() == "release.apply"));

        // Claim-only is a third authority. Do not count its 4 capabilities
        // as the ordinary/Root release identity used by a SourceCut.
        let mut claim_only = dedicated_finalizer;
        claim_only.retain(|t| CLAIM_ONLY_TOOL_NAMES.contains(&t.name.as_ref()));
        assert_eq!(claim_only.len(), 4);
        assert!(!claim_only.iter().any(|t| t.name.as_ref() == "release.apply"));
    }

    #[test]
    fn contained_ordinary_catalog_hides_new_operator_release_but_keeps_readback() {
        let mut catalog=PgRuntimeServer::catalog_for_route(true,false);
        assert!(catalog.iter().any(|tool|tool.name.as_ref()=="release.apply"));
        restrict_new_effect_catalog(&mut catalog,Some(ExecutionProfile::ContainedLocal));
        assert!(!catalog.iter().any(|tool|tool.name.as_ref()=="release.apply"));
        assert!(catalog.iter().any(|tool|tool.name.as_ref()=="release.get"));
        let exec=catalog.iter().find(|tool|tool.name.as_ref()=="workspace.exec").unwrap();
        assert!(exec.description.as_ref().unwrap().contains("contained_local-only"));
    }
}

#[cfg(test)]
mod direct_implicit_execution_profile_tests {
    use super::*;

    #[test]
    fn explicit_trusted_or_present_null_can_never_be_auto_reinterpreted() {
        assert!(profile_omitted_from_raw_tool_arguments(&json!({
            "execution":{"workspaceId":"ws-direct","executable":"/usr/bin/true"}
        })));
        for explicit in [
            json!({"execution":{"executionProfile":"trusted_local"}}),
            json!({"execution":{"executionProfile":"contained_local"}}),
            json!({"execution":{"executionProfile":null}}),
            json!({"notExecution":{}}),
        ] {
            assert!(!profile_omitted_from_raw_tool_arguments(&explicit));
        }
    }
}
