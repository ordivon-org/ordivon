from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from ordivon_agent.continuation_r1 import (
    AgentContinuationCoordinator,
    AgentContinuationError,
    ContinuationAction,
)
from ordivon_agent.response_continuity_r1 import (
    ResponseContinuityReceipt,
    ResponseContinuityStore,
    ResponseDeliveryState,
)


class FakeRun:
    def __init__(
        self,
        *,
        status: str = "running",
        revision: int = 7,
        mechanical: bool = False,
        resume_required: bool = False,
    ) -> None:
        self.harness_run_id = "harness-run:r1"
        self._status = status
        self._revision = revision
        self._mechanical = mechanical
        self._resume_required = resume_required
        self.resumed = False

    def recovery_status(self):
        return {
            "schemaVersion": 1,
            "kind": "ordivon.harness-run-recovery-status",
            "harnessRunId": self.harness_run_id,
            "callerId": "caller:chatgpt",
            "callerRunRef": "conversation:turn-42",
            "runRevision": self._revision,
            "nativeStatus": self._status,
            "resumeRequired": self._resume_required,
            "mechanicalRecoveryRequired": self._mechanical,
        }

    def resume(self, *, cancellation=None):
        self.resumed = True
        return {"resumed": True, "cancellation": cancellation}


def receipt(*, state: ResponseDeliveryState, source_revision: int = 7):
    return ResponseContinuityReceipt(
        response_id="response:r1",
        caller_id="caller:chatgpt",
        caller_run_ref="conversation:turn-42",
        harness_run_id="harness-run:r1",
        source_run_revision=source_revision,
        output_digest="sha256:" + "a" * 64,
        evidence_refs=("artifact:r1",),
        observed_attention_sequence=0,
        presented_attention_sequence=0,
        state=state,
        revision=1,
        created_at_ms=10,
        updated_at_ms=10,
    )


def test_unconfirmed_response_takes_priority_over_execution_recovery():
    with TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as responses:
            responses.create(receipt(state=ResponseDeliveryState.PREPARED))
            plan = AgentContinuationCoordinator(responses).inspect(
                FakeRun(mechanical=True)  # type: ignore[arg-type]
            )
            assert plan.action is ContinuationAction.REPRESENT_UNCONFIRMED_RESPONSE
            assert plan.response_rehydration_required is True
            assert plan.effect_redispatch_allowed is False


def test_mechanical_recovery_resumes_only_existing_run():
    with TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as responses:
            coordinator = AgentContinuationCoordinator(responses)
            run = FakeRun(mechanical=True)
            plan = coordinator.inspect(run)  # type: ignore[arg-type]
            assert plan.action is ContinuationAction.RECOVER_EXISTING_RUN
            result = coordinator.recover_existing_run(run, plan)  # type: ignore[arg-type]
            assert result == {"resumed": True, "cancellation": None}
            assert run.resumed is True
            assert plan.effect_redispatch_allowed is False


def test_paused_run_waits_for_caller_input_without_recovery_effect():
    with TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as responses:
            plan = AgentContinuationCoordinator(responses).inspect(
                FakeRun(status="paused", resume_required=True)  # type: ignore[arg-type]
            )
            assert plan.action is ContinuationAction.AWAIT_CALLER_INPUT
            assert plan.response_rehydration_required is False


def test_terminal_and_running_runs_project_distinct_actions():
    with TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as responses:
            coordinator = AgentContinuationCoordinator(responses)
            terminal = coordinator.inspect(FakeRun(status="completed"))  # type: ignore[arg-type]
            running = coordinator.inspect(FakeRun(status="running"))  # type: ignore[arg-type]
            assert terminal.action is ContinuationAction.INSPECT_TERMINAL
            assert running.action is ContinuationAction.CONTINUE_EXISTING_RUN


