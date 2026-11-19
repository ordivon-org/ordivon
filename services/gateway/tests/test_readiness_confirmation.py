"""Explicit read-only confirmation: actual second observations, never disguised effects."""

from __future__ import annotations

import asyncio
from collections import Counter
from typing import Any

import pytest
from mcp import Client

from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService


def runtime(target: str, *, configured: Any = True, available: Any = True) -> dict:
    return {
        "schemaVersion": 1,
        "node": {"nodeId": "test-native"},
        "targets": [{"target": target, "configured": configured, "available": available}],
    }


class SequencedOwners:
    def __init__(self, observations: dict[str, list[dict | Exception]]) -> None:
        self.observations = observations
        self.calls: list[tuple[str, str, dict]] = []

    def is_configured(self, owner_id: str) -> bool:
        return owner_id in self.observations

    def configuration_error(self, owner_id: str) -> str | None:
        return None if self.is_configured(owner_id) else "owner endpoint missing"

    async def call_tool(self, owner_id: str, tool_name: str, arguments: dict) -> dict:
        assert tool_name in {"runtime.describe", "host.status"}
        self.calls.append((owner_id, tool_name, dict(arguments)))
        queued = self.observations[owner_id]
        item = queued.pop(0)
        if isinstance(item, Exception):
            raise item
        return dict(item)


def probe(service: GatewayService, capability: str, *, confirm: bool):
    return asyncio.run(
        service.capability_inquire(
            capability=capability,
            verify_read_only=confirm,
        )
    )


def test_default_does_one_status_read_and_has_no_confirmation() -> None:
    owners = SequencedOwners({"runtime.linux": [runtime("local_linux"), runtime("local_linux")]})
    result = probe(GatewayService(owners), "execution.linux", confirm=False)
    assert result.verification is None
    assert result.readiness_state == "ready"
    assert owners.calls == [("runtime.linux", "runtime.describe", {"schemaVersion": 1})]


def test_one_explicit_readonly_recheck_recovers_initial_timeout_and_retains_both() -> None:
    owners = SequencedOwners(
        {"runtime.windows": [TimeoutError("first call lost"), runtime("windows_native")]}
    )
    result = probe(GatewayService(owners), "execution.windows", confirm=True)
    assert result.readiness_state == "ready"
    evidence = result.verification
    assert evidence is not None
    assert evidence.initial_readiness_state == "unknown"
    assert evidence.verdict == "changed_observation"
    assert evidence.receipts[0].outcome == "result_observed"
    assert evidence.receipts[0].execution_state == "attempted_read_only"
    assert any(
        item.predicate == "owner.status_observed"
        and item.previous_states == ["unobserved"]
        and item.current_states == ["supported"]
        for item in evidence.fact_changes
    )
    assert any(
        f.predicate == "owner.status_observed" and f.state == "unobserved"
        for f in evidence.initial_inquiry.facts
    )
    assert Counter(call[1] for call in owners.calls) == {"runtime.describe": 2}
    assert all(call[2] == {"schemaVersion": 1} for call in owners.calls)


def test_raw_owner_json_witness_changes_even_when_legacy_projection_is_identical() -> None:
    first = runtime("local_linux")
    last = runtime("local_linux")
    # These are opaque Owner fields, never part of Gateway's public readiness
    # projection. They still deserve a digest-level change signal.
    first["opaqueNativeDiagnostic"] = {"detail": "first-internal-tag"}
    last["opaqueNativeDiagnostic"] = {"detail": "changed-internal-tag"}
    owners = SequencedOwners({"runtime.linux": [first, last]})
    result = probe(GatewayService(owners), "execution.linux", confirm=True)
    verified = result.verification
    assert verified is not None
    assert verified.verdict == "changed_observation"
    assert verified.initial_projection_digest == verified.latest_projection_digest
    assert verified.fact_changes == []
    receipt = verified.receipts[0]
    assert receipt.first_payload_digest != receipt.latest_payload_digest
    assert receipt.first_payload_digest.startswith("sha256:")
    assert receipt.latest_payload_digest.startswith("sha256:")
    payload = result.model_dump_json()
    assert "first-internal-tag" not in payload
    assert "changed-internal-tag" not in payload
    assert result.inquiry.observations[0].payload_digest == receipt.latest_payload_digest
    assert verified.initial_inquiry.observations[0].payload_digest == receipt.first_payload_digest


def test_two_timeouts_are_unresolved_not_certified_offline() -> None:
    owners = SequencedOwners(
        {
            "runtime.windows": [
                TimeoutError("first"),
                TimeoutError("second"),
            ]
        }
    )
    result = probe(GatewayService(owners), "execution.windows", confirm=True)
    verification = result.verification
    assert verification is not None
    assert result.readiness_state == "unknown"
    assert verification.verdict == "still_unresolved"
    assert verification.receipts[0].outcome == "no_result"
    assert verification.receipts[0].first_payload_digest is None
    assert verification.receipts[0].latest_payload_digest is None
    assert verification.initial_readiness_state == "unknown"
    assert len(owners.calls) == 2


def test_same_owner_repeated_ready_status_does_not_claim_physical_job_started() -> None:
    owners = SequencedOwners(
        {
            "runtime.linux": [
                runtime("local_linux"),
                runtime("local_linux"),
            ]
        }
    )
    result = probe(GatewayService(owners), "execution.linux", confirm=True)
    verified = result.verification
    assert verified is not None
    assert verified.verdict == "same_owner_observation_stable"
    assert verified.fact_changes == []
    assert verified.initial_projection_digest == verified.latest_projection_digest
    assert "same_owner" in verified.receipts[0].evidence_source
    assert any(
        f.predicate == "owner.physical_job_spawned" and f.state == "unobserved"
        for f in result.inquiry.facts
    )
    assert all(name == "runtime.describe" for _, name, _ in owners.calls)


