// PostgreSQL-specific Job scheduling readback, composed onto the real MCP
// success contract. The portable Runtime Core Job structs do not own this PG
// scheduler facet; the PG adapter must describe every field it actually emits.
use ordivon_runtime_core::resource_scheduling::ResourceScheduling;

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
enum PgJobSchedulingState {
    Pending,
    Allocated,
    Released,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct PgJobSchedulingReadback {
    state: PgJobSchedulingState,
    request: ResourceScheduling,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pending_reason: Option<String>,
}

/// Extend only the exact PG success projections that contain the scheduler's
/// own readback. Retain the SDK's original error branch and closed object
/// contract; never set additionalProperties=true to suppress schema failures.
fn qualify_pg_scheduling_output_schema(tool: &mut Tool) {
    let definition = match tool.name.as_ref() {
        "workspace.exec" | "workspace.execPlan" | "job.observe" | "job.cancel" => {
            "JobObservation"
        }
        "job.list" => "RuntimeJobSummary",
        "job.get" => "RuntimeJobInspection",
        _ => return,
    };
    let mut schema = tool
        .output_schema
        .as_ref()
        .expect("PG must reuse an official SDK output schema")
        .as_ref()
        .clone();

    let mut readback = serde_json::to_value(schemars::schema_for!(PgJobSchedulingReadback))
        .expect("PG readback schema must serialize");
    let readback_root = readback
        .as_object_mut()
        .expect("PG scheduling schema root must be an object");
    let nested_definitions = readback_root
        .remove("$defs")
        .expect("PG scheduling schema must declare ResourceScheduling dependencies");
    readback_root.remove("$schema");

    let definitions = schema
        .get_mut("$defs")
        .and_then(serde_json::Value::as_object_mut)
        .expect("SDK success/error schema must have $defs");
    for (name, value) in nested_definitions
        .as_object()
        .expect("nested scheduling definitions must be objects")
    {
        match definitions.get(name) {
            Some(existing) => assert_eq!(existing, value, "conflicting schema definition {name}"),
            None => {
                definitions.insert(name.to_owned(), value.clone());
            }
        }
    }
    // Make the actual PG scheduling value a typed, closed contract that reuses
    // the Core ResourceScheduling type, not an unbounded JSON object.
    let earlier = definitions.insert(
        "PgJobSchedulingReadback".to_owned(),
        serde_json::Value::Object(readback_root.clone()),
    );
    assert!(earlier.is_none(), "duplicate PG scheduling schema definition");

    let target = definitions
        .get_mut(definition)
        .and_then(serde_json::Value::as_object_mut)
        .expect("SDK must publish the expected exact PG success definition");
    let properties = target
        .get_mut("properties")
        .and_then(serde_json::Value::as_object_mut)
        .expect("success definition must be an object");
    assert!(
        properties
            .insert(
                "scheduling".to_owned(),
                json!({"$ref":"#/$defs/PgJobSchedulingReadback"}),
            )
            .is_none(),
        "scheduler annotation must not shadow a Core field"
    );
    target
        .get_mut("required")
        .and_then(serde_json::Value::as_array_mut)
        .expect("Core success schema must have required fields")
        .push(json!("scheduling"));

    tool.output_schema = Some(Arc::new(schema));
}

#[cfg(test)]
mod pg_scheduling_output_contract_tests {
    use super::*;

    #[test]
    fn exact_success_schema_exposes_scheduling_but_preserves_closed_objects_and_errors() {
        for (tool_name, definition) in [
            ("workspace.exec", "JobObservation"),
            ("workspace.execPlan", "JobObservation"),
            ("job.observe", "JobObservation"),
            ("job.cancel", "JobObservation"),
            ("job.list", "RuntimeJobSummary"),
            ("job.get", "RuntimeJobInspection"),
        ] {
            let tool = PgRuntimeServer::catalog()
                .into_iter()
                .find(|tool| tool.name.as_ref() == tool_name)
                .expect("PG tool must exist");
            let schema = serde_json::Value::Object(
                tool.output_schema.expect("output schema").as_ref().clone(),
            );
            assert_eq!(schema["oneOf"].as_array().unwrap().len(), 2, "{tool_name}");
            assert_eq!(
                schema["$defs"][definition]["properties"]["scheduling"]["$ref"],
                "#/$defs/PgJobSchedulingReadback",
                "{tool_name}"
            );
            assert!(
                schema["$defs"][definition]["required"]
                    .as_array()
                    .unwrap()
                    .contains(&json!("scheduling")),
                "{tool_name}"
            );
            let portable = RuntimeServer::tool_router()
                .list_all()
                .into_iter()
                .find(|item| item.name.as_ref() == tool_name)
                .expect("portable MCP surface");
            let original = serde_json::Value::Object(
                portable.output_schema.expect("original output").as_ref().clone(),
            );
            assert_eq!(
                schema["$defs"][definition]["additionalProperties"],
                original["$defs"][definition]["additionalProperties"],
                "{tool_name}: never weaken original object closure"
            );
            assert!(schema["$defs"]["ToolErrorEnvelope"].is_object(), "{tool_name}");
            assert_eq!(
                schema["$defs"]["PgJobSchedulingReadback"]["additionalProperties"],
                false,
                "{tool_name}"
            );
            assert_eq!(
                schema["$defs"]["PgJobSchedulingState"]["enum"],
                json!(["pending", "allocated", "released"]),
                "{tool_name}"
            );
        }
    }

    #[test]
    fn typed_pg_scheduling_readback_rejects_malformed_provider_data() {
        let request = serde_json::to_value(ResourceScheduling::default()).unwrap();
        for (state, reason) in [
            ("pending", Some("waiting_for_resources_pressure_or_workspace_lease")),
            ("allocated", None),
            ("released", None),
        ] {
            let valid = json!({
                "state": state,
                "request": request,
                "pendingReason": reason
            });
            let typed: PgJobSchedulingReadback = serde_json::from_value(valid).unwrap();
            assert_eq!(serde_json::to_value(typed).unwrap()["state"], state);
        }
        let bad_state = json!({"state":"SUCCESS","request":request});
        assert!(serde_json::from_value::<PgJobSchedulingReadback>(bad_state).is_err());
        let unknown_field = json!({"state":"released","request":request,"proof":true});
        assert!(serde_json::from_value::<PgJobSchedulingReadback>(unknown_field).is_err());
    }

    #[test]
    fn non_scheduler_tool_contract_stays_unmodified() {
        let native = RuntimeServer::tool_router()
            .list_all()
            .into_iter()
            .find(|tool| tool.name.as_ref() == "workspace.close")
            .unwrap();
        let pg = PgRuntimeServer::catalog()
            .into_iter()
            .find(|tool| tool.name.as_ref() == "workspace.close")
            .unwrap();
        assert_eq!(native.output_schema, pg.output_schema);
        assert_eq!(native.input_schema, pg.input_schema);
    }
}
