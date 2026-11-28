//! Real consumer tests: ingress, contained Jobs, protected Claims and catalog behavior.
use super::*;

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


#[cfg(test)]
mod claim_release_route_authority_tests {
    use super::*;

    #[test]
    fn standalone_claim_finalizer_cannot_admit_jobs_or_close_workspaces() {
        assert!(!ClaimReleaseIngress::DedicatedClaimOnly.may_release());
        assert!(!ClaimReleaseIngress::Ordinary.may_release());
        for name in CLAIM_ONLY_TOOL_NAMES {
            assert!(claim_only_route_guard(ClaimReleaseIngress::DedicatedClaimOnly, name).is_ok());
        }
        for forbidden in [
            "workspace.exec", "workspace.execPlan", "workspace.open",
            "workspace.close", "workspace.mutate", "job.cancel", "job.observe",
            "release.apply", "release.get", "artifact.content",
        ] {
            assert!(claim_only_route_guard(
                ClaimReleaseIngress::DedicatedClaimOnly, forbidden
            ).is_err(), "{forbidden}");
            assert!(claim_only_route_guard(
                ClaimReleaseIngress::DedicatedFinalizer, forbidden
            ).is_ok(), "existing same-PG Harness issuer mode must retain {forbidden}");
        }
        assert!(claim_release_route_guard(
            ClaimReleaseIngress::Ordinary.may_release(), "workspace.claim.release"
        ).is_err());
    }

    #[test]
    fn ordinary_ingress_must_never_inherit_finalizer_release_capability() {
        // Production may boot with no dedicated Harness profile at all. The
        // ordinary /mcp constructor must not silently permit raw Claim release.
        assert!(!ClaimReleaseIngress::Ordinary.may_release());
        assert!(!ClaimReleaseIngress::DedicatedFinalizer.may_release());
        assert!(claim_release_route_guard(
            ClaimReleaseIngress::Ordinary.may_release(),
            "workspace.claim.release"
        ).is_err());
        for (route, expected) in [
            (ClaimReleaseIngress::Ordinary, false),
            (ClaimReleaseIngress::DedicatedFinalizer, false),
            (ClaimReleaseIngress::DedicatedClaimOnly, false),
        ] {
            let catalog = PgRuntimeServer::catalog_for_route(false, route.may_release());
            assert_eq!(
                catalog.iter().any(|tool| tool.name.as_ref() == "workspace.claim.release"),
                expected,
            );
            assert_eq!(
                claim_release_route_guard(route.may_release(), "workspace.claim.release").is_ok(),
                expected,
            );
        }
    }

    #[test]
    fn raw_tool_dispatch_blocks_normal_known_key_but_not_claim_readback() {
        assert!(claim_release_route_guard(false, "workspace.claim.release").is_err());
        assert!(claim_release_route_guard(true, "workspace.claim.release").is_err());
        assert!(claim_release_route_guard(false, "workspace.claim.get").is_ok());
        assert!(claim_release_route_guard(false, "workspace.claim.reserve").is_ok());
        // Tool-name obfuscation cannot become an alternate release API.
        assert!(!PgRuntimeServer::catalog().iter().any(|t|
            t.name.as_ref() == "workspace.claim.release"));
        assert!(!PgRuntimeServer::catalog().iter().any(|t|
            t.name.as_ref() == "workspace.claim.release.legacy"));
        let isolated = PgRuntimeServer::catalog_for_route(false, false);
        let dedicated = PgRuntimeServer::catalog_for_route(false, true);
        assert!(!dedicated.iter().any(|t| t.name.as_ref() == "workspace.claim.release"));
        assert!(!isolated.iter().any(|t| t.name.as_ref() == "workspace.claim.release"));
        assert_eq!(dedicated.len(), isolated.len());
        assert!(isolated.iter().any(|t| t.name.as_ref() == "workspace.claim.reserve"));
        assert!(isolated.iter().any(|t| t.name.as_ref() == "workspace.claim.get"));
    }

    #[test]
    fn privileged_route_without_independent_domain_and_all_issued_os_receipt_cannot_release() {
        // This is the original real two-PG negative: a bearer/key/RunRef is
        // NOT an independently delivered complete original output set, nor
        // the OS manager's proof of no future spawn. Do not invent a false
        // authorization bit until an actual original finalizer exists.
        for ingress in [
            ClaimReleaseIngress::Ordinary,
            ClaimReleaseIngress::DedicatedFinalizer,
            ClaimReleaseIngress::DedicatedClaimOnly,
        ] {
            assert!(!ingress.may_release(), "{ingress:?}");
            assert!(claim_release_route_guard(
                ingress.may_release(), "workspace.claim.release"
            ).is_err(), "raw route {ingress:?} must hold original Claim");
            let catalog = PgRuntimeServer::catalog_for_route(false, ingress.may_release());
            assert!(!catalog.iter().any(|tool| tool.name.as_ref() == "workspace.claim.release"));
            for name in ["workspace.claim.reserve", "workspace.claim.get"] {
                assert!(catalog.iter().any(|tool| tool.name.as_ref() == name));
                assert!(claim_release_route_guard(ingress.may_release(), name).is_ok());
            }
        }
    }
}

