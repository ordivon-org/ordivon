"""Descriptive historical expected-shortfall statistic without effects."""

from __future__ import annotations

import math
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
    # Integrate the inverse empirical CDF over (confidence, 1], rather
    # than averaging every value at/above an interpolated VaR threshold.
    # The latter gives the wrong tail probability for finite samples and
    # overweights tied observations at the boundary.
    losses = np.sort(-values)
    value_at_risk = float(np.quantile(losses, confidence, method="inverted_cdf"))
    tail_mass = (1.0 - confidence) * losses.size
    nearest_integer = round(tail_mass)
    if nearest_integer >= 1 and math.isclose(
        tail_mass, nearest_integer, rel_tol=0.0, abs_tol=1e-12
    ):
        tail_mass = float(nearest_integer)
    whole_observations = int(tail_mass)
    fractional_observation = tail_mass - whole_observations
    weighted_tail = (
        [float(loss) / tail_mass for loss in losses[-whole_observations:]]
        if whole_observations
        else []
    )
    if fractional_observation:
        weighted_tail.append(
            float(losses[-whole_observations - 1]) * (fractional_observation / tail_mass)
        )
    expected_shortfall = math.fsum(weighted_tail)
    if not math.isfinite(expected_shortfall):
        raise PortfolioRiskError("expected-shortfall aggregate is non-finite")

    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.risk.historical-expected-shortfall",
        "componentId": "historical-expected-shortfall",
        "method": "EMPIRICAL_QUANTILE_INTEGRATED_TAIL",
        "confidence": format(confidence, ".6f"),
        "observationCount": int(values.size),
        "tailObservationCount": whole_observations + int(fractional_observation > 0),
        "effectiveTailObservationWeight": format(tail_mass, ".12g"),
        "valueAtRiskLossFraction": format(value_at_risk, ".8f"),
        "expectedShortfallLossFraction": format(expected_shortfall, ".8f"),
        "liquidityHorizonScalingApplied": False,
        "regulatoryCapitalCalculation": False,
    }
