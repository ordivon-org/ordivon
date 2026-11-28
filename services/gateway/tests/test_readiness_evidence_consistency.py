"""The same exact Owner observation must support descriptor and inquiry facts."""

from __future__ import annotations

import asyncio

import pytest

from ordivon_gateway.service import GatewayService


class Caller:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def is_configured(self, owner):
        return owner == "runtime.linux"

    def configuration_error(self, owner):
        return None if self.is_configured(owner) else "not configured"

    async def call_tool(self, owner, tool, args):
        self.calls.append((owner, tool, args))
        return self.response


def response(version=1, **extra):
    return {
        "schemaVersion": version,
        "node": {"nodeId": "linux-pg", "platform": "linux", "native": True},
        "targets": [
            {
                "target": "local_linux",
                "configured": True,
                "available": True,
                "executionProfiles": ["trusted_local"],
            }
        ],
        **extra,
    }


def inquire(value, capability, verify=False):
    caller = Caller(value)
    result = asyncio.run(
        GatewayService(caller).capability_inquire(capability=capability, verify_read_only=verify)
    )
    assert caller.calls == [("runtime.linux", "runtime.describe", {"schemaVersion": 1})] * (
        2 if verify else 1
    )
    return result


def fact(result, predicate, owner="runtime.linux"):
    return [
        f.state for f in result.inquiry.facts if f.owner_id == owner and f.predicate == predicate
    ]


@pytest.mark.parametrize("version", [True, 1.0, "1", 2, None])
def test_artifact_aggregate_cannot_support_ready_from_invalid_envelope(version):
    result = inquire(response(version), "artifact.runtime")
    assert result.readiness_state == "unknown"
    assert fact(result, "owner.any_runtime_target_ready", "runtime.dynamic") == ["unobserved"]


def test_malformed_target_identity_is_not_duplicate_identity():
    result = inquire(
        response(targets=[{"configured": True, "available": True}]), "artifact.runtime"
    )
    assert result.readiness_state == "unknown"
    assert fact(result, "owner.target_identity_unique") == []
    assert fact(result, "owner.target_identity:index-0") == ["invalid"]


def test_release_flag_from_wrong_envelope_is_not_qualified():
    result = inquire(response("1", structuredReleaseConfigured=True), "runtime.release.linux")
    assert result.readiness_state == "unknown"
    assert fact(result, "owner.structured_release_configured") == ["unobserved"]


def test_configured_owner_no_result_is_unknown_not_negative():
    result = inquire(None, "execution.linux", True)
    assert result.readiness_state == "unknown"
    assert fact(result, "owner.status_observed") == ["unobserved"]
    assert result.verification.verdict == "still_unresolved"


def test_release_nonobject_result_is_unknown_and_not_an_exception():
    result = inquire(["not an envelope"], "runtime.release.linux")
    assert result.readiness_state == "unknown"
    assert fact(result, "owner.status_envelope_valid") == ["invalid"]
    assert fact(result, "owner.structured_release_configured") == ["unobserved"]


def test_artifact_configured_owner_no_result_is_unknown():
    result = inquire(None, "artifact.runtime")
    assert result.readiness_state == "unknown"
    assert fact(result, "owner.any_runtime_target_ready", "runtime.dynamic") == ["unobserved"]


def test_only_explicit_inquiry_materializes_diagnostic_evidence(monkeypatch):
    from ordivon_gateway.capabilities import discovery

    actual = discovery.project_readiness_inquiry
    materialized = []

    def record(descriptor, route, **kwargs):
        materialized.append(route.capability)
        return actual(descriptor, route, **kwargs)

    monkeypatch.setattr(discovery, "project_readiness_inquiry", record)
    caller = Caller(response())

    async def run():
        svc = GatewayService(caller)
        await svc.capability_describe()
        await svc.capability_search(query="runtime")
        assert materialized == []
        caller.calls.clear()
        result = await svc.capability_inquire(capability="execution.linux", verify_read_only=True)
        assert materialized == ["execution.linux", "execution.linux"]
        assert len(caller.calls) == 2
        assert result.verification.verdict == "same_owner_observation_stable"

    asyncio.run(run())
