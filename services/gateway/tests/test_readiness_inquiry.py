"""Real source inquiry: preserve evidence before grouping as UNKNOWN.

The investigative API performs only the existing read-only Owner status
request. Listed forward/reverse checks are not secretly executed.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp import Client

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.security.http_ingress_guard import GatewayHTTPIngressGuard
from ordivon_gateway.service import GatewayService


class Owners:
    def __init__(self, responses: dict[str, dict[str, Any] | Exception]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def is_configured(self, owner_id: str) -> bool:
        return owner_id in self.responses

    def configuration_error(self, owner_id: str) -> str | None:
        return None if self.is_configured(owner_id) else "owner endpoint is not configured"

    async def call_tool(self, owner_id: str, tool_name: str, arguments: dict[str, Any]) -> dict:
        self.calls.append((owner_id, tool_name, dict(arguments)))
        result = self.responses[owner_id]
        if isinstance(result, Exception):
            raise result
        return dict(result)


def runtime(target: str, *, configured: Any = True, available: Any = True) -> dict:
    return {
        "schemaVersion": 1,
        "node": {"nodeId": "test-runtime"},
        "targets": [
            {
                "target": target,
                "configured": configured,
                "available": available,
                "executionProfiles": ["trusted_local"],
            }
        ],
    }


def facts(value) -> dict[tuple[str, str], str]:
    return {(f.owner_id, f.predicate): f.state for f in value.inquiry.facts}


def test_readiness_ready_proves_target_status_not_physical_job() -> None:
    owners = Owners({"runtime.linux": runtime("local_linux")})
    item = asyncio.run(GatewayService(owners).capability_inquire(capability="execution.linux"))
    assert item.readiness_state == "ready"
    proof = facts(item)
    assert proof["runtime.linux", "owner.status_observed"] == "supported"
    assert proof["runtime.linux", "owner.target_available:local_linux"] == "supported"
    assert proof["runtime.linux", "owner.physical_job_spawned"] == "unobserved"
    assert any(
        c.direction == "forward"
        and c.action == "workspace.exec"
        and c.effect == "requires_authorized_context"
        for c in item.inquiry.next_checks
    )
    assert owners.calls == [("runtime.linux", "runtime.describe", {"schemaVersion": 1})]


def test_runtime_timeout_has_two_nonasserted_hypotheses_and_a_readonly_recheck() -> None:
    owners = Owners({"runtime.windows": TimeoutError("no response")})
    inquiry = asyncio.run(GatewayService(owners).capability_inquire(capability="execution.windows"))
    assert inquiry.readiness_state == "unknown"
    assert facts(inquiry)["runtime.windows", "owner.status_observed"] == "unobserved"
    assert len(inquiry.inquiry.possible_explanations) >= 2
    assert any(
        c.direction == "reverse"
        and c.action == "runtime.describe"
        and c.request == {"schemaVersion": 1}
        for c in inquiry.inquiry.next_checks
    )
    assert owners.calls == [("runtime.windows", "runtime.describe", {"schemaVersion": 1})]


def test_contradictory_runtime_data_does_not_coerce_truthiness() -> None:
    owners = Owners(
        {
            "runtime.windows": runtime(
                "windows_native",
                configured=False,
                available=True,
            )
        }
    )
    inquiry = asyncio.run(GatewayService(owners).capability_inquire(capability="execution.windows"))
    proof = facts(inquiry)
    assert inquiry.readiness_state == "unknown"
    assert proof["runtime.windows", "owner.target_configured:windows_native"] == "refuted"
    assert proof["runtime.windows", "owner.target_available:windows_native"] == "supported"
    assert proof["runtime.windows", "owner.target_consistent:windows_native"] == "contradictory"
    assert any(
        c.action == "runtime.describe" and c.effect == "read_only"
        for c in inquiry.inquiry.next_checks
    )


def test_invalid_bool_is_invalid_not_false_or_owner_unavailable() -> None:
    owners = Owners(
        {
            "runtime.windows": runtime(
                "windows_native",
                configured="true",
                available=True,
            )
        }
    )
    inquiry = asyncio.run(GatewayService(owners).capability_inquire(capability="execution.windows"))
    assert inquiry.readiness_state == "unknown"
    assert facts(inquiry)["runtime.windows", "owner.target_configured:windows_native"] == "invalid"


def test_local_owner_configuration_failure_is_not_claim_owner_failure() -> None:
    owners = Owners({})
    inquiry = asyncio.run(GatewayService(owners).capability_inquire(capability="execution.linux"))
    proof = facts(inquiry)
    assert inquiry.readiness_state == "unknown"
    assert proof["runtime.linux", "gateway.owner_endpoint_qualified"] == "refuted"
    assert proof["runtime.linux", "owner.status_observed"] == "unobserved"
    assert any(
        c.direction == "forward" and c.action == "inspect_owner_configuration"
        for c in inquiry.inquiry.next_checks
    )
    assert owners.calls == []


def test_artifact_multi_owner_keeps_success_and_unknown_on_separate_facets() -> None:
    owners = Owners(
        {
            "runtime.linux": runtime("local_linux"),
            "runtime.windows": TimeoutError("status deadline"),
        }
    )
    inquiry = asyncio.run(GatewayService(owners).capability_inquire(capability="artifact.runtime"))
    proof = facts(inquiry)
    assert inquiry.readiness_state == "ready"
    assert inquiry.inquiry.scope == "multi_owner_status"
    assert proof["runtime.linux", "owner.target_available:local_linux"] == "supported"
    assert proof["runtime.windows", "owner.status_observed"] == "unobserved"
    assert proof["runtime.dynamic", "artifact.bytes_retrievable"] == "unobserved"
    assert {row[0] for row in owners.calls} == {"runtime.linux", "runtime.windows"}
    assert all(row[1] == "runtime.describe" for row in owners.calls)


def test_duplicate_runtime_target_does_not_make_artifact_aggregate_ready() -> None:
    duplicate = runtime("local_linux")
    duplicate["targets"].append(dict(duplicate["targets"][0]))
    owners = Owners({"runtime.linux": duplicate})
    inquiry = asyncio.run(GatewayService(owners).capability_inquire(capability="artifact.runtime"))
    proof = facts(inquiry)
    assert inquiry.readiness_state == "unknown"
    assert proof["runtime.linux", "owner.target_identity_unique"] == "contradictory"
    assert proof["runtime.dynamic", "owner.any_runtime_target_ready"] == "unobserved"
    assert any(
        c.direction == "reverse" and c.action == "runtime.describe"
        for c in inquiry.inquiry.next_checks
    )
    assert owners.calls == [("runtime.linux", "runtime.describe", {"schemaVersion": 1})]


def test_host_status_read_does_not_establish_work_get_permission() -> None:
    owners = Owners({"host": {"schemaVersion": 3, "kind": "ordivon.host-status"}})
    inquiry = asyncio.run(
        GatewayService(owners).capability_inquire(capability="continuity.external")
    )
    assert inquiry.readiness_state == "ready"
    proof = facts(inquiry)
    assert proof["host", "host.status_envelope_valid"] == "supported"
    assert proof["host", "host.specific_work_read_authorized"] == "unobserved"
    assert owners.calls == [("host", "host.status", {"detail": "summary"})]


def test_research_inquiry_does_not_perform_external_owner_effect() -> None:
    owners = Owners({})
    result = asyncio.run(
        GatewayService(owners).capability_inquire(
            capability="research.statistical.analysis",
        )
    )
    assert result.readiness_state == "unknown"
    assert facts(result)["research.composition", "research.provider_effect_ready"] == "unobserved"
    assert any(
        c.direction == "reverse" and c.action == "verify_domain_evidence"
        for c in result.inquiry.next_checks
    )
    assert owners.calls == []


def test_release_inquiry_separates_configuration_installation_and_grant() -> None:
    response = runtime("local_linux")
    response["node"] = {"nodeId": "linux-pg", "platform": "linux", "native": True}
    response["structuredReleaseConfigured"] = True
    owners = Owners({"runtime.linux": response})
    inquiry = asyncio.run(
        GatewayService(owners).capability_inquire(capability="runtime.release.linux")
    )
    assert inquiry.readiness_state == "unknown"
    proof = facts(inquiry)
    assert proof["runtime.linux", "owner.structured_release_configured"] == "supported"
    assert proof["runtime.linux", "installed_gateway_release_tool"] == "unobserved"
    assert proof["runtime.linux", "verified_principal_effect_permission"] == "unobserved"
    assert not any(name != "runtime.describe" for _, name, _ in owners.calls)


def test_native_mcp_inquiry_validates_and_legacy_tool_schema_digest_is_identical() -> None:
    # Source verification, not any installed Gateway release.
    async def scenario() -> None:
        owners = Owners({})
        async with Client(build_server(GatewayService(owners)), raise_exceptions=True) as client:
            tools = (await client.list_tools()).tools
            listed = {t.name for t in tools}
            assert "capability.inquire" in listed
            response = await client.call_tool(
                "capability.inquire", {"capability": "research.statistical.analysis"}
            )
            assert response.is_error is False
            content = response.structured_content
            assert content["kind"] == "ordivon.gateway-capability-inquiry"
            assert content["inquiry"]["facts"][0]["state"] == "supported"
            assert content["inquiry"]["next_checks"]
            assert owners.calls == []

            # Compute the original real SDK Tool schemas, not manually mirrored
            # names/inputs. Only one NEW tool is allowed; the old ABI stays exact.
            import hashlib

            previous = [
                t.model_dump(mode="json", by_alias=True, exclude_none=True)
                for t in tools
                if t.name != "capability.inquire"
            ]
            records = [
                {
                    "name": t["name"],
                    "inputSchema": t["inputSchema"],
                    "outputSchema": t.get("outputSchema"),
                }
                for t in previous
            ]
            canonical = json.dumps(
                sorted(records, key=lambda r: r["name"]),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            digest = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
            assert (
                digest == "sha256:b60a50c2371ff6afd6ba0714f71f308b4d07ed19b9aaf0cb19e8b27790abd9f3"
            )

    asyncio.run(scenario())


def test_inquiry_is_not_anonymous_http_metadata() -> None:
    from types import SimpleNamespace

    guard = GatewayHTTPIngressGuard()
    ctx = SimpleNamespace(
        method="tools/call",
        params={"name": "capability.inquire", "arguments": {"capability": "execution.linux"}},
        request=SimpleNamespace(scope={"state": {}}),
    )

    async def next_handler(_context):
        raise AssertionError("unverified caller must not reach inquiry")

    result = asyncio.run(guard(ctx, next_handler))
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "HTTP_INGRESS_IDENTITY_MISSING"
