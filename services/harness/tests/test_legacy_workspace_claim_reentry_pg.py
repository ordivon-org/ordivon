"""Original PostgreSQL Run re-entry under a native Workspace Claim.

These tests exercise the supported HarnessAgentRun.open consumer for older
nonterminal Runs whose original PG Journal predates a native Workspace Claim.
Fake Native transport is a strict test double, NOT proof that Runtime protected
a real old Workspace. Real adoption also requires independently verified
original Workspace provenance, existing physical source, and native readback.
"""
from __future__ import annotations

import uuid

import pytest

from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.runtime_port import HarnessWorkspaceAdmissionUnavailable
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from tests.pg_test_support import FakeNativeWorkspaceClaimClient
from tests.test_r3_supported_agent_run import (
    FakeRuntime, completed, contract, execution_binding, needs_input,
)


class LostReserveReplyClient(FakeNativeWorkspaceClaimClient):
    """Only the first reserve response is lost, after committing the fake claim."""

    def __init__(self):
        super().__init__()
        self.lost_reply = False
        self.reserve_calls = 0

    def call_tool(self, name, arguments):
        if name == "workspace.claim.reserve":
            self.reserve_calls += 1
            result = super().call_tool(name, arguments)
            if not self.lost_reply:
                self.lost_reply = True
                raise ConnectionError("fake native reserve committed; response lost")
            return result
        return super().call_tool(name, arguments)


def _legacy_run(pg_schema):
    dsn, schema = pg_schema
    value = contract("legacy-claim-" + uuid.uuid4().hex[:12], tools=True)
    # Simulate the ORIGINAL independent PG Run already committed by an
    # older Harness version that never used the Native Workspace Claim.
    with PostgresHarnessStore(dsn, schema=schema) as store:
        store.create_run(value)
        assert store.load_run(value.harness_run_id).status.value == "created"
    return dsn, schema, value


def _reopen(dsn, schema, value, client, *, workspace_id=None, turn=None):
    binding = execution_binding(value)
    if workspace_id is not None:
        from dataclasses import replace

        binding = replace(binding, workspace_ref=workspace_id)
    return HarnessAgentRun.open(
        dsn, schema, value.harness_run_id,
        lambda _: ScriptedTurnAdapter((turn or needs_input(),)),
        execution_binding=binding,
        runtime=FakeRuntime(),
        workspace_claim_client=client,
        workspace_claim_workspace_id=binding.workspace_ref,
    )


def test_legacy_pg_run_is_recovered_and_pinned_before_model_execution(pg_schema):
    dsn, schema, value = _legacy_run(pg_schema)
    client = FakeNativeWorkspaceClaimClient()
    assert client._claim is None

    restored = _reopen(dsn, schema, value, client)
    assert restored.workspace_claim is not None
    assert restored.workspace_claim.require_held()["runRef"] == value.harness_run_id
    assert restored.status()["status"] == "created"
    assert restored.adapter.requests == []

    paused = restored.run(({"role": "user", "content": "historical task"},))
    assert paused.paused
    assert restored.status()["status"] == "paused"
    assert len(restored.adapter.requests) == 1

    continued = _reopen(dsn, schema, value, client, turn=completed())
    assert continued.workspace_claim is not None
    assert continued.workspace_claim.request_id == restored.workspace_claim.request_id
    assert continued.workspace_claim.require_held()["state"] == "held"
    assert continued.adapter.requests == []

    completed_result = continued.resume(
        additional_messages=({"role": "user", "content": "answer"},)
    )
    assert completed_result.loop_result.stop_code.value == "candidate_completed"
    assert continued.status()["status"] == "completed"
    # An isolated Run terminal receipt is not an external Domain acknowledgment.
    assert client._claim["state"] == "held"


def test_legacy_pg_run_requires_native_claim_client_before_model_call(pg_schema):
    dsn, schema, value = _legacy_run(pg_schema)
    binding = execution_binding(value)
    adapter = ScriptedTurnAdapter((needs_input(),))
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="native Runtime Claim"):
        HarnessAgentRun.open(
            dsn, schema, value.harness_run_id, lambda _: adapter,
            execution_binding=binding, runtime=FakeRuntime(),
            workspace_claim_workspace_id=binding.workspace_ref,
        )
    assert adapter.requests == []
    with PostgresHarnessStore(dsn, schema=schema) as store:
        assert store.load_run(value.harness_run_id).status.value == "created"


