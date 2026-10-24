from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

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


def test_retired_hux_milestone_history_has_no_live_harness_consumer() -> None:
    """HUX plan edits and their retirement are one obsolete responsibility, not two features."""
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-01")
    entry = next(
        row for row in issue["consumerSelections"]
        if row["localCommit"] == "bf1b282ff64fe94a796eaea96366d9e25a243b6f"
    )
    assert entry["owner"] == "services/harness"
    assert entry["disposition"] == "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER"
    assert entry["evidenceScope"] == "IN_TREE_CONSUMER_ABSENCE_EXTERNAL_UNKNOWN"
    assert entry["historicalCohort"] == [
        "591672cd8637ba4fdc68bc3f31ce5a90918cdb71",
        "bf1b282ff64fe94a796eaea96366d9e25a243b6f",
    ]
    assert entry["sourceQualification"]["branchDeletionAllowed"] is False
    assert entry["sourceQualification"]["tipRelation"] == "BOTH_TIPS_ABSENT"
    paths = entry["retiredPaths"]
    assert len(paths) == 4 and len(set(paths)) == 4
    assert all(path.startswith("services/harness/planning/") for path in paths)
    assert all(not (ROOT / path).exists() for path in paths)
    module.validate_formal_issue_census(census, plans)


def test_git01_exact_committed_tree_secret_scanner_preserves_current_ci_and_local_scopes() -> None:
    """Only the historic committed-source scan is reused; do not narrow current CI."""
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-01")
    selected = {row["localCommit"]: row for row in issue["consumerSelections"]}
    old = "334d0eb75adb297b676b35b39808c9bac661ec76"
    row = selected[old]
    assert row["owner"] == "tools/repo"
    assert row["disposition"] == "SKIP_DUPLICATE_CHERRY_PICK"
    assert row["evidenceScope"] == "NATIVE_CONSUMER_PASS"
    assert row["sourceQualification"]["branchDeletionAllowed"] is False
    assert row["verifiedEqualChangedBlobs"] is True
    assert set(row["verifiedEqualChangedPaths"]) == {
        "tools/repo/check_tracked_secrets.sh",
        "tools/repo/test_tracked_secrets.py",
    }
    assert "equalChangedBlobOids" not in row
    assert "run: tools/repo/check_tracked_secrets.sh" in (ROOT / ".github/workflows/ci.yml").read_text()
    root_mise = (ROOT / "mise.toml").read_text()
    assert 'gitleaks git --no-banner' in root_mise
    assert 'gitleaks dir --no-banner' in root_mise
    module.validate_formal_issue_census(census, plans)


def test_retired_next_historical_owner_cohorts_are_not_reintroduced() -> None:
    """Six nonmerge historic commits select four retired Next responsibilities."""
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-01")
    entries = {row["localCommit"]: row for row in issue["consumerSelections"]}
    cases = {
        "dcd9702fbee31237ecbce6820327dda8bdad5f7f": {
            "count": 8,
            "commits": {"dcd9702fbee31237ecbce6820327dda8bdad5f7f"},
        },
        "b81ae9d0bf9ffe77726e4fb95ba1d89b44e3d363": {
            "count": 7,
            "commits": {
                "b81ae9d0bf9ffe77726e4fb95ba1d89b44e3d363",
                "ba339f80c0c3730b9770f092e0566fae24e71488",
            },
        },
        "832468936934e03aa2b8f67836182a8543b124a6": {
            "count": 16,
            "commits": {
                "832468936934e03aa2b8f67836182a8543b124a6",
                "1c20627bce9ab12bda2e92917962c4c233da6d88",
            },
        },
        "0dcead882cec69318243326858a13fa48989a772": {
            "count": 5,
            "commits": {"0dcead882cec69318243326858a13fa48989a772"},
        },
    }
    retired = set()
    for primary, case in cases.items():
        row = entries[primary]
        assert row["owner"] == "meta/next"
        assert row["disposition"] == "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER"
        assert row["evidenceScope"] == "IN_TREE_CONSUMER_ABSENCE_EXTERNAL_UNKNOWN"
        assert row["sourceQualification"]["branchDeletionAllowed"] is False
        assert row["sourceQualification"]["tipRelation"] == "BOTH_TIPS_ABSENT"
        assert set(row["historicalCohort"]) == case["commits"]
        paths = row["retiredPaths"]
        assert len(paths) == case["count"]
        assert all(path.startswith("meta/next/") for path in paths)
        assert all(not (ROOT / path).exists() for path in paths)
        assert not retired.intersection(paths)
        retired.update(paths)
    assert len(retired) == 36
    # The current Social Fabric Owner is retained, not replaced by old R2.
    assert (ROOT / "meta/next/scripts/social_fabric_r1.py").is_file()
    assert (ROOT / "meta/next/tests/test_social_fabric_r1.py").is_file()
    module.validate_formal_issue_census(census, plans)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("duplicate", "duplicate historical Git selection"),
        ("bad_sha", "invalid historical Git SHA"),
        ("unknown_owner", "undeclared historical Git owner"),
        ("unhashable_owner", "undeclared historical Git owner"),
        ("unowned_with_implementation_authority", "undeclared historical Git owner"),
        ("missing_consumer", "historical Git selection missing consumer"),
        ("unknown_disposition", "invalid historical Git disposition"),
        ("unknown_evidence", "invalid historical Git evidenceScope"),
        ("retirement", "historical Git selection cannot authorize branch deletion"),
        ("missing_retirement_flag", "historical Git selection cannot authorize branch deletion"),
        ("wrong_local_cut", "historical Git selection local SourceCut mismatch"),
        ("bad_cohort", "invalid historical Git cohort"),
        ("bad_remote_cut", "invalid historical Git protected SourceCut"),
    ],
)
def test_git01_formal_selection_type_invariants_fail_closed(
    mutation: str, expected_error: str
) -> None:
    """Parallel history cohorts cannot silently change type or deletion authority."""
    import copy

    census, plans = formal_issue_inputs()
    census = copy.deepcopy(census)
    issue = next(item for item in census["issues"] if item["id"] == "GIT-01")
    row = next(
        item for item in issue["consumerSelections"]
        if isinstance(item.get("sourceQualification"), dict)
    )
    if mutation == "duplicate":
        issue["consumerSelections"].append(copy.deepcopy(row))
    elif mutation == "bad_sha":
        row["localCommit"] = "not-a-sha"
    elif mutation == "unknown_owner":
        row["owner"] = "UNKNOWN_OWNER_NOT_IN_MANIFEST"
    elif mutation == "unowned_with_implementation_authority":
        row["owner"] = "ROOT_UNOWNED"
    elif mutation == "unhashable_owner":
        row["owner"] = ["tools/repo"]
    elif mutation == "missing_consumer":
        row["consumer"] = ""
    elif mutation == "unknown_disposition":
        row["disposition"] = "SAFE_TO_DELETE_EVERYTHING"
    elif mutation == "unknown_evidence":
        row["evidenceScope"] = "PRODUCTION_IS_PROVEN_BY_GIT_SHA"
    elif mutation == "retirement":
        row["sourceQualification"]["branchDeletionAllowed"] = True
    elif mutation == "missing_retirement_flag":
        row["sourceQualification"].pop("branchDeletionAllowed")
    elif mutation == "wrong_local_cut":
        row["sourceQualification"]["localMain"] = "f" * 40
    elif mutation == "bad_cohort":
        row["historicalCohort"] = [row["localCommit"], row["localCommit"]]
    elif mutation == "bad_remote_cut":
        row["sourceQualification"]["protectedMain"] = "wrong"
    with pytest.raises(module.ArchitectureDocsError, match=expected_error):
        module.validate_formal_issue_census(census, plans)


