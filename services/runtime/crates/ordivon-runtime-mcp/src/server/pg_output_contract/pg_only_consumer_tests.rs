//! Original PG-only JobList identity and nullable corrupt Plan readback behavior.
    use super::*;

    #[test]
    fn pg_only_job_list_preserves_qualified_identity_and_explicit_unknown_plan_fields() {
        let tool = PgRuntimeServer::catalog()
            .into_iter()
            .find(|item| item.name.as_ref() == "job.list")
            .expect("original PG-only MCP must publish job.list");
        let schema = serde_json::Value::Object(
            tool.output_schema
                .expect("PG-only job.list must have output schema")
                .as_ref()
                .clone(),
        );
        assert_eq!(schema["oneOf"].as_array().unwrap().len(), 2);
        assert!(schema["$defs"]["ToolErrorEnvelope"].is_object());
        let job = &schema["$defs"]["RuntimeJobSummary"];
        assert_eq!(job["additionalProperties"], false);
        let required = job["required"].as_array().unwrap();

        // A corrupt committed Plan must not invent its source/executable/CWD.
        // Explicit null is accepted, while omitting the field is not.
        for name in ["sourceRevision", "executableName", "cwdRelative"] {
            assert_eq!(
                job["properties"][name],
                json!({"type":["string","null"]}),
                "{name}: PG-only source qualification requires explicit UNKNOWN"
            );
            assert!(required.contains(&json!(name)), "{name}: required");
        }
        // A row that cannot prove its Plan must still preserve exact PG identity.
        for name in ["jobId", "operationDigest", "clientRequestId", "workspaceId"] {
            assert_eq!(job["properties"][name]["type"], "string", "{name}");
            assert!(required.contains(&json!(name)), "{name}: required");
        }
        for name in ["recoveryRequired", "executionTerminal"] {
            assert_eq!(job["properties"][name]["type"], "boolean", "{name}");
            assert!(required.contains(&json!(name)), "{name}: required");
        }
        assert!(required.contains(&json!("deliveryDisposition")));
        assert_eq!(
            job["properties"]["scheduling"]["oneOf"],
            json!([
                {"$ref":"#/$defs/PgJobSchedulingReadback"},
                {"type":"null"}
            ])
        );
        assert!(required.contains(&json!("scheduling")));
    }
