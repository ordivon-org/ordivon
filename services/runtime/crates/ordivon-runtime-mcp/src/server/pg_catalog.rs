// One typed MCP PG catalog over the existing portable Serde/JsonSchema contracts.
// No legacy Registry or RuntimeServer is constructed or linked by this catalog.
//
// The legacy SDK ToolRouter is checked against this exact typed catalog in
// contract tests. Tool names and flags are not independent JSON snapshots.

fn pg_portable_tool_catalog() -> Vec<Tool> {
    fn entry<Input: JsonSchema + 'static, Output: JsonSchema + 'static>(
        name: &'static str,
        title: &'static str,
        read_only: bool,
        destructive: bool,
        idempotent: bool,
        open_world: bool,
    ) -> Tool {
        let input_schema = rmcp::handler::server::common::schema_for_input::<Input>()
            .expect("portable MCP input must be a typed object");
        let output_schema = rmcp::handler::server::common::schema_for_output::<ToolOutcome<Output>>();
        Tool::new(name, "", input_schema)
            .with_raw_output_schema(output_schema)
            .with_annotations(ToolAnnotations::from_raw(
                Some(title.to_owned()),
                Some(read_only),
                Some(destructive),
                Some(idempotent),
                Some(open_world),
            ))
    }

    vec![
        entry::<RuntimeDescribeRequest, RuntimeDescribeResult>("runtime.describe", "Describe runtime affordances", true, false, true, false),
        entry::<RuntimeReleaseApplyToolRequest, RuntimeReleaseAdmission>("release.apply", "Apply structured Runtime release", false, true, true, true),
        entry::<RuntimeReleaseGetToolRequest, RuntimeReleaseProjection>("release.get", "Get structured Runtime release", true, false, true, false),
        entry::<WorkspaceOpenRequest, CompactWorkspaceOpenResult>("workspace.open", "Open isolated workspace", false, false, false, false),
        entry::<WorkspaceCloseRequest, WorkspaceCloseResult>("workspace.close", "Close workspace", false, true, true, false),
        entry::<RuntimeWorkspaceGetRequest, RuntimeWorkspaceSummary>("workspace.get", "Get workspace state", true, false, true, false),
        entry::<RuntimeWorkspaceListRequest, RuntimeWorkspaceListResult>("workspace.list", "List open workspaces", true, false, true, false),
        entry::<WorkspaceReadRequest, WorkspaceReadResult>("workspace.read", "Read workspace content", true, false, true, false),
        entry::<WorkspaceFileToolRequest, WorkspaceFileProjectionMetadata>("workspace.file", "Read verified workspace file", true, false, true, false),
        entry::<WorkspaceContentRequest, WorkspaceContentMetadata>("workspace.content", "Read verified workspace media content", true, false, true, false),
        entry::<WorkspaceMutateRequest, WorkspaceMutateResult>("workspace.mutate", "Mutate workspace files", false, true, false, false),
        entry::<WorkspaceChangesRequest, WorkspaceChangePageResult>("workspace.changes", "Page workspace changes", true, false, true, false),
        entry::<WorkspaceDiffRequest, CompactWorkspaceDiffResult>("workspace.diff", "Inspect workspace diff", true, false, true, false),
        entry::<WorkspaceExecRequest, JobObservation>("workspace.exec", "Execute transactional workspace job", false, true, false, true),
        entry::<WorkspaceExecPlanRequest, JobObservation>("workspace.execPlan", "Execute fail-fast workspace plan", false, true, false, true),
        entry::<JobGetRequest, RuntimeJobInspection>("job.get", "Get transactional job", true, false, true, false),
        entry::<JobObserveRequest, JobObservation>("job.observe", "Observe transactional job", false, true, true, true),
        entry::<JobCancelRequest, JobObservation>("job.cancel", "Cancel transactional job", false, true, true, false),
        entry::<RuntimeJobListRequest, RuntimeJobListResult>("job.list", "List transactional jobs", true, false, true, false),
        entry::<ArtifactContentRequest, ArtifactContentProjectionMetadata>("artifact.content", "Read verified job artifact content", true, false, true, false),
        entry::<ArtifactReadRequest, ArtifactReadResult>("artifact.read", "Read transactional job artifact", true, false, true, false),
    ]
}

#[cfg(all(test, feature = "legacy-runtime"))]
mod pg_portable_catalog_parity_tests {
    use super::*;

    #[test]
    fn pg_portable_catalog_is_exactly_the_legacy_sdk_schema_for_each_exposed_tool() {
        let legacy = RuntimeServer::tool_router().list_all();
        let portable = pg_portable_tool_catalog();
        assert_eq!(portable.len(), 21);
        for tool in portable {
            let original = legacy.iter().find(|t| t.name == tool.name)
                .unwrap_or_else(|| panic!("missing legacy contract for {}", tool.name));
            assert_eq!(tool.input_schema, original.input_schema, "{} input", tool.name);
            assert_eq!(tool.output_schema, original.output_schema, "{} output", tool.name);
            assert_eq!(tool.annotations, original.annotations, "{} annotations", tool.name);
        }
    }
}

/// Additional PG-native Workspace ownership tools: deliberately not legacy
/// SDK parity tools, and not tied to Harness's independent database.
fn pg_workspace_claim_catalog() -> Vec<Tool> {
    fn entry<I: JsonSchema + 'static, O: JsonSchema + 'static>(
        name: &'static str, title: &'static str, read_only: bool
    ) -> Tool {
        let input = rmcp::handler::server::common::schema_for_input::<I>()
            .expect("PG Workspace Claim input must be typed");
        let output = rmcp::handler::server::common::schema_for_output::<ToolOutcome<O>>();
        Tool::new(name, "", input).with_raw_output_schema(output)
            .with_annotations(ToolAnnotations::from_raw(
                Some(title.to_owned()), Some(read_only),
                Some(!read_only), Some(true), Some(false),
            ))
    }
    vec![
        entry::<ordivon_runtime_core::WorkspaceClaimReserveRequest,
                 ordivon_runtime_core::WorkspaceClaimProjection>(
            "workspace.claim.reserve", "Pin workspace for logical Run", false),
        entry::<ordivon_runtime_core::WorkspaceClaimKeyRequest,
                 ordivon_runtime_core::WorkspaceClaimProjection>(
            "workspace.claim.get", "Read exact Runtime workspace claim", true),
        entry::<ordivon_runtime_core::WorkspaceClaimKeyRequest,
                 ordivon_runtime_core::WorkspaceClaimProjection>(
            "workspace.claim.release", "Release physical Workspace pin", false),
    ]
}


#[cfg(all(test, feature = "postgres-runtime"))]
mod workspace_claim_catalog_contract_tests {
    use super::*;

    #[test]
    fn runtime_owned_pin_tools_are_typed_and_distinct_from_legacy_contracts() {
        let additions = pg_workspace_claim_catalog();
        let names = additions.iter().map(|t| t.name.to_string()).collect::<Vec<_>>();
        assert_eq!(names, [
            "workspace.claim.reserve", "workspace.claim.get", "workspace.claim.release"
        ]);
        assert!(additions.iter().all(|t| !t.input_schema.is_empty()));
        assert!(additions.iter().all(|t| t.output_schema.is_some()));
        assert_eq!(pg_portable_tool_catalog().len(), 21);
        assert!(additions.iter().all(|a|
            pg_portable_tool_catalog().iter().all(|old| old.name != a.name)));
    }
}