def test_git01_network_uv_nonmerge_uses_current_native_route_consumer() -> None:
    """One absent historic source; native Network verifies the current route."""
    import tomllib

    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-01")
    rows = [row for row in issue["consumerSelections"] if row["localCommit"] == "167112a8e6e1ba7f9af776fe6b85124b60d97cbe"]
    assert len(rows) == 1
    selection = rows[0]
    assert selection["owner"] == "platform/network"
    assert selection["disposition"] == "SKIP_OLDER_SOURCECUT"
    assert selection["evidenceScope"] == "NATIVE_CONSUMER_PASS"
    assert selection["sourceQualification"]["branchDeletionAllowed"] is False
    owner = tomllib.loads((ROOT / "platform/network/mise.toml").read_text())
    assert owner["tools"]["uv"] == "0.13.5"
    assert "ci" in owner["tasks"] and "behavior" in owner["tasks"]
    module.validate_formal_issue_census(census, plans)


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("overlap_cohort", "invalid historical Git cohort"),
        ("selected_blocked", "historical Git selected and blocked collision"),
        ("numeric_retirement", "historical Git selection cannot authorize branch deletion"),
    ],
)
def test_git01_owner_proof_union_cannot_silently_weaken_preexisting_guards(
    mutation: str, error: str
) -> None:
    census, plans = formal_issue_inputs()
    issue = next(x for x in census["issues"] if x["id"] == "GIT-01")
    rows = issue["consumerSelections"]
    if mutation == "overlap_cohort":
        cases = [x for x in rows if "historicalCohort" in x]
        assert len(cases) >= 2
        cases[1]["historicalCohort"].append(cases[0]["historicalCohort"][0])
    elif mutation == "selected_blocked":
        issue["consumerBlockedSelections"][0]["localCommit"] = rows[0]["localCommit"]
    elif mutation == "numeric_retirement":
        rows[0]["branchDeletionAllowed"] = 1
    else:
        raise AssertionError(mutation)
    with pytest.raises(module.ArchitectureDocsError, match=error):
        module.validate_formal_issue_census(census, plans)


@pytest.mark.parametrize(
    ("order", "message"),
    [
        ("before", "invalid historical Git cohort"),
        ("after", "historical Git cohort member collision"),
        ("blocker", "historical Git selected and blocked collision"),
    ],
)
def test_git01_cohort_members_have_one_owner_decision(
    order: str, message: str
) -> None:
    """Every SHA within a historical cohort has exactly one disposition."""
    census, plans = formal_issue_inputs()
    issue = next(x for x in census["issues"] if x["id"] == "GIT-01")
    entries = issue["consumerSelections"]
    primary = next(x for x in entries if len(x.get("historicalCohort", [])) > 1)
    secondary = next(
        sha for sha in primary["historicalCohort"]
        if sha != primary["localCommit"]
    )
    assert all(x["localCommit"] != secondary for x in entries)
    if order == "blocker":
        claim = copy.deepcopy(issue["consumerBlockedSelections"][0])
        claim["localCommit"] = secondary
        issue["consumerBlockedSelections"].append(claim)
    else:
        claim = copy.deepcopy(next(
            x for x in entries if not x.get("historicalCohort")
        ))
        claim["localCommit"] = secondary
        if order == "before":
            entries.insert(0, claim)
        else:
            entries.append(claim)
    with pytest.raises(module.ArchitectureDocsError, match=message):
        module.validate_formal_issue_census(census, plans)


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
        # The canonical validator below is the single enum authority.
        # Its negative-mutant tests prove unknown dispositions fail closed.
        assert isinstance(item["disposition"], str) and item["disposition"]
        assert isinstance(item["evidenceScope"], str) and item["evidenceScope"]
        if item["evidenceScope"] == "EXACT_OWNER_LOCKED_COMPONENTS_NO_LIVE_PROVIDER":
            assert item["disposition"] == "SKIP_DUPLICATE_CHERRY_PICK"
            assert item["sourceQualification"]["tipRelation"] == "PARTIAL_TIP_LOCK_COMPONENT_IDENTITY"
            assert item["sourceQualification"]["branchDeletionAllowed"] is False
            assert item["owner"] == "platform/workstation"
        if item["evidenceScope"] == "SOURCE_ABSENCE_ONLY_NO_NATIVE_CDC":
            assert item["disposition"] == "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER"
            assert item["sourceQualification"]["branchDeletionAllowed"] is False
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
    # Algebraic identity of exact tip blobs is a proof category, not the
    # identity of a historical commit or its concrete consumer disposition.
    # Keep qualified records type checked; independent owner-native tests
    # determine when corrected current source supersedes an old source cut.
    identical = [
        item for item in candidates
        if item["disposition"] == "SKIP_IDENTICAL_TIP_WITH_NATIVE_CONSUMER"
    ]
    assert identical
    for selected in identical:
        assert selected["owner"]
        assert selected["evidenceScope"] == "EXACT_GIT_BLOB_AND_NATIVE_CONSUMER_PASS"
        proof = selected["sourceQualification"]
        assert proof["localMain"] == source["localMain"]
        assert len(proof["protectedMain"]) == 40
        assert proof["kind"] == "non-merge"
        assert proof["patchRelation"] == "PATCH_DISTINCT_UNQUALIFIED"
        assert proof["branchDeletionAllowed"] is False
        paths = proof["changedPathIdentities"]
        assert paths and len({row["path"] for row in paths}) == len(paths)
        assert all(len(row["blobOid"]) == 40 and row["mode"] for row in paths)
    # A corrected Gateway or Workstation source cut is not an exact historical
    # blob: those bounded obligations are independently tested below.
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
        "63f0076e9aea0f5ae22d7e3fc9e8142619420446",
    }
    assert {row["owner"] for row in candidates} == {
        "domains/capital", "platform/network", "apps/web"
    }
    assert {row["historicalNativeTestResult"] for row in candidates} == {
        "12_PASSED", "NOT_REEXECUTED_NO_CURRENT_CONSUMER"
    }
    for row in candidates:
        assert row["modernConsumerAdmitted"] is False
        assert row["branchRetirement"] == "NOT_PROVEN"
        assert row["selection"] == "PRESERVE_HISTORICAL_SOURCE_NO_WHOLE_COMMIT_CHERRY_PICK"
        assert row["historicalTestSourceCut"] == row["historicalCommit"]
        assert row["protectedMainSourceCut"] in {
            "e74e94a298077432df589e58c61a9b1499a28c5c",
            "d6e15f621aad7cdb65fbfe97e712540eebcb6309",
        }
        if row["owner"] == "apps/web":
            assert row["historicalNativeTestResult"] == "NOT_REEXECUTED_NO_CURRENT_CONSUMER"
            assert row["historicalCommit"] == "63f0076e9aea0f5ae22d7e3fc9e8142619420446"
            assert all(path.startswith("apps/web/") for path in row["historicOnlyFiles"])
        else:
            assert row["historicalNativeTestResult"] == "12_PASSED"
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