def test_lost_native_reserve_reply_recovers_existing_claim_without_reissue(pg_schema):
    dsn, schema, value = _legacy_run(pg_schema)
    client = LostReserveReplyClient()
    restored = _reopen(dsn, schema, value, client)
    assert client.lost_reply
    assert client.reserve_calls == 1
    assert restored.workspace_claim.require_held()["state"] == "held"
    restored_again = _reopen(dsn, schema, value, client)
    assert restored_again.workspace_claim.require_held()["claimId"] == "wclaim-test-double"
    assert client.reserve_calls == 1
    assert restored.adapter.requests == []
    assert restored_again.adapter.requests == []


def test_original_run_cannot_rebind_to_other_workspace_after_claim(pg_schema):
    dsn, schema, value = _legacy_run(pg_schema)
    client = FakeNativeWorkspaceClaimClient()
    _reopen(dsn, schema, value, client)
    original = client._claim["workspaceId"]
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="identity"):
        _reopen(dsn, schema, value, client, workspace_id="workspace:other-source")
    assert client._claim["workspaceId"] == original


def test_released_claim_cannot_be_resurrected_on_legacy_reentry(pg_schema):
    dsn, schema, value = _legacy_run(pg_schema)
    client = FakeNativeWorkspaceClaimClient()
    _reopen(dsn, schema, value, client)
    client._claim["state"] = "released"
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="not HELD"):
        _reopen(dsn, schema, value, client)
    assert client._claim["state"] == "released"


class MissingWorkspaceClient(FakeNativeWorkspaceClaimClient):
    """Native Runtime cannot verify the original physical Workspace."""

    def call_tool(self, name, arguments):
        if name == "workspace.get":
            return True, {"error": {"code": "WORKSPACE_NOT_FOUND"}}
        return super().call_tool(name, arguments)


def test_historical_paused_pg_run_can_repin_before_original_resume(pg_schema):
    dsn, schema = pg_schema
    value = contract("legacy-paused-" + uuid.uuid4().hex[:12], tools=True)
    binding = execution_binding(value)
    first_client = FakeNativeWorkspaceClaimClient()
    original = HarnessAgentRun.create(
        dsn, schema, value,
        lambda _: ScriptedTurnAdapter((needs_input(),)),
        execution_binding=binding,
        runtime=FakeRuntime(),
        workspace_claim_client=first_client,
    )
    first = original.run(({"role": "user", "content": "begin original job"},))
    assert first.paused
    assert original.status()["status"] == "paused"
    assert len(original.adapter.requests) == 1

    # This new transport represents the old PG Run with no native Claim.
    # It is a test-only source fixture; the old real Runtime Claim would not
    # actually disappear merely because a new Harness process is created.
    cold_native_client = FakeNativeWorkspaceClaimClient()
    assert cold_native_client._claim is None
    resumed = _reopen(dsn, schema, value, cold_native_client, turn=completed())
    assert resumed.status()["status"] == "paused"
    assert resumed.workspace_claim.require_held()["state"] == "held"
    assert resumed.adapter.requests == []
    done = resumed.resume(
        additional_messages=({"role": "user", "content": "continue safely"},)
    )
    assert done.loop_result.stop_code.value == "candidate_completed"
    assert resumed.status()["status"] == "completed"
    assert len(resumed.adapter.requests) == 1
    assert cold_native_client._claim["state"] == "held"


def test_legacy_run_with_missing_physical_workspace_cannot_start_model(pg_schema):
    dsn, schema, value = _legacy_run(pg_schema)
    client = MissingWorkspaceClient()
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="rejected"):
        _reopen(dsn, schema, value, client)
    assert client._claim is None
    with PostgresHarnessStore(dsn, schema=schema) as store:
        assert store.load_run(value.harness_run_id).status.value == "created"
