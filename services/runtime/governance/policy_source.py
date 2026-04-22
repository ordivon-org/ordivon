from __future__ import annotations

from dataclasses import dataclass, field

from governance.risk_engine.policies.forbidden_symbols import ForbiddenSymbolsPolicy


@dataclass(frozen=True, slots=True)
class GovernancePolicySnapshot:
    policy_set_id: str
    active_policy_ids: tuple[str, ...] = field(default_factory=tuple)
    default_decision_rule_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, object]:
        return {
            "policy_set_id": self.policy_set_id,
            "active_policy_ids": list(self.active_policy_ids),
            "default_decision_rule_ids": list(self.default_decision_rule_ids),
        }


class GovernancePolicySource:
    """Minimal source-of-truth for active governance policies."""

    def get_active_snapshot(self) -> GovernancePolicySnapshot:
        return GovernancePolicySnapshot(
            policy_set_id="governance.default.v1",
            active_policy_ids=("forbidden_symbols_policy",),
            default_decision_rule_ids=(
                "default_no_actions_escalate",
                "default_pass_execute",
            ),
        )

    def get_active_policies(self) -> list[object]:
        return [ForbiddenSymbolsPolicy()]

    def get_active_policy_ids(self) -> tuple[str, ...]:
        return self.get_active_snapshot().active_policy_ids
