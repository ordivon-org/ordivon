"""Scoped executable falsifiers for the semantic-refinement capability."""

from dataclasses import replace
from itertools import product

import pytest

from ordivon_composition.semantic_refinement_r1 import (
    Action,
    ActionTrace,
    GoalObservation,
    Obligation,
    Standing,
    _aggregate,
    examine_semantic_refinement,
)

OBLIGATION = Obligation(
    "work:fixture", "git:source-fixture", "goal:original", "consumer:fixture", "attempt:fixture"
)
ACTION = Action(OBLIGATION, "write", "repo:example")
TRACE = ActionTrace(OBLIGATION, (ACTION,), True, "runtime:closed-trace")
GOAL = GoalObservation(OBLIGATION, Standing.PASS, "domain:independent-readback")


def check(*, trace=TRACE, goal=GOAL, authorized=True):
    return examine_semantic_refinement(
        OBLIGATION,
        read_execution_trace=lambda _: trace,
        action_authorized=lambda *_: authorized,
        observe_goal=lambda _: goal,
    )


def test_positive_requires_both_owner_projections():
    result = check()
    assert result.overall == Standing.PASS
    assert result.authorization == Standing.PASS
    assert result.completion == Standing.PASS
    assert result.evidence_refs == ("domain:independent-readback", "runtime:closed-trace")


@pytest.mark.parametrize(
    ("trace", "goal", "authorized", "expected", "reason"),
    [
        (TRACE, GOAL, False, Standing.FAIL, "OBSERVED_UNAUTHORIZED_ACTION"),
        (
            TRACE,
            replace(GOAL, standing=Standing.FAIL),
            True,
            Standing.FAIL,
            "OWNER_DOMAIN_OBSERVATION",
        ),
        (
            TRACE,
            replace(GOAL, standing=Standing.UNKNOWN),
            True,
            Standing.UNKNOWN,
            "OWNER_DOMAIN_OBSERVATION",
        ),
        (
            replace(TRACE, complete=False),
            GOAL,
            True,
            Standing.UNKNOWN,
            "UNPROVEN_TRACE_CLOSURE_OR_ACTION_GRANT",
        ),
        (
            replace(TRACE, binding=replace(OBLIGATION, source_cut="git:foreign")),
            GOAL,
            True,
            Standing.UNKNOWN,
            "OWNER_TRACE_MISSING_OR_FOREIGN",
        ),
        (
            TRACE,
            replace(GOAL, binding=replace(OBLIGATION, goal_ref="goal:altered")),
            True,
            Standing.UNKNOWN,
            "DOMAIN_OBSERVATION_MISSING_OR_FOREIGN",
        ),
        (TRACE, None, True, Standing.UNKNOWN, "DOMAIN_OBSERVATION_MISSING_OR_FOREIGN"),
        (None, GOAL, True, Standing.UNKNOWN, "OWNER_TRACE_MISSING_OR_FOREIGN"),
        (
            replace(TRACE, evidence_ref=""),
            GOAL,
            True,
            Standing.UNKNOWN,
            "OWNER_TRACE_MISSING_OR_FOREIGN",
        ),
        (
            TRACE,
            replace(GOAL, evidence_ref=""),
            True,
            Standing.UNKNOWN,
            "DOMAIN_OBSERVATION_MISSING_OR_FOREIGN",
        ),
        (TRACE, GOAL, None, Standing.UNKNOWN, "UNPROVEN_TRACE_CLOSURE_OR_ACTION_GRANT"),
        (
            replace(
                TRACE,
                actions=(
                    replace(ACTION, binding=replace(OBLIGATION, attempt_ref="attempt:other")),
                ),
            ),
            GOAL,
            True,
            Standing.UNKNOWN,
            "OWNER_TRACE_MISSING_OR_FOREIGN",
        ),
    ],
)
def test_real_semantic_counterexamples(trace, goal, authorized, expected, reason):
    result = check(trace=trace, goal=goal, authorized=authorized)
    assert result.overall == expected
    assert reason in {result.authorization_reason, result.completion_reason}


def test_model_completed_claim_has_no_ingress():
    """No model claim appears in the API; success requires actual owner callbacks."""
    fake_model_claim = {"completed": True, "testsPassed": True}
    assert fake_model_claim["completed"]
    assert check(trace=None, goal=None).overall == Standing.UNKNOWN


def test_owner_exceptions_never_become_positive_or_false_negative():
    def broken(_):
        raise ConnectionError("owner offline")

    result = examine_semantic_refinement(
        OBLIGATION,
        read_execution_trace=broken,
        action_authorized=lambda *_: True,
        observe_goal=broken,
    )
    assert result.overall == Standing.UNKNOWN
    assert result.authorization == Standing.UNKNOWN
    assert result.completion == Standing.UNKNOWN


def test_invalid_binding_rejected_before_consulting_owner():
    with pytest.raises(ValueError):
        examine_semantic_refinement(
            replace(OBLIGATION, source_cut=" "),
            read_execution_trace=lambda _: TRACE,
            action_authorized=lambda *_: True,
            observe_goal=lambda _: GOAL,
        )


def test_all_nine_three_valued_combinations():
    """Exhaustive truth table of the pure composition rule, not implementation proof."""
    for authorization, completion in product(Standing, repeat=2):
        expected = (
            Standing.FAIL
            if Standing.FAIL in (authorization, completion)
            else Standing.PASS
            if authorization is Standing.PASS and completion is Standing.PASS
            else Standing.UNKNOWN
        )
        assert _aggregate(authorization, completion) == expected


def test_one_forbidden_action_cannot_be_masked_by_allowed_actions():
    actions = (
        Action(OBLIGATION, "read", "repo:example"),
        Action(OBLIGATION, "write", "repo:forbidden"),
        Action(OBLIGATION, "read", "repo:example"),
    )
    result = examine_semantic_refinement(
        OBLIGATION,
        read_execution_trace=lambda _: replace(TRACE, actions=actions, complete=False),
        action_authorized=lambda _, action: action.resource != "repo:forbidden",
        observe_goal=lambda _: GOAL,
    )
    assert result.authorization == Standing.FAIL
    assert result.overall == Standing.FAIL


def test_a_qualified_forbidden_witness_survives_a_later_oracle_failure():
    def partly_unavailable(_, action):
        if action.resource == "repo:forbidden":
            return False
        raise ConnectionError("next grant oracle unavailable")

    trace = replace(TRACE, actions=(Action(OBLIGATION, "write", "repo:forbidden"), ACTION))
    result = examine_semantic_refinement(
        OBLIGATION,
        read_execution_trace=lambda _: trace,
        action_authorized=partly_unavailable,
        observe_goal=lambda _: GOAL,
    )
    assert result.overall == Standing.FAIL
    assert result.authorization_reason == "OBSERVED_UNAUTHORIZED_ACTION"
