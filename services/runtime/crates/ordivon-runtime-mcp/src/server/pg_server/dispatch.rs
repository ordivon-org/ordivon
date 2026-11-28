//! Native PG MCP Tool dispatch preserving original effect/replay and PG readback contracts.
use super::{
    CallToolResult, Digest, ExecWorkspaceChangePageRequest,
    ExecWorkspaceDiffRequest, ExecWorkspaceReadRequest, ExecutionProfile, JobGetRequest,
    McpError, PgRuntimeServer, RUNTIME_SCHEMA_VERSION, RuntimeDescribeRequest,
    RuntimeError, RuntimeJobListRequest, RuntimeReleaseApplyToolRequest,
    RuntimeReleaseGetRequest, RuntimeReleaseGetToolRequest, RuntimeReleaseRequest,
    RuntimeWorkspaceGetRequest, RuntimeWorkspaceListRequest, Sha256,
    ToolError, ToolOutcome, WorkspaceChangesRequest, WorkspaceCloseRequest,
    WorkspaceDiffRequest, WorkspaceExecPlanRequest, WorkspaceFileToolRequest,
    WorkspaceMutateRequest, WorkspaceOpenRequest, WorkspaceReadMode, WorkspaceReadRequest,
    WorkspaceReadSliceRequest, artifact_content_call_result, claim_only_route_guard,
    json, pg_scheduling_success_definition, profile_omitted_from_raw_tool_arguments,
    project_ingress_execution_profiles, read_workspace_slice_compact,
    read_workspace_text_compact, run_pg_direct_implicit_profile,
    runtime_release_owner_commit, runtime_release_source_identity, workspace_changes_page,
    workspace_content_call_result, workspace_diff_compact, workspace_file_call_result,
};

impl PgRuntimeServer {
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
    }}
