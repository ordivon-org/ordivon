from __future__ import annotations

import unittest
from dataclasses import replace

from anc_canonical import canonical_digest

from ordivon_harness.completion import (
    decode_structured_completion_result,
    encode_structured_completion_result,
    structured_completion_contract_digest,
)
from ordivon_harness.core_contracts import HarnessPrivacyPolicy
from ordivon_harness.ordivon.loop import RunBudget, RunStopCode
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentStructuredResult,
    AgentTurnResult,
    ScriptedTurnAdapter,
)
from ordivon_harness.ordivon.agent_bridge import HarnessAgentBridge
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.standalone import StandaloneHarnessRunner
from tests.pg_test_support import isolated_harness_schema
from tests.test_p0_sqlite_agent_loop import FixedClock
from tests.test_structured_result_conformance import completion, contract


class StructuredResultCarrierTests(unittest.TestCase):
    def test_carrier_round_trip_preserves_json_null_and_has_explicit_bound(self) -> None:
        null_carrier = AgentStructuredResult(None)
        conclusion = AgentRunConclusion(
            status="candidate_completed",
            summary=f"Structured result {null_carrier.digest}",
            structured_result=null_carrier,
        )
        decoded = AgentRunConclusion.from_dict(conclusion.to_dict())
        assert decoded.structured_result is not None
        self.assertIsNone(decoded.structured_result.value)
        with self.assertRaisesRegex(ValueError, "exceeds one MiB"):
            AgentStructuredResult({"payload": "x" * 1_048_576})
        with self.assertRaisesRegex(ValueError, "legacy conclusion summary"):
            encode_structured_completion_result(
                completion({"type": "object"}),
                {"payload": "x" * 9_000},
            )

    def test_carrier_value_is_an_immutable_digest_snapshot(self) -> None:
        source = {"nested": {"items": [{"id": "original"}]}}
        carrier = AgentStructuredResult(source)
        original_digest = carrier.digest

        source["nested"]["items"][0]["id"] = "caller-mutated"
        reader_view = carrier.value
        reader_view["nested"]["items"].append({"id": "reader-mutated"})
        serialized_view = carrier.to_dict()
        serialized_view["value"]["nested"]["items"].clear()

        self.assertEqual(carrier.digest, original_digest)
        self.assertEqual(
            carrier.value,
            {"nested": {"items": [{"id": "original"}]}},
        )
        self.assertEqual(
            carrier.to_dict()["value"],
            {"nested": {"items": [{"id": "original"}]}},
        )

    def test_large_result_survives_terminal_store_without_entering_summary(self) -> None:
        completion_contract = completion(
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "payload": {"type": "string", "minLength": 9_000, "maxLength": 12_000},
                },
                "required": ["payload"],
            }
        )
        base_contract = contract("large-terminal-carrier", completion_contract)
        run_contract = replace(
            base_contract,
            completion_contract=completion_contract,
            privacy=HarnessPrivacyPolicy(
                content_policy="bounded-private-content",
                allow_model_content=True,
                allow_tool_content=False,
            ),
        )
        value = {"payload": "x" * 9_500}
        carrier = AgentStructuredResult(value)
        summary = f"Structured result {carrier.digest}"
        turn = AgentTurnResult(
            model_call_id="model-call:structured-large-terminal",
            model_id=ScriptedTurnAdapter.model_id,
            content=None,
            tool_calls=(),
            conclusion=AgentRunConclusion(
                status="candidate_completed",
                summary=summary,
                structured_result=carrier,
            ),
            usage={"inputTokens": 10, "outputTokens": 2_500, "totalTokens": 2_510},
            finish_reason="stop",
            raw_response_digest=canonical_digest({"large-terminal": carrier.digest}),
        )
        adapter = ScriptedTurnAdapter((turn,))
        adapter.structured_completion_contract_digest = (
            structured_completion_contract_digest(completion_contract)
        )
        clock = FixedClock()

        with (
            isolated_harness_schema() as (dsn, schema),
            PostgresHarnessStore(dsn, schema=schema) as store,
        ):
            store.create_run(run_contract)
            continuity = EventSourcedRunContinuity(
                store,
                run_contract,
                clock_ms=clock,
            )
            runner = StandaloneHarnessRunner(
                run_contract,
                continuity,
                adapter,
                HarnessAgentBridge(run_contract, continuity),
                budget=RunBudget.from_contract_dict(run_contract.budget),
                clock_ms=clock,
                monotonic_ms=clock,
            )

            execution = runner.run(
                ({"role": "user", "content": "return the bounded large result"},)
            )

            self.assertEqual(
                execution.loop_result.stop_code,
                RunStopCode.CANDIDATE_COMPLETED,
            )
            assert execution.terminal_result is not None
            terminal = execution.terminal_result
            assert terminal.conclusion is not None
            assert terminal.conclusion.structured_result is not None
            self.assertIsNotNone(terminal.conclusion_object)
            self.assertEqual(
                decode_structured_completion_result(
                    run_contract,
                    terminal.conclusion,
                ),
                value,
            )
            self.assertEqual(terminal.conclusion.summary, summary)
            self.assertLess(len(terminal.conclusion.summary.encode("utf-8")), 8_000)
            assert terminal.completion_proposal is not None
            self.assertEqual(terminal.completion_proposal.summary, summary)


if __name__ == "__main__":
    unittest.main()
