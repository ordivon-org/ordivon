from __future__ import annotations

from dataclasses import dataclass, field

from governance_engine.risk_engine.policies.forbidden_symbols import ForbiddenSymbolsPolicy
from packs.finance.policy import get_finance_policy_overlays
from packs.finance.tool_refs import get_finance_tool_refs


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
            active_policy_ids=("forbidden_symbols_policy", "trading_discipline_policy"),
            default_decision_rule_ids=(
                "default_no_actions_escalate",
                "default_pass_execute",
            ),
        )

    def get_active_policies(self) -> list[object]:
        # Only return policies that can validate AnalysisResult.
        # TradingDisciplinePolicy is intake-only and is applied directly
        # in RiskEngine.validate_intake().
        return [ForbiddenSymbolsPolicy()]

    def get_active_policy_ids(self) -> tuple[str, ...]:
        return self.get_active_snapshot().active_policy_ids

    def get_finance_policy_overlay_refs(self) -> tuple[str, ...]:
        return tuple(str(ref.path) for ref in get_finance_policy_overlays())

    def get_finance_tool_namespace_refs(self) -> dict[str, tuple[str, ...]]:
        refs = get_finance_tool_refs()
        return {
            "market_data": refs.market_data,
            "news_data": refs.news_data,
            "broker": refs.broker,
        }
