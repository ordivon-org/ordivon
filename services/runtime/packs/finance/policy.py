from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FinancePolicyOverlayRef:
    policy_id: str
    path: Path


def finance_trading_limits_policy_path() -> Path:
    return Path(__file__).resolve().parents[2] / "policies" / "trading_limits.yaml"


def get_finance_policy_overlays() -> tuple[FinancePolicyOverlayRef, ...]:
    return (
        FinancePolicyOverlayRef(
            policy_id="finance.trading_limits",
            path=finance_trading_limits_policy_path(),
        ),
    )