def test_git01_three_selected_historical_owner_effects_have_sufficient_source_proof() -> None:
    """An exact Git source cut plus paths replaces redundant duplicated Git blob hashes."""
    census, plans = formal_issue_inputs()
    issue = next(item for item in census["issues"] if item["id"] == "GIT-01")
    selected = {entry["localCommit"][:12]: entry for entry in issue["consumerSelections"]}
    expected = {
        "9fbce29650fb": {
            "owner": "services/gateway",
            "paths": {
                "services/gateway/src/ordivon_gateway/upstream.py",
                "services/gateway/tests/test_upstream_identity.py",
            },
        },
        "eaa045252ef7": {
            "owner": "services/gateway",
            "paths": {
                "services/gateway/packaging/windows/verify_release.py",
                "services/gateway/tests/test_windows_release_contract.py",
            },
        },
        "bec31a81ba5b": {
            "owner": "platform/workstation",
            "paths": {
                "platform/workstation/providers/cloudflare/scripts/ordivon_cloudflare_tofu_handoff.py",
                "platform/workstation/providers/cloudflare/test/handoff_tofu_test.py",
                "platform/workstation/tofu/agent-birth-handoff/main.tf",
            },
        },
    }
    for short, consumer in expected.items():
        entry = selected[short]
        assert entry["owner"] == consumer["owner"]
        assert set(entry["changedPaths"]) == consumer["paths"]
        assert entry["verifiedEqualChangedBlobs"] is True
        assert "equalChangedBlobOids" not in entry
        assert entry["evidenceScope"] == "NATIVE_CONSUMER_PASS"
        assert entry["disposition"] == "SKIP_DUPLICATE_CHERRY_PICK"
        assert entry["sourceQualification"] == {
            "localMain": "13704d0cac9e113b395f2d5a21b5bf8119aa04a5",
            "protectedMain": "0fcc7c0b188e4b981b25c95f76dfb17a41fc82fb",
            "patchRelation": "PATCH_DISTINCT_UNQUALIFIED",
            "tipRelation": "SAME_BLOB_AND_MODE",
            "consumerStanding": "CURRENT_OWNER_COVERED",
            "branchDeletionAllowed": False,
        }
    assert "WINDOWS_SOURCE_CONTRACT_ONLY" in selected["eaa045252ef7"]["remoteWitness"]
    assert "NO_LIVE_CLOUDFLARE_CUTOVER" in selected["bec31a81ba5b"]["remoteWitness"]
    module.validate_formal_issue_census(census, plans)


def test_retired_repository_status_projections_stay_absent() -> None:
    """Deleted status/reporting helpers had no current callers; the owner verifier remains."""
    legacy = (
        "tools/repo/document_currentness.py",
        "tools/repo/test_document_currentness.py",
        "tools/repo/living_view.py",
        "tools/repo/test_living_view.py",
        "tools/repo/first_contact_eval_receipt.py",
        "tools/repo/first_contact_eval_matrix.py",
        "tests/first_contact/test_eval_receipt_r6.py",
        "tests/first_contact/test_eval_matrix_r7.py",
    )
    assert (ROOT / "tools/repo/check_architecture_docs.py").is_file()
    for relative in legacy:
        assert not (ROOT / relative).exists(), f"unconsumed historical tool restored: {relative}"
    census, plans = formal_issue_inputs()
    issue = next(x for x in census["issues"] if x["id"] == "GIT-01")
    row = next(x for x in issue["consumerSelections"] if x["localCommit"].startswith("9c0684c02c"))
    assert len(row["historicalCohort"]) == len(set(row["historicalCohort"])) == 10
    assert set(row["historicalCohort"]) >= {
        "ba9732f8bcc7348c73d570509ebdc2fdf4b30fcf",
        "a1768d039268f1396439bfef8605a7700935c617",
        "709816a1f89ce2a4811d7162a658f2f6f84018d9",
        "61de83cb01b71793301907862840e3176f169b3a",
    }
    module.validate_formal_issue_census(census, plans)


