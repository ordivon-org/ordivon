/// Independently launched fresh-PG MCP adapter. The SQLite Engine is never constructed.
#[derive(Clone)]
pub struct PgRuntimeServer {
    runtime: ordivon_runtime_core::PgRuntime,
    execution: ExecutionContext,
}

impl PgRuntimeServer {
    pub fn new(runtime: ordivon_runtime_core::PgRuntime, execution: ExecutionContext) -> Self {
        Self { runtime, execution }
    }
    pub fn catalog() -> Vec<Tool> {
        RuntimeServer::tool_router().list_all().into_iter().filter_map(|mut t| {
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
                "workspace.close" => "Close a fresh-epoch Git Workspace only after the PostgreSQL Job admission fence finds no active or held consumer.",
                "workspace.mutate" => "Apply the mature atomic Workspace mutation contract, serialized against active PostgreSQL Job admission.",
                "workspace.read" => "Read bounded UTF-8 files from an isolated fresh-epoch Workspace using the native Workspace path authority.",
                "workspace.open" => "Create a fresh Git Workspace using the native Workspace contract. No SQLite history is imported.",
                "workspace.execPlan" => "Run an ordered plan with the mature native Runner; PG commits the exact immutable step plan before physical launch. No input or credential bindings.",
                "workspace.exec" => "Fresh PostgreSQL execution vertical: one trusted_local local_linux command. Steps, hostDependencies, foreignReferences and Windows context are rejected. PostgreSQL commits admission and dispatch intent before the existing systemd runner launches. A starting Attempt is dispatch intent, not proof of a running process. Ambiguous launches are never automatically reissued. Use job.observe to reconcile native runner evidence.",
                "job.get" => "Read a PostgreSQL Job projection without dispatch or reconciliation. migrationVersion=0 identifies the fresh PG schema rather than SQLite migrations.",
                "job.observe" => "Observe and reconcile a principal-owned PostgreSQL Job using native runner evidence; may dispatch an accepted Job once. Supports terminal and change_or_terminal waiting with bounded output offsets. Does not claim domain semantic completion.",
                "job.cancel" => "Persist PostgreSQL cancellation intent before requesting the native systemd cgroup stop. A stop submission never proves terminal execution. Unissued cancelled work remains reserved pending recovery.",
                "artifact.read" => "Read a bounded verified UTF-8 range of a PostgreSQL-registered Artifact. Revalidates retained bytes against their digest and length.",
                _ => return None,
            };
            t.description=Some(description.into());
            Some(t)
        }).collect()
    }
    /// Shared by the MCP handler and protocol consumer tests; performs real Core calls.
    pub async fn call(&self, name: String, arguments: serde_json::Value) -> Result<CallToolResult, McpError> {
        if !Self::catalog().iter().any(|t|t.name.as_ref()==name) {
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
                    value(runtime.describe())
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
                    let request:WorkspaceExecPlanRequest=parse(arguments)?;
                    let bound=execution.bind_plan(request)?;
                    value(runtime.run(&bound))
                },
                "workspace.exec" => value(runtime.run(&execution.bind(parse(arguments)?))),
                "job.get" => {let r:JobGetRequest=parse(arguments)?; if r.schema_version!=1 {return Err(ToolError::invalid("schemaVersion must be 1","schemaVersion"));} value(runtime.get(&execution.principal,&r.job_id,r.event_limit))},
                "job.observe" => value(runtime.observe(&execution.principal,&parse(arguments)?)),
                "job.cancel" => value(runtime.cancel(&execution.principal,&parse(arguments)?)),
                "artifact.read" => value(runtime.read_artifact(&execution.principal,&parse(arguments)?)),
                _ => unreachable!(),
            }
        }).await.map_err(|e|McpError::internal_error(e.to_string(),None))?;
        match result {
            Ok(value) => Ok(CallToolResult::structured(value)),
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
        Ok(ListToolsResult::with_all_items(Self::catalog()).with_ttl_ms(0).with_cache_scope(CacheScope::Private))
    }
    fn get_tool(&self,name:&str) -> Option<Tool> {Self::catalog().into_iter().find(|t|t.name.as_ref()==name)}
    async fn call_tool(&self, request:CallToolRequestParams, _:RequestContext<RoleServer>) -> Result<CallToolResponse,McpError> {
        self.call(request.name.to_string(),serde_json::Value::Object(request.arguments.unwrap_or_default())).await.map(CallToolResponse::Complete)
    }
    async fn discover(&self,_:RequestContext<RoleServer>) -> Result<DiscoverResult,McpError> {
        let mut result=DiscoverResult::from_server_info(self.supported_protocol_versions().into_owned(),self.get_info());
        let mut catalog=Self::catalog(); catalog.sort_by(|a,b|a.name.cmp(&b.name));
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
