from __future__ import annotations

from dataclasses import dataclass, field


VALID_GOVERNANCE_DECISIONS = {"execute", "escalate", "reject"}
VALID_GOVERNANCE_SCOPES = {"system", "workflow", "action_family", "entity"}


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
class GovernanceEvidence:
    object_type: str
    object_id: str
    summary: str | None = None

    def __post_init__(self) -> None:
        if not self.object_type:
            raise ValueError("Governance evidence requires object_type.")
        if not self.object_id:
            raise ValueError("Governance evidence requires object_id.")

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "object_type": self.object_type,
            "object_id": self.object_id,
        }
        if self.summary:
            payload["summary"] = self.summary
        return payload


@dataclass(frozen=True, slots=True)
class GovernanceActor:
    actor_id: str
    actor_type: str = "system"

    def __post_init__(self) -> None:
        if not self.actor_id:
            raise ValueError("Governance actor requires actor_id.")
        if not self.actor_type:
            raise ValueError("Governance actor requires actor_type.")

    def to_payload(self) -> dict[str, object]:
        return {
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
        }


@dataclass(frozen=True, slots=True)
class GovernanceScope:
    scope_type: str = "system"
    scope_id: str | None = None

    def __post_init__(self) -> None:
        if self.scope_type not in VALID_GOVERNANCE_SCOPES:
            raise ValueError(f"Unsupported governance scope: {self.scope_type}")

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {"scope_type": self.scope_type}
        if self.scope_id:
            payload["scope_id"] = self.scope_id
        return payload


@dataclass(frozen=True, slots=True)
class GovernanceDecision:
    decision: str
    reasons: list[str] = field(default_factory=list)
    source: str = "governance.unknown"
    advisory_hints: tuple[GovernanceAdvisoryHint, ...] = field(default_factory=tuple)
    evidence: tuple[GovernanceEvidence, ...] = field(default_factory=tuple)
    actor: GovernanceActor = field(default_factory=lambda: GovernanceActor(actor_id="governance.system"))
    scope: GovernanceScope = field(default_factory=GovernanceScope)
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
            "evidence": [item.to_payload() for item in self.evidence],
            "actor": self.actor.to_payload(),
            "scope": self.scope.to_payload(),
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
    evidence: tuple[GovernanceEvidence, ...] | list[GovernanceEvidence] | None = None,
    actor: GovernanceActor | None = None,
    scope: GovernanceScope | None = None,
    policy_set_id: str = "governance.unknown",
    active_policy_ids: tuple[str, ...] | list[str] | None = None,
    default_decision_rule_ids: tuple[str, ...] | list[str] | None = None,
) -> GovernanceDecision:
    return GovernanceDecision(
        decision=decision,
        reasons=list(reasons or []),
        source=source,
        advisory_hints=tuple(advisory_hints or ()),
        evidence=tuple(evidence or ()),
        actor=actor or GovernanceActor(actor_id=source, actor_type="system"),
        scope=scope or GovernanceScope(),
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
    actor: GovernanceActor | None = None,
    scope: GovernanceScope | None = None,
) -> dict[str, object] | None:
    if decision is None:
        return None
    parsed = build_governance_decision(
        decision=decision,
        reasons=[reason] if reason else [],
        source=source or "recommendation.recorded_decision",
        actor=actor,
        scope=scope or GovernanceScope(scope_type="entity"),
        policy_set_id=policy_set_id or "recommendation.recorded_policy_source",
        active_policy_ids=active_policy_ids or (),
        default_decision_rule_ids=default_decision_rule_ids or (),
    )
    return parsed.to_payload()
