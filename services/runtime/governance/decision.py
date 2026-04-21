from __future__ import annotations

from dataclasses import dataclass, field


VALID_GOVERNANCE_DECISIONS = {"execute", "escalate", "reject"}


@dataclass(frozen=True, slots=True)
class GovernanceAdvisoryHint:
    target: str
    hint_type: str
    summary: str
    evidence_object_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, object]:
        return {
            "target": self.target,
            "hint_type": self.hint_type,
            "summary": self.summary,
            "evidence_object_ids": list(self.evidence_object_ids),
        }


@dataclass(frozen=True, slots=True)
class GovernanceDecision:
    decision: str
    reasons: list[str] = field(default_factory=list)
    source: str = "governance.unknown"
    advisory_hints: tuple[GovernanceAdvisoryHint, ...] = field(default_factory=tuple)
    policy_set_id: str = "governance.unknown"
    active_policy_ids: tuple[str, ...] = field(default_factory=tuple)
    default_decision_rule_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.decision not in VALID_GOVERNANCE_DECISIONS:
            raise ValueError(f"Unsupported governance decision: {self.decision}")

    @property
    def allowed(self) -> bool:
        return self.decision == "execute"

    def allows_execution(self) -> bool:
        return self.decision == "execute"

    def to_payload(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "reasons": list(self.reasons),
            "source": self.source,
            "advisory_hints": [hint.to_payload() for hint in self.advisory_hints],
            "policy_set_id": self.policy_set_id,
            "active_policy_ids": list(self.active_policy_ids),
            "default_decision_rule_ids": list(self.default_decision_rule_ids),
        }


def build_governance_decision(
    *,
    decision: str,
    reasons: list[str] | None = None,
    source: str,
    advisory_hints: tuple[GovernanceAdvisoryHint, ...] | list[GovernanceAdvisoryHint] | None = None,
    policy_set_id: str = "governance.unknown",
    active_policy_ids: tuple[str, ...] | list[str] | None = None,
    default_decision_rule_ids: tuple[str, ...] | list[str] | None = None,
) -> GovernanceDecision:
    return GovernanceDecision(
        decision=decision,
        reasons=list(reasons or []),
        source=source,
        advisory_hints=tuple(advisory_hints or ()),
        policy_set_id=policy_set_id,
        active_policy_ids=tuple(active_policy_ids or ()),
        default_decision_rule_ids=tuple(default_decision_rule_ids or ()),
    )


def recommendation_governance_view(
    *,
    decision: str | None,
    reason: str | None,
    source: str | None,
    policy_set_id: str | None = None,
    active_policy_ids: list[str] | tuple[str, ...] | None = None,
    default_decision_rule_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, object] | None:
    if decision is None:
        return None
    parsed = build_governance_decision(
        decision=decision,
        reasons=[reason] if reason else [],
        source=source or "recommendation.recorded_decision",
        policy_set_id=policy_set_id or "recommendation.recorded_policy_source",
        active_policy_ids=active_policy_ids or (),
        default_decision_rule_ids=default_decision_rule_ids or (),
    )
    return parsed.to_payload()