def test_git01_retired_network_router_cohort_has_one_qualified_lego() -> None:
    """Eight obsolete commits describe one removed service, not eight providers."""
    census, plans = formal_issue_inputs()
    issue = next(x for x in census["issues"] if x["id"] == "GIT-01")
    rows = [
        x for x in issue["consumerSelections"]
        if x["disposition"] == "SKIP_RETIRED_UNCONSUMED"
        and x["owner"] == "platform/network"
    ]
    assert len(rows) == 1
    retired = rows[0]
    assert retired["owner"] == "platform/network"
    assert len(retired["historicalCohort"]) == len(set(retired["historicalCohort"])) == 8
    assert retired["localCommit"] in retired["historicalCohort"]
    assert all(len(commit) == 40 for commit in retired["historicalCohort"])
    assert retired["sourceQualification"]["branchDeletionAllowed"] is False
    assert retired["sourceQualification"]["patchRelation"] == "DISTINCT_HISTORICAL_RETIRED_EFFECT"
    network = plans["platform/network/planning/lego-plan-r1.json"]
    requirement = next(node for node in network["nodes"] if node["id"] == "N01")
    assert any("Retired custom Network Capability Router" in a for a in requirement["acceptance"])
    assert "tests/test_shared_provider_carrier.py::test_retired_network_capability_router_stays_retired" in requirement["evidence"]
    module.validate_formal_issue_census(census, plans)


def test_git01_retired_history_cohorts_are_owner_scoped() -> None:
    census, plans = formal_issue_inputs()
    issue = next(item for item in census["issues"] if item["id"] == "GIT-01")
    rows = [item for item in issue["consumerSelections"]
            if item["disposition"] == "SKIP_RETIRED_UNCONSUMED"]
    assert {"tools/repo", "platform/network"} <= {item["owner"] for item in rows}
    seen: set[str] = set()
    for row in rows:
        cohort = row["historicalCohort"]
        assert row["localCommit"] in cohort
        assert all(len(sha) == 40 for sha in cohort)
        assert len(cohort) == len(set(cohort))
        assert not set(cohort) & seen
        seen.update(cohort)
    module.validate_formal_issue_census(census, plans)


def test_git01_frozen_dualmain_nonmerge_endpoint_partition_requires_consumer_proofs() -> None:
    # Immutable SourceCut projection, not a second dynamic Git-history authority.
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-01")
    partition = issue["frozenDualMainCommitEffectPartition"]
    assert partition["localMain"] == census["source"]["linuxLocalMain"]
    assert len(partition["protectedMain"]) == 40
    classes = partition["nonMergePathFinalStates"]
    assert set(classes) == {
        "ALL_PRESENT_IDENTICAL", "ALL_BOTH_ABSENT",
        "MIXED_IDENTICAL_AND_ABSENT", "REQUIRES_OWNER_CDC",
    }
    assert all(type(value) is int and value >= 0 for value in classes.values())
    assert sum(classes.values()) == partition["localNonMergeCommits"]
    assert (
        partition["localNonMergeCommits"] + partition["localMergeConnectors"]
        == partition["localOnlyCommits"]
    )
    assert partition["localOnlyCommits"] == 2300
    remote_classes = partition["remoteNonMergePathFinalStates"]
    assert set(remote_classes) == set(classes)
    assert all(type(value) is int and value >= 0 for value in remote_classes.values())
    assert sum(remote_classes.values()) == partition["remoteNonMergeCommits"]
    assert (
        partition["remoteNonMergeCommits"] + partition["remoteMergeConnectors"]
        == partition["remoteOnlyCommits"]
    )
    assert partition["remoteOnlyCommits"] == 639
    assert partition["evidenceStanding"] == "TIP_STATE_ONLY_NOT_BEHAVIORAL_EQUIVALENCE"
    assert partition["branchDeletionAllowed"] is False
    assert classes["REQUIRES_OWNER_CDC"] > 0
    module.validate_formal_issue_census(census, plans)


def test_git01_old_capital_r3_office_has_no_current_consumer() -> None:
    """Deleted R3 Office is an historical LEGO, not current capital authority."""
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-01")
    entry = next(x for x in issue["consumerSelections"] if x["localCommit"].startswith("d116d1e468"))
    assert entry["owner"] == "domains/capital"
    assert entry["disposition"] == "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER"
    assert entry["evidenceScope"] == "SOURCE_ABSENCE_ONLY_NO_NATIVE_CDC"
    source = entry["sourceQualification"]
    assert source["localMain"] == "13704d0cac9e113b395f2d5a21b5bf8119aa04a5"
    assert source["tipRelation"] == "BOTH_TIPS_ABSENT"
    assert source["branchDeletionAllowed"] is False
    removed = entry["removedHistoricalPaths"]
    assert len(removed) == 42
    assert len(set(removed)) == len(removed)
    assert all(name.startswith("domains/capital/") for name in removed)
    assert all(not (ROOT / name).exists() for name in removed)
    assert "domains/capital/config/capital_office_registry.json" in removed
    assert "domains/capital/src/ordivon_capital/governance/owner_authority.py" in removed
    module.validate_formal_issue_census(census, plans)


def test_git01_browser_harness_legacy_nonmerge_effects_are_source_bound() -> None:
    """Two historical patches have distinct Owners and do not override the live browser."""
    census, plans = formal_issue_inputs()
    issue = next(item for item in census["issues"] if item["id"] == "GIT-01")
    by_sha = {item["localCommit"]: item for item in issue["consumerSelections"]}
    observer = by_sha["ee1f938010915f348ce96413a06d7407d5434efe"]
    assert observer["owner"] == "services/harness"
    assert observer["pairedRevertCommit"] == "82239de6a1731b1f54f59166b06e95f9003fcd15"
    assert observer["disposition"] == "SKIP_CANCELLED_HISTORY_PAIR"
    assert observer["beforeTreeOid"] == observer["afterTreeOid"] == (
        "c6ae0ba390a6e37d69ee403395547cc6318f7992"
    )
    assert observer["sourceQualification"]["patchRelation"] == "INVERSE_DIRECT_CHILD"
    assert observer["sourceQualification"]["historicalRuntimeParity"] == "UNKNOWN"
    assert observer["sourceQualification"]["branchDeletionAllowed"] is False

    legacy = by_sha["d6f0d184dec98746704291ce74639b38fa645d8e"]
    assert legacy["owner"] == "packages/composition"
    assert legacy["disposition"] == "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER"
    assert legacy["evidenceScope"] == "IN_TREE_CONSUMER_ABSENCE_EXTERNAL_UNKNOWN"
    assert legacy["sourceQualification"]["historicalSourceState"] == "BOTH_TIPS_ABSENT"
    assert legacy["sourceQualification"]["branchDeletionAllowed"] is False
    assert all(not (ROOT / path).exists() for path in legacy["changedPaths"])

    # Preserve the current natural Owner, not the obsolete Composition API.
    current = (ROOT / "services/harness/scripts/browserless_podman_deploy.py").read_text()
    assert "def resolve_network_binding(" in current
    assert "PRODUCTION_CUTOVER_PASS" in current
    assert "generationDigest" in current
    assert "network-v2" in current
    assert (ROOT / "services/harness/tests/test_browserless_podman_deploy.py").is_file()
    module.validate_formal_issue_census(census, plans)


