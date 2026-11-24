//! Original portable-vs-PG contract and actual UNKNOWN/null corruption behavior.
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
                schema["$defs"][definition]["properties"]["scheduling"]["oneOf"],
                json!([
                    {"$ref": "#/$defs/PgJobSchedulingReadback"},
                    {"type": "null"}
                ]),
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
                portable
                    .output_schema
                    .expect("original output")
                    .as_ref()
                    .clone(),
            );
            assert_eq!(
                schema["$defs"][definition]["additionalProperties"],
                original["$defs"][definition]["additionalProperties"],
                "{tool_name}: never weaken original object closure"
            );
            assert!(
                schema["$defs"]["ToolErrorEnvelope"].is_object(),
                "{tool_name}"
            );
            assert_eq!(
                schema["$defs"]["PgJobSchedulingReadback"]["additionalProperties"], false,
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
    fn invalid_plan_projection_can_be_null_without_fabricating_resource_request() {
        // When an accepted execution plan is corrupt, the Job and its durable
        // events remain observable, but no ResourceScheduling can be decoded.
        // Preserve the closed PG wire contract and require an explicit null.
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
                .expect("PG Tool must exist");
            let schema =
                serde_json::Value::Object(tool.output_schema.expect("schema").as_ref().clone());
            assert_eq!(
                schema["$defs"][definition]["properties"]["scheduling"],
                json!({"oneOf": [
                    {"$ref": "#/$defs/PgJobSchedulingReadback"},
                    {"type": "null"}
                ]}),
                "{tool_name}: known scheduling or explicitly unknown, never a fake default"
            );
            assert!(
                schema["$defs"][definition]["required"]
                    .as_array()
                    .unwrap()
                    .contains(&json!("scheduling")),
                "{tool_name}: missing scheduling must not become silent success"
            );
        }
    }

    #[test]
    fn pg_list_corrupt_plan_retains_identity_and_explicit_unknown_plan_details() {
        // PG JobList is JSON-projected from independently committed Job/Attempt
        // and Workspace snapshot facts. A corrupt accepted execution plan must
        // not force false executable/cwd claims or destroy a healthy entire page.
        let pg = PgRuntimeServer::catalog()
            .into_iter()
            .find(|tool| tool.name.as_ref() == "job.list")
            .expect("PG job.list must exist");
        let schema =
            serde_json::Value::Object(pg.output_schema.expect("PG output schema").as_ref().clone());
        let job = &schema["$defs"]["RuntimeJobSummary"];
        // A bad frozen Plan AND a damaged immutable Workspace snapshot leave
        // sourceRevision unverified; never trust an unrelated Plan revision.
        for field in ["sourceRevision", "executableName", "cwdRelative"] {
            assert_eq!(
                job["properties"][field],
                json!({"type": ["string", "null"]}),
                "{field}: unverified frozen source/Plan detail must be explicit null"
            );
            assert!(
                job["required"].as_array().unwrap().contains(&json!(field)),
                "{field}: missing information must not be silently omitted"
            );
        }
        // The verified PostgreSQL Job identity survives both corrupt blobs.
        for field in ["jobId", "operationDigest", "clientRequestId", "workspaceId"] {
            assert_eq!(
                job["properties"][field]["type"],
                json!("string"),
                "{field}: qualified PG Job identity must remain a string"
            );
            assert!(job["required"].as_array().unwrap().contains(&json!(field)));
        }
        assert_eq!(job["additionalProperties"], false);

        // The original portable/Legacy contract still requires real strings.
        let portable = RuntimeServer::tool_router()
            .list_all()
            .into_iter()
            .find(|tool| tool.name.as_ref() == "job.list")
            .expect("portable job.list");
        let old = serde_json::Value::Object(
            portable
                .output_schema
                .expect("portable schema")
                .as_ref()
                .clone(),
        );
        for field in ["sourceRevision", "executableName", "cwdRelative"] {
            assert_eq!(
                old["$defs"]["RuntimeJobSummary"]["properties"][field]["type"],
                json!("string"),
                "PG partial truth must not break legacy JobList"
            );
        }
    }

    #[test]
    fn typed_pg_scheduling_readback_rejects_malformed_provider_data() {
        let request = serde_json::to_value(ResourceScheduling::default()).unwrap();
        for (state, reason) in [
            ("pending", Some("cause_unobserved")),
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
        let stale_invented_reason = json!({
            "state": "pending", "request": request,
            "pendingReason": "waiting_for_resources_pressure_or_workspace_lease"
        });
        assert!(serde_json::from_value::<PgJobSchedulingReadback>(stale_invented_reason).is_err());
        let bad_state = json!({"state":"SUCCESS","request":request});
        assert!(serde_json::from_value::<PgJobSchedulingReadback>(bad_state).is_err());
        let unknown_field = json!({"state":"released","request":request,"proof":true});
        assert!(serde_json::from_value::<PgJobSchedulingReadback>(unknown_field).is_err());
    }

    #[test]
    fn scheduling_output_gate_rejects_unrelated_job_identity_and_artifact_response() {
        for tool in [
            "artifact.read",
            "artifact.content",
            "workspace.get",
            "workspace.close",
            "release.get",
            "runtime.describe",
        ] {
            assert_eq!(pg_scheduling_success_definition(tool), None, "{tool}");
        }
        for tool in [
            "workspace.exec",
            "workspace.execPlan",
            "job.observe",
            "job.cancel",
            "job.list",
            "job.get",
        ] {
            assert!(pg_scheduling_success_definition(tool).is_some(), "{tool}");
        }
        // An artifact contains the real Job ID, but it is not a Job
        // scheduling readback. Do not widen its official SDK output schema.
        let ordinary = RuntimeServer::tool_router()
            .list_all()
            .into_iter()
            .find(|tool| tool.name.as_ref() == "artifact.read")
            .unwrap();
        let pg = PgRuntimeServer::catalog()
            .into_iter()
            .find(|tool| tool.name.as_ref() == "artifact.read")
            .unwrap();
        assert_eq!(ordinary.output_schema, pg.output_schema);
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
