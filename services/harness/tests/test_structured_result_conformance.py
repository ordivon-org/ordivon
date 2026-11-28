from __future__ import annotations

from dataclasses import replace
import unittest

from anc_canonical import canonical_digest

from ordivon_harness.completion import (
    decode_structured_completion_result,
    encode_structured_completion_result,
    structured_completion_contract_digest,
)
from ordivon_harness.core_contracts import HarnessRunContract
from ordivon_harness.ordivon.loop import RunBudget, RunStopCode
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentTurnResult,
    ScriptedTurnAdapter,
)
from ordivon_harness.ordivon.agent_bridge import HarnessAgentBridge
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.standalone import StandaloneHarnessRunner
from ordivon_harness.structured_result_conformance import (
    JSON_SCHEMA_DRAFT_2020_12_URI,
    LEGACY_LOCAL_JSON_SCHEMA_DRAFT_2020_12_PROFILE_V1,
    validate_structured_result_instance,
)

from tests.pg_test_support import isolated_harness_schema
from tests.test_p0_sqlite_agent_loop import FixedClock, contract as base_contract
from tests.test_p1_procedural_capital import PROCEDURE_RESULT_SCHEMA


DIALECT = JSON_SCHEMA_DRAFT_2020_12_URI
LEGACY_POLICY = LEGACY_LOCAL_JSON_SCHEMA_DRAFT_2020_12_PROFILE_V1

CHOICE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "choice": {"type": "string", "enum": ["observe"]},
        "rationale": {"type": "string", "minLength": 1, "maxLength": 80},
    },
    "required": ["choice", "rationale"],
}


def completion(
    schema=CHOICE_SCHEMA,
    *,
    dialect: str | None = DIALECT,
    legacy_policy: str | None = None,
):
    result_schema = dict(schema)
    if dialect is not None:
        result_schema = {"$schema": dialect, **result_schema}
    value = {
        "mode": "structured-result-v1",
        "resultKind": "conformance-test",
        "resultSchema": result_schema,
    }
    if legacy_policy is not None:
        value["conformancePolicy"] = legacy_policy
    return value


def contract(suffix: str, completion_contract) -> HarnessRunContract:
    base = base_contract(f"structured-conformance-{suffix}")
    budget = dict(base.budget)
    budget.update(
        {
            "maxModelCalls": 2,
            "maxToolCalls": 0,
            "maxWallTimeMs": 10_000,
            "maxTotalTokens": 10_000,
            "maxConclusionCorrections": 1,
            "maxToolCorrections": 0,
        }
    )
    return replace(base, completion_contract=completion_contract, budget=budget)


def turn(suffix: str, completion_contract, value) -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id=f"model-call:structured-conformance-{suffix}",
        model_id=ScriptedTurnAdapter.model_id,
        content=f"candidate {suffix}",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed",
            summary=encode_structured_completion_result(completion_contract, value),
        ),
        usage={"inputTokens": 10, "outputTokens": 5, "totalTokens": 15},
        finish_reason="stop",
        raw_response_digest=canonical_digest({"structured-conformance": suffix}),
    )


class CountingDomainGateBridge(HarnessAgentBridge):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.validated_summaries: list[str] = []

    def validate_conclusion(self, conclusion: AgentRunConclusion) -> None:
        self.validated_summaries.append(conclusion.summary)