def test_git01_retired_standalone_catalog_checker_has_next_owner_consumer() -> None:
    """Source-absent historical helper cannot supersede the live Next authority provider."""
    census, plans = formal_issue_inputs()
    issue = next(row for row in census["issues"] if row["id"] == "GIT-01")
    selected = [row for row in issue["consumerSelections"] if row["localCommit"] == "733481b66259399671888eeb109ad6c6ad3edae6"]
    assert len(selected) == 1
    row = selected[0]
    assert row["owner"] == "meta/next"
    assert row["disposition"] == "SKIP_RETIRED_UNCONSUMED"
    assert row["evidenceScope"] == "NATIVE_CONSUMER_PASS"
    assert row["sourceQualification"]["protectedMain"] == "78895b2291830be75fa472f3621fc24ebd2e67f3"
    assert row["sourceQualification"]["branchDeletionAllowed"] is False
    assert not (ROOT / "tools/catalog/check_authority_catalog.py").exists()
    assert (ROOT / "meta/next/scripts/check_authority_catalog_r1.py").is_file()
    assert (ROOT / "meta/next/tests/test_authority_catalog.py").is_file()
    module.validate_formal_issue_census(census, plans)


def test_nonmerge_runtime_formal_history_preserves_stronger_current_acceptance() -> None:
    """Selected historical nonmerge effects must retain their proof scope."""
    census, plans = formal_issue_inputs()
    issue = next(item for item in census["issues"] if item["id"] == "GIT-01")
    selections = {entry["localCommit"]: entry for entry in issue["consumerSelections"]}
    accepted = selections["e66aaa1eabcb21b02b58e139b687162dac0e930f"]
    assert accepted["owner"] == "services/runtime"
    assert accepted["disposition"] == "SKIP_OLDER_SOURCECUT"
    assert accepted["evidenceScope"] == "NATIVE_CONSUMER_PASS"
    assert (ROOT / "services/runtime/formal/RuntimeDispatchR1.trace-r1.acceptance.json").is_file()
    for entry in (accepted,):
        proof = entry["sourceQualification"]
        assert proof["localMain"] == issue["consumerSourceCut"]["localMain"]
        assert len(proof["protectedMain"]) == 40
        assert proof["branchDeletionAllowed"] is False
        assert all(not (ROOT / path).exists() for path in entry["retiredSourcePaths"])
    module.validate_formal_issue_census(census, plans)


def test_git01_environment_preflight_history_reuses_current_native_consumers() -> None:
    """Three local non-merge commits have current fail-closed owner consumers."""
    census, plans = formal_issue_inputs()
    issue = next(x for x in census["issues"] if x["id"] == "GIT-01")
    selected = {x["localCommit"][:12]: x for x in issue["consumerSelections"]}
    for sha in ("abbeace5d271", "96a5d01aa5dc", "492efb2d28a3"):
        row = selected[sha]
        assert row["owner"] == "tools/repo"
        assert row["evidenceScope"] == "NATIVE_CONSUMER_PASS"
        assert row["disposition"] == "SKIP_DUPLICATE_CHERRY_PICK"
        assert row["sourceQualification"]["patchRelation"] == "PATCH_DISTINCT_UNQUALIFIED"
        assert row["sourceQualification"]["branchDeletionAllowed"] is False
        assert "tools/repo/workspace-ready" in row["changedPaths"]
        assert "tools/repo/test_workspace_ready.py" in row["changedPaths"]
        assert row["consumer"] and row["remoteWitness"]
    module.validate_formal_issue_census(census, plans)


def test_git01_historical_agent_patch_shim_is_not_restored_without_consumer() -> None:
    """An absent historical provider cannot justify reinstalling a parallel Runtime patch API."""
    census, plans = formal_issue_inputs()
    issue = next(item for item in census["issues"] if item["id"] == "GIT-01")
    rows = {row["localCommit"]: row for row in issue["consumerSelections"]}
    historical = rows["40479e09d849401f5cfd4297fbe43db0372fe011"]
    assert historical["owner"] == "ROOT_UNOWNED"
    assert historical["disposition"] == "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER"
    assert historical["evidenceScope"] == "IN_TREE_CONSUMER_ABSENCE_EXTERNAL_UNKNOWN"
    assert historical["sourceQualification"]["historicalSourceState"] == "BOTH_TIPS_ABSENT"
    assert historical["sourceQualification"]["branchDeletionAllowed"] is False
    assert set(historical["changedPaths"]) == {
        "apps/agent/tests/test_native_coding_runtime_mcp_port_r1.py",
        "apps/agent/src/ordivon_agent/native_coding_runtime_mcp_port_r1.py",
    }
    assert all(not (ROOT / path).exists() for path in historical["changedPaths"])
    module.validate_formal_issue_census(census, plans)


def test_host_historical_retirement_snapshot_is_not_a_live_consumer() -> None:
    """Keep current SWF Owner proof, not the deleted one-off historical receipt."""
    census, plans = formal_issue_inputs()
    issue = next(item for item in census["issues"] if item["id"] == "GIT-01")
    selected = next(
        item for item in issue["consumerSelections"]
        if item["localCommit"] == "ce973c944d5835c32d559a856fa55b070968aea5"
    )
    assert selected["owner"] == "services/host"
    assert selected["disposition"] == "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER"
    proof = selected["sourceQualification"]
    assert proof["pathFinalRelation"] == "TWO_IDENTICAL_ONE_BOTH_ABSENT"
    assert proof["branchDeletionAllowed"] is False
    assert proof["liveDatabaseReverified"] is False
    assert proof["archiveRestoreReverified"] is False
    assert len(proof["identicalTipModeBlobs"]) == 2
    assert not (ROOT / proof["retiredHistoricalReceiptPath"]).exists()
    host = json.loads((ROOT / "services/host/planning/social-work-fabric-r1.json").read_text())
    legacy = host["legacyRetirement"]
    assert legacy["standing"] == "LIVE_SCHEMA9_RETIRED_PASS"
    assert legacy["archive"]["restoreVerification"] == "PASS"
    assert legacy["liveAcceptance"]["legacyActiveTableCount"] == 0
    assert legacy["liveAcceptance"]["legacyActiveModuleCount"] == 0
    assert legacy["liveAcceptance"]["legacyMcpToolCount"] == 0
    module.validate_formal_issue_census(census, plans)


