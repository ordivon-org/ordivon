from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import textwrap

from ordivon_harness.api import (
    NO_TOOL_AGENT_GRANT_DIGEST,
    NO_TOOL_AGENT_SURFACE_DIGEST,
    AgentTurnResult,
    HarnessAgentRun,
    HarnessBoundReference,
    HarnessPrivacyPolicy,
    HarnessRunContract,
)
from ordivon_harness.ordivon.model import AgentRunConclusion, ScriptedTurnAdapter

from ordivon_agent import (
    ResponseContinuityReceipt,
    ResponseContinuityStore,
    ResponseDeliveryState,
)


def _digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def _needs_input() -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id="model-call:response-loss-before-disconnect",
        model_id=ScriptedTurnAdapter.model_id,
        content="Need caller input.",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="needs_input",
            summary="Need caller input before continuing.",
            unresolved_unknowns=("caller reply",),
        ),
        usage={"inputTokens": 1, "outputTokens": 1},
        finish_reason="stop",
        raw_response_digest=_digest("needs-input"),
    )


def _contract() -> HarnessRunContract:
    return HarnessRunContract(
        harness_run_id="harness-run:response-loss-reconnect-r1",
        harness_implementation_id="ordivon-harness@response-loss-reconnect-r1",
        caller_id="caller:chatgpt",
        caller_run_ref="conversation:response-loss-reconnect-r1",
        objective_ref=HarnessBoundReference(
            "objective:response-loss-reconnect-r1",
            "objective",
            _digest("objective"),
        ),
        context_refs=(
            HarnessBoundReference(
                "context:response-loss-reconnect-r1",
                "context",
                _digest("context"),
            ),
        ),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        tool_catalog_digest=NO_TOOL_AGENT_SURFACE_DIGEST,
        tool_grant_digest=NO_TOOL_AGENT_GRANT_DIGEST,
        budget={
            "maxModelCalls": 4,
            "maxToolCalls": 0,
            "maxObservationBytes": 65536,
            "maxWallTimeMs": 10000,
            "maxTotalTokens": 10000,
            "maxModelRetries": 1,
            "maxToolCorrections": 2,
            "maxConclusionCorrections": 3,
            "maxObservationOnlyTurns": 4,
            "maxNoProgressTurns": 3,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            "manifest:response-loss-reconnect-r1",
            "system-manifest",
            _digest("manifest"),
        ),
        created_at_ms=1000,
        privacy=HarnessPrivacyPolicy(),
    )


def test_fresh_process_reattaches_original_run_and_represents_unknown_delivery(tmp_path) -> None:
    harness_root = tmp_path / "harness"
    response_root = tmp_path / "responses"
    contract = _contract()
    original = HarnessAgentRun.create(
        harness_root,
        contract,
        lambda _contract: ScriptedTurnAdapter((_needs_input(),)),
    )
    assert original.run(({"role": "user", "content": "start"},)).paused

    with ResponseContinuityStore(response_root) as responses:
        prepared = responses.create(
            ResponseContinuityReceipt(
                response_id="response:response-loss-reconnect-r1",
                caller_id=contract.caller_id,
                caller_run_ref=contract.caller_run_ref,
                harness_run_id=contract.harness_run_id,
                source_run_revision=original.recovery_status()["runRevision"],
                output_digest=_digest("response-body"),
                evidence_refs=("evidence:response-loss-reconnect-r1",),
                observed_attention_sequence=9,
                presented_attention_sequence=0,
                state=ResponseDeliveryState.PREPARED,
                revision=1,
                created_at_ms=2000,
                updated_at_ms=2000,
            )
        )
        unknown = responses.transition(
            prepared.response_id,
            expected_revision=prepared.revision,
            state=ResponseDeliveryState.DELIVERY_UNKNOWN,
            updated_at_ms=2001,
        )
        assert unknown.state is ResponseDeliveryState.DELIVERY_UNKNOWN

    child = textwrap.dedent(
        """
        import hashlib
        import json
        import sys
        from pathlib import Path

        from ordivon_agent import AgentContinuationCoordinator, ResponseContinuityStore
        from ordivon_harness.api import AgentTurnResult
        from ordivon_harness.ordivon.model import AgentRunConclusion, ScriptedTurnAdapter

        def digest(label):
            return "sha256:" + hashlib.sha256(label.encode()).hexdigest()

        def completed():
            return AgentTurnResult(
                model_call_id="model-call:fresh-process-would-continue-existing-run",
                model_id=ScriptedTurnAdapter.model_id,
                content="continued",
                tool_calls=(),
                conclusion=AgentRunConclusion(
                    status="candidate_completed",
                    summary="continued existing run",
                ),
                usage={"inputTokens": 1, "outputTokens": 1},
                finish_reason="stop",
                raw_response_digest=digest("fresh-process-completed"),
            )

        harness_root = Path(sys.argv[1])
        response_root = Path(sys.argv[2])
        with ResponseContinuityStore(response_root) as responses:
            coordinator = AgentContinuationCoordinator(responses)
            run, plan = coordinator.locate_and_inspect(
                harness_root,
                "caller:chatgpt",
                "conversation:response-loss-reconnect-r1",
                lambda _contract: ScriptedTurnAdapter((completed(),)),
            )
            print(json.dumps({
                "harnessRunId": run.harness_run_id,
                "action": plan.action.value,
                "responseRehydrationRequired": plan.response_rehydration_required,
                "effectRedispatchAllowed": plan.effect_redispatch_allowed,
                "responseState": None if plan.latest_response is None else plan.latest_response.state.value,
                "runRevision": plan.run_revision,
            }, sort_keys=True))
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", child, str(harness_root), str(response_root)],
        check=True,
        capture_output=True,
        text=True,
    )
    observed = json.loads(completed.stdout)
    assert observed == {
        "action": "represent-unconfirmed-response",
        "effectRedispatchAllowed": False,
        "harnessRunId": contract.harness_run_id,
        "responseRehydrationRequired": True,
        "responseState": "delivery-unknown",
        "runRevision": original.recovery_status()["runRevision"],
    }

    reopened = HarnessAgentRun.open_for_caller(
        harness_root,
        contract.caller_id,
        contract.caller_run_ref,
        lambda _contract: ScriptedTurnAdapter((_needs_input(),)),
    )
    assert reopened.harness_run_id == original.harness_run_id
    assert reopened.recovery_status()["resumeRequired"] is True
