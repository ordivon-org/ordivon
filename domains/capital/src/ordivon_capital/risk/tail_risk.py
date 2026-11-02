"""Descriptive historical expected-shortfall statistic without effects."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from .risk_values import PortfolioRiskError, _float


def historical_expected_shortfall(
    returns: Sequence[Any],
    *,
    confidence: float = 0.975,
) -> dict[str, Any]:
    """Empirical one-period loss VaR and expected shortfall.

    This is a descriptive historical tail statistic. It performs no regulatory
    capital calculation, distribution fitting, forecasting, or liquidity-horizon
    scaling.
    """

    if not (0 < confidence < 1):
        raise PortfolioRiskError("confidence must be in (0, 1)")
    if len(returns) < 20:
        raise PortfolioRiskError(
            "at least 20 returns are required for historical expected shortfall"
        )

    values = np.asarray(
        [_float(value, f"returns[{i}]") for i, value in enumerate(returns)],
        dtype=float,
    )
    losses = -values
    value_at_risk = float(np.quantile(losses, confidence, method="linear"))
    tail = losses[losses >= value_at_risk]
    if tail.size == 0:
        raise PortfolioRiskError("expected-shortfall tail set is empty")
    expected_shortfall = float(np.mean(tail))

    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.risk.historical-expected-shortfall",
        "componentId": "historical-expected-shortfall",
        "method": "EMPIRICAL_HISTORICAL_TAIL_MEAN",
        "confidence": format(confidence, ".6f"),
        "observationCount": int(values.size),
        "tailObservationCount": int(tail.size),
        "valueAtRiskLossFraction": format(value_at_risk, ".8f"),
        "expectedShortfallLossFraction": format(expected_shortfall, ".8f"),
        "liquidityHorizonScalingApplied": False,
        "regulatoryCapitalCalculation": False,
    }
