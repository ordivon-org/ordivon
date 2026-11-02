"""Task-local semantic-refinement witness comparator (no policy or domain authority).

Inputs are owner-provided *callbacks*; a model's plan, narrative, or completion
claim is deliberately not an input. This checks only the observations actually
returned by those callbacks. Binding a provider to a genuine owner, proving
trace completeness, enforcing effects, and establishing domain truth remain
the caller's independently qualified obligations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum


class Standing(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Obligation:
    """Exact consumer/attempt/source/specification binding."""

    work_ref: str
    source_cut: str
    goal_ref: str
    consumer_ref: str
    attempt_ref: str

    def valid(self) -> bool:
        return all(
            isinstance(value, str) and bool(value.strip())
            for value in (
                self.work_ref,
                self.source_cut,
                self.goal_ref,
                self.consumer_ref,
                self.attempt_ref,
            )
        )


@dataclass(frozen=True)
class Action:
    """An effect event *observed by* the execution owner, not a proposed plan."""

    binding: Obligation
    operation: str
    resource: str


@dataclass(frozen=True)
class ActionTrace:
    binding: Obligation
    actions: tuple[Action, ...]
    complete: bool
    evidence_ref: str


@dataclass(frozen=True)
class GoalObservation:
    binding: Obligation
    standing: Standing
    evidence_ref: str


@dataclass(frozen=True)
class SemanticResult:
    authorization: Standing
    completion: Standing
    overall: Standing
    authorization_reason: str
    completion_reason: str
    evidence_refs: tuple[str, ...]
    claim_boundary: str = (
        "Conditional on caller-qualified independent owner callbacks, "
        "action-time enforcement, trace completeness and domain observation; "
        "not permission, not a proof of provider authenticity, and not "
        "proof of source-to-installed implementation refinement."
    )


def _aggregate(authorization: Standing, completion: Standing) -> Standing:
    if Standing.FAIL in (authorization, completion):
        return Standing.FAIL
    if authorization is Standing.PASS and completion is Standing.PASS:
        return Standing.PASS
    return Standing.UNKNOWN


def examine_semantic_refinement(
    obligation: Obligation,
    *,
    read_execution_trace: Callable[[Obligation], ActionTrace | None],
    action_authorized: Callable[[Obligation, Action], bool | None],
    observe_goal: Callable[[Obligation], GoalObservation | None],
) -> SemanticResult:
    """Evaluate two independent obligations without using an Agent's self-report.

    FAIL means a qualified owner witness contradicts the requirement. UNKNOWN
    means the supplied callbacks could not establish the claim. PASS is scoped
    to the exact obligation and to the *assumed* integrity of these callbacks.
    """
    if not obligation.valid():
        raise ValueError("exact nonempty obligation identity is required")

    evidence: set[str] = set()
    auth = Standing.UNKNOWN
    auth_reason = "EXECUTION_TRACE_UNKNOWN"

    try:
        trace = read_execution_trace(obligation)
        if (
            trace is not None
            and trace.binding == obligation
            and bool(trace.evidence_ref.strip())
            and isinstance(trace.actions, tuple)
            and all(action.binding == obligation for action in trace.actions)
        ):
            evidence.add(trace.evidence_ref)
            unknown = False
            forbidden = False
            for action in trace.actions:
                try:
                    decision = action_authorized(obligation, action)
                except Exception:
                    decision = None
                if decision is False:
                    forbidden = True
                elif decision is not True:
                    unknown = True
            if forbidden:
                auth = Standing.FAIL
                auth_reason = "OBSERVED_UNAUTHORIZED_ACTION"
            elif trace.complete and not unknown:
                auth = Standing.PASS
                auth_reason = "OWNER_TRACE_CLOSED_AND_ACTIONS_AUTHORIZED"
            else:
                auth_reason = "UNPROVEN_TRACE_CLOSURE_OR_ACTION_GRANT"
        else:
            auth_reason = "OWNER_TRACE_MISSING_OR_FOREIGN"
    except Exception:
        # An unavailable owner is not an authorization proof. Do not make
        # operational errors look like a model-verified negative witness.
        auth = Standing.UNKNOWN
        auth_reason = "EXECUTION_OWNER_ERROR"

    completion = Standing.UNKNOWN
    completion_reason = "DOMAIN_OBSERVATION_UNKNOWN"
    try:
        observation = observe_goal(obligation)
        if (
            observation is not None
            and observation.binding == obligation
            and bool(observation.evidence_ref.strip())
            and isinstance(observation.standing, Standing)
        ):
            evidence.add(observation.evidence_ref)
            completion = observation.standing
            completion_reason = "OWNER_DOMAIN_OBSERVATION"
        else:
            completion_reason = "DOMAIN_OBSERVATION_MISSING_OR_FOREIGN"
    except Exception:
        completion_reason = "DOMAIN_OWNER_ERROR"

    return SemanticResult(
        authorization=auth,
        completion=completion,
        overall=_aggregate(auth, completion),
        authorization_reason=auth_reason,
        completion_reason=completion_reason,
        evidence_refs=tuple(sorted(evidence)),
    )
