from __future__ import annotations

import asyncio
from typing import Any

from ordivon_gateway.service import GatewayService


class ProjectionCaller:
    def __init__(
        self,
        responses: dict[tuple[str, str], dict[str, Any]],
        configured: set[str],
    ) -> None:
        self.responses = responses
        self.configured = configured
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def is_configured(self, owner_id: str) -> bool:
        return owner_id in self.configured

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