class StructuredResultConformanceTests(unittest.TestCase):
    def test_legacy_policy_absent_remains_unverified_and_decode_compatible(self) -> None:
        legacy = completion(dialect=None)
        run_contract = contract("legacy", legacy)
        invalid = {"choice": "observe", "rationale": ""}
        conclusion = turn("legacy", legacy, invalid).conclusion
        assert conclusion is not None
        self.assertEqual(decode_structured_completion_result(run_contract, conclusion), invalid)

    def test_standard_dialect_and_legacy_profile_keep_distinct_semantics(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported structured completion JSON Schema dialect"):
            contract(
                "unknown-dialect",
                completion(dialect="https://example.invalid/json-schema/draft"),
            )

        reusable_schema = {
            "$defs": {"choice": {"type": "string", "enum": ["observe"]}},
            "type": "object",
            "additionalProperties": False,
            "properties": {"choice": {"$ref": "#/$defs/choice"}},
            "required": ["choice"],
        }
        current = completion(reusable_schema)
        current_contract = contract("standard-ref", current)
        current_conclusion = turn("standard-ref", current, {"choice": "observe"}).conclusion
        assert current_conclusion is not None
        self.assertEqual(
            decode_structured_completion_result(current_contract, current_conclusion),
            {"choice": "observe"},
        )

        with self.assertRaisesRegex(ValueError, "legacy structured completion conformance profile rejects unsupported schema keywords"):
            contract(
                "legacy-ref",
                completion(
                    reusable_schema,
                    dialect=None,
                    legacy_policy=LEGACY_POLICY,
                ),
            )

        with self.assertRaisesRegex(ValueError, "additionalProperties.*must be boolean"):
            contract(
                "legacy-additional-schema",
                completion(
                    {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                    dialect=None,
                    legacy_policy=LEGACY_POLICY,
                ),
            )

        legacy = completion(dialect=None, legacy_policy=LEGACY_POLICY)
        legacy_contract = contract("legacy-reader", legacy)
        invalid_legacy = turn(
            "legacy-reader",
            legacy,
            {"choice": "observe", "rationale": ""},
        ).conclusion
        assert invalid_legacy is not None
        with self.assertRaisesRegex(ValueError, "non-empty|too short"):
            decode_structured_completion_result(legacy_contract, invalid_legacy)

        with self.assertRaisesRegex(ValueError, "requires structured-result-v1"):
            replace(
                base_contract("policy-on-record"),
                completion_contract={
                    "mode": "record",
                    "conformancePolicy": LEGACY_POLICY,
                },
            )

    def test_standard_dialect_requires_local_reference_closure_at_admission(self) -> None:
        cases = (
            (
                "missing-local-ref",
                {
                    "type": "object",
                    "properties": {"choice": {"$ref": "#/$defs/missing"}},
                },
            ),
            (
                "unbound-external-ref",
                {
                    "type": "object",
                    "properties": {
                        "choice": {"$ref": "https://example.invalid/unbound-schema"}
                    },
                },
            ),
        )
        for suffix, schema in cases:
            with self.subTest(suffix=suffix):
                with self.assertRaisesRegex(ValueError, "unresolvable local"):
                    contract(suffix, completion(schema))

    def test_standard_dialect_local_registry_respects_ids_without_remote_retrieval(self) -> None:
        schema = {
            "$id": "https://schemas.example/structured/root",
            "$defs": {
                "choice": {
                    "$id": "choice",
                    "type": "string",
                    "enum": ["observe"],
                }
            },
            "type": "object",
            "additionalProperties": False,
            "properties": {"choice": {"$ref": "choice"}},
            "required": ["choice"],
        }
        completion_contract = completion(schema)
        run_contract = contract("bound-absolute-local-resource", completion_contract)
        conclusion = turn(
            "bound-absolute-local-resource",
            completion_contract,
            {"choice": "observe"},
        ).conclusion
        assert conclusion is not None
        self.assertEqual(
            decode_structured_completion_result(run_contract, conclusion),
            {"choice": "observe"},
        )

    def test_reference_closure_does_not_claim_recursive_termination(self) -> None:
        # Local reference closure is intentionally distinct from recursion/termination policy.
        run_contract = contract("self-reference-admission", completion({"$ref": "#"}))
        self.assertIsInstance(run_contract, HarnessRunContract)

    def test_policy_decode_rejects_f1_style_nested_objects_and_length_overflow(self) -> None:
        f1_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "problemReformulation": {"type": "string", "maxLength": 8},
                "candidateMechanisms": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 2,
                    "items": {"type": "string", "maxLength": 20},
                },
            },
            "required": ["problemReformulation", "candidateMechanisms"],
        }
        structured = completion(f1_schema)
        run_contract = contract("f1-shape", structured)
        nested = {
            "problemReformulation": "short",
            "candidateMechanisms": [
                {"hypothesis": "embedded", "predictedObservation": "detail"}
            ],
        }
        nested_conclusion = turn("f1-nested", structured, nested).conclusion
        assert nested_conclusion is not None
        with self.assertRaisesRegex(ValueError, "not of type 'string'"):
            decode_structured_completion_result(run_contract, nested_conclusion)

        too_long = {
            "problemReformulation": "123456789",
            "candidateMechanisms": ["mechanism"],
        }
        long_conclusion = turn("f1-long", structured, too_long).conclusion
        assert long_conclusion is not None
        with self.assertRaisesRegex(ValueError, "too long"):
            decode_structured_completion_result(run_contract, long_conclusion)

    def test_policy_rejects_procedural_capital_partial_manual_bypass_shape(self) -> None:
        structured = completion(PROCEDURE_RESULT_SCHEMA)
        invalid = {
            "taskClass": "bounded-repository-repair",
            "procedure": "safe-looking procedure",
            "validityConditions": 42,
            "claimedBenefit": ["wrong-type"],
            "falsifier": {"wrong": "type"},
        }
        with self.assertRaisesRegex(ValueError, "does not conform|violates bound schema"):
            validate_structured_result_instance(structured, invalid)

    def test_policy_rejects_selector_numeric_string_coercion_shape(self) -> None:
        selector_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "profileId": {"type": "string", "enum": ["profile:partial-evidence"]},
                "maxTotalTokens": {"type": "integer", "minimum": 1, "maximum": 65_536},
                "maxWallTimeMs": {"type": "integer", "minimum": 1, "maximum": 120_000},
                "maxOutputTokens": {"type": "integer", "minimum": 1, "maximum": 8_192},
                "adoptPriorCompletionProposal": {"type": "boolean"},
                "adoptIndependentVerification": {"type": "boolean"},
                "rationale": {"type": "string", "minLength": 1},
            },
            "required": [
                "profileId",
                "maxTotalTokens",
                "maxWallTimeMs",
                "maxOutputTokens",
                "adoptPriorCompletionProposal",
                "adoptIndependentVerification",
                "rationale",
            ],
        }
        invalid = {
            "profileId": "profile:partial-evidence",
            "maxTotalTokens": "16000",
            "maxWallTimeMs": "60000",
            "maxOutputTokens": "1024",
            "adoptPriorCompletionProposal": False,
            "adoptIndependentVerification": False,
            "rationale": "schema-invalid numeric strings",
        }
        with self.assertRaisesRegex(ValueError, "not of type 'integer'"):
            validate_structured_result_instance(completion(selector_schema), invalid)

    def test_mechanical_gate_runs_before_and_preserves_domain_gate(self) -> None:
        completion_contract = completion()
        run_contract = contract("gate-order", completion_contract)
        invalid = {"choice": "observe", "rationale": ""}
        valid = {"choice": "observe", "rationale": "inspect first"}
        adapter = ScriptedTurnAdapter(
            (
                turn("gate-invalid", completion_contract, invalid),
                turn("gate-valid", completion_contract, valid),
            )
        )
        adapter.structured_completion_contract_digest = structured_completion_contract_digest(
            completion_contract
        )
        clock = FixedClock()
        with (
            isolated_harness_schema() as (dsn, schema),
            PostgresHarnessStore(dsn, schema=schema) as store,
        ):
            store.create_run(run_contract)
            continuity = EventSourcedRunContinuity(store, run_contract, clock_ms=clock)
            bridge = CountingDomainGateBridge(run_contract, continuity)
            runner = StandaloneHarnessRunner(
                run_contract,
                continuity,
                adapter,
                bridge,
                budget=RunBudget.from_contract_dict(run_contract.budget),
                clock_ms=clock,
                monotonic_ms=clock,
            )
            execution = runner.run(
                ({"role": "user", "content": "return one valid structured result"},)
            )
            self.assertEqual(execution.loop_result.stop_code, RunStopCode.CANDIDATE_COMPLETED)
            self.assertEqual(len(bridge.validated_summaries), 1)
            self.assertEqual(
                bridge.validated_summaries[0],
                encode_structured_completion_result(completion_contract, valid),
            )

    def test_runner_rejects_invalid_result_then_accepts_corrected_result(self) -> None:
        completion_contract = completion()
        run_contract = contract("correction", completion_contract)
        invalid = {"choice": "observe", "rationale": ""}
        valid = {"choice": "observe", "rationale": "inspect first"}
        adapter = ScriptedTurnAdapter(
            (
                turn("invalid", completion_contract, invalid),
                turn("corrected", completion_contract, valid),
            )
        )
        adapter.structured_completion_contract_digest = structured_completion_contract_digest(
            completion_contract
        )
        clock = FixedClock()
        with (
            isolated_harness_schema() as (dsn, schema),
            PostgresHarnessStore(dsn, schema=schema) as store,
        ):
            store.create_run(run_contract)
            continuity = EventSourcedRunContinuity(store, run_contract, clock_ms=clock)
            bridge = HarnessAgentBridge(run_contract, continuity)
            runner = StandaloneHarnessRunner(
                run_contract,
                continuity,
                adapter,
                bridge,
                budget=RunBudget.from_contract_dict(run_contract.budget),
                clock_ms=clock,
                monotonic_ms=clock,
            )
            execution = runner.run(
                ({"role": "user", "content": "return one valid structured result"},)
            )
            result = execution.loop_result
            self.assertEqual(result.stop_code, RunStopCode.CANDIDATE_COMPLETED)
            self.assertEqual(result.model_calls, 2)
            self.assertEqual(result.usage["conclusionCorrections"], 1)
            self.assertEqual(len(adapter.requests), 2)
            assert result.conclusion is not None
            self.assertEqual(decode_structured_completion_result(run_contract, result.conclusion), valid)
            rejected = [event for event in result.trace.events if event.kind == "conclusion_rejected"]
            self.assertEqual(len(rejected), 1)
            self.assertEqual(rejected[0].payload["errorKind"], "model_correctable")


if __name__ == "__main__":
    unittest.main()
