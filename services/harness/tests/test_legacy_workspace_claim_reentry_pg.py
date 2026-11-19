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
from ordivon_harness.workspace_claim import WorkspaceRunClaim
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
    # Represent a separately authenticated Native Owner's original
    # Workspace adoption. The original PG Run alone cannot create this.
    WorkspaceRunClaim(
        value, execution_binding(value).workspace_ref, client
    ).reserve_or_recover()

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
    dsn, schema = pg_schema
    value = contract("new-lost-reply-" + uuid.uuid4().hex[:12], tools=True)
    client = LostReserveReplyClient()
    restored = HarnessAgentRun.create(
        dsn, schema, value,
        lambda _: ScriptedTurnAdapter((needs_input(),)),
        execution_binding=execution_binding(value),
        runtime=FakeRuntime(), workspace_claim_client=client,
    )
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
    WorkspaceRunClaim(value, execution_binding(value).workspace_ref, client).reserve_or_recover()
    _reopen(dsn, schema, value, client)
    original = client._claim["workspaceId"]
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="identity"):
        _reopen(dsn, schema, value, client, workspace_id="workspace:other-source")
    assert client._claim["workspaceId"] == original


def test_released_claim_cannot_be_resurrected_on_legacy_reentry(pg_schema):
    dsn, schema, value = _legacy_run(pg_schema)
    client = FakeNativeWorkspaceClaimClient()
    WorkspaceRunClaim(value, execution_binding(value).workspace_ref, client).reserve_or_recover()
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


def test_historical_paused_pg_run_needs_original_held_claim_before_resume(pg_schema):
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

    # A fake unclaimed native transport cannot retroactively adopt this
    # already-PAUSED original Run, even if caller supplies the same ID.
    cold_native_client = FakeNativeWorkspaceClaimClient()
    assert cold_native_client._claim is None
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="not HELD"):
        _reopen(dsn, schema, value, cold_native_client, turn=completed())
    assert cold_native_client._claim is None

    # Re-entry against the ORIGINAL preexisting held claim remains live.
    resumed = _reopen(dsn, schema, value, first_client, turn=completed())
    assert resumed.status()["status"] == "paused"
    assert resumed.workspace_claim.require_held()["state"] == "held"
    done = resumed.resume(
        additional_messages=({"role": "user", "content": "continue safely"},)
    )
    assert done.loop_result.stop_code.value == "candidate_completed"
    assert resumed.status()["status"] == "completed"
    assert len(resumed.adapter.requests) == 1
    assert first_client._claim["state"] == "held"


def test_legacy_run_with_missing_physical_workspace_cannot_start_model(pg_schema):
    dsn, schema, value = _legacy_run(pg_schema)
    client = MissingWorkspaceClient()
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="not HELD"):
        _reopen(dsn, schema, value, client)
    assert client._claim is None
    with PostgresHarnessStore(dsn, schema=schema) as store:
        assert store.load_run(value.harness_run_id).status.value == "created"


def test_existing_original_pg_run_without_claim_must_not_auto_reserve(pg_schema):
    dsn, schema, value = _legacy_run(pg_schema)
    client = FakeNativeWorkspaceClaimClient()
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="not HELD"):
        _reopen(dsn, schema, value, client)
    assert client._claim is None
    with PostgresHarnessStore(dsn, schema=schema) as store:
        assert store.load_run(value.harness_run_id).status.value == "created"


def test_idempotent_create_cannot_adopt_existing_run_into_caller_workspace(pg_schema):
    dsn, schema, value = _legacy_run(pg_schema)
    client = FakeNativeWorkspaceClaimClient()
    binding = execution_binding(value)
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="not HELD"):
        HarnessAgentRun.create(
            dsn, schema, value, lambda _: ScriptedTurnAdapter((needs_input(),)),
            execution_binding=binding, runtime=FakeRuntime(),
            workspace_claim_client=client,
        )
    assert client._claim is None


def test_failed_initial_native_claim_does_not_commit_pg_and_allows_true_new_birth(pg_schema):
    """Before PG birth neither Run nor physical Claim can claim W1 as original."""
    from dataclasses import replace

    dsn, schema = pg_schema
    value = contract("birth-missing-claim-" + uuid.uuid4().hex[:12], tools=True)
    binding = execution_binding(value)
    adapter = ScriptedTurnAdapter((needs_input(),))
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable):
        HarnessAgentRun.create(
            dsn, schema, value, lambda _: adapter,
            execution_binding=binding, runtime=FakeRuntime(),
            workspace_claim_client=MissingWorkspaceClient(),
        )
    assert adapter.requests == []
    with PostgresHarnessStore(dsn, schema=schema) as store:
        with pytest.raises(KeyError):
            store.load_run(value.harness_run_id)

    # The first W1 claim never committed AND PG Run never existed. A new
    # properly admitted Run can be born against W2 without inheriting a
    # false historical binding from the failed, pre-birth attempt.
    later_client = FakeNativeWorkspaceClaimClient()
    admitted = HarnessAgentRun.create(
        dsn, schema, value, lambda _: adapter,
        execution_binding=replace(binding, workspace_ref="workspace:foreign-W2"),
        runtime=FakeRuntime(), workspace_claim_client=later_client,
    )
    assert admitted.status()["status"] == "created"
    assert later_client._claim["workspaceId"] == "workspace:foreign-W2"
    assert later_client._claim["state"] == "held"
    assert adapter.requests == []


