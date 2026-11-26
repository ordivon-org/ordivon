//! Add a PG scheduling facet only to SDK Job success; retain closed error/readback schemas.
use super::pg_job_scheduling_wire::PgJobSchedulingReadback;
use rmcp::model::Tool;
use serde_json::json;
use std::sync::Arc;

/// The one source of truth for which MCP Tool success schemas actually
/// permit a PG scheduling facet. In particular artifact.read has a jobId
/// but its closed ArtifactReadResult schema does NOT contain scheduling.
pub(super) fn pg_scheduling_success_definition(name: &str) -> Option<&'static str> {
    match name {
        "workspace.exec" | "workspace.execPlan" | "job.observe" | "job.cancel" => {
            Some("JobObservation")
        }
        "job.list" => Some("RuntimeJobSummary"),
        "job.get" => Some("RuntimeJobInspection"),
        _ => None,
    }
}

/// Extend only the exact PG success projections that contain the scheduler's
/// own readback. Retain the SDK's original error branch and closed object
/// contract; never set additionalProperties=true to suppress schema failures.
pub(super) fn qualify_pg_scheduling_output_schema(tool: &mut Tool) {
    let Some(definition) = pg_scheduling_success_definition(tool.name.as_ref()) else {
        return;
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
    assert!(
        earlier.is_none(),
        "duplicate PG scheduling schema definition"
    );

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
                json!({"oneOf": [
                    {"$ref": "#/$defs/PgJobSchedulingReadback"},
                    {"type": "null"}
                ]}),
            )
            .is_none(),
        "scheduler annotation must not shadow a Core field"
    );
    // Only PG job.list can project a previously accepted corrupt Plan as a
    // partial JSON readback. Qualified Job identities remain mandatory.
    // If the frozen Workspace snapshot also cannot be authenticated, its
    // sourceRevision is UNKNOWN too; never use an unrelated Plan revision.
    // This is deliberately NOT a Core RuntimeJobSummary or Legacy ABI change.
    if tool.name.as_ref() == "job.list" {
        for field in ["sourceRevision", "executableName", "cwdRelative"] {
            let value = properties
                .get_mut(field)
                .expect("Core JobList must declare the expected plan-derived field");
            assert_eq!(
                *value,
                json!({"type": "string"}),
                "unexpected Core JobList field {field}; review the PG override"
            );
            *value = json!({"type": ["string", "null"]});
        }
    }

    target
        .get_mut("required")
        .and_then(serde_json::Value::as_array_mut)
        .expect("Core success schema must have required fields")
        .push(json!("scheduling"));

    tool.output_schema = Some(Arc::new(schema));
}
