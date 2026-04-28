"""Policy State Machine — validates and executes Policy lifecycle transitions.

Pure domain logic. No ORM, no DB writes, no RiskEngine, no side effects.
Operates on PolicyRecord value objects from domains/policies/models.py.

Does NOT: activate policies, enforce policies, modify Pack policies,
or interact with any runtime governance component.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from domains.policies.models import (
    PolicyRecord,
    PolicyState,
    PolicyRisk,
    PolicyEvidenceRef,
    PolicyRollbackPlan,
    PolicyOwner,
)


# ── Allowed Transitions ──────────────────────────────────────────────

# Maps current state → set of allowed next states
_ALLOWED_TRANSITIONS: dict[PolicyState, set[PolicyState]] = {
    PolicyState.DRAFT: {
        PolicyState.PROPOSED,
        PolicyState.REJECTED,
    },
    PolicyState.PROPOSED: {
        PolicyState.APPROVED,
        PolicyState.REJECTED,
    },
    PolicyState.APPROVED: {
        PolicyState.ACTIVE_SHADOW,
        PolicyState.REJECTED,
    },
    PolicyState.ACTIVE_SHADOW: {
        PolicyState.ACTIVE_ENFORCED,
        PolicyState.DEPRECATED,
    },
    PolicyState.ACTIVE_ENFORCED: {
        PolicyState.DEPRECATED,
        PolicyState.ROLLED_BACK,
    },
    # Terminal states — no outgoing transitions
    PolicyState.DEPRECATED: set(),
    PolicyState.ROLLED_BACK: set(),
    PolicyState.REJECTED: set(),
}

# States that require evidence_refs, owner, and rollback_plan before activation
_ACTIVATION_STATES: set[PolicyState] = {
    PolicyState.ACTIVE_SHADOW,
    PolicyState.ACTIVE_ENFORCED,
}


@dataclass(frozen=True)
class TransitionResult:
    """The result of a state transition attempt."""

    allowed: bool
    new_policy: PolicyRecord | None = None
    reasons: tuple[str, ...] = ()

    @property
    def rejected(self) -> bool:
        return not self.allowed


# ── Transition Guards ────────────────────────────────────────────────

# Each guard is a function (policy, target_state) → (allowed: bool, reason: str)
GuardFunc = Callable[[PolicyRecord, PolicyState], tuple[bool, str]]


def _guard_requires_evidence(policy: PolicyRecord, target: PolicyState) -> tuple[bool, str]:
    """Require evidence_refs for activation states."""
    if target in _ACTIVATION_STATES:
        if not policy.evidence_refs:
            return False, "Activation requires at least one PolicyEvidenceRef."
    return True, ""


def _guard_requires_owner(policy: PolicyRecord, target: PolicyState) -> tuple[bool, str]:
    """Require owner for activation states."""
    if target in _ACTIVATION_STATES:
        if policy.owner is None:
            return False, "Activation requires a PolicyOwner."
    return True, ""


def _guard_requires_rollback_plan(policy: PolicyRecord, target: PolicyState) -> tuple[bool, str]:
    """Require rollback_plan for activation states."""
    if target in _ACTIVATION_STATES:
        if policy.rollback_plan is None:
            return False, "Activation requires a PolicyRollbackPlan."
    return True, ""


def _guard_active_enforced_requires_explicit_approval(policy: PolicyRecord, target: PolicyState) -> tuple[bool, str]:
    """ACTIVE_ENFORCED requires the policy to have been through ACTIVE_SHADOW first.

    The shadow→enforced transition is itself the signal that shadow mode
    observation is complete. We validate that the predecessor was in shadow
    state by checking the policy's current state (ACTIVE_SHADOW is the only
    valid source for this transition per the allowed transitions table).
    """
    if target == PolicyState.ACTIVE_ENFORCED:
        if policy.state != PolicyState.ACTIVE_SHADOW:
            return False, "ACTIVE_ENFORCED requires transition from ACTIVE_SHADOW."
    return True, ""


def _guard_rollback_requires_reason(policy: PolicyRecord, target: PolicyState) -> tuple[bool, str]:
    """Rollback must provide a reason."""
    if target == PolicyState.ROLLED_BACK:
        # The reason is set on the resulting PolicyRecord, validated at transition time
        pass  # validated in PolicyStateMachine.transition()
    return True, ""


def _guard_no_direct_activation_to_enforced(policy: PolicyRecord, target: PolicyState) -> tuple[bool, str]:
    """Cannot jump from draft/proposed/approved directly to ACTIVE_ENFORCED."""
    if target == PolicyState.ACTIVE_ENFORCED:
        if policy.state not in (PolicyState.ACTIVE_SHADOW,):
            return False, (
                f"Cannot transition from {policy.state.value} directly to ACTIVE_ENFORCED. "
                "Must pass through ACTIVE_SHADOW first."
            )
    return True, ""


def _guard_no_draft_to_shadow(policy: PolicyRecord, target: PolicyState) -> tuple[bool, str]:
    """Draft cannot jump directly to active_shadow."""
    if target == PolicyState.ACTIVE_SHADOW:
        if policy.state == PolicyState.DRAFT:
            return False, "Draft cannot transition directly to ACTIVE_SHADOW."
    return True, ""


# All guards applied during transition validation
_ALL_GUARDS: tuple[GuardFunc, ...] = (
    _guard_requires_evidence,
    _guard_requires_owner,
    _guard_requires_rollback_plan,
    _guard_active_enforced_requires_explicit_approval,
    _guard_no_direct_activation_to_enforced,
    _guard_no_draft_to_shadow,
)


# ── State Machine ────────────────────────────────────────────────────


class PolicyStateMachine:
    """Validates and executes Policy lifecycle transitions.

    Pure domain logic. No side effects. No ORM. No RiskEngine.
    Each transition produces a new PolicyRecord (immutable pattern).

    Usage:
        machine = PolicyStateMachine()
        result = machine.transition(policy, PolicyState.PROPOSED)
        if result.allowed:
            new_policy = result.new_policy
    """

    def __init__(self):
        self._guards: list[GuardFunc] = list(_ALL_GUARDS)

    def transition(self, policy: PolicyRecord, target: PolicyState, **overrides) -> TransitionResult:
        """Attempt to transition a Policy from its current state to the target state.

        Args:
            policy: The current PolicyRecord.
            target: The desired target PolicyState.
            **overrides: Additional keyword arguments to pass to with_state()
                         (e.g., risk, evidence_refs, owner, rollback_plan,
                         rollback_reason, deprecation_reason).

        Returns:
            TransitionResult with allowed=False if the transition is invalid,
            or allowed=True with the new PolicyRecord.
        """
        # 0. Validate same-state transition (no-op)
        if policy.state == target:
            return TransitionResult(
                allowed=False,
                reasons=(f"Policy is already in state '{target.value}'.",),
            )

        # 1. Check allowed state transition
        allowed_targets = _ALLOWED_TRANSITIONS.get(policy.state, set())
        if target not in allowed_targets:
            return TransitionResult(
                allowed=False,
                reasons=(
                    f"Invalid transition: '{policy.state.value}' → '{target.value}' "
                    f"is not allowed. Allowed: {sorted(s.value for s in allowed_targets)}.",
                ),
            )

        # 2. Run all guards
        violations: list[str] = []
        for guard in self._guards:
            allowed, reason = guard(policy, target)
            if not allowed:
                violations.append(reason)
        if violations:
            return TransitionResult(allowed=False, reasons=tuple(violations))

        # 3. Validate target-state-specific metadata
        if target == PolicyState.ROLLED_BACK:
            if not overrides.get("rollback_reason", "").strip():
                return TransitionResult(
                    allowed=False,
                    reasons=("ROLLED_BACK requires rollback_reason.",),
                )
        if target == PolicyState.DEPRECATED:
            if not overrides.get("deprecation_reason", "").strip():
                return TransitionResult(
                    allowed=False,
                    reasons=("DEPRECATED requires deprecation_reason.",),
                )

        # 4. Create new PolicyRecord with updated state
        new_policy = policy.with_state(target, **overrides)
        return TransitionResult(allowed=True, new_policy=new_policy)

    def can_transition(self, policy: PolicyRecord, target: PolicyState) -> bool:
        """Check if a transition is allowed without executing it."""
        result = self.transition(policy, target)
        return result.allowed

    @staticmethod
    def is_terminal(state: PolicyState) -> bool:
        """Check if a state is terminal (no outgoing transitions)."""
        return state in (PolicyState.DEPRECATED, PolicyState.ROLLED_BACK, PolicyState.REJECTED)

    @staticmethod
    def allowed_transitions_from(state: PolicyState) -> set[PolicyState]:
        """Return the set of states that can be transitioned to from the given state."""
        return _ALLOWED_TRANSITIONS.get(state, set())
