#!/usr/bin/env python3
"""Migration-only Harness segment driver for the Temporal NEEDS_INPUT seam pilot.

This file deliberately uses the existing Harness API and scripted provider fixture. It is not a
new lifecycle owner. Temporal may retry this local activity: already-paused and already-terminal
state is observed and returned without redispatching the scripted provider.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path

from ordivon_harness.core_contracts import HarnessPrivacyPolicy
from ordivon_harness.independent_result import IndependentRunRecorder
from ordivon_harness.ordivon.loop import RunStopCode
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from ordivon_harness.ordivon.sqlite_agent_bridge import SQLiteHarnessAgentBridge
from ordivon_harness.ordivon.sqlite_run_store import SQLiteHarnessRunContinuityStore
from ordivon_harness.sqlite_store import SQLiteHarnessStore
from ordivon_harness.standalone import StandaloneHarnessRunner
from ordivon_harness.store import HarnessRunStatus
from tests.test_p0_sqlite_agent_loop import FixedClock, budget, completed_result, contract, needs_input_result

_SUFFIX = "temporal-needs-input-pilot"


def _contract():
    return replace(
        contract(_SUFFIX),
        privacy=HarnessPrivacyPolicy(
            content_policy="bounded-private-content",
            allow_model_content=True,
            allow_tool_content=False,
        ),
    )


def _runner(run_contract, continuity, adapter, clock, *, provider_source=None):
    return StandaloneHarnessRunner(
        run_contract,
        continuity,
        adapter,
        SQLiteHarnessAgentBridge(run_contract, continuity, provider_source=provider_source),
        budget=budget(),
        clock_ms=clock,
        monotonic_ms=clock,
    )


def _projection(store: SQLiteHarnessStore, continuity: SQLiteHarnessRunContinuityStore) -> dict:
    run = store.load_run(continuity.harness_run_id)
    events = store.list_run_events(continuity.harness_run_id)
    value = {
        "harnessRunId": continuity.harness_run_id,
        "status": run.status.value,
        "revision": run.revision,
        "traceSegments": sum(event.event_kind == "harness.trace-recorded" for event in events),
        "providerDispatches": sum(
            event.event_kind == "harness.provider-call-dispatching" for event in events
        ),
    }
    if run.status is HarnessRunStatus.PAUSED:
        snapshot = continuity.load_current_snapshot().snapshot
        value.update(
            {
                "stopCode": RunStopCode.NEEDS_INPUT.value,
                "pauseReason": snapshot.pause_reason.value,
                "snapshotDigest": snapshot.digest,
            }
        )
    elif run.status.terminal:
        terminal = IndependentRunRecorder(
            store,
            continuity.contract,
            continuity.binding,
            clock_ms=continuity.clock_ms,
        ).load_terminal_result()
        value.update(
            {
                "stopReason": terminal.receipt.stop_reason,
                "terminalReceiptDigest": terminal.receipt.digest,
            }
        )
    return value


def start(root: Path) -> dict:
    run_contract = _contract()
    clock = FixedClock()
    database = root / "harness.sqlite3"
    if database.exists():
        with SQLiteHarnessStore(root) as store:
            continuity = SQLiteHarnessRunContinuityStore.open(
                store, run_contract.harness_run_id, clock_ms=clock
            )
            current = store.load_run(run_contract.harness_run_id)
            if current.status is HarnessRunStatus.PAUSED or current.status.terminal:
                return _projection(store, continuity)
            raise RuntimeError("pilot start found a non-paused non-terminal existing Harness Run")

    store = SQLiteHarnessStore.initialize(root)
    try:
        store.create_run(run_contract)
        continuity = SQLiteHarnessRunContinuityStore(
            store, run_contract, clock_ms=clock
        )
        execution = _runner(
            run_contract,
            continuity,
            ScriptedTurnAdapter((needs_input_result(_SUFFIX + "-pause"),)),
            clock,
        ).run(({"role": "user", "content": "start the bounded pilot"},))
        if execution.loop_result.stop_code is not RunStopCode.NEEDS_INPUT:
            raise RuntimeError("pilot first Harness segment did not stop at NEEDS_INPUT")
        return _projection(store, continuity)
    finally:
        store.close()


def resume(root: Path, messages: tuple[dict[str, object], ...]) -> dict:
    run_contract = _contract()
    clock = FixedClock()
    with SQLiteHarnessStore(root) as store:
        continuity = SQLiteHarnessRunContinuityStore.open(
            store, run_contract.harness_run_id, clock_ms=clock
        )
        current = store.load_run(run_contract.harness_run_id)
        if current.status.terminal:
            return _projection(store, continuity)
        if current.status is not HarnessRunStatus.PAUSED:
            raise RuntimeError("pilot resume requires an existing PAUSED Harness Run")
        retained = continuity.load_current_snapshot()
        if retained.snapshot.pause_reason.value != "needs-input":
            raise RuntimeError("pilot resume refuses a non-NEEDS_INPUT Harness snapshot")
        execution = _runner(
            run_contract,
            continuity,
            ScriptedTurnAdapter((completed_result(_SUFFIX + "-resume"),)),
            clock,
            provider_source=continuity.snapshot_provider_source(retained),
        ).resume(additional_messages=messages)
        if execution.loop_result.stop_code is not RunStopCode.CANDIDATE_COMPLETED:
            raise RuntimeError("pilot resumed Harness segment did not complete")
        return _projection(store, continuity)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--phase", choices=("start", "resume"), required=True)
    parser.add_argument("--messages-json")
    args = parser.parse_args()
    root = args.state_root.resolve()
    if args.phase == "start":
        value = start(root)
    else:
        raw = [] if args.messages_json is None else json.loads(args.messages_json)
        if not isinstance(raw, list) or not raw or any(not isinstance(item, dict) for item in raw):
            raise ValueError("resume messages must be one non-empty JSON array of objects")
        messages = tuple(dict(item) for item in raw)
        if any(set(item) != {"role", "content"} or item.get("role") != "user" or not isinstance(item.get("content"), str) for item in messages):
            raise ValueError("pilot wake accepts only plain user messages")
        value = resume(root, messages)
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