def test_first_ready_second_malformed_status_is_regression_not_success() -> None:
    owners = SequencedOwners(
        {
            "runtime.windows": [
                runtime("windows_native"),
                runtime("windows_native", configured="true"),
            ]
        }
    )
    result = probe(GatewayService(owners), "execution.windows", confirm=True)
    assert result.readiness_state == "unknown"
    verification = result.verification
    assert verification is not None
    assert verification.initial_readiness_state == "ready"
    assert verification.verdict == "changed_observation"
    assert verification.receipts[0].outcome == "invalid_result"
    assert any(
        c.predicate == "owner.target_configured:windows_native" and c.current_states == ["invalid"]
        for c in verification.fact_changes
    )


def test_artifact_probes_each_natural_owner_once_per_round_and_never_reads_artifacts() -> None:
    owners = SequencedOwners(
        {
            "runtime.linux": [runtime("local_linux"), runtime("local_linux")],
            "runtime.windows": [TimeoutError("offline?"), runtime("windows_native")],
        }
    )
    result = probe(GatewayService(owners), "artifact.runtime", confirm=True)
    assert result.readiness_state == "ready"
    verification = result.verification
    assert verification is not None
    assert verification.verdict == "changed_observation"
    assert [row.owner_id for row in verification.receipts] == ["runtime.linux", "runtime.windows"]
    assert all(row.action == "runtime.describe" for row in verification.receipts)
    assert Counter((owner, name) for owner, name, _ in owners.calls) == {
        ("runtime.linux", "runtime.describe"): 2,
        ("runtime.windows", "runtime.describe"): 2,
    }
    assert any(
        f.predicate == "artifact.bytes_retrievable" and f.state == "unobserved"
        for f in result.inquiry.facts
    )


def test_no_configured_owner_never_calls_remote_status_even_under_confirmation() -> None:
    owners = SequencedOwners({})
    result = probe(GatewayService(owners), "execution.linux", confirm=True)
    assert result.verification is not None
    assert result.verification.receipts[0].outcome == "skipped_unconfigured"
    assert result.verification.receipts[0].execution_state == "not_executed"
    assert result.verification.verdict == "no_qualified_probe"
    assert owners.calls == []


def test_host_recheck_is_status_only_and_never_claims_work_authorized() -> None:
    host = {"schemaVersion": 3, "kind": "ordivon.host-status"}
    owners = SequencedOwners({"host": [host, host]})
    result = probe(GatewayService(owners), "continuity.external", confirm=True)
    assert result.readiness_state == "ready"
    assert result.verification is not None
    assert result.verification.receipts[0].action == "host.status"
    assert owners.calls == [("host", "host.status", {"detail": "summary"})] * 2
    assert any(
        row.predicate == "host.specific_work_read_authorized" and row.state == "unobserved"
        for row in result.inquiry.facts
    )


def test_research_has_no_owner_status_probe_and_no_effect_or_fake_receipt() -> None:
    owners = SequencedOwners({})
    result = probe(GatewayService(owners), "research.statistical.analysis", confirm=True)
    assert result.verification is not None
    assert result.verification.verdict == "no_qualified_probe"
    assert result.verification.receipts == []
    assert result.verification.initial_inquiry == result.inquiry
    assert owners.calls == []


def test_release_recheck_keeps_unobserved_security_grant_and_receipt() -> None:
    result = runtime("local_linux")
    result["node"] = {"nodeId": "linux-pg", "native": True, "platform": "linux"}
    result["structuredReleaseConfigured"] = True
    owners = SequencedOwners({"runtime.linux": [result, result]})
    value = probe(GatewayService(owners), "runtime.release.linux", confirm=True)
    assert value.verification is not None
    assert len(owners.calls) == 2
    assert all(call[1] == "runtime.describe" for call in owners.calls)
    for predicate in (
        "verified_principal_effect_permission",
        "runtime_release_admission_and_receipt",
    ):
        assert any(
            f.predicate == predicate and f.state == "unobserved" for f in value.inquiry.facts
        )


@pytest.mark.parametrize("not_bool", [None, "true", 1, [], {}])
def test_verification_requires_exact_boolean_not_python_truthiness(not_bool: Any) -> None:
    owners = SequencedOwners({"runtime.linux": [runtime("local_linux"), runtime("local_linux")]})
    with pytest.raises(Exception, match="verifyReadOnly"):
        asyncio.run(
            GatewayService(owners).capability_inquire(
                capability="execution.linux", verify_read_only=not_bool
            )
        )
    assert owners.calls == []


def test_real_native_sdk_inquire_confirm_is_typed_and_never_spawns_a_job() -> None:
    async def scenario() -> None:
        owners = SequencedOwners(
            {"runtime.linux": [runtime("local_linux"), runtime("local_linux")]}
        )
        async with Client(build_server(GatewayService(owners)), raise_exceptions=True) as client:
            result = await client.call_tool(
                "capability.inquire",
                {
                    "capability": "execution.linux",
                    "verifyReadOnly": True,
                },
            )
            assert not result.is_error
            content = result.structured_content
            assert content["readiness_state"] == "ready"
            assert content["verification"]["verdict"] == "same_owner_observation_stable"
            assert (
                content["verification"]["receipts"][0]["execution_state"] == "attempted_read_only"
            )
            assert len(owners.calls) == 2
            assert set(action for _, action, _ in owners.calls) == {"runtime.describe"}

    asyncio.run(scenario())
