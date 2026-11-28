"""Synthetic original public Run -> paused state owner -> native budget test.

The fixture exports only caller-created synthetic state inside the existing
disposable PG test cluster. It is not a production state-reader endpoint.
"""
from dataclasses import replace
import os
from pathlib import Path

from anc_canonical import canonical_bytes
from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from ordivon_harness.ordivon.run_contract import RunBudget
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.postgres_store import PostgresHarnessStore
from tests.test_r3_supported_agent_run import FixedClock, contract, needs_input


def main():
    dsn = os.environ["HARNESS_RUST_TEST_PG_DSN"]
    schema = os.environ["HARNESS_RUST_TEST_SCHEMA"]
    clock = FixedClock()
    value = contract("native-budget-cold")
    run_id = value.harness_run_id

    def adapter(call, usage):
        return lambda _: ScriptedTurnAdapter((replace(needs_input(call), usage=usage),))

    first = HarnessAgentRun.create(
        dsn, schema, value,
        adapter("model-call:native-budget-first", {"totalTokens": 0, "inputTokens": 90, "outputTokens": 60}),
        clock_ms=clock, monotonic_ms=clock,
    )
    first_result = first.run(({"role": "user", "content": "synthetic first"},))
    assert first_result.paused

    def snapshot():
        with PostgresHarnessStore(dsn, schema=schema) as store:
            current = EventSourcedRunContinuity.open(store, run_id, clock_ms=clock).load_current_snapshot()
            projection = store.load_run(run_id)
            events = store.list_run_events(run_id)
            assert events[-1].run_revision == projection.revision
            event = next(e for e in reversed(events) if "snapshotObjectDigest" in e.data)
            assert event.data["snapshotObjectDigest"] == current.snapshot_object.digest
            assert event.data["stateObjectDigest"] == current.state_object.digest
            raw = store.get_object(current.state_object.digest, expected_kind="harness-run-state")
            return {
                "revision": projection.revision,
                "eventId": event.event_id,
                "stateDigest": current.state_object.digest,
                "snapshotDigest": current.snapshot_object.digest,
                "state": raw,
            }

    earlier = snapshot()
    for index, usage in enumerate(({"prompt_tokens": 90, "output_tokens": 60}, {"totalTokens": 0})):
        reopened = HarnessAgentRun.open(
            dsn, schema, run_id, adapter(f"model-call:native-budget-{index}", usage),
            clock_ms=clock, monotonic_ms=clock,
        )
        result = reopened.resume(additional_messages=({"role": "user", "content": "synthetic reply"},))
        assert result.paused
    current = snapshot()
    assert current["revision"] > earlier["revision"]
    assert result.loop_result.usage["totalTokens"] == 150
    assert result.loop_result.usage["modelCalls"] == 3
    assert result.loop_result.usage["tokenCounterCoverage"]["uncountableCalls"] == 1
    fixture = {
        "runId": run_id,
        "contractDigest": value.digest,
        "limits": RunBudget.from_contract_dict(value.budget).to_contract_dict(),
        "earlier": earlier,
        "current": current,
        "observedUsage": result.loop_result.usage,
    }
    Path(os.environ["HARNESS_RUST_TEST_BUDGET_FIXTURE"]).write_bytes(canonical_bytes(fixture))
    print("PYTHON_PUBLIC_RUN_COLD_PAUSED_BUDGET_READY")


if __name__ == "__main__":
    main()
