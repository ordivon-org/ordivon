from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "repo" / "check_architecture_docs.py"
GRAPH = ROOT / "docs" / "architecture" / "deployed-architecture-r1.json"

spec = importlib.util.spec_from_file_location("check_architecture_docs", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def graph():
    return json.loads(GRAPH.read_text(encoding="utf-8"))


def test_current_repository_architecture_docs_are_converged() -> None:
    module.validate_repository(ROOT)


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
import sys
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
