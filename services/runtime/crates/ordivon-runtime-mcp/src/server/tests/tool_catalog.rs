use super::*;

#[test]
fn tool_catalog_uses_transactional_job_contract() {
    let sandbox = Sandbox::new("catalog");
    let server = sandbox.server();
    let mut tools = server.tool_router.list_all();
    tools.sort_by(|left, right| left.name.cmp(&right.name));
    let names: Vec<_> = tools.iter().map(|tool| tool.name.as_ref()).collect();
    assert_eq!(
        names,
        [
            "artifact.read",
            "input.ingest",
            "job.cancel",
            "job.get",
            "job.list",
            "job.observe",
            "release.apply",
            "release.get",
            "runtime.describe",
            "workspace.changes",
            "workspace.close",
            "workspace.content",
            "workspace.diff",
            "workspace.exec",
            "workspace.execBound",
            "workspace.execBoundTrusted",
            "workspace.execCredentialBoundTrusted",
            "workspace.execPlan",
            "workspace.get",
            "workspace.list",
            "workspace.mutate",
            "workspace.open",
            "workspace.read",
        ]
    );
    for tool in tools.iter().filter(|tool| tool.name.as_ref() != "job.list") {
        let schema = serde_json::to_value(&tool.input_schema).unwrap();
        assert_eq!(
            schema.pointer("/properties/schemaVersion/const"),
            Some(&serde_json::json!(1)),
            "{} schemaVersion const drifted",
            tool.name
        );
        assert_eq!(
            schema.pointer("/properties/schemaVersion/minimum"),
            Some(&serde_json::json!(1)),
            "{} schemaVersion minimum drifted",
            tool.name
        );
        assert_eq!(
            schema.pointer("/properties/schemaVersion/maximum"),
            Some(&serde_json::json!(1)),
            "{} schemaVersion maximum drifted",
            tool.name
        );
    }

    let exec = tools
        .iter()
        .find(|tool| tool.name.as_ref() == "workspace.exec")
        .unwrap();

    assert_eq!(
        exec.annotations
            .as_ref()
            .and_then(|annotations| annotations.idempotent_hint),
        Some(false)
    );
    let schema = serde_json::to_string(&exec.input_schema).unwrap();
    assert!(schema.contains("clientRequestId"));
    assert!(!schema.contains("taskId"));
    let exec_schema = serde_json::to_value(&exec.input_schema).unwrap();
    assert!(exec_schema
        .pointer("/$defs/ExecutionProposal/properties/executable/description")
        .and_then(Value::as_str)
        .is_some_and(|description| description.contains("Absolute host path")));
    assert!(exec_schema
        .pointer("/$defs/ExecutionProposal/properties/cwdRelative/description")
        .and_then(Value::as_str)
        .is_some_and(|description| description.contains("relative to the Workspace root")));
    for (tool_name, execution_definition) in [
        ("workspace.exec", "ExecutionProposal"),
        ("workspace.execBound", "WorkspaceExecBoundExecution"),
        ("workspace.execPlan", "WorkspaceExecPlanInput"),
    ] {
        let tool = tools
            .iter()
            .find(|tool| tool.name.as_ref() == tool_name)
            .unwrap();
        let tool_schema = serde_json::to_value(&tool.input_schema).unwrap();
        assert!(
            tool_schema
                .pointer("/properties/stdoutTailBytes/description")
                .and_then(Value::as_str)
                .is_some_and(|description| {
                    description.contains("MCP response tail")
                        && description.contains("execution.stdoutLimitBytes")
                }),
            "{tool_name} stdoutTailBytes must distinguish response tail from Job retention"
        );
        assert!(
            tool_schema
                .pointer("/properties/stderrTailBytes/description")
                .and_then(Value::as_str)
                .is_some_and(|description| {
                    description.contains("MCP response tail")
                        && description.contains("execution.stderrLimitBytes")
                }),
            "{tool_name} stderrTailBytes must distinguish response tail from Job retention"
        );
        assert!(
            tool_schema
                .pointer(&format!(
                    "/$defs/{execution_definition}/properties/stdoutLimitBytes/description"
                ))
                .and_then(Value::as_str)
                .is_some_and(|description| {
                    description.contains("Job/Attempt") && description.contains("stdoutTailBytes")
                }),
            "{tool_name} stdoutLimitBytes must distinguish Job retention from response tail"
        );
        assert!(
            tool_schema
                .pointer(&format!(
                    "/$defs/{execution_definition}/properties/stderrLimitBytes/description"
                ))
                .and_then(Value::as_str)
                .is_some_and(|description| {
                    description.contains("Job/Attempt") && description.contains("stderrTailBytes")
                }),
            "{tool_name} stderrLimitBytes must distinguish Job retention from response tail"
        );
    }
    assert_eq!(
        exec_schema.pointer("/$defs/ExecutionProposal/properties/executionProfile/default"),
        Some(&serde_json::json!("trusted_local"))
    );
    assert_eq!(
        exec_schema.pointer("/$defs/ExecutionProfile/enum"),
        Some(&serde_json::json!(["trusted_local", "contained_local"]))
    );
    assert_eq!(
        exec_schema.pointer("/$defs/ExecutionProposal/properties/executionTarget/default"),
        Some(&serde_json::json!("local_linux"))
    );
    assert_eq!(
        exec_schema.pointer("/$defs/ExecutionTarget/enum"),
        Some(&serde_json::json!(["local_linux", "windows_native"]))
    );
    assert_eq!(
        exec_schema.pointer("/$defs/ExecutionProposal/properties/windowsAuthority/default"),
        Some(&serde_json::json!("limited"))
    );
    assert_eq!(
        exec_schema.pointer("/$defs/WindowsAuthority/enum"),
        Some(&serde_json::json!(["limited", "elevated", "active_user"]))
    );
    assert!(exec_schema
        .pointer("/$defs/ExecutionProposal/properties/foreignReferences/maxItems")
        .is_none());
    assert_eq!(
        exec_schema.pointer("/$defs/ExecutionProposal/properties/foreignReferences/items/$ref"),
        Some(&serde_json::json!("#/$defs/ForeignReference"))
    );
    assert_eq!(
        exec_schema.pointer("/$defs/ForeignReference/required"),
        Some(&serde_json::json!(["namespace", "type", "id"]))
    );
    assert_eq!(
        exec_schema.pointer("/$defs/ForeignReference/additionalProperties"),
        Some(&serde_json::json!(false))
    );

    for budget_field in ["memoryMaxBytes", "tasksMax", "cpuQuotaPercent"] {
        assert_eq!(
            exec_schema.pointer(&format!(
                "/$defs/ExecutionBudget/properties/{budget_field}/minimum"
            )),
            Some(&serde_json::json!(1))
        );
        assert!(exec_schema
            .pointer(&format!(
                "/$defs/ExecutionBudget/properties/{budget_field}/maximum"
            ))
            .is_none());
    }
    for server_owned in ["principal", "globalLimit", "profileLimit"] {
        assert!(
            !schema.contains(server_owned),
            "schema exposes {server_owned}"
        );
    }

    let mutate = tools
        .iter()
        .find(|tool| tool.name.as_ref() == "workspace.mutate")
        .unwrap();
    let mutate_schema = serde_json::to_value(&mutate.input_schema).unwrap();
    assert_eq!(
        mutate_schema.pointer("/$defs/WorkspaceMutation/properties/mode/enum"),
        Some(&serde_json::json!(["WRITE", "APPEND", "REPLACE_EXACT"]))
    );
    assert_eq!(
        mutate_schema.pointer("/properties/mutations/minItems"),
        Some(&serde_json::json!(1))
    );
    assert!(mutate_schema
        .pointer("/properties/mutations/maxItems")
        .is_none());
    assert!(
        mutate_schema
            .pointer("/$defs/WorkspaceMutation/properties/expectedDigest/description")
            .and_then(Value::as_str)
            .is_some_and(
                |description| description.contains("Required when the target already exists")
            )
    );

    let observe = tools
        .iter()
        .find(|tool| tool.name.as_ref() == "job.observe")
        .unwrap();
    let observe_schema = serde_json::to_value(&observe.input_schema).unwrap();
    assert_eq!(
        observe_schema.pointer("/properties/waitMs/maximum"),
        Some(&serde_json::json!(30_000))
    );
    assert_eq!(
        observe_schema.pointer("/properties/stdoutTailBytes/maximum"),
        Some(&serde_json::json!(65_536))
    );
    assert!(observe_schema.pointer("/properties/stdoutOffset").is_some());
    assert!(observe_schema.pointer("/properties/stderrOffset").is_some());

    let list = tools
        .iter()
        .find(|tool| tool.name.as_ref() == "job.list")
        .unwrap();
    let list_schema = serde_json::to_value(&list.input_schema).unwrap();
    assert_eq!(
        list_schema.pointer("/properties/limit/maximum"),
        Some(&serde_json::json!(100))
    );
    assert_eq!(
        list_schema.pointer("/properties/limit/default"),
        Some(&serde_json::json!(20))
    );
    assert!(list_schema.pointer("/properties/clientRequestId").is_some());

    let close = tools
        .iter()
        .find(|tool| tool.name.as_ref() == "workspace.close")
        .unwrap();
    let close_schema = serde_json::to_value(&close.input_schema).unwrap();
    assert_eq!(
        close_schema.pointer("/properties/force/default"),
        Some(&serde_json::json!(false))
    );
}
#[test]
fn tool_catalog_digest_is_deterministic_and_discovery_visible() {
    let sandbox = Sandbox::new("catalog-digest");
    let server = sandbox.server();
    let first = server.tool_catalog_digest();
    let second = server.tool_catalog_digest();
    assert_eq!(first, second);
    assert!(first.starts_with("sha256:"));
    assert_eq!(first.len(), 71);

    let result = server.discovery_result();
    assert_eq!(result.ttl_ms, 0);
    assert_eq!(result.cache_scope, CacheScope::Private);
    assert_eq!(
        result
            .meta
            .as_ref()
            .and_then(|meta| meta.0.get("com.ordivon/runtime/toolCatalogDigest"))
            .and_then(serde_json::Value::as_str),
        Some(first.as_str())
    );
    assert_eq!(
        result.supported_versions,
        vec![
            ProtocolVersion::V_2026_07_28,
            ProtocolVersion::V_2025_11_25,
            ProtocolVersion::V_2025_06_18,
        ]
    );
    assert!(result.capabilities.tools.is_some());
    assert!(result.capabilities.extensions.is_none());
}
#[test]
fn tools_list_projection_carries_required_private_zero_ttl_cache_hints() {
    let server = Sandbox::new("tools-list-cache-hints").server();
    let value = serde_json::to_value(server.list_tools_projection()).unwrap();
    assert_eq!(value.get("ttlMs"), Some(&serde_json::json!(0)));
    assert_eq!(value.get("cacheScope"), Some(&serde_json::json!("private")));
    assert_eq!(
        value.get("resultType"),
        Some(&serde_json::json!("complete"))
    );
    assert!(value.get("tools").and_then(Value::as_array).is_some());
}
#[test]
fn compiled_tool_catalog_identity_is_deterministic_and_host_extension_free() {
    let first = RuntimeServer::compiled_tool_catalog_identity();
    let second = RuntimeServer::compiled_tool_catalog_identity();
    assert_eq!(first, second);
    assert_eq!(first.0, 23);
    assert!(first.1.starts_with("sha256:"));
    assert_eq!(first.1.len(), 71);

    let sandbox = Sandbox::new("compiled-catalog-base");
    let server = sandbox.server_with_input_ingress();
    assert_eq!(RuntimeServer::compiled_tool_catalog_identity(), first);
    assert_ne!(server.tool_catalog_digest(), first.1);
}
