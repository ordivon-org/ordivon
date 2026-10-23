use super::*;

#[test]
fn job_get_schema_is_projection_only_and_detail_free() {
    let sandbox = Sandbox::new("job-get-schema");
    let server = sandbox.server();
    let job_get = server
        .tool_router
        .list_all()
        .into_iter()
        .find(|tool| tool.name.as_ref() == "job.get")
        .unwrap();
    let input = serde_json::to_value(&job_get.input_schema).unwrap();
    assert_eq!(
        input.pointer("/properties/eventLimit/default"),
        Some(&serde_json::json!(DEFAULT_INSPECTION_EVENT_LIMIT))
    );
    assert_eq!(
        input.pointer("/properties/eventLimit/maximum"),
        Some(&serde_json::json!(MAX_INSPECTION_EVENT_LIMIT))
    );
    assert!(input.pointer("/properties/includeDetail").is_none());
    assert!(input.pointer("/properties/waitMs").is_none());
    assert!(input.pointer("/properties/stdoutTailBytes").is_none());

    let output = serde_json::to_value(job_get.output_schema.as_ref().unwrap()).unwrap();
    let encoded = serde_json::to_string(&output).unwrap();
    for expected in [
        "sourceRevision",
        "workspaceSourceDigest",
        "mechanicallyConverged",
        "semanticCompletionEvaluated",
        "attemptsTruncated",
        "eventsTruncated",
        "timeline",
        "episodes",
        "artifacts",
    ] {
        assert!(
            encoded.contains(expected),
            "job.get output omitted {expected}"
        );
    }
}
#[test]
fn workspace_projection_output_schema_distinguishes_lineage_from_current_head() {
    let sandbox = Sandbox::new("workspace-revision-output-schema");
    let tools = sandbox.server().tool_router.list_all();
    for name in ["workspace.get", "workspace.list"] {
        let tool = tools
            .iter()
            .find(|tool| tool.name.as_ref() == name)
            .unwrap();
        let schema = serde_json::to_string(tool.output_schema.as_ref().unwrap()).unwrap();
        assert!(
            schema.contains("sourceRevision"),
            "{name} omitted sourceRevision"
        );
        assert!(
            schema.contains("currentHeadRevision"),
            "{name} omitted currentHeadRevision"
        );
    }
}
#[test]
fn workspace_list_schema_makes_exact_source_digest_opt_in() {
    let sandbox = Sandbox::new("workspace-list-schema");
    let server = sandbox.server();
    let tool = server
        .tool_router
        .list_all()
        .into_iter()
        .find(|tool| tool.name.as_ref() == "workspace.list")
        .unwrap();
    let schema = serde_json::to_value(&tool.input_schema).unwrap();
    let required = schema
        .pointer("/required")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    assert!(!required
        .iter()
        .any(|value| value.as_str() == Some("includeSourceStateDigest")));
    assert!(!required
        .iter()
        .any(|value| value.as_str() == Some("cursor")));
    assert!(schema.pointer("/properties/cursor").is_some());
    assert!(schema
        .pointer("/$defs/RuntimeWorkspaceListCursor/properties/createdAtMs")
        .is_some());
    assert!(schema
        .pointer("/$defs/RuntimeWorkspaceListCursor/properties/workspaceId")
        .is_some());
    assert_eq!(
        schema
            .pointer("/properties/includeSourceStateDigest/default")
            .and_then(Value::as_bool),
        Some(false)
    );
}