def test_historical_node_types_pin_has_both_current_owner_consumers() -> None:
    """One historical patch may have multiple natural consumers without a new registry."""
    census, plans = formal_issue_inputs()
    git_issue = next(x for x in census["issues"] if x["id"] == "GIT-01")
    commit = "557e436d19b79fb6983c5c8fdc4e3965d0e25ddd"
    matches = [x for x in git_issue["consumerSelections"] if x["localCommit"] == commit]
    assert len(matches) == 1
    row = matches[0]
    assert row["disposition"] == "SKIP_DUPLICATE_CHERRY_PICK"
    assert row["evidenceScope"] == "NATIVE_CONSUMER_PASS"
    assert row["sourceQualification"]["consumerOwners"] == ["apps/web", "domains/game"]
    assert row["sourceQualification"]["branchDeletionAllowed"] is False
    assert row["evaluatedRemoteMain"] == "d375287686b7ad7f04b1f5ef181bff846ac9cc94"
    for manifest in ("apps/web/package.json", "domains/game/package.json"):
        data = json.loads((ROOT / manifest).read_text(encoding="utf-8"))
        assert data["devDependencies"]["@types/node"] == "26.6.5"
    module.validate_formal_issue_census(census, plans)


def test_repo_test_function_names_are_unique() -> None:
    import ast
    from collections import Counter

    for source in sorted((ROOT / "tools/repo").glob("test_*.py")):
        tree = ast.parse(source.read_text())
        functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]
        duplicates = [name for name, number in Counter(functions).items() if number > 1]
        assert not duplicates, (source, duplicates)


def test_git01_three_uv_owner_nonmerge_effects_use_current_verified_consumers() -> None:
    """Old uv 0.13.5 patches must not replace the current native Owner graph."""
    import tomllib

    census, plans = formal_issue_inputs()
    issue = next(item for item in census["issues"] if item["id"] == "GIT-01")
    selected = {item["localCommit"][:12]: item for item in issue["consumerSelections"]}
    qualification = {
        "47ecd35d70c8": ("platform/security", "verify"),
        "dd3163920cb4": ("capabilities/media", "verify"),
        "993ed44db090": ("capabilities/distribution", "verify"),
    }
    for sha, (owner, task) in qualification.items():
        record = selected[sha]
        assert record["owner"] == owner
        assert record["disposition"] == "SKIP_OLDER_SOURCECUT"
        assert record["evidenceScope"] == "NATIVE_CONSUMER_PASS"
        proof = record["sourceQualification"]
        assert proof["localMain"] == "13704d0cac9e113b395f2d5a21b5bf8119aa04a5"
        assert proof["branchDeletionAllowed"] is False
        assert proof["patchRelation"] == "PATCH_DISTINCT_UNQUALIFIED"
        assert record["consumer"].strip() and record["remoteWitness"].strip()
        mise = tomllib.loads((ROOT / owner / "mise.toml").read_text(encoding="utf-8"))
        assert tuple(map(int, mise["tools"]["uv"].split("."))) >= (0, 13, 5)
        assert task in mise["tasks"]
    module.validate_formal_issue_census(census, plans)


def test_git01_gateway_windows_release_historical_verifier_consumer() -> None:
    """Do not replay an old Gateway verifier when current owner has stronger CDC."""
    census, plans = formal_issue_inputs()
    owner = next(issue for issue in census["issues"] if issue["id"] == "GIT-01")
    matches = [entry for entry in owner["consumerSelections"]
               if entry["localCommit"].startswith("d91d63b70da5")]
    assert len(matches) == 1
    evidence = matches[0]
    assert evidence["owner"] == "services/gateway"
    assert evidence["disposition"] == "SKIP_DUPLICATE_CHERRY_PICK"
    assert evidence["evidenceScope"] == "NATIVE_CONSUMER_PASS"
    assert evidence["sourceQualification"]["branchDeletionAllowed"] is False
    assert evidence["sourceQualification"]["historicalTestBlobEqual"] is False
    verifier = ROOT / "services/gateway/packaging/windows/verify_release.py"
    current_test = ROOT / "services/gateway/tests/test_windows_release_contract.py"
    assert verifier.is_file() and current_test.is_file()
    assert "SURFACE_PATH" in verifier.read_text()
    assert "test_windows_release_dependencies_do_not_share_cache_acl" in current_test.read_text()
    module.validate_formal_issue_census(census, plans)


def test_git01_workstation_cloudflare_gateway_tunnel_historical_correction() -> None:
    """Old Gateway DNS tunnel switch may not override the corrected owner carrier."""
    census, plans = formal_issue_inputs()
    ledger = next(x for x in census["issues"] if x["id"] == "GIT-01")
    matches = [x for x in ledger["consumerSelections"]
               if x["localCommit"].startswith("0fbdd2445e1a")]
    assert len(matches) == 1
    row = matches[0]
    assert row["owner"] == "platform/workstation"
    assert row["disposition"] == "SKIP_OLDER_SOURCECUT"
    assert row["evidenceScope"] == "NATIVE_CONSUMER_PASS"
    assert row["sourceQualification"]["branchDeletionAllowed"] is False
    assert row["sourceQualification"]["currentGatewayCname"] == "native_tunnel"
    p = ROOT / "platform/workstation/tofu/agent-birth-handoff/main.tf"
    source = p.read_text()
    gateway = source.split('resource "cloudflare_dns_record" "gateway_mcp" {', 1)[1].split("\n}", 1)[0]
    assert 'content = "${local.native_tunnel_id}.cfargotunnel.com"' in gateway
    module.validate_formal_issue_census(census, plans)

