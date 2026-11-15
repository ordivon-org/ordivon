"""Bounded behavioral and aliasing tests for extracted Harness evidence transitions."""

from __future__ import annotations

from ordivon_harness.agent_tool_observation import HarnessToolObservation
from ordivon_harness.ordivon.model import AgentToolCall
from ordivon_harness.ordivon.run_contract import RunBudget
from ordivon_harness.ordivon.run_recovery import (
    _advance_turn_evidence,
    _decide_turn_progress,
)


OBSERVATION_ONLY = frozenset({"search_workspace", "read_workspace"})


def search(call_id: str, path: str = "src") -> AgentToolCall:
    return AgentToolCall(
        tool_call_id=call_id,
        name="search_workspace",
        arguments={"query": "term", "relativePath": path},
    )


def observed(call_id: str, *, exit_code: int = 0) -> HarnessToolObservation:
    return HarnessToolObservation(
        tool_call_id=call_id,
        tool_name="search_workspace",
        status="observed",
        structured_content={
            "matches": [{"path": "src/a.py", "line": 7, "text": "term"}],
            "exitCode": exit_code,
            "executionDisposition": "succeeded" if exit_code == 0 else "failed",
        },
    )


def test_transition_does_not_mutate_predecessor_state() -> None:
    state_signatures = {"prior"}
    state_searches = {("other", "src"): {"old"}}
    first = _advance_turn_evidence(
        (search("call-1"),),
        (observed("call-1"),),
        OBSERVATION_ONLY,
        state_signatures,
        state_searches,
    )
    assert first.observation_only
    assert not first.action_progress
    assert first.new_evidence
    assert state_signatures == {"prior"}
    assert state_searches == {("other", "src"): {"old"}}
    assert first.search_evidence[("term", "src")]


def test_identical_and_subsumed_search_do_not_create_progress() -> None:
    first = _advance_turn_evidence(
        (search("call-1"),),
        (observed("call-1"),),
        OBSERVATION_ONLY,
        set(),
        {},
    )
    replay = _advance_turn_evidence(
        (search("call-2"),),
        (observed("call-2"),),
        OBSERVATION_ONLY,
        first.evidence_signatures,
        first.search_evidence,
    )
    assert not replay.new_evidence
    narrower = _advance_turn_evidence(
        (search("call-3", "src/sub"),),
        (observed("call-3"),),
        OBSERVATION_ONLY,
        replay.evidence_signatures,
        replay.search_evidence,
    )
    assert not narrower.new_evidence
    assert narrower.observation_only
    assert not narrower.action_progress


def test_search_failure_is_new_evidence_even_with_same_partial_matches() -> None:
    first = _advance_turn_evidence(
        (search("call-1"),),
        (observed("call-1"),),
        OBSERVATION_ONLY,
        set(),
        {},
    )
    second = _advance_turn_evidence(
        (search("call-2"),),
        (observed("call-2", exit_code=2),),
        OBSERVATION_ONLY,
        first.evidence_signatures,
        first.search_evidence,
    )
    assert second.new_evidence
    assert second.observation_only


def test_rejected_tool_is_not_action_progress() -> None:
    call = AgentToolCall(tool_call_id="call-1", name="apply_workspace", arguments={})
    rejected = HarnessToolObservation(
        tool_call_id=call.tool_call_id,
        tool_name=call.name,
        status="rejected",
        structured_content={"reason": "not admitted"},
    )
    result = _advance_turn_evidence(
        (call,),
        (rejected,),
        OBSERVATION_ONLY,
        set(),
        {},
    )
    assert not result.new_evidence
    assert not result.action_progress
    assert not result.observation_only


def test_turn_progress_decision_replays_without_new_evidence_or_mutating_state() -> None:
    budget = RunBudget(
        max_model_calls=5,
        max_tool_calls=5,
        max_observation_bytes=1_024,
        max_wall_time_ms=10_000,
        max_no_progress_turns=2,
    )
    first = _decide_turn_progress(
        (search("call-1"),),
        (observed("call-1"),),
        OBSERVATION_ONLY,
        set(),
        {},
        prior_observation_only_turns=0,
        prior_no_progress_turns=0,
        budget=budget,
    )
    assert first.evidence.new_evidence
    assert first.observation_only_turns == 1
    assert first.no_progress_turns == 0
    assert first.gate_reason is None

    previous_signatures = set(first.evidence.evidence_signatures)
    previous_searches = {
        key: set(matches) for key, matches in first.evidence.search_evidence.items()
    }
    second = _decide_turn_progress(
        (search("call-2"),),
        (observed("call-2"),),
        OBSERVATION_ONLY,
        previous_signatures,
        previous_searches,
        prior_observation_only_turns=first.observation_only_turns,
        prior_no_progress_turns=first.no_progress_turns,
        budget=budget,
    )
    assert not second.evidence.new_evidence
    assert second.observation_only_turns == 2
    assert second.no_progress_turns == 1
    assert second.gate_reason is None
    assert previous_signatures == first.evidence.evidence_signatures
    assert previous_searches == first.evidence.search_evidence

    third = _decide_turn_progress(
        (search("call-3"),),
        (observed("call-3"),),
        OBSERVATION_ONLY,
        second.evidence.evidence_signatures,
        second.evidence.search_evidence,
        prior_observation_only_turns=second.observation_only_turns,
        prior_no_progress_turns=second.no_progress_turns,
        budget=budget,
    )
    assert third.no_progress_turns == 2
    assert third.gate_reason is not None


def test_turn_progress_decision_resets_counters_for_observed_action() -> None:
    decision = _decide_turn_progress(
        (AgentToolCall(tool_call_id="action-1", name="apply_workspace", arguments={}),),
        (
            HarnessToolObservation(
                tool_call_id="action-1",
                tool_name="apply_workspace",
                status="observed",
                structured_content={"executionDisposition": "succeeded"},
            ),
        ),
        OBSERVATION_ONLY,
        set(),
        {},
        prior_observation_only_turns=4,
        prior_no_progress_turns=2,
        budget=RunBudget(
            max_model_calls=5,
            max_tool_calls=5,
            max_observation_bytes=1_024,
            max_wall_time_ms=10_000,
        ),
    )
    assert decision.evidence.action_progress
    assert not decision.evidence.observation_only
    assert decision.observation_only_turns == 0
    assert decision.no_progress_turns == 0
    assert decision.gate_reason is None
