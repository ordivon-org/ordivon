from __future__ import annotations

import asyncio
from typing import Any

from ordivon_gateway.capability_projection import (
    project_capability_search,
    project_execution_capability,
)
from ordivon_gateway.contracts import CapabilityDescriptor, CapabilityProjection
from ordivon_gateway.routes import default_routes
from ordivon_gateway.service import GatewayService


class ProjectionCaller:
    def __init__(
        self,
        responses: dict[tuple[str, str], dict[str, Any]],
        configured: set[str],
        configuration_errors: dict[str, str] | None = None,
    ) -> None:
        self.responses = responses
        self.configured = configured
        self.configuration_errors = configuration_errors or {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def is_configured(self, owner_id: str) -> bool:
        return owner_id in self.configured

    def configuration_error(self, owner_id: str) -> str | None:
        return self.configuration_errors.get(owner_id)

    async def call_tool(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append((owner_id, tool_name, arguments))
        return self.responses[(owner_id, tool_name)]


def test_capability_projection_rebuilds_from_runtime_owner_truth() -> None:
    caller = ProjectionCaller(
        {
            ("runtime.linux", "runtime.describe"): {
                "schemaVersion": 1,
                "node": {"nodeId": "linux-local", "platform": "linux", "native": True},
                "targets": [
                    {
                        "target": "local_linux",
                        "configured": True,
                        "available": True,
                        "executionProfiles": ["trusted_local", "contained_local"],
                        "structuredPlan": True,
                        "immutableInputs": True,
                        "hostDependencyCommitments": True,
                    }
                ],
            },
            ("runtime.windows", "runtime.describe"): {
                "schemaVersion": 1,
                "node": {
                    "nodeId": "windows-main-r6-candidate",
                    "platform": "windows",
                    "native": True,
                },
                "targets": [
                    {
                        "target": "windows_native",
                        "configured": True,
                        "available": True,
                        "executionProfiles": ["trusted_local"],
                        "windowsAuthorities": ["limited", "elevated", "active_user"],
                        "windowsContexts": [
                            {"identity": "service", "privilege": "limited"},
                            {"identity": "service", "privilege": "elevated"},
                            {"identity": "active_user", "privilege": "limited"},
                            {"identity": "active_user", "privilege": "elevated"},
                        ],
                        "structuredPlan": True,
                        "immutableInputs": True,
                        "hostDependencyCommitments": False,
                    }
                ],
            },
            ("host", "host.status"): {
                "schemaVersion": 3,
                "kind": "ordivon.host-status",
            },
        },
        {"runtime.linux", "runtime.windows", "host"},
    )
    service = GatewayService(caller)

    projection = asyncio.run(service.capability_describe())

    by_id = {item.capability: item for item in projection.capabilities}
    linux = by_id["execution.linux"]
    assert linux.configured is True
    assert linux.available is True
    assert linux.contexts == ["trusted_local", "contained_local"]
    assert linux.owner_node_id == "linux-local"

    windows = by_id["execution.windows"]
    assert windows.available is True
    assert windows.context_mode == "provider-defined-json"
    assert windows.contexts == [
        {"identity": "service", "privilege": "limited"},
        {"identity": "service", "privilege": "elevated"},
        {"identity": "active_user", "privilege": "limited"},
        {"identity": "active_user", "privilege": "elevated"},
    ]
    assert windows.owner_node_id == "windows-main-r6-candidate"

    continuity = by_id["continuity.external"]
    assert continuity.available is True
    assert continuity.contexts == []

    artifact = by_id["artifact.runtime"]
    assert artifact.available is True
    assert sorted(artifact.owner_node_ids) == [
        "linux-local",
        "windows-main-r6-candidate",
    ]

    assert projection.projection_digest.startswith("sha256:")
    assert len(projection.projection_digest) == 71


def test_unconfigured_owner_is_visible_without_probe() -> None:
    caller = ProjectionCaller(
        {
            ("runtime.linux", "runtime.describe"): {
                "schemaVersion": 1,
                "node": {"nodeId": "linux-local", "platform": "linux", "native": True},
                "targets": [
                    {
                        "target": "local_linux",
                        "configured": True,
                        "available": True,
                        "executionProfiles": ["trusted_local"],
                    }
                ],
            },
        },
        {"runtime.linux"},
    )
    service = GatewayService(caller)

    projection = asyncio.run(service.capability_describe("execution.windows"))
    item = projection.capabilities[0]

    assert item.capability == "execution.windows"
    assert item.configured is False
    assert item.available is False
    assert item.contexts == []
    assert caller.calls == []


def test_missing_runtime_identity_is_projected_as_not_configured_not_owner_down() -> None:
    caller = ProjectionCaller(
        {},
        set(),
        {"runtime.windows": "owner authentication is not configured"},
    )
    service = GatewayService(caller)

    projection = asyncio.run(service.capability_describe("execution.windows"))
    item = projection.capabilities[0]

    assert item.configured is False
    assert item.available is False
    assert item.observation_error == "owner authentication is not configured"
    assert caller.calls == []


def test_projection_digest_is_deterministic_for_same_owner_truth() -> None:
    response = {
        ("runtime.linux", "runtime.describe"): {
            "schemaVersion": 1,
            "node": {"nodeId": "linux-local", "platform": "linux", "native": True},
            "targets": [
                {
                    "target": "local_linux",
                    "configured": True,
                    "available": True,
                    "executionProfiles": ["trusted_local", "contained_local"],
                }
            ],
        },
    }
    service_a = GatewayService(ProjectionCaller(response, {"runtime.linux"}))
    service_b = GatewayService(ProjectionCaller(response, {"runtime.linux"}))

    a = asyncio.run(service_a.capability_describe("execution.linux"))
    b = asyncio.run(service_b.capability_describe("execution.linux"))

    assert a.projection_digest == b.projection_digest


def test_capability_projection_includes_source_owned_discovery_metadata() -> None:
    caller = ProjectionCaller({}, set())
    projection = asyncio.run(GatewayService(caller).capability_describe("execution.linux"))
    item = projection.capabilities[0]
    assert item.description == "Execute bounded physical work through the Linux Runtime owner."
    assert item.tags == ["execution", "job", "linux", "runtime", "workspace"]
    assert not hasattr(item, "authorized")
    assert not hasattr(item, "callable")


def test_capability_search_is_deterministic_bounded_discovery_not_authorization() -> None:
    caller = ProjectionCaller(
        {
            ("runtime.linux", "runtime.describe"): {
                "schemaVersion": 1,
                "node": {"nodeId": "linux-local", "platform": "linux", "native": True},
                "targets": [
                    {
                        "target": "local_linux",
                        "configured": True,
                        "available": True,
                        "executionProfiles": ["trusted_local"],
                    }
                ],
            },
            ("runtime.windows", "runtime.describe"): {
                "schemaVersion": 1,
                "node": {"nodeId": "windows-local", "platform": "windows", "native": True},
                "targets": [
                    {
                        "target": "windows_native",
                        "configured": True,
                        "available": True,
                        "executionProfiles": ["trusted_local"],
                        "windowsAuthorities": ["limited"],
                    }
                ],
            },
            ("host", "host.status"): {"schemaVersion": 3, "kind": "ordivon.host-status"},
        },
        {"runtime.linux", "runtime.windows", "host"},
    )
    service = GatewayService(caller)

    exact = asyncio.run(service.capability_search(query="execution.linux"))
    assert exact.total_matches == 1
    assert exact.matches[0].match_kind == "exact"
    assert exact.matches[0].capability.capability == "execution.linux"

    token = asyncio.run(service.capability_search(query="runtime windows", category="execution"))
    assert token.total_matches == 1
    assert token.matches[0].match_kind == "token"
    assert token.matches[0].capability.capability == "execution.windows"

    filtered = asyncio.run(
        service.capability_search(query="runtime", owner_id="runtime.linux", limit=1)
    )
    assert filtered.total_matches == 1
    assert [match.capability.capability for match in filtered.matches] == ["execution.linux"]
    assert filtered.projection_digest.startswith("sha256:")

    owner_tools = [tool for _, tool, _ in caller.calls]
    assert owner_tools
    assert set(owner_tools).issubset({"runtime.describe", "host.status"})
    assert "workspace.exec" not in owner_tools
    assert "job.list" not in owner_tools


def test_capability_search_does_not_misclassify_observation_error_as_proven_unavailable() -> None:
    class FailingCaller(ProjectionCaller):
        async def call_tool(
            self, owner_id: str, tool_name: str, arguments: dict[str, Any]
        ) -> dict[str, Any]:
            self.calls.append((owner_id, tool_name, arguments))
            raise RuntimeError("synthetic transport observation failure")

    caller = FailingCaller({}, {"runtime.linux"})
    result = asyncio.run(
        GatewayService(caller).capability_search(
            query="linux",
            owner_id="runtime.linux",
            include_unavailable=False,
        )
    )
    assert result.total_matches == 1
    item = result.matches[0].capability
    assert item.available is False
    assert item.observation_error is not None
    assert "synthetic transport observation failure" in item.observation_error


def test_capability_search_rejects_invalid_bounds_without_owner_calls() -> None:
    caller = ProjectionCaller({}, set())
    service = GatewayService(caller)
    import pytest

    with pytest.raises(Exception, match="trimmed"):
        asyncio.run(service.capability_search(query=" linux"))
    with pytest.raises(Exception, match="between 1 and 50"):
        asyncio.run(service.capability_search(query="linux", limit=0))
    assert caller.calls == []


def test_execution_descriptor_is_pure_and_preserves_owner_observation() -> None:
    route = default_routes()["execution.windows"]
    owner_response = {
        "node": {"nodeId": "Windows-A"},
        "targets": [
            {
                "target": "windows_native",
                "configured": True,
                "available": True,
                "windowsContexts": [{"identity": "active_user", "privilege": "limited"}, "invalid"],
                "windowsAuthorities": ["limited"],
            }
        ],
    }
    original = {
        "node": dict(owner_response["node"]),
        "targets": [
            {
                key: (list(value) if isinstance(value, list) else value)
                for key, value in owner_response["targets"][0].items()
            }
        ],
    }
    descriptor = project_execution_capability(
        route,
        configured_at_gateway=True,
        owner_response=owner_response,
    )
    assert descriptor.available is True
    assert descriptor.context_mode == "provider-defined-json"
    assert descriptor.contexts == [{"identity": "active_user", "privilege": "limited"}]
    assert descriptor.owner_node_id == "Windows-A"
    assert owner_response == original


def test_projection_preserves_unconfigured_and_missing_target_distinction() -> None:
    route = default_routes()["execution.linux"]
    unconfigured = project_execution_capability(
        route,
        configured_at_gateway=False,
        owner_response={"targets": [{"target": "local_linux", "available": True}]},
        configuration_error="not installed",
    )
    assert not unconfigured.configured
    assert not unconfigured.available
    assert unconfigured.observation_error == "not installed"
    unavailable = project_execution_capability(
        route,
        configured_at_gateway=True,
        owner_response=None,
        observation_error="read timeout",
    )
    assert unavailable.configured
    assert not unavailable.available
    assert unavailable.observation_error == "read timeout"
    mismatched = project_execution_capability(
        route,
        configured_at_gateway=True,
        owner_response={"targets": [{"target": "windows_native"}]},
    )
    assert not mismatched.configured
    assert mismatched.observation_error == "owner did not advertise the routed execution target"


def test_pure_search_projection_preserves_ranked_contract_and_unknown_truth() -> None:
    def descriptor(
        name: str,
        *,
        description: str = "",
        available: bool = True,
        observation_error: str | None = None,
    ) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            capability=name,
            owner_id="runtime.linux",
            category="execution",
            configured=True,
            available=available,
            context_mode="none",
            truth_boundary="non-authoritative-test-observation",
            description=description,
            observation_error=observation_error,
        )

    projection = CapabilityProjection(
        projection_digest="sha256:" + "a" * 64,
        capabilities=[
            descriptor("service.record", description="linuxish"),
            descriptor("linux-unknown", available=False, observation_error="observer timed out"),
            descriptor("plugin.audit", description="needs linux agent"),
            descriptor("linux"),
            descriptor("linux-prefix"),
            descriptor("linux-rejected", available=False),
        ],
    )
    original_bytes = projection.model_dump_json()
    result = project_capability_search(
        projection,
        query="linux",
        category="execution",
        owner_id="runtime.linux",
        limit=4,
        include_unavailable=False,
    )

    assert result.total_matches == 5
    assert [(m.match_kind, m.capability.capability) for m in result.matches] == [
        ("exact", "linux"),
        ("prefix", "linux-prefix"),
        ("prefix", "linux-unknown"),
        ("token", "plugin.audit"),
    ]
    assert result.matches[2].capability.available is False
    assert result.matches[2].capability.observation_error == "observer timed out"
    assert result.projection_digest == projection.projection_digest
    assert projection.model_dump_json() == original_bytes
    assert (
        project_capability_search(
            projection,
            query="linux",
            category="execution",
            owner_id=None,
            limit=10,
            include_unavailable=True,
        ).total_matches
        == 6
    )


def test_pure_search_projection_does_not_confer_execution_authority() -> None:
    projection = CapabilityProjection(
        projection_digest="sha256:" + "b" * 64,
        capabilities=[
            CapabilityDescriptor(
                capability="execution.linux",
                owner_id="runtime.linux",
                category="execution",
                configured=False,
                available=False,
                context_mode="none",
                truth_boundary="projection only",
                observation_error="owner unavailable",
            )
        ],
    )
    result = project_capability_search(
        projection,
        query="execution.linux",
        category=None,
        owner_id=None,
        limit=10,
        include_unavailable=False,
    )
    assert result.total_matches == 1
    assert result.truth_role == "rebuildable-non-authoritative-discovery-projection"
    assert result.matches[0].capability.observation_error == "owner unavailable"