@pytest.mark.parametrize(
    "fault",
    [
        "missing_revert",
        "bad_revert_sha",
        "same_commit",
        "missing_before_tree",
        "unequal_trees",
        "wrong_patch_relation",
    ],
)
def test_git01_cancelled_pair_requires_equal_typed_full_trees(fault: str) -> None:
    """A cancelled pair must carry an internally consistent full-tree witness."""
    census, plans = formal_issue_inputs()
    selections = next(
        issue["consumerSelections"] for issue in census["issues"]
        if issue["id"] == "GIT-01"
    )
    witness = next(
        row for row in selections if row["disposition"] == "SKIP_CANCELLED_HISTORY_PAIR"
    )
    source = witness["sourceQualification"]
    if fault == "missing_revert":
        witness.pop("pairedRevertCommit")
    elif fault == "bad_revert_sha":
        witness["pairedRevertCommit"] = "not-an-object-id"
    elif fault == "same_commit":
        witness["pairedRevertCommit"] = witness["localCommit"]
    elif fault == "missing_before_tree":
        witness.pop("beforeTreeOid")
    elif fault == "unequal_trees":
        witness["afterTreeOid"] = "0" * 40
    elif fault == "wrong_patch_relation":
        source["patchRelation"] = "UNQUALIFIED"
    with pytest.raises(module.ArchitectureDocsError, match="cancelled pair tree proof"):
        module.validate_formal_issue_census(census, plans)


@pytest.mark.parametrize(
    ("evidence_scope", "false_disposition"),
    [
        ("SOURCE_PROVIDER_NEWER_NO_NATIVE_NIX_PROOF", "SKIP_DUPLICATE_CHERRY_PICK"),
        ("SOURCE_ABSENCE_ONLY_NO_NATIVE_CDC", "SKIP_DUPLICATE_CHERRY_PICK"),
        ("CURRENT_CONSUMER_ELSEWHERE_NO_OLD_EFFECT", "SKIP_DUPLICATE_CHERRY_PICK"),
        ("EXACT_OWNER_LOCKED_COMPONENTS_NO_LIVE_PROVIDER", "NO_PORT_WITHOUT_VERIFIED_LIVE_CONSUMER"),
        ("FROZEN_GATEWAY_CONSUMER_ONLY", "SKIP_DUPLICATE_CHERRY_PICK"),
    ],
)
def test_formal_git01_evidence_cannot_escalate_historical_consumer_admission(
    evidence_scope: str, false_disposition: str,
) -> None:
    """Proof level cannot silently become stronger when parallel Agents merge."""
    census, plans = formal_issue_inputs()
    row = next(
        item
        for item in next(x for x in census["issues"] if x["id"] == "GIT-01")["consumerSelections"]
        if item["evidenceScope"] == evidence_scope
    )
    row["disposition"] = false_disposition
    with pytest.raises(module.ArchitectureDocsError, match="incompatible historical Git evidence"):
        module.validate_formal_issue_census(census, plans)


def test_opa_empty_suite_historical_effect_retains_consumer_proof() -> None:
    """Code-green Security cannot silently drop its source-qualified Git proof."""
    census, plans = formal_issue_inputs()
    decisions = next(x for x in census["issues"] if x["id"] == "GIT-01")["consumerSelections"]
    required = {
        "3d93b188d1022d58040c297f735dd548d8eb076e": "PORT_REQUIRED_OWNER_EFFECT",
        "2dadc4c2eb7a8ab6d2c8eeac34709a9a32a94028": "SKIP_DUPLICATE_CHERRY_PICK",
    }
    for commit, disposition in required.items():
        found = [x for x in decisions if x["localCommit"] == commit]
        assert len(found) == 1
        row = found[0]
        assert row["owner"] == "platform/security"
        assert row["disposition"] == disposition
        assert row["sourceQualification"]["branchDeletionAllowed"] is False

    assert "opa test -v --fail-on-empty policies" in (
        ROOT / "platform/security/mise.toml"
    ).read_text()
    module.validate_formal_issue_census(census, plans)


def test_opa_port_required_without_native_consumer_is_rejected() -> None:
    """Reject vacuous effect-port evidence even when Git SHA and Owner are real."""
    census, plans = formal_issue_inputs()
    negative = json.loads(json.dumps(census))
    rows = next(x for x in negative["issues"] if x["id"] == "GIT-01")["consumerSelections"]
    selected = next(
        x for x in rows if x["localCommit"] == "3d93b188d1022d58040c297f735dd548d8eb076e"
    )
    selected["evidenceScope"] = "EXACT_GIT_BLOBS"
    with pytest.raises(module.ArchitectureDocsError, match="requires native Owner acceptance"):
        module.validate_formal_issue_census(negative, plans)


def test_formal_r21_host_existing_typed_dependencies_form_nontrivial_frontiers() -> None:
    plan = json.loads((ROOT / "services/host/planning/lego-plan-r1.json").read_text())
    nodes, fronts = module.validate_owner_lego_dependencies(plan, "services/host")
    depth = {node: d for d, front in enumerate(fronts) for node in front}
    assert nodes == {"O01", "O02", "O03", "O04"}
    assert depth["O04"] < depth["O01"]
    assert depth["O04"] < depth["O02"]
    assert any(e["from"] == "O02" and e["to"] == "O03" and e["type"] == "DATA"
               for e in plan["edges"])


def test_formal_r21_typed_dependency_cycle_rejected_not_just_node_dependencies() -> None:
    plan = json.loads((ROOT / "services/host/planning/lego-plan-r1.json").read_text())
    plan["edges"].append({"from": "O01", "to": "O04", "type": "DEPENDENCY"})
    with pytest.raises(module.ArchitectureDocsError, match="cyclic LEGO dependencies"):
        module.validate_owner_lego_dependencies(plan, "services/host")


def test_formal_r21_nonprerequisite_feedback_is_not_silently_scheduled() -> None:
    plan = json.loads((ROOT / "platform/network/planning/lego-plan-r1.json").read_text())
    plan["edges"].append({"from": "N04", "to": "N01", "type": "OBSERVATION"})
    _, fronts = module.validate_owner_lego_dependencies(plan, "platform/network")
    assert len(fronts) >= 2


