//! Pure RMCP ServerHandler transport boundary; tool execution stays in dispatch.
use super::{
    CacheScope, CallToolRequestParams, CallToolResponse, Cow, Digest, DiscoverResult,
    Implementation, ListToolsResult, McpError, PaginatedRequestParams, PgRuntimeServer,
    ProtocolVersion, RequestContext, RoleServer, ServerCapabilities, ServerHandler, Sha256,
    Tool, json,
};
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