#[cfg(test)]
mod authenticated_execution_profile_projection_tests {
    use super::*;

    #[test]
    fn only_bound_contained_profile_is_advertised_to_normal_agents() {
        let mut description=json!({
            "targets":[
                {"target":"local_linux","executionProfiles":["trusted_local","contained_local"]},
                {"target":"windows_native","executionProfiles":["trusted_local"]}
            ]
        });
        project_ingress_execution_profiles(&mut description,Some(ExecutionProfile::ContainedLocal));
        assert_eq!(description["targets"][0]["executionProfiles"],json!(["contained_local"]));
        assert_eq!(description["targets"][1]["executionProfiles"],json!(["trusted_local"]));
        let unchanged=description.clone();
        project_ingress_execution_profiles(&mut description,None);
        assert_eq!(description,unchanged);
    }

    #[test]
    fn root_release_qualified_catalog_count_differs_from_no_root_fixture() {
        // R62 real production release rolled back before acceptance because
        // the disposable/no-Root integration profile advertised 22 tools but
        // Root-qualified ordinary /mcp advertised 23 (release.apply added).
        // Keep these exact *route/identity/config* contracts distinct.
        let ordinary_without_release = PgRuntimeServer::catalog_for_route(false, false);
        let ordinary_with_release = PgRuntimeServer::catalog_for_route(true, false);
        assert_eq!(ordinary_without_release.len(), 22);
        assert_eq!(ordinary_with_release.len(), 23);
        assert!(!ordinary_without_release.iter().any(|t| t.name.as_ref() == "release.apply"));
        assert!(ordinary_with_release.iter().any(|t| t.name.as_ref() == "release.apply"));
        assert!(!ordinary_with_release
            .iter()
            .any(|t| t.name.as_ref() == "workspace.claim.release"));
        assert!(ordinary_with_release
            .iter()
            .any(|t| t.name.as_ref() == "release.get"));

        let dedicated_finalizer = PgRuntimeServer::catalog_for_route(true, true);
        assert_eq!(dedicated_finalizer.len(), 23);
        assert!(!dedicated_finalizer
            .iter()
            .any(|t| t.name.as_ref() == "workspace.claim.release"));

        // An authenticated ordinary contained-only profile cannot admit a
        // new Root release even when the operator's timer is configured.
        let mut ordinary_contained = ordinary_with_release;
        restrict_new_effect_catalog(
            &mut ordinary_contained,
            Some(ExecutionProfile::ContainedLocal),
        );
        assert_eq!(ordinary_contained.len(), 22);
        assert!(!ordinary_contained
            .iter()
            .any(|t| t.name.as_ref() == "release.apply"));

        // Claim-only is a third identity, NOT a finalization proof; only the
        // original pin reserve/get remain callable before independent Domain/OS.
        let mut claim_only = dedicated_finalizer;
        claim_only.retain(|t| CLAIM_ONLY_TOOL_NAMES.contains(&t.name.as_ref()));
        // workspace.get + Claim reserve/get remain available read-only;
        // the former raw release slot has been retired for every route.
        assert_eq!(claim_only.len(), 3);
        assert!(!claim_only.iter().any(|t| t.name.as_ref() == "release.apply"));
    }

    #[test]
    fn contained_ordinary_catalog_hides_new_operator_release_but_keeps_readback() {
        let mut catalog=PgRuntimeServer::catalog_for_route(true,false);
        assert!(catalog.iter().any(|tool|tool.name.as_ref()=="release.apply"));
        restrict_new_effect_catalog(&mut catalog,Some(ExecutionProfile::ContainedLocal));
        assert!(!catalog.iter().any(|tool|tool.name.as_ref()=="release.apply"));
        assert!(catalog.iter().any(|tool|tool.name.as_ref()=="release.get"));
        let exec=catalog.iter().find(|tool|tool.name.as_ref()=="workspace.exec").unwrap();
        assert!(exec.description.as_ref().unwrap().contains("contained_local-only"));
    }
}

#[cfg(test)]
mod direct_implicit_execution_profile_tests {
    use super::*;

    #[test]
    fn explicit_trusted_or_present_null_can_never_be_auto_reinterpreted() {
        assert!(profile_omitted_from_raw_tool_arguments(&json!({
            "execution":{"workspaceId":"ws-direct","executable":"/usr/bin/true"}
        })));
        for explicit in [
            json!({"execution":{"executionProfile":"trusted_local"}}),
            json!({"execution":{"executionProfile":"contained_local"}}),
            json!({"execution":{"executionProfile":null}}),
            json!({"notExecution":{}}),
        ] {
            assert!(!profile_omitted_from_raw_tool_arguments(&explicit));
        }
    }
}