@pytest.mark.parametrize(
    ("owner", "cycle_a", "cycle_b"),
    [
        ("services/runtime/planning/lego-plan-r1.json", "R00", "R01"),
        ("services/harness/planning/lego-plan-r1.json", "H01", "H02"),
        ("platform/network/planning/lego-plan-r1.json", "N01", "N02"),
        ("platform/security/planning/lego-plan-r1.json", "S01", "S02"),
    ],
)
def test_formal_lego21_registered_owner_graph_rejects_cycle(
    owner: str, cycle_a: str, cycle_b: str
) -> None:
    census, plans = formal_issue_inputs()
    nodes = {node["id"]: node for node in plans[owner]["nodes"]}
    nodes[cycle_a]["dependencies"] = [cycle_b]
    nodes[cycle_b]["dependencies"] = [cycle_a]
    with pytest.raises(module.ArchitectureDocsError, match="cyclic LEGO dependencies"):
        module.validate_formal_issue_census(census, plans)


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("dangling", "unknown LEGO dependency"),
        ("duplicate_edge", "duplicate LEGO dependency"),
        ("duplicate_node", "duplicate LEGO node identity"),
        ("untyped_dependencies", "untyped LEGO dependencies"),
    ],
)
def test_formal_lego21_runtime_dependency_relation_is_typed(
    mutation: str, reason: str
) -> None:
    census, plans = formal_issue_inputs()
    nodes = plans["services/runtime/planning/lego-plan-r1.json"]["nodes"]
    node = next(n for n in nodes if n["id"] == "R01")
    if mutation == "dangling":
        node["dependencies"] = ["NONEXISTENT"]
    elif mutation == "duplicate_edge":
        node["dependencies"] = ["R00", "R00"]
    elif mutation == "duplicate_node":
        nodes.append(copy.deepcopy(nodes[0]))
    else:
        node["dependencies"] = "R00"
    with pytest.raises(module.ArchitectureDocsError, match=reason):
        module.validate_formal_issue_census(census, plans)


def test_recursive_lego_r21_source_digest_matches_current_declared_contract() -> None:
    """A referenced formal source must exist and match its exact declared provenance."""
    document = (
        ROOT / "docs/architecture/AGENT_CONCEPTS_FORMAL_LEGO_RESEARCH_20261024.md"
    ).read_text(encoding="utf-8")
    declared = re.search(r"observed model SHA-256 .([0-9a-f]{64}).", document)
    assert declared is not None, "R2.1 declaration must bind a source digest"

    skill_root = ROOT / ".agents/skills/recursive-lego-calculus"
    skill = skill_root / "SKILL.md"
    reference = skill_root / "references/formal-model.md"
    assert skill.is_file() and reference.is_file(), (
        "R2.1 original Skill/model disappeared while the live architecture names it"
    )
    assert "name: recursive-lego-calculus" in skill.read_text(encoding="utf-8")
    assert hashlib.sha256(reference.read_bytes()).hexdigest() == declared.group(1)



def test_formal_r21_empty_host_owner_graph_must_not_pass_owner_admission() -> None:
    """Host R1 is a declared 2.1 Owner; an empty DAG cannot witness its five contracts."""
    plan = json.loads((ROOT / "services/host/planning/lego-plan-r1.json").read_text())
    plan["nodes"] = []
    plan["edges"] = []
    plan["slices"] = []
    with pytest.raises(module.ArchitectureDocsError, match="empty LEGO owner graph"):
        module.validate_owner_lego_dependencies(plan, "services/host")


def test_formal_r21_empty_harness_graph_must_not_pass_registered_census() -> None:
    """Census links may not bless empty Owner graph after its node list was erased."""
    census, plans = formal_issue_inputs()
    owner = "services/harness/planning/lego-plan-r1.json"
    plans[owner]["nodes"] = []
    plans[owner]["edges"] = []
    with pytest.raises(module.ArchitectureDocsError, match="empty LEGO owner graph"):
        module.validate_formal_issue_census(census, plans)


def test_r21_single_six_role_contract_enforced_at_repository_admission() -> None:
    """R2.1 semantic lenses must never silently replace the original LEGO interface."""
    vocabulary = (
        ROOT / "docs/architecture/AGENT_CONCEPTS_FORMAL_LEGO_RESEARCH_20261024.md"
    ).read_text(encoding="utf-8")
    module.validate_r21_lego_vocabulary(vocabulary)
    canonical = "L = (identity, responsibility, inputs, outputs, contract, acceptance)"
    assert vocabulary.count(canonical) == 1

    with pytest.raises(module.ArchitectureDocsError, match="canonical"):
        module.validate_r21_lego_vocabulary(vocabulary.replace(canonical, "L=(C,I,O,S,R,A,G,V)"))
    with pytest.raises(module.ArchitectureDocsError, match="competing"):
        module.validate_r21_lego_vocabulary(
            vocabulary + "\nL = (I, O, A, G, E, V)\n"
        )
    with pytest.raises(module.ArchitectureDocsError, match="consumer"):
        module.validate_r21_lego_vocabulary(
            vocabulary.replace(
                "services/host/tests/test_social_work_fabric_postgres.py",
                "services/host/tests/test_unverified_nonexistent_contract.py",
            )
        )


@pytest.mark.parametrize(
    ("relative", "target", "predecessor"),
    [
        ("services/runtime/planning/lego-plan-r1.json", "R00", "R01"),
        ("services/harness/planning/lego-plan-r1.json", "H01", "H02"),
        ("platform/network/planning/lego-plan-r1.json", "N05", "N02"),
    ],
)
def test_r21_repository_always_checks_core_owner_prerequisites(
    relative: str, target: str, predecessor: str
) -> None:
    """An Owner's validity is independent of time-scoped issue registrations."""
    plan = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    node = next(row for row in plan["nodes"] if row["id"] == target)
    # Close the existing typed predecessor path into an invalid cycle.
    node["dependencies"].append(predecessor)
    if relative == "services/harness/planning/lego-plan-r1.json":
        # H05 had no admitted alternate executor, so its speculative dependency
        # is retired. Falsify the exact same owner graph verifier by synthesizing
        # two opposite prerequisites between remaining, real H01/H02 nodes.
        partner = next(row for row in plan["nodes"] if row["id"] == predecessor)
        partner["dependencies"].append(target)
    loader = module._load_json

    def mutated_owner(path: Path):
        if Path(path) == ROOT / relative:
            return plan
        return loader(path)

    # Disable only the optional census consumer to prove the main admission
    # gate itself checks every registered native Owner.
    with patch.object(module, "_load_json", side_effect=mutated_owner), patch.object(
        module, "validate_formal_issue_census", return_value=None
    ):
        with pytest.raises(module.ArchitectureDocsError, match="cyclic LEGO dependencies"):
            module.validate_repository(ROOT)
