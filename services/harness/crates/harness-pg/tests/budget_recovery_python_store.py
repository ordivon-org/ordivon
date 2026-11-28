"""Private synthetic PG fixture: original owner emits state and real Resume budgets."""
from dataclasses import replace
import json
import os
from pathlib import Path

from anc_canonical import canonical_bytes, canonical_digest
from ordivon_harness.agent_run import HarnessAgentRun
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.ordivon.model import ScriptedTurnAdapter
from ordivon_harness.ordivon.run_contract import RunBudget
from tests.test_r3_supported_agent_run import FixedClock, completed, contract, needs_input


def main():
    dsn = os.environ["HARNESS_RUST_BUDGET_WRITER_DSN"]
    schema = os.environ["HARNESS_RUST_BUDGET_SCHEMA"]
    output = Path(os.environ["HARNESS_RUST_BUDGET_FIXTURE"])
    with PostgresHarnessStore(dsn, schema=schema, initialize=True):
        pass
    clock = FixedClock()
    value = contract("native-budget-recovery")
    limits = RunBudget.from_contract_dict(value.budget).to_contract_dict()
    turns = (
        replace(needs_input("model-call:budget-mixed"), usage={"prompt_tokens": 90, "output_tokens": 60}),
        replace(needs_input("model-call:budget-known"), usage={"totalTokens": 1, "inputTokens": 90, "outputTokens": 60}),
        replace(completed("model-call:budget-zero"), usage={"totalTokens": 0}),
    )
    run = HarnessAgentRun.create(
        dsn, schema, value, lambda _: ScriptedTurnAdapter((turns[0],)),
        clock_ms=clock, monotonic_ms=clock,
    )
    assert run.run(({"role": "user", "content": "synthetic start"},)).paused
    cases = []
    for index, turn in enumerate(turns[1:]):
        with run._open_store() as store:
            retained = run._continuity(store).load_current_snapshot()
            raw = store.get_object(retained.state_object.digest, expected_kind="harness-run-state")
            assert canonical_digest(raw) == retained.state_object.digest
            state = canonical_bytes(raw).decode()
            case = {
                "state": state,
                "state_digest": retained.state_object.digest,
                "snapshot_digest": retained.snapshot_object.digest,
                "revision": store.load_run(value.harness_run_id).revision,
            }
        adapter = ScriptedTurnAdapter((turn,))
        run = HarnessAgentRun.open(
            dsn, schema, value.harness_run_id, lambda _: adapter,
            clock_ms=clock, monotonic_ms=clock,
        )
        result = run.resume(additional_messages=({"role": "user", "content": "synthetic reply"},))
        assert len(adapter.requests) == 1
        assert result.paused == (index == 0)
        case["request_budget"] = adapter.requests[0].remaining_budget
        cases.append(case)
    assert run.doctor()["healthy"] is True
    assert cases[0]["request_budget"]["totalTokens"] == limits["maxTotalTokens"]
    assert cases[1]["request_budget"]["totalTokens"] == limits["maxTotalTokens"] - 150
    output.write_text(json.dumps({"run": value.harness_run_id, "limits": limits, "cases": cases}))
    print("PYTHON_PUBLIC_RESUME_FIXTURE cases=2")


if __name__ == "__main__":
    main()