def test_future_response_revision_fails_closed():
    with TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as responses:
            responses.create(receipt(state=ResponseDeliveryState.PREPARED, source_revision=8))
            with pytest.raises(AgentContinuationError, match="future Harness Run revision"):
                AgentContinuationCoordinator(responses).inspect(
                    FakeRun(revision=7)  # type: ignore[arg-type]
                )


def test_recover_existing_run_rejects_non_recovery_plan():
    with TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as responses:
            coordinator = AgentContinuationCoordinator(responses)
            run = FakeRun()
            plan = coordinator.inspect(run)  # type: ignore[arg-type]
            with pytest.raises(AgentContinuationError, match="does not authorize Run recovery"):
                coordinator.recover_existing_run(run, plan)  # type: ignore[arg-type]


class FakeAttentionReplay:
    def __init__(self, events):
        self.events = tuple(events)
        self.calls = []

    def replay(self, actor_ref, *, after_sequence, through_sequence):
        self.calls.append((actor_ref, after_sequence, through_sequence))
        return self.events


def test_attention_ack_and_confirmed_presentation_are_separate_watermarks():
    with TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as responses:
            initial = receipt(state=ResponseDeliveryState.PREPARED)
            observed = ResponseContinuityReceipt(
                response_id=initial.response_id,
                caller_id=initial.caller_id,
                caller_run_ref=initial.caller_run_ref,
                harness_run_id=initial.harness_run_id,
                source_run_revision=initial.source_run_revision,
                output_digest=initial.output_digest,
                evidence_refs=initial.evidence_refs,
                observed_attention_sequence=12,
                presented_attention_sequence=0,
                state=initial.state,
                revision=initial.revision,
                created_at_ms=initial.created_at_ms,
                updated_at_ms=initial.updated_at_ms,
            )
            responses.create(observed)
            replay = FakeAttentionReplay(
                ({"sequence": 7, "kind": "work.updated"}, {"sequence": 12, "kind": "message"})
            )
            plan = AgentContinuationCoordinator(responses).inspect(
                FakeRun(),  # type: ignore[arg-type]
                attention_actor_ref="agent:continuation",
                attention_replay=replay,
            )
            assert plan.action is ContinuationAction.REPRESENT_UNCONFIRMED_RESPONSE
            assert plan.confirmed_attention_sequence == 0
            assert plan.observed_attention_sequence == 12
            assert [event["sequence"] for event in plan.unpresented_attention] == [7, 12]
            assert replay.calls == [("agent:continuation", 0, 12)]


def test_attention_replay_fails_closed_on_events_beyond_bound_response():
    with TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as responses:
            initial = receipt(state=ResponseDeliveryState.PREPARED)
            observed = ResponseContinuityReceipt(
                response_id=initial.response_id,
                caller_id=initial.caller_id,
                caller_run_ref=initial.caller_run_ref,
                harness_run_id=initial.harness_run_id,
                source_run_revision=initial.source_run_revision,
                output_digest=initial.output_digest,
                evidence_refs=initial.evidence_refs,
                observed_attention_sequence=4,
                presented_attention_sequence=0,
                state=initial.state,
                revision=initial.revision,
                created_at_ms=initial.created_at_ms,
                updated_at_ms=initial.updated_at_ms,
            )
            responses.create(observed)
            replay = FakeAttentionReplay(({"sequence": 5},))
            with pytest.raises(AgentContinuationError, match="out-of-range"):
                AgentContinuationCoordinator(responses).inspect(
                    FakeRun(),  # type: ignore[arg-type]
                    attention_actor_ref="agent:continuation",
                    attention_replay=replay,
                )


def test_attention_recovery_requires_actor_and_port_together():
    with TemporaryDirectory() as directory:
        with ResponseContinuityStore(Path(directory)) as responses:
            with pytest.raises(AgentContinuationError, match="requires both"):
                AgentContinuationCoordinator(responses).inspect(
                    FakeRun(),  # type: ignore[arg-type]
                    attention_actor_ref="agent:continuation",
                )