def test_no_tool_legacy_created_run_still_recovers_without_claim(pg_schema):
    """No physical Workspace and no native Claim needed for a pure model Run."""
    dsn, schema = pg_schema
    value = contract("pure-legacy-" + uuid.uuid4().hex[:12], tools=False)
    with PostgresHarnessStore(dsn, schema=schema) as store:
        store.create_run(value)
    restored = HarnessAgentRun.open(
        dsn, schema, value.harness_run_id,
        lambda _: ScriptedTurnAdapter((needs_input(),)),
    )
    result = restored.run(({"role": "user", "content": "pure model"},))
    assert result.paused
    assert restored.workspace_claim is None


def test_orphan_held_native_claim_recovers_after_first_pg_birth_failure(pg_schema):
    """Native HELD precedes PG; a failed PG commit is retried under one key."""
    from unittest.mock import patch

    dsn, schema = pg_schema
    value = contract("native-orphan-retry-" + uuid.uuid4().hex[:12], tools=True)
    binding = execution_binding(value)
    client = LostReserveReplyClient()
    adapter = ScriptedTurnAdapter((needs_input(),))
    with patch.object(
        PostgresHarnessStore, "create_run",
        side_effect=RuntimeError("injected PG birth failure after original native HELD"),
    ):
        with pytest.raises(RuntimeError, match="injected PG birth failure"):
            HarnessAgentRun.create(
                dsn, schema, value, lambda _: adapter,
                execution_binding=binding, runtime=FakeRuntime(),
                workspace_claim_client=client,
            )
    assert client._claim["state"] == "held"
    assert client.reserve_calls == 1
    with PostgresHarnessStore(dsn, schema=schema) as store:
        with pytest.raises(KeyError):
            store.load_run(value.harness_run_id)
    retried = HarnessAgentRun.create(
        dsn, schema, value, lambda _: adapter,
        execution_binding=binding, runtime=FakeRuntime(),
        workspace_claim_client=client,
    )
    assert retried.status()["status"] == "created"
    assert client.reserve_calls == 1
    assert retried.workspace_claim.require_held()["runRef"] == value.harness_run_id
    assert adapter.requests == []


def test_native_held_but_pg_unborn_rejects_caller_workspace_swap(pg_schema):
    """W1 remains durable and cannot be overwritten by W2 before PG birth."""
    from dataclasses import replace
    from unittest.mock import patch

    dsn, schema = pg_schema
    value = contract("native-orphan-no-swap-" + uuid.uuid4().hex[:12], tools=True)
    binding = execution_binding(value)
    client = LostReserveReplyClient()
    with patch.object(
        PostgresHarnessStore, "create_run",
        side_effect=RuntimeError("PG unavailable after Native HELD"),
    ):
        with pytest.raises(RuntimeError, match="PG unavailable"):
            HarnessAgentRun.create(
                dsn, schema, value,
                lambda _: ScriptedTurnAdapter((needs_input(),)),
                execution_binding=binding, runtime=FakeRuntime(),
                workspace_claim_client=client,
            )
    original_workspace = client._claim["workspaceId"]
    with pytest.raises(HarnessWorkspaceAdmissionUnavailable, match="identity"):
        HarnessAgentRun.create(
            dsn, schema, value,
            lambda _: ScriptedTurnAdapter((needs_input(),)),
            execution_binding=replace(binding, workspace_ref="workspace:malicious-W2"),
            runtime=FakeRuntime(), workspace_claim_client=client,
        )
    assert client._claim["workspaceId"] == original_workspace
    assert client.reserve_calls == 1
    with PostgresHarnessStore(dsn, schema=schema) as store:
        with pytest.raises(KeyError):
            store.load_run(value.harness_run_id)

    restored = HarnessAgentRun.create(
        dsn, schema, value,
        lambda _: ScriptedTurnAdapter((needs_input(),)),
        execution_binding=binding, runtime=FakeRuntime(),
        workspace_claim_client=client,
    )
    assert restored.status()["status"] == "created"
    assert client.reserve_calls == 1
