"""Risk-owned descriptive tail-report composition."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .risk_values import PortfolioRiskError
from .tail_risk import historical_expected_shortfall


def build_tail_risk_report(
    series: Sequence[Mapping[str, Any]],
    *,
    confidence: float = 0.975,
) -> dict[str, Any]:
    """Compose empirical tail-risk calculations with explicit sample/horizon metadata."""

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, spec in enumerate(series):
        series_id = str(spec.get("seriesId") or "").strip()
        returns = spec.get("returns")
        if not series_id or series_id in seen:
            raise PortfolioRiskError(f"series[{i}].seriesId must be unique and non-empty")
        if not isinstance(returns, Sequence) or isinstance(returns, (str, bytes)):
            raise PortfolioRiskError(f"series[{i}].returns must be a sequence")
        seen.add(series_id)
        calculation = historical_expected_shortfall(returns, confidence=confidence)
        rows.append(
            {
                "seriesId": series_id,
                "returnHorizon": spec.get("returnHorizon"),
                "sampleLabel": spec.get("sampleLabel"),
                "liquidityHorizonDays": spec.get("liquidityHorizonDays"),
                "calculation": calculation,
            }
        )

    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.risk.tail-risk-report",
        "componentId": "tail-risk-report",
        "confidence": format(confidence, ".6f"),
        "seriesCount": len(rows),
        "series": rows,
        "liquidityHorizonScalingApplied": False,
    }
