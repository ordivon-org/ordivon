//! Opt-in disposable PG18 test of A validated RunContract → B Tool Grant.
//! No Tool execution and no production PG credentials are used.
use ordivon_harness_core::{canonical_bytes, loads_strict, CanonicalDocument, CanonicalRef};
use ordivon_harness_loop_b_probe::pg_domain_read::{
    inspect_pg_domain_run, ExpectedModel, PgDomainInspectionError,
};
use ordivon_harness_loop_b_probe::tool_call::{inspect_model_tool_call, ModelToolCallStanding};
use ordivon_harness_loop_b_probe::tool_surface::ToolSurfaceError;
use ordivon_harness_pg::ReadError;
use postgres::{Client, NoTls};
use std::{collections::HashSet, fs};

fn text<'a>(doc: &'a CanonicalDocument, key: &str) -> &'a str {
    doc.field(key).and_then(CanonicalRef::as_str).unwrap()
}

#[test]
#[ignore = "requires A-owned disposable PostgreSQL18 fixture; no production connection"]
fn python_pg_run_v2_contract_binds_exact_custom_tool_surface_without_dispatch() {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").expect("PG DSN");
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").expect("scratch schema");
    let fixture = std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").expect("fixture path");
    let raw = fs::read_to_string(fixture).unwrap();
    let all = loads_strict(&raw).unwrap();
    let binding = all.get("domain_bridge").unwrap();
    let catalog = binding.get("catalog").unwrap();
    let run_id = text(&binding, "runId");
    let allowed_values = binding.field("allowedTools").unwrap();
    let allowed: Vec<&str> = (0..allowed_values.array_len().unwrap())
        .map(|i| allowed_values.index(i).unwrap().as_str().unwrap())
        .collect();
    let identity = ExpectedModel {
        provider_id: text(&binding, "providerId"),
        adapter_id: text(&binding, "adapterId"),
        requested_model_id: text(&binding, "requestedModelId"),
    };
    let mut client = Client::connect(&dsn, NoTls).unwrap();
    let qualified =
        inspect_pg_domain_run(&mut client, &schema, run_id, &catalog, &allowed, identity)
            .expect("A PG read-only + Contract + B Catalog/Grant must bind");
    assert_eq!(qualified.run_id(), run_id);
    assert_eq!(
        qualified.contract_digest(),
        text(&binding, "contractDigest")
    );
    assert_eq!(qualified.revision(), 1);
    assert_eq!(qualified.status(), "created");
    assert_eq!(qualified.provider_id(), identity.provider_id);
    assert_eq!(qualified.adapter_id(), identity.adapter_id);
    assert_eq!(qualified.model_id(), identity.requested_model_id);
    assert_eq!(qualified.ordered_tool_names(), &["read", "edit"]);

    let call = inspect_model_tool_call(
        &loads_strict(r#"{"toolCallId":"call:pg1","name":"read","arguments":{"text":"hello"}}"#)
            .unwrap(),
    )
    .unwrap();
    assert_eq!(
        qualified
            .preflight(&catalog, &call, &HashSet::new())
            .unwrap(),
        ModelToolCallStanding::NeedsAuthenticatedContractAndDurableAdmission
    );
    let seen = HashSet::from([call.tool_call_id().to_owned()]);
    assert_eq!(
        qualified.preflight(&catalog, &call, &seen).unwrap(),
        ModelToolCallStanding::DuplicateCallIdentity
    );

    let denied = inspect_model_tool_call(
        &loads_strict(r#"{"toolCallId":"call:pg2","name":"delete","arguments":{}}"#).unwrap(),
    )
    .unwrap();
    assert_eq!(
        qualified
            .preflight(&catalog, &denied, &HashSet::new())
            .unwrap(),
        ModelToolCallStanding::NotOnVisibleGrantedToolSurface
    );

    let malformed = inspect_model_tool_call(
        &loads_strict(r#"{"toolCallId":"call:pg3","name":"read","arguments":{},"providerArguments":{"error":"invalid_json","rawDigest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","preview":"{"}}"#).unwrap()
    ).unwrap();
    assert_eq!(
        qualified
            .preflight(&catalog, &malformed, &HashSet::new())
            .unwrap(),
        ModelToolCallStanding::LocallyRejectedProviderArguments
    );

    for (field, bad_model) in [
        (
            "providerId",
            ExpectedModel {
                provider_id: "provider:wrong",
                ..identity
            },
        ),
        (
            "adapterId",
            ExpectedModel {
                adapter_id: "adapter:wrong",
                ..identity
            },
        ),
        (
            "requestedModelId",
            ExpectedModel {
                requested_model_id: "model:wrong",
                ..identity
            },
        ),
    ] {
        assert!(matches!(
            inspect_pg_domain_run(&mut client, &schema, run_id, &catalog, &allowed, bad_model),
            Err(PgDomainInspectionError::ProviderSelectionMismatch(found)) if found == field
        ));
    }
    assert!(matches!(
        inspect_pg_domain_run(&mut client, &schema, run_id, &catalog, &["read"], identity),
        Err(PgDomainInspectionError::DomainToolBinding(
            ToolSurfaceError::BindingMismatch
        ))
    ));
    let wrong_catalog = String::from_utf8(canonical_bytes(&catalog))
        .unwrap()
        .replace("Source-verified read", "Changed read");
    let wrong_catalog = loads_strict(&wrong_catalog).unwrap();
    assert!(matches!(
        inspect_pg_domain_run(
            &mut client,
            &schema,
            run_id,
            &wrong_catalog,
            &allowed,
            identity
        ),
        Err(PgDomainInspectionError::DomainToolBinding(
            ToolSurfaceError::BindingMismatch
        ))
    ));
    assert!(matches!(
        qualified.preflight(&wrong_catalog, &call, &HashSet::new()),
        Err(ToolSurfaceError::BindingMismatch)
    ));
    assert!(matches!(
        inspect_pg_domain_run(
            &mut client,
            &schema,
            "harness-run:missing",
            &catalog,
            &allowed,
            identity
        ),
        Err(PgDomainInspectionError::Store(ReadError::MissingRun(_)))
    ));
    let unrelated_run = text(&all, "valid");
    assert!(matches!(
        inspect_pg_domain_run(
            &mut client,
            &schema,
            unrelated_run,
            &catalog,
            &allowed,
            identity
        ),
        Err(PgDomainInspectionError::ProviderSelectionMismatch(_))
    ));
    // Independent C-style full Contract falsifier is populated by A's
    // existing optional scratch-PG runner. Prove the *B consumer* itself
    // cannot bypass A's semantic Contract gate on any of the 24 bad Runs.
    if let Ok(bad_cases) = std::env::var("HARNESS_RUST_TEST_INVALID_CONTRACT_CASES") {
        let mut count = 0;
        for line in bad_cases.lines() {
            let (label, bad_run_id) = line.split_once('|').expect("case|run id");
            let decision = inspect_pg_domain_run(
                &mut client,
                &schema,
                bad_run_id,
                &catalog,
                &allowed,
                identity,
            );
            assert!(
                matches!(decision, Err(PgDomainInspectionError::Store(ReadError::Corruption(_)))),
                "B read-only consumer accepted or misclassified Python-invalid Run {label}: {decision:?}"
            );
            count += 1;
        }
        assert!(
            count >= 24,
            "missing external invalid Contract corpus: {count}"
        );
        println!("PG18_B_CONSUMER_CONTRACT_REJECTED={count}");
    }
    println!("PG18_PYTHON_CONTRACT_DOMAIN_GRANT_AND_MODEL_BOUND_READONLY_PASS");
}
