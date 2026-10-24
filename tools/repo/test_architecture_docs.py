from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "repo" / "check_architecture_docs.py"
GRAPH = ROOT / "docs" / "architecture" / "deployed-architecture-r1.json"
GATEWAY_SURFACE = ROOT / "services" / "gateway" / "mcp-surface.json"

spec = importlib.util.spec_from_file_location("check_architecture_docs", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def graph():
    return json.loads(GRAPH.read_text(encoding="utf-8"))


def test_current_repository_architecture_docs_are_converged() -> None:
    module.validate_repository(ROOT)


def test_gateway_source_surface_is_owned_by_source_manifest() -> None:
    manifest = json.loads(GATEWAY_SURFACE.read_text(encoding="utf-8"))
    observed = set(manifest["tools"])
    module.validate_source_tool_surface(observed, manifest, service="ordivon-gateway")
    mutated = copy.deepcopy(manifest)
    mutated["tools"] = mutated["tools"][:-1]
    with pytest.raises(module.ArchitectureDocsError, match="differs from source manifest"):
        module.validate_source_tool_surface(observed, mutated, service="ordivon-gateway")


def test_gateway_cannot_become_authoritative() -> None:
    value = graph()
    value["defaultNorthbound"]["authoritative"] = True
    with pytest.raises(module.ArchitectureDocsError, match="non-authoritative"):
        module.validate_deployed_graph(value)


def test_method_router_cannot_become_gateway_router() -> None:
    value = graph()
    value["routers"]["methodRouter"]["kind"] = "gateway-static-owner-projection"
    with pytest.raises(module.ArchitectureDocsError, match="Method Router"):
        module.validate_deployed_graph(value)


def test_deployed_capability_set_is_exact() -> None:
    value = graph()
    value["routers"]["capabilityRouter"]["capabilities"].append("harness.run")
    with pytest.raises(module.ArchitectureDocsError, match="capability set"):
        module.validate_deployed_graph(value)


def test_default_plugin_rejects_direct_owner_servers() -> None:
    value = {
        "mcpServers": {
            "ordivon-gateway": {
                "url": "https://gateway-mcp.ordivon.com/mcp"
            },
            "ordivonRuntime": {
                "url": "https://mcp.ordivon.com/mcp"
            },
        }
    }
    with pytest.raises(module.ArchitectureDocsError, match="exactly one Gateway"):
        module.validate_plugin(value)


def test_persistent_trace_backend_cannot_regress_to_not_admitted() -> None:
    value = graph()
    value["notAdmitted"].append("persistent-queryable-trace-backend")
    with pytest.raises(module.ArchitectureDocsError, match="cannot remain not-admitted"):
        module.validate_deployed_graph(value)


def test_vector_trace_preservation_is_architecture_contract() -> None:
    value = graph()
    value["observability"]["ingress"]["preserveOtlpTraces"] = False
    with pytest.raises(module.ArchitectureDocsError, match="preserve OTLP trace"):
        module.validate_deployed_graph(value)


def test_tempo_remains_on_demand_non_semantic_backend() -> None:
    value = graph()
    value["observability"]["status"] = "semantic-authority"
    with pytest.raises(module.ArchitectureDocsError, match="deployed-on-demand"):
        module.validate_deployed_graph(value)


def test_gateway_trace_export_remains_opt_in_by_default() -> None:
    value = graph()
    value["observability"]["gatewayExport"]["base"] = "OTEL_TRACES_EXPORTER=otlp_proto_http"
    with pytest.raises(module.ArchitectureDocsError, match="base trace exporter"):
        module.validate_deployed_graph(value)


def test_trace_storage_never_becomes_product_correctness_authority() -> None:
    value = graph()
    value["observability"]["gatewayExport"]["requiredForProductCorrectness"] = True
    with pytest.raises(module.ArchitectureDocsError, match="product correctness"):
        module.validate_deployed_graph(value)


def test_heavy_observability_default_posture_stays_cold() -> None:
    value = graph()
    value["observability"]["defaultPosture"] = "always-on"
    with pytest.raises(module.ArchitectureDocsError, match="cold by default"):
        module.validate_deployed_graph(value)


def test_gateway_normal_host_surface_cannot_drop_actions() -> None:
    value = graph()
    value["hostNorthbound"]["normalTools"].remove("work.snapshot.commit")
    with pytest.raises(module.ArchitectureDocsError, match="normal Host northbound Tool set"):
        module.validate_deployed_graph(value)


def test_gateway_cannot_absorb_host_admin_surface() -> None:
    value = graph()
    value["hostNorthbound"]["adminOnlyDirect"] = []
    with pytest.raises(module.ArchitectureDocsError, match="status/Doctor"):
        module.validate_deployed_graph(value)


def test_connector_catalog_owner_stays_external() -> None:
    value = graph()
    value["hostNorthbound"]["connectorCatalogOwner"] = "gateway"
    with pytest.raises(module.ArchitectureDocsError, match="catalog freshness owner"):
        module.validate_deployed_graph(value)


QUEUE_TELEMETRY_PATH = ROOT / "tools" / "repo" / "queue_telemetry.py"
queue_spec = importlib.util.spec_from_file_location("queue_telemetry", QUEUE_TELEMETRY_PATH)
assert queue_spec is not None and queue_spec.loader is not None
queue_module = importlib.util.module_from_spec(queue_spec)
sys.modules[queue_spec.name] = queue_module
queue_spec.loader.exec_module(queue_module)


def test_queue_telemetry_provider_projection_is_deterministic() -> None:
    snapshot = queue_module.ProviderSnapshot(
        repository="o/r",
        pulls=[
            {"number": 7, "merged_at": "2026-09-22T12:00:40Z"},
            {"number": 8, "merged_at": "2026-09-22T12:01:00Z"},
        ],
        timelines={
            "7": [
                {"event": "added_to_merge_queue", "created_at": "2026-09-22T12:00:00Z"},
                {"event": "removed_from_merge_queue", "created_at": "2026-09-22T12:00:40Z"},
            ],
            "8": [
                {"event": "added_to_merge_queue", "created_at": "2026-09-22T12:00:10Z"},
                {"event": "removed_from_merge_queue", "created_at": "2026-09-22T12:01:00Z"},
            ],
        },
        merge_group_runs=[
            {"id": 70, "head_branch": "gh-readonly-queue/main/pr-7-base",
             "head_sha": "a", "created_at": "2026-09-22T12:00:05Z", "conclusion": "success"},
            {"id": 80, "head_branch": "gh-readonly-queue/main/pr-8-base",
             "head_sha": "b", "created_at": "2026-09-22T12:00:20Z", "conclusion": "failure"},
            {"id": 81, "head_branch": "gh-readonly-queue/main/pr-8-base2",
             "head_sha": "c", "created_at": "2026-09-22T12:00:30Z", "conclusion": "success"},
        ],
        jobs={
            "70": [{"name": "root-verification", "created_at": "2026-09-22T12:00:06Z",
                    "started_at": "2026-09-22T12:00:08Z", "completed_at": "2026-09-22T12:00:30Z"}],
            "80": [{"name": "root-verification", "created_at": "2026-09-22T12:00:21Z",
                    "started_at": "2026-09-22T12:00:22Z", "completed_at": "2026-09-22T12:00:27Z"}],
            "81": [{"name": "root-verification", "created_at": "2026-09-22T12:00:31Z",
                    "started_at": "2026-09-22T12:00:32Z", "completed_at": "2026-09-22T12:00:50Z"}],
        },
    )
    result = queue_module.analyze(snapshot)
    assert result["authority"]["durableLocalQueueState"] is False
    assert result["coverage"]["queueAttributedPullRequests"] == 2
    assert result["metrics"]["observedPeakQueueDepthLowerBound"] == 2
    assert result["metrics"]["unsuccessfulMergeGroupRuns"] == 1
    assert result["metrics"]["unsuccessfulMergeGroupExecutionSeconds"] == 5
    assert result["metrics"]["queueDispatchSeconds"]["median"] == 12.5
    assert "pressureGate" not in result
    assert result == queue_module.project(queue_module.normalize(snapshot))
    by_pr = {row["pr"]: row for row in result["episodeMetrics"]}
    assert by_pr[7]["verificationSeconds"] == 22
    assert by_pr[8]["mergeGroupRuns"] == 2


CI_TELEMETRY_PATH = ROOT / "tools" / "repo" / "ci_telemetry.py"
ci_spec = importlib.util.spec_from_file_location("ci_telemetry", CI_TELEMETRY_PATH)
assert ci_spec is not None and ci_spec.loader is not None
ci_module = importlib.util.module_from_spec(ci_spec)
sys.modules[ci_spec.name] = ci_module
ci_spec.loader.exec_module(ci_module)

PRESSURE_PATH = ROOT / "tools" / "repo" / "convergence_pressure.py"
pressure_spec = importlib.util.spec_from_file_location("convergence_pressure", PRESSURE_PATH)
assert pressure_spec is not None and pressure_spec.loader is not None
pressure_module = importlib.util.module_from_spec(pressure_spec)
sys.modules[pressure_spec.name] = pressure_module
pressure_spec.loader.exec_module(pressure_module)


def ci_fixture():
    return ci_module.ProviderSnapshot(
        repository="o/r",
        runs=[
            {
                "id": 101,
                "workflow_id": 1,
                "name": "Monorepo Required",
                "event": "pull_request",
                "head_sha": "pr-a",
                "head_branch": "agent/a",
                "run_attempt": 1,
                "status": "completed",
                "conclusion": "cancelled",
                "created_at": "2026-09-23T00:00:00Z",
                "run_started_at": "2026-09-23T00:00:02Z",
                "updated_at": "2026-09-23T00:00:55Z",
            },
            {
                "id": 102,
                "workflow_id": 1,
                "name": "Monorepo Required",
                "event": "merge_group",
                "head_sha": "mg-a",
                "head_branch": "gh-readonly-queue/main/pr-7-a",
                "run_attempt": 1,
                "status": "completed",
                "conclusion": "success",
                "created_at": "2026-09-23T00:01:00Z",
                "run_started_at": "2026-09-23T00:01:03Z",
                "updated_at": "2026-09-23T00:01:43Z",
            },
        ],
        jobs={
            "101": [
                {
                    "id": 1001,
                    "name": "root-verification",
                    "status": "completed",
                    "conclusion": "cancelled",
                    "created_at": "2026-09-23T00:00:01Z",
                    "started_at": "2026-09-23T00:00:03Z",
                    "completed_at": "2026-09-23T00:00:53Z",
                    "steps": [
                        {
                            "number": 1,
                            "name": "Repository mechanics",
                            "status": "completed",
                            "conclusion": "success",
                            "started_at": "2026-09-23T00:00:03Z",
                            "completed_at": "2026-09-23T00:00:13Z",
                        },
                        {
                            "number": 2,
                            "name": "Verify affected owners",
                            "status": "completed",
                            "conclusion": "success",
                            "started_at": "2026-09-23T00:00:13Z",
                            "completed_at": "2026-09-23T00:00:43Z",
                        },
                    ],
                }
            ],
            "102": [
                {
                    "id": 1002,
                    "name": "root-verification",
                    "status": "completed",
                    "conclusion": "success",
                    "created_at": "2026-09-23T00:01:01Z",
                    "started_at": "2026-09-23T00:01:04Z",
                    "completed_at": "2026-09-23T00:01:40Z",
                    "steps": [
                        {
                            "number": 1,
                            "name": "Verify affected owners",
                            "status": "completed",
                            "conclusion": "success",
                            "started_at": "2026-09-23T00:01:05Z",
                            "completed_at": "2026-09-23T00:01:35Z",
                        }
                    ],
                }
            ],
        },
    )


def test_ci_telemetry_keeps_termination_separate_from_economic_judgment() -> None:
    normalized = ci_module.normalize(ci_fixture())
    result = ci_module.project(normalized)
    assert result["metrics"]["runs"] == 2
    assert result["metrics"]["terminationReasonCounts"] == {
        "CANCELLED": 1,
        "SUCCESS": 1,
    }
    assert result["metrics"]["economicOutcomeCounts"] == {"UNCLASSIFIED": 2}
    assert result["metrics"]["explicitAvoidableWasteRuns"] == 0
    assert result["metrics"]["stepSecondsByName"]["Verify affected owners"]["max"] == 30
    assert all(run["economicOutcome"] == "UNCLASSIFIED" for run in result["runs"])


def test_ci_telemetry_requires_explicit_evidence_to_call_work_waste() -> None:
    normalized = ci_module.normalize(
        ci_fixture(),
        economic_annotations={
            "101": {
                "economicOutcome": "AVOIDABLE_WASTE",
                "reason": "fixture establishes superseded work",
            }
        },
    )
    result = ci_module.project(normalized)
    assert result["metrics"]["explicitAvoidableWasteRuns"] == 1
    assert result["metrics"]["explicitAvoidableWasteExecutionSeconds"] == 50


def test_pressure_gate_has_no_provider_or_control_side_effects() -> None:
    queue_snapshot = queue_module.ProviderSnapshot(
        repository="o/r",
        pulls=[{"number": 7, "merged_at": "2026-09-23T00:00:40Z"}],
        timelines={
            "7": [
                {"event": "added_to_merge_queue", "created_at": "2026-09-23T00:00:00Z"},
                {"event": "removed_from_merge_queue", "created_at": "2026-09-23T00:00:40Z"},
            ]
        },
        merge_group_runs=[
            {
                "id": 70,
                "head_branch": "gh-readonly-queue/main/pr-7-base",
                "head_sha": "a",
                "created_at": "2026-09-23T00:00:05Z",
                "conclusion": "success",
            }
        ],
        jobs={
            "70": [
                {
                    "name": "root-verification",
                    "created_at": "2026-09-23T00:00:06Z",
                    "started_at": "2026-09-23T00:00:08Z",
                    "completed_at": "2026-09-23T00:00:30Z",
                }
            ]
        },
    )
    queue_projection = queue_module.analyze(queue_snapshot)
    ci_projection = ci_module.project(ci_module.normalize(ci_fixture()))
    assessment = pressure_module.assess(queue_projection, ci_projection)
    gates = {row["gate"]: row for row in assessment["gates"]}
    assert gates["QUEUE_CONTENTION"]["status"] == "NOT_PROVEN"
    assert gates["CI_WASTE"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert assessment["controlsAdmitted"] == []

    annotated_ci = ci_module.project(
        ci_module.normalize(
            ci_fixture(),
            economic_annotations={
                "101": {
                    "economicOutcome": "AVOIDABLE_WASTE",
                    "reason": "fixture establishes superseded work",
                }
            },
        )
    )
    admitted = pressure_module.assess(queue_projection, annotated_ci)
    admitted_gates = {row["gate"]: row for row in admitted["gates"]}
    assert admitted_gates["CI_WASTE"]["status"] == "PROVEN"
    assert admitted["controlsAdmitted"] == [
        "cancellation-optimization",
        "ci-deduplication",
    ]


SCHEMA_DIR = ROOT / "docs" / "architecture" / "schemas"


@pytest.mark.parametrize(
    ("name", "kind", "schema_version"),
    [
        (
            "convergence-queue-observation-v1.schema.json",
            "ordivon.queue-observation-projection",
            2,
        ),
        (
            "convergence-ci-observation-v1.schema.json",
            "ordivon.ci-observation-projection",
            1,
        ),
        (
            "convergence-pressure-assessment-v1.schema.json",
            "ordivon.convergence-pressure-assessment",
            1,
        ),
    ],
)
def test_convergence_observation_schema_contracts(
    name: str, kind: str, schema_version: int
) -> None:
    value = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
    assert value["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert value["$id"].startswith("urn:ordivon:schema:")
    assert value["type"] == "object"
    assert value["properties"]["schemaVersion"]["const"] == schema_version
    assert value["properties"]["kind"]["const"] == kind
    assert {"schemaVersion", "kind"} <= set(value["required"])


def test_convergence_observation_r2_keeps_control_out_of_observation() -> None:
    value = json.loads(
        (ROOT / "docs" / "architecture" / "convergence-queue-lego-r1.json").read_text(
            encoding="utf-8"
        )
    )
    r2 = value["convergenceObservationR2"]
    assert r2["standing"] == "OBSERVATION_IMPLEMENTED_CONTROL_BLOCKED"
    assert r2["authorityBoundary"]["observation"] == "rebuildable non-authoritative projection"
    assert "adaptive speculation" in r2["blockedControls"]
    assert "batching/bisection" in r2["blockedControls"]
    assert "predictive cost scheduling" in r2["blockedControls"]


FORMAL_ISSUE_CENSUS = ROOT / "docs" / "architecture" / "evidence" / "FORMAL_LEGO_ISSUE_CENSUS_20261024_R1.json"


def formal_issue_inputs():
    census = json.loads(FORMAL_ISSUE_CENSUS.read_text(encoding="utf-8"))
    plans = {
        ref["ownerPlan"]: json.loads((ROOT / ref["ownerPlan"]).read_text(encoding="utf-8"))
        for ref in census["registrations"]
    }
    return census, plans


@pytest.mark.parametrize("role", ["protectedGithubMain", "linuxLocalMain", "mergeBase", "researchLocalMain"])
def test_formal_issue_census_rejects_untyped_git_source_cut(role: str) -> None:
    census, plans = formal_issue_inputs()
    census["source"][role] = "not-an-exact-git-oid"
    with pytest.raises(module.ArchitectureDocsError, match=f"invalid Git source revision: {role}"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_rejects_missing_protected_source_cut() -> None:
    census, plans = formal_issue_inputs()
    del census["source"]["protectedGithubMain"]
    with pytest.raises(module.ArchitectureDocsError, match="lacks protected Git source revision"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_incremental_source_cut_is_valid() -> None:
    census, plans = formal_issue_inputs()
    census["source"] = {"protectedGithubMain": census["source"]["protectedGithubMain"]}
    module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_preserves_existing_owner_legos() -> None:
    census, plans = formal_issue_inputs()
    module.validate_formal_issue_census(census, plans)


def test_workspace_lifecycle_issue_binds_existing_runtime_state_lego() -> None:
    census, plans = formal_issue_inputs()
    issue = next(issue for issue in census["issues"] if issue["id"] == "WS-01")
    assert issue["naturalOwner"] == "services/runtime"
    assert issue["registration"] == {
        "state": "LINKED",
        "ownerPlan": "services/runtime/planning/lego-plan-r1.json",
        "slice": "RW1",
    }
    runtime_plan = plans[issue["registration"]["ownerPlan"]]
    runtime_slice = next(
        slice_ for slice_ in runtime_plan["slices"] if slice_["id"] == "RW1"
    )
    assert "R02" in runtime_slice["nodeIds"]
    module.validate_formal_issue_census(census, plans)

def test_runtime_workspace_lego_unknown_slice_state_is_rejected() -> None:
    census, plans = formal_issue_inputs()
    runtime_plan = plans["services/runtime/planning/lego-plan-r1.json"]
    slice_ = next(x for x in runtime_plan["slices"] if x["id"] == "RW1")
    slice_["status"] = "UNKNOWN"
    with pytest.raises(module.ArchitectureDocsError, match="unknown state"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_rejects_unbound_lego_node() -> None:
    census, plans = formal_issue_inputs()
    owner_plan = census["registrations"][0]["ownerPlan"]
    slice_id = census["registrations"][0]["slice"]
    next(item for item in plans[owner_plan]["slices"] if item["id"] == slice_id)["nodeIds"].append("UNKNOWN-NODE")
    with pytest.raises(module.ArchitectureDocsError, match="unknown LEGO node"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_rejects_duplicate_problem_identity() -> None:
    census, plans = formal_issue_inputs()
    census["issues"].append(copy.deepcopy(census["issues"][0]))
    with pytest.raises(module.ArchitectureDocsError, match="duplicate issue"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_cannot_grant_authority() -> None:
    census, plans = formal_issue_inputs()
    census["truthRole"] = "semantic-authority"
    with pytest.raises(module.ArchitectureDocsError, match="non-authoritative"):
        module.validate_formal_issue_census(census, plans)


def test_representation_first_all_issues_have_one_primary_and_witness() -> None:
    census, plans = formal_issue_inputs()
    module.validate_formal_issue_census(census, plans)
    census["issues"][0].pop("representation")
    with pytest.raises(module.ArchitectureDocsError, match="representation"):
        module.validate_formal_issue_census(census, plans)


def test_representation_first_rejects_unknown_or_unbounded_methods() -> None:
    census, plans = formal_issue_inputs()
    for issue in census["issues"]:
        issue["representation"] = {
            "primary": "type",
            "supporting": [],
            "methodSkill": None,
            "requiredWitness": "Native consumer test on an exact source cut.",
            "selectionReason": "Avoid speculative method proliferation.",
        }
    census["issues"][0]["representation"]["primary"] = "made-up-method"
    with pytest.raises(module.ArchitectureDocsError, match="primary representation"):
        module.validate_formal_issue_census(census, plans)
    census["issues"][0]["representation"]["primary"] = "type"
    census["issues"][0]["representation"]["supporting"] = [
        "graph", "constraint", "state-machine",
    ]
    with pytest.raises(module.ArchitectureDocsError, match="supporting representation"):
        module.validate_formal_issue_census(census, plans)


def test_representation_first_rejects_unbound_skill_and_missing_evidence() -> None:
    census, plans = formal_issue_inputs()
    for issue in census["issues"]:
        issue["representation"] = {
            "primary": "type",
            "supporting": [],
            "methodSkill": None,
            "requiredWitness": "Run exact owner test.",
            "selectionReason": "Prefer concrete owner contracts.",
        }
    census["issues"][0]["representation"]["methodSkill"] = ".agents/skills/missing-method/SKILL.md"
    with pytest.raises(module.ArchitectureDocsError, match="method Skill"):
        module.validate_formal_issue_census(census, plans)
    census["issues"][0]["representation"]["methodSkill"] = None
    census["issues"][0]["representation"]["requiredWitness"] = ""
    with pytest.raises(module.ArchitectureDocsError, match="requiredWitness"):
        module.validate_formal_issue_census(census, plans)


def test_representation_first_rejects_non_scalar_values_without_crashing() -> None:
    census, plans = formal_issue_inputs()
    census["issues"][0]["representation"]["primary"] = ["graph"]
    with pytest.raises(module.ArchitectureDocsError, match="primary representation"):
        module.validate_formal_issue_census(census, plans)
    census["issues"][0]["representation"]["primary"] = "graph"
    census["issues"][0]["representation"]["supporting"] = [{"arbitrary": "state-machine"}]
    with pytest.raises(module.ArchitectureDocsError, match="supporting representation"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_rejects_missing_registration_disposition() -> None:
    census, plans = formal_issue_inputs()
    del census["issues"][0]["registration"]
    with pytest.raises(module.ArchitectureDocsError, match="lacks registration disposition"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_rejects_unbound_problem_slice() -> None:
    census, plans = formal_issue_inputs()
    issue = next(issue for issue in census["issues"] if issue["id"] == "NET-01")
    issue["registration"]["slice"] = "NS-NOT-DEFINED"
    with pytest.raises(module.ArchitectureDocsError, match="links unknown owner-local LEGO"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_rejects_cross_owner_problem_link() -> None:
    census, plans = formal_issue_inputs()
    issue = next(issue for issue in census["issues"] if issue["id"] == "NET-01")
    issue["registration"]["ownerPlan"] = "services/harness/planning/lego-plan-r1.json"
    issue["registration"]["slice"] = "HS2"
    with pytest.raises(module.ArchitectureDocsError, match="linked outside natural owner"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_rejects_unexplained_gap() -> None:
    census, plans = formal_issue_inputs()
    issue = next(issue for issue in census["issues"] if issue["id"] == "GIT-02")
    issue["registration"]["reason"] = " "
    with pytest.raises(module.ArchitectureDocsError, match="lacks unregistered reason"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_rejects_unconsumed_lego_registration() -> None:
    census, plans = formal_issue_inputs()
    for issue in census["issues"]:
        if issue["registration"].get("slice") == "NS2":
            issue["registration"] = {"state": "UNREGISTERED", "reason": "no consumer linkage"}
    with pytest.raises(module.ArchitectureDocsError, match="orphan owner-local LEGO registration"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_rejects_malformed_link_shape() -> None:
    census, plans = formal_issue_inputs()
    issue = next(issue for issue in census["issues"] if issue["id"] == "NET-01")
    issue["registration"]["ownerPlan"] = ["platform/network/planning/lego-plan-r1.json"]
    with pytest.raises(module.ArchitectureDocsError, match="invalid owner-local LEGO link"):
        module.validate_formal_issue_census(census, plans)


def test_formal_issue_census_rejects_gap_disguised_as_link() -> None:
    census, plans = formal_issue_inputs()
    issue = next(issue for issue in census["issues"] if issue["id"] == "GIT-02")
    issue["registration"]["ownerPlan"] = "platform/network/planning/lego-plan-r1.json"
    with pytest.raises(module.ArchitectureDocsError, match="mixes gap and linked registration"):
        module.validate_formal_issue_census(census, plans)


@pytest.mark.parametrize("owner", ["services/unknown", "services/runtime-shadow", "tools/unknown"])
def test_formal_issue_census_rejects_undeclared_natural_owner(owner: str) -> None:
    census, plans = formal_issue_inputs()
    census["issues"][0]["naturalOwner"] = owner
    with pytest.raises(module.ArchitectureDocsError, match="undeclared naturalOwner"):
        module.validate_formal_issue_census(census, plans)


def test_issue_owner_source_cut_is_explicit(tmp_path: Path) -> None:
    census, plans = formal_issue_inputs()
    owner_file = tmp_path / "tools" / "repo" / "owners.toml"
    owner_file.parent.mkdir(parents=True)
    owner_file.write_text(
        '[[owners]]\nname = "alternate"\nroot = "services/alternate/"\n'
    )
    with pytest.raises(module.ArchitectureDocsError, match="undeclared naturalOwner"):
        module.validate_formal_issue_census(census, plans, root=tmp_path)


def test_ci_telemetry_reads_all_requested_pages_not_only_first_hundred() -> None:
    calls = []

    def fake_api(endpoint):
        calls.append(endpoint)
        if "/jobs?" in endpoint:
            return {"jobs": []}
        page = 2 if "page=2" in endpoint else 1
        start, end = (101, 102) if page == 2 else (1, 101)
        return {"workflow_runs": [
            {"id": i, "name": "Monorepo Required", "created_at": "2026-10-24T00:00:00Z"}
            for i in range(start, end)
        ]}

    owner = ci_module.Gh("ordivon-org/ordivon")
    owner.api = fake_api
    observed = owner.collect(limit=101, events=("pull_request",), workflow_name=None)
    assert [run["id"] for run in observed.runs] == list(range(1, 102))
    assert any("page=2" in endpoint and "/actions/runs?" in endpoint for endpoint in calls)


def test_ci_telemetry_filter_continues_after_unmatched_first_page() -> None:
    calls = []

    def fake_api(endpoint):
        calls.append(endpoint)
        if "/jobs?" in endpoint:
            return {"jobs": []}
        if "page=2" in endpoint:
            return {"workflow_runs": [
                {"id": 101, "name": "Monorepo Required", "created_at": "2026-10-24T00:00:00Z"}
            ]}
        return {"workflow_runs": [
            {"id": i, "name": "Unrelated Workflow", "created_at": "2026-10-24T00:00:00Z"}
            for i in range(1, 101)
        ]}

    owner = ci_module.Gh("ordivon-org/ordivon")
    owner.api = fake_api
    observed = owner.collect(limit=101, events=("pull_request",), workflow_name="Monorepo Required")
    assert [run["id"] for run in observed.runs] == [101]
    assert any("page=2" in endpoint and "/actions/runs?" in endpoint for endpoint in calls)


def test_ci_telemetry_collects_all_jobs_of_one_run() -> None:
    calls = []

    def fake_api(endpoint):
        calls.append(endpoint)
        if "/jobs?" not in endpoint:
            return {"workflow_runs": [
                {"id": 7, "name": "Monorepo Required", "created_at": "2026-10-24T00:00:00Z"}
            ]}
        page = 2 if "page=2" in endpoint else 1
        return {"jobs": ([{"id": i} for i in range(101, 102)]
                         if page == 2 else [{"id": i} for i in range(1, 101)])}

    owner = ci_module.Gh("ordivon-org/ordivon")
    owner.api = fake_api
    observed = owner.collect(limit=1, events=("pull_request",), workflow_name=None)
    assert [job["id"] for job in observed.jobs["7"]] == list(range(1, 102))
    assert any("page=2" in endpoint and "/jobs?" in endpoint for endpoint in calls)

def test_formal_issue_skill_is_bound_to_candidate_source(tmp_path: Path) -> None:
    """A Skill in the tool's checkout must not validate another source cut."""
    census, plans = formal_issue_inputs()
    owner_manifest = tmp_path / "tools/repo/owners.toml"
    owner_manifest.parent.mkdir(parents=True)
    owner_manifest.write_bytes((ROOT / "tools/repo/owners.toml").read_bytes())
    for ref in census["registrations"]:
        plan = tmp_path / ref["ownerPlan"]
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_bytes((ROOT / ref["ownerPlan"]).read_bytes())
    skills = sorted({
        issue["representation"]["methodSkill"]
        for issue in census["issues"]
        if issue["representation"].get("methodSkill")
    })
    assert skills
    for skill in skills[1:]:
        path = tmp_path / skill
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("candidate-local skill\n", encoding="utf-8")
    # One missing source-cut Skill must fail even though the real checkout has it.
    with pytest.raises(module.ArchitectureDocsError, match="unavailable method Skill"):
        module.validate_formal_issue_census(census, plans, root=tmp_path)
    missing = tmp_path / skills[0]
    missing.parent.mkdir(parents=True, exist_ok=True)
    missing.write_text("candidate-local skill\n", encoding="utf-8")
    module.validate_formal_issue_census(census, plans, root=tmp_path)


def test_formal_issue_skill_symlink_cannot_escape_source_cut(tmp_path: Path) -> None:
    """Existence outside the candidate source tree is not source-bound proof."""
    census, plans = formal_issue_inputs()
    owner_manifest = tmp_path / "tools/repo/owners.toml"
    owner_manifest.parent.mkdir(parents=True)
    owner_manifest.write_bytes((ROOT / "tools/repo/owners.toml").read_bytes())
    for ref in census["registrations"]:
        plan = tmp_path / ref["ownerPlan"]
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_bytes((ROOT / ref["ownerPlan"]).read_bytes())
    skills = sorted({
        issue["representation"]["methodSkill"]
        for issue in census["issues"]
        if issue["representation"].get("methodSkill")
    })
    for skill in skills:
        path = tmp_path / skill
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("candidate-local skill\n", encoding="utf-8")
    (tmp_path / skills[0]).unlink()
    (tmp_path / skills[0]).symlink_to(ROOT / skills[0])
    with pytest.raises(module.ArchitectureDocsError, match="unavailable method Skill"):
        module.validate_formal_issue_census(census, plans, root=tmp_path)


def test_git_source_comparison_consumes_local_commit_as_owner_lego() -> None:
    """A Git-only commit cannot be called unique without a source-bound consumer comparison."""
    census, plans = formal_issue_inputs()
    issue = next(item for item in census["issues"] if item["id"] == "GIT-01")
    source = issue["consumerSourceCut"]
    assert source["localMain"] == "13704d0cac9e113b395f2d5a21b5bf8119aa04a5"
    assert source["remoteMain"] == "4f83f744e424c1c5ed583c3b60fc473d29f1efe9"
    candidates = issue["consumerSelections"]
    # GIT-01 is the canonical selected-commit registry: do not duplicate the
    # evolving roster of Git SHAs in test source. Test invariants instead.
    assert candidates
    sha_values = [item["localCommit"] for item in candidates]
    assert len(sha_values) == len(set(sha_values))
    assert all(
        isinstance(sha, str) and len(sha) == 40
        and all(character in "0123456789abcdef" for character in sha)
        for sha in sha_values
    )
    for item in candidates:
        assert len(item["localCommit"]) == 40
        assert item["owner"]
        assert item["consumer"]
        assert item["remoteWitness"]
        assert item["disposition"] in {
            "SKIP_DUPLICATE_CHERRY_PICK", "SKIP_OLDER_PIN",
            "SKIP_OLDER_SOURCECUT", "SKIP_UNCONSUMED_PERMISSION",
            "NO_WHOLE_COMMIT_REPLAY_WITHOUT_PRODUCER_AUTHORITY",
            "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER",
            "SKIP_CANCELLED_HISTORY_PAIR",
        }
        assert item["evidenceScope"] in {
            "NATIVE_CONSUMER_PASS", "EXACT_GIT_BLOBS",
            "SOURCE_PROVIDER_NEWER_NO_NATIVE_NIX_PROOF",
            "LATEST_STABLE_SOURCE_NO_UPGRADE",
            "CURRENT_CONSUMER_ELSEWHERE_NO_OLD_EFFECT",
            "FROZEN_GATEWAY_CONSUMER_ONLY",
            "IN_TREE_CONSUMER_ABSENCE_EXTERNAL_UNKNOWN",
        }
        if item["evidenceScope"] == "SOURCE_PROVIDER_NEWER_NO_NATIVE_NIX_PROOF":
            assert item["disposition"] == "SKIP_OLDER_PIN"
        if item["localCommit"].startswith(("ecca6ad", "86298d7", "9c8e37d", "fcf5fc6")):
            assert item["evaluatedRemoteMain"] == "a56afcf30aafd8d5bcd0f41adb950504f5724267"
        if item["localCommit"].startswith(("82c8fa2924", "84baec0ea1", "7a96b238fb", "7c2fa8c4d2")):
            assert item["evaluatedRemoteMain"] == "41a1073703343aad61c3ffacac34edfb91019800"
        if item["evidenceScope"] == "CURRENT_CONSUMER_ELSEWHERE_NO_OLD_EFFECT":
            assert item["disposition"] == "SKIP_UNCONSUMED_PERMISSION"
        if item["localCommit"].startswith(("af6f3f48f1", "8ac2e7f814")):
            proof = item["sourceQualification"]
            assert proof["localMain"] == source["localMain"]
            assert proof["protectedMain"] == "6d44eb7860cff086e27bedd1a59e49415a4c87cc"
            assert proof["branchDeletionAllowed"] is False
            if item["evidenceScope"] == "FROZEN_GATEWAY_CONSUMER_ONLY":
                assert item["disposition"] == "NO_WHOLE_COMMIT_REPLAY_WITHOUT_PRODUCER_AUTHORITY"
            else:
                assert item["evidenceScope"] == "IN_TREE_CONSUMER_ABSENCE_EXTERNAL_UNKNOWN"
                assert item["disposition"] == "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER"
    module.validate_formal_issue_census(census, plans)


def test_divergent_history_does_not_weaken_frozen_artifact_receipts() -> None:
    """Semantically identical output does not qualify a different frozen source SHA."""
    census, _ = formal_issue_inputs()
    git_issue = next(item for item in census["issues"] if item["id"] == "GIT-01")
    blockers = git_issue["consumerBlockedSelections"]
    assert len({entry["localCommit"] for entry in blockers}) == len(blockers)
    for entry in blockers:
        assert len(entry["localCommit"]) == len(entry["protectedMain"]) == 40
        assert entry["owner"] == "capabilities/artifact"
        assert entry["disposition"] == "KEEP_FROZEN_SOURCE_PENDING_NEW_CONSUMER_ACCEPTANCE"
        assert entry["branchDeletionAllowed"] is False
        assert entry["frozenReceiptPaths"]
        for receipt in entry["frozenReceiptPaths"]:
            assert (ROOT / "capabilities/artifact/artifact-delivery/consumer-acceptance" / receipt).is_file()
    assert any(entry["localCommit"].startswith("e9547525bae3") for entry in blockers)


def test_formal_issue_owner_plan_cannot_escape_source_cut(tmp_path: Path) -> None:
    """A plausible LEGO plan outside the candidate checkout is not an owner link."""
    census, plans = formal_issue_inputs()
    source = tmp_path / "source"
    owner_manifest = source / "tools/repo/owners.toml"
    owner_manifest.parent.mkdir(parents=True)
    owner_manifest.write_bytes((ROOT / "tools/repo/owners.toml").read_bytes())
    for issue in census["issues"]:
        method = issue["representation"].get("methodSkill")
        if method:
            skill = source / method
            skill.parent.mkdir(parents=True, exist_ok=True)
            skill.write_bytes((ROOT / method).read_bytes())
    for ref in census["registrations"]:
        plan_path = source / ref["ownerPlan"]
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_bytes((ROOT / ref["ownerPlan"]).read_bytes())
    module.validate_formal_issue_census(census, plans, root=source)

    owner_plan = source / census["registrations"][0]["ownerPlan"]
    local_content = owner_plan.read_bytes()
    owner_plan.unlink()
    with pytest.raises(module.ArchitectureDocsError, match="owner-local LEGO plan.*SourceCut"):
        module.validate_formal_issue_census(census, plans, root=source)
    owner_plan.write_bytes(local_content)
    module.validate_formal_issue_census(census, plans, root=source)
    external = tmp_path / "external-owner-plan.json"
    external.write_bytes(local_content)
    owner_plan.unlink()
    owner_plan.symlink_to(external)
    with pytest.raises(module.ArchitectureDocsError, match="owner-local LEGO plan.*SourceCut"):
        module.validate_formal_issue_census(census, plans, root=source)



@pytest.mark.parametrize(
    ("relative", "label"),
    [
        ("docs/architecture/evidence/FORMAL_LEGO_ISSUE_CENSUS_20261024_R1.json", "formal issue census"),
        ("tools/repo/owners.toml", "owner manifest"),
    ],
)
def test_formal_registry_sources_bound_before_loading(
    tmp_path: Path, relative: str, label: str
) -> None:
    """Both census and canonical owner types must come from the candidate tree."""
    source = tmp_path / "source"
    local = source / relative
    local.parent.mkdir(parents=True, exist_ok=True)
    value = (ROOT / relative).read_bytes()
    local.write_bytes(value)
    assert module._source_bound_file(source, relative, label) == local

    local.unlink()
    with pytest.raises(module.ArchitectureDocsError, match=f"{label} escapes SourceCut"):
        module._source_bound_file(source, relative, label)

    external = tmp_path / "external-input"
    external.write_bytes(value)
    local.symlink_to(external)
    with pytest.raises(module.ArchitectureDocsError, match=f"{label} escapes SourceCut"):
        module._source_bound_file(source, relative, label)


def test_git01_graph_projection_has_exact_repository_owner_lego_registration() -> None:
    """The executable GIT-01 graph belongs to repo mechanics, not the census."""
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-01")
    registration = issue["registration"]
    assert registration["state"] == "LINKED"
    assert registration["ownerPlan"] == "tools/repo/planning/lego-plan-r1.json"
    assert registration["slice"] == "RG1"
    plan = plans[registration["ownerPlan"]]
    source = next(x for x in plan["nodes"] if x["id"] == "RG1_SOURCE")
    assert "source_history_legos.py" in source["evidence"]
    assert "test_source_history_legos.py" in source["evidence"]
    assert (ROOT / "tools/repo/source_history_legos.py").is_file()
    module.validate_formal_issue_census(census, plans)


def test_git02_unadmitted_historical_finance_and_network_consumers_remain_source_bound() -> None:
    """Historical CDC success must not invent current consumers or authorize deletion."""
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-02")
    candidates = issue["historicalUnadmittedOwnerConsumers"]
    assert {row["historicalCommit"] for row in candidates} == {
        "1df72119bc2a04cc6b1f93501d068873546f934f",
        "5f4d4759b2809a5ccc57174e3e110eb6926f135d",
    }
    assert {row["owner"] for row in candidates} == {"domains/capital", "platform/network"}
    assert {row["historicalNativeTestResult"] for row in candidates} == {"12_PASSED"}
    for row in candidates:
        assert row["modernConsumerAdmitted"] is False
        assert row["branchRetirement"] == "NOT_PROVEN"
        assert row["selection"] == "PRESERVE_HISTORICAL_SOURCE_NO_WHOLE_COMMIT_CHERRY_PICK"
        assert row["historicalTestSourceCut"] == row["historicalCommit"]
        assert row["protectedMainSourceCut"] == "e74e94a298077432df589e58c61a9b1499a28c5c"
        assert row["behaviorScope"].strip()
        assert row["missingCurrentConsumerEvidence"].strip()
        assert all(not (ROOT / path).exists() for path in row["historicOnlyFiles"])
    module.validate_formal_issue_census(census, plans)


def test_git02_gateway_historical_branch_is_consumer_scoped_not_mass_deletable() -> None:
    """Branch-tip difference is not a consumer-qualified reason to cherry-pick or delete."""
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-02")
    source = issue["historicalGatewaySourceCut"]
    assert source["historicalHead"] == "bb26e32ed40e4c37534ae6f367fbdf747317682c"
    assert source["protectedMain"] == "4379351658e7ffaad9c1510e0c7579e449e82438"
    assert source["classification"] == "OWNER_CONSUMER_COVERAGE_NOT_BRANCH_EQUIVALENCE"
    assert source["branchRetirement"] == "NOT_PROVEN"
    selected = issue["historicalGatewayConsumerSelections"]
    assert {entry["historicalCommit"] for entry in selected} == {
        "8d22cda4f0a2e789f80c43c28720df3879fdaf7f",
        "bb26e32ed40e4c37534ae6f367fbdf747317682c",
    }
    assert issue["registration"]["state"] == "UNREGISTERED"
    for entry in selected:
        assert entry["owner"] == "services/gateway"
        assert entry["status"] == "CONSUMER_COVERED_DO_NOT_CHERRY_PICK_WHOLE_COMMIT"
        assert entry["evidenceScope"] == "NATIVE_CONSUMER_TESTS_ONLY"
        assert entry["historicalObligation"].strip()
        assert entry["remoteConsumer"].strip()
        for path in entry["remoteTestPaths"]:
            assert path.startswith("services/gateway/tests/")
            assert (ROOT / path).is_file()
    module.validate_formal_issue_census(census, plans)


def test_git02_unique_codex_oauth_discovery_history_is_not_relabelled_redundant() -> None:
    """A passing historical consumer absent from Main is a preservation candidate."""
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-02")
    entry = issue["historicalCodexOAuthSourceCut"]
    assert entry["historicalCommit"] == "228d789a752386ebe31a3706925bfaf5f665ad94"
    assert entry["candidateStatus"] == "PRESERVE_SOURCE_PENDING_CONSUMER_ADMISSION"
    assert entry["historyDisposition"] == "NO_CHERRY_PICK_OR_DELETE_AUTHORIZED"
    assert entry["sourceUniqueAtCut"] is True
    assert entry["nativeFixtureProof"] == "23_OFFLINE_SOURCECUT_TESTS_PASS"
    assert entry["scope"] == "DISCOVERY_ONLY_NO_CREDENTIALS_OR_LIVE_GATEWAY"
    assert entry["protectedConsumerAdmitted"] is False
    assert issue["registration"]["state"] == "UNREGISTERED"
    module.validate_formal_issue_census(census, plans)


def test_git01_four_distinct_patch_equivalents_preserve_consumers_and_actual_source_cut() -> None:
    """Patch equivalence alone grants no branch deletion, owner effects remain typed."""
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-01")
    selected = {row["localCommit"][:12]: row for row in issue["consumerSelections"]}
    four = ("225192c6e711", "2919a6d8406a", "495b45d4610d", "f93faa57cf99")
    for key in four:
        entry = selected[key]
        assert entry["disposition"] == "SKIP_DUPLICATE_CHERRY_PICK"
        source = entry["sourceQualification"]
        assert source["localMain"] == "13704d0cac9e113b395f2d5a21b5bf8119aa04a5"
        assert source["protectedMain"] == "688ed35d1f502549b04a1fb931a6e86d8350050c"
        assert source["patchRelation"] == "PATCH_ID_EQUIVALENT"
        assert source["branchDeletionAllowed"] is False
        assert entry["remoteWitness"] and entry["consumer"]
    old = selected["225192c6e711"]
    assert old["sourceQualification"]["tipRelation"] == "BOTH_TIPS_ABSENT"
    assert old["sourceQualification"]["consumerStanding"] == "NO_CURRENT_CONSUMER"
    for key in ("2919a6d8406a", "495b45d4610d"):
        row = selected[key]
        assert row["sourceQualification"]["consumerStanding"] == "CURRENT_OWNER_COVERED"
        assert row["sourceQualification"]["tipRelation"] == "SAME_BLOB_AND_MODE"
        assert row["verifiedEqualChangedBlobs"] is True
        assert row["evaluatedRemoteMain"] == row["sourceQualification"]["protectedMain"]
        assert all(len(sha) == 40 for sha in row["equalChangedBlobOids"].values())
    assert selected["f93faa57cf99"]["sourceQualification"]["tipRelation"] == "SAME_BLOB_AND_MODE"
    module.validate_formal_issue_census(census, plans)

def test_git01_workstation_history_inverse_pair_is_a_single_non_live_effect() -> None:
    """An adjacent add/revert is one historical identity, not two live LEGo parts."""
    census, _ = formal_issue_inputs()
    issue = next(x for x in census["issues"] if x["id"] == "GIT-01")
    additions = [x for x in issue["consumerSelections"] if x["localCommit"].startswith("e51472db")]
    assert len(additions) == 1
    pair = additions[0]
    assert pair["owner"] == "platform/workstation"
    assert pair["pairedRevertCommit"] == "07255e4dfd26d172ebb5e62c5844ff2d661081f8"
    assert pair["disposition"] == "SKIP_CANCELLED_HISTORY_PAIR"
    assert pair["sourceQualification"]["branchDeletionAllowed"] is False
    assert pair["sourceQualification"]["consumerStanding"] == "NO_CURRENT_CONSUMER"
    assert pair["beforeTreeOid"] == pair["afterTreeOid"] == "ad4aab81359fb9de9223023b702137e8d9101344"
    files = [
        "platform/workstation/tests/test_real_chrome_browser_harness_provider.py",
        "platform/workstation/workstation/providers/real_chrome_browser_harness/materialize.py",
        "platform/workstation/workstation/providers/real_chrome_browser_harness/README.md",
        "platform/workstation/workstation/providers/real_chrome_browser_harness/RealChromeBrowserHarnessProvider.ps1",
    ]
    assert all(not (ROOT / path).exists() for path in files)
