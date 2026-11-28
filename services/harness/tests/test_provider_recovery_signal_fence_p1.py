from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import tempfile
import unittest

from ordivon_harness.ordivon.loop import OrdivonAgentLoop
from ordivon_harness.ordivon.model import (
    AgentTurnRequest,
    AgentTurnResult,
    ScriptedTurnAdapter,
    static_provider_request_digest,
)
from ordivon_harness.ordivon.run_store_port import HarnessProviderCallRecoveryRequired
from ordivon_harness.ordivon.agent_bridge import HarnessAgentBridge
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.sqlite_store import SQLiteHarnessStore
from tests.pg_test_support import isolated_harness_schema
from tests.test_p0_sqlite_agent_loop import FixedClock, budget, contract


class DeadlineHandle:
    def __init__(self, clock: FixedClock) -> None:
        self.clock = clock
        self.cancel_calls = 0
        self.poll_calls = 0

    def poll(self, timeout_seconds: float) -> AgentTurnResult | None:
        del timeout_seconds
        self.poll_calls += 1
        self.clock.value += 20_000
        return None

    def cancel(self) -> None:
        self.cancel_calls += 1


class DeadlineAdapter:
    adapter_id = ScriptedTurnAdapter.adapter_id
    model_id = ScriptedTurnAdapter.model_id
    provider_request_digest = static_provider_request_digest
    supports_call_handle = True

    def __init__(self, clock: FixedClock) -> None:
        self.handle = DeadlineHandle(clock)
        self.requests: list[AgentTurnRequest] = []

    def start_invoke(self, request: AgentTurnRequest, control) -> DeadlineHandle:
        del control
        self.requests.append(request)
        return self.handle

    def invoke(self, request: AgentTurnRequest) -> AgentTurnResult:
        raise AssertionError(f"controlled Adapter unexpectedly used invoke(): {request.turn_id}")


class RecoveryAfterDurableFailureBridge(HarnessAgentBridge):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fail_calls = 0

    def fail_provider_call(self, request, error, *, unknown) -> None:
        self.fail_calls += 1
        if self.fail_calls > 1:
            raise AssertionError("Provider failure was admitted more than once")
        super().fail_provider_call(request, error, unknown=unknown)
        raise HarnessProviderCallRecoveryRequired(
            "Provider outcome was durably admitted; explicit resume is required"
        )


class ProviderRecoverySignalFenceP1Tests(unittest.TestCase):
    @contextmanager
    def _store(self):
        with tempfile.TemporaryDirectory() as directory:
            with SQLiteHarnessStore.initialize(Path(directory) / "state") as store:
                yield store

    def test_recovery_signal_after_durable_failure_is_not_reclassified_as_provider_unknown(self) -> None:
        with self._store() as store:
            clock = FixedClock()
            run_contract = contract("p1-provider-recovery-signal")
            store.create_run(run_contract)
            continuity = EventSourcedRunContinuity(
                store,
                run_contract,
                clock_ms=clock,
            )
            bridge = RecoveryAfterDurableFailureBridge(run_contract, continuity)
            adapter = DeadlineAdapter(clock)
            loop = OrdivonAgentLoop(
                adapter,
                bridge,
                budget=budget(),
                clock_ms=clock,
                monotonic_ms=clock,
                assignment_deadline_ms=run_contract.deadline_ms,
            )
            with self.assertRaisesRegex(
                HarnessProviderCallRecoveryRequired,
                "explicit resume",
            ):
                loop.run(
                    harness_run_id=run_contract.harness_run_id,
                    assignment_id=continuity.binding.assignment_id,
                    context_digest=run_contract.context_refs[0].digest,
                    initial_messages=(
                        {"role": "user", "content": "exercise Provider recovery fencing"},
                    ),
                )
            self.assertEqual(bridge.fail_calls, 1)
            self.assertEqual(len(adapter.requests), 1)
            self.assertEqual(adapter.handle.cancel_calls, 1)
            retained = continuity.load_current_provider_call()
            self.assertIsNotNone(retained.failure)


class ProviderRecoverySignalFenceP1PostgresTests(ProviderRecoverySignalFenceP1Tests):
    @contextmanager
    def _store(self):
        with isolated_harness_schema() as (dsn, schema):
            with PostgresHarnessStore(dsn, schema=schema) as store:
                yield store


if __name__ == "__main__":
    unittest.main()
