"""The catalog transforms already-observed evidence; no authority or transport."""

from __future__ import annotations

import asyncio
from dataclasses import replace

import pytest

from ordivon_gateway.logic.catalog_identity import route_digest
from ordivon_gateway.logic.catalog_projection import (
    project_artifact_capability,
    project_host_capability,
    project_static_capability,
)
from ordivon_gateway.logic.routing import default_routes
from ordivon_gateway.service import GatewayService


def runtime_response(node_id="linux-pg", *, available=True):
    return {
        "schemaVersion": 1,
        "node": {"nodeId": node_id},
        "targets": [{"target": "local_linux", "configured": True, "available": available}],
    }


def test_catalog_route_identity_is_order_invariant_and_content_bound():
    routes = default_routes()
    assert route_digest(routes) == route_digest(dict(reversed(list(routes.items()))))
    changed = dict(routes)
    changed["execution.linux"] = replace(
        changed["execution.linux"], description="different route identity"
    )
    assert route_digest(routes) != route_digest(changed)


@pytest.mark.parametrize("bad", [[], "not-an-object", 1, True, {"schemaVersion": 1.0}])
def test_artifact_malformed_envelope_cannot_be_promoted_to_ready(bad):
    route = default_routes()["artifact.runtime"]
    result = project_artifact_capability(route, observations=[("runtime.linux", True, bad, None)])
    assert not result.available
    assert result.readiness_state == "unknown"
    assert result.observation_error == "runtime.linux: invalid versioned Runtime status envelope"


def test_artifact_aggregation_preserves_partial_positive_and_error():
    route = default_routes()["artifact.runtime"]
    result = project_artifact_capability(
        route,
        observations=[
            ("runtime.linux", True, runtime_response(), None),
            ("runtime.windows", True, None, "unobserved"),
        ],
    )
    assert result.available and result.configured
    assert result.owner_node_ids == ["linux-pg"]
    assert result.observation_error == "runtime.windows: unobserved"


@pytest.mark.parametrize("version", [True, 3.0, "3", None])
def test_host_requires_exact_versioned_status(version):
    result = project_host_capability(
        default_routes()["continuity.external"],
        configured=True,
        result={"kind": "ordivon.host-status", "schemaVersion": version},
        error=None,
    )
    assert not result.available
    assert result.readiness_state == "unknown"


def test_research_static_metadata_does_not_claim_provider_readiness():
    route = default_routes()["research.citation.metadata"]
    result = project_static_capability(route)
    assert result.configured and not result.available
    assert result.readiness_state == "unknown"


def test_one_observation_per_runtime_owner_and_no_cross_request_status_cache():
    calls = []

    class Caller:
        def is_configured(self, owner):
            return owner == "runtime.linux"

        async def call_tool(self, owner, tool, args):
            calls.append((owner, tool, args))
            return runtime_response(available=len(calls) == 1)

    async def run():
        gateway = GatewayService(Caller())
        first = await gateway.capability_describe()
        second = await gateway.capability_describe()
        first_artifact = next(x for x in first.capabilities if x.capability == "artifact.runtime")
        second_artifact = next(x for x in second.capabilities if x.capability == "artifact.runtime")
        assert first_artifact.available
        assert not second_artifact.available
        assert first.route_digest == second.route_digest
        assert first.projection_digest != second.projection_digest

    asyncio.run(run())
    assert calls == [("runtime.linux", "runtime.describe", {"schemaVersion": 1})] * 2
