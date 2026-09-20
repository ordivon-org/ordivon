from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from scipy.stats import ks_2samp, wasserstein_distance
from sklearn.linear_model import HuberRegressor, LinearRegression
from sklearn.metrics import mean_absolute_error

from .portfolio_risk import PortfolioRiskError


def _finite(value: Any, label: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise PortfolioRiskError(f"non-finite value for {label}")
    return out


def _aligned(
    base_returns: Mapping[int, float],
    proxy_returns: Mapping[int, float],
) -> tuple[list[int], np.ndarray, np.ndarray]:
    timestamps = sorted(set(base_returns) & set(proxy_returns))
    if not timestamps:
        raise PortfolioRiskError("no overlapping returns")
    base = np.asarray(
        [_finite(base_returns[t], f"base_returns[{t}]") for t in timestamps],
        dtype=float,
    )
    proxy = np.asarray(
        [_finite(proxy_returns[t], f"proxy_returns[{t}]") for t in timestamps],
        dtype=float,
    )
    return timestamps, base, proxy


def assess_paired_return_data_quality(
    *,
    base_returns: Mapping[int, float],
    proxy_returns: Mapping[int, float],
    as_of_ms: int | None = None,
    expected_interval_ms: int | None = None,
) -> dict[str, Any]:
    """Measure paired-return completeness, timeliness and interval regularity."""

    if as_of_ms is not None and (not isinstance(as_of_ms, int) or as_of_ms < 0):
        raise PortfolioRiskError("as_of_ms must be a non-negative integer")
    if expected_interval_ms is not None and (
        not isinstance(expected_interval_ms, int) or expected_interval_ms <= 0
    ):
        raise PortfolioRiskError("expected_interval_ms must be a positive integer")

    timestamps, _, _ = _aligned(base_returns, proxy_returns)
    base_keys = set(base_returns)
    proxy_keys = set(proxy_returns)
    overlap = len(timestamps)
    union = len(base_keys | proxy_keys)

    gaps = np.diff(np.asarray(timestamps, dtype=np.int64)) if len(timestamps) > 1 else np.asarray([], dtype=np.int64)
    interval_stats: dict[str, Any] | None = None
    if gaps.size:
        interval_stats = {
            "medianObservedIntervalMs": int(np.median(gaps)),
            "maxObservedIntervalMs": int(np.max(gaps)),
        }
        if expected_interval_ms is not None:
            interval_stats["expectedIntervalMs"] = expected_interval_ms
            interval_stats["intervalDeviationMs"] = {
                "medianAbsolute": int(np.median(np.abs(gaps - expected_interval_ms))),
                "maxAbsolute": int(np.max(np.abs(gaps - expected_interval_ms))),
            }

    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.paired-return-data-quality",
        "componentId": "dependence-model-monitoring",
        "frameworkReference": "BCBS239_PROPORTIONAL_REFERENCE",
        "baseObservationCount": len(base_keys),
        "proxyObservationCount": len(proxy_keys),
        "overlapObservationCount": overlap,
        "unionObservationCount": union,
        "overlapToBaseRatio": format(overlap / len(base_keys), ".6f") if base_keys else None,
        "overlapToProxyRatio": format(overlap / len(proxy_keys), ".6f") if proxy_keys else None,
        "overlapToUnionRatio": format(overlap / union, ".6f") if union else None,
        "firstOverlapObservedAtMs": timestamps[0],
        "lastOverlapObservedAtMs": timestamps[-1],
        "intervalStatistics": interval_stats,
    }
    if as_of_ms is not None:
        if as_of_ms < timestamps[-1]:
            raise PortfolioRiskError("as_of_ms cannot precede the latest overlapping observation")
        result["asOfMs"] = as_of_ms
        result["latestOverlapAgeMs"] = as_of_ms - timestamps[-1]
    return result


def _fit_and_score(
    *,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    estimator_name: str,
) -> dict[str, Any]:
    if estimator_name == "LinearRegression":
        model = LinearRegression()
    elif estimator_name == "HuberRegressor":
        model = HuberRegressor()
    else:
        raise PortfolioRiskError(f"unsupported estimator: {estimator_name}")

    model.fit(x_train.reshape(-1, 1), y_train)
    pred = model.predict(x_test.reshape(-1, 1))
    residual = y_test - pred
    unhedged_variance = float(np.var(y_test, ddof=1)) if len(y_test) > 1 else 0.0
    residual_variance = float(np.var(residual, ddof=1)) if len(y_test) > 1 else 0.0
    variance_reduction = (
        None if unhedged_variance <= 0 else 1 - residual_variance / unhedged_variance
    )

    return {
        "estimator": f"sklearn.linear_model.{estimator_name}",
        "beta": format(float(model.coef_[0]), ".6f"),
        "intercept": format(float(model.intercept_), ".6f"),
        "realizedMeanAbsoluteError": format(float(mean_absolute_error(y_test, pred)), ".8f"),
        "realizedUnhedgedVariance": format(unhedged_variance, ".10f"),
        "realizedResidualVariance": format(residual_variance, ".10f"),
        "realizedVarianceReductionVsUnhedged": (
            format(variance_reduction, ".6f") if variance_reduction is not None else None
        ),
    }


def monitor_dependence_outcomes(
    *,
    base_instrument_id: str,
    proxy_instrument_id: str,
    reference_base_returns: Mapping[int, float],
    reference_proxy_returns: Mapping[int, float],
    realized_base_returns: Mapping[int, float],
    realized_proxy_returns: Mapping[int, float],
) -> dict[str, Any]:
    """Evaluate frozen reference fits against strictly later realized observations."""

    ref_ts, ref_base, ref_proxy = _aligned(reference_base_returns, reference_proxy_returns)
    realized_ts, realized_base, realized_proxy = _aligned(realized_base_returns, realized_proxy_returns)
    if len(ref_ts) < 20:
        raise PortfolioRiskError("at least 20 aligned reference returns are required")
    if len(realized_ts) < 5:
        raise PortfolioRiskError("at least 5 aligned realized returns are required")
    if ref_ts[-1] >= realized_ts[0]:
        raise PortfolioRiskError("realized outcomes must begin strictly after the reference sample")

    primary = _fit_and_score(
        x_train=ref_proxy,
        y_train=ref_base,
        x_test=realized_proxy,
        y_test=realized_base,
        estimator_name="LinearRegression",
    )
    challenger = _fit_and_score(
        x_train=ref_proxy,
        y_train=ref_base,
        x_test=realized_proxy,
        y_test=realized_base,
        estimator_name="HuberRegressor",
    )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.dependence-model-outcomes-monitoring",
        "componentId": "dependence-model-monitoring",
        "validatedComponentId": "portfolio-dependence-analysis",
        "baseInstrumentId": base_instrument_id,
        "proxyInstrumentId": proxy_instrument_id,
        "referenceObservationCount": len(ref_ts),
        "realizedObservationCount": len(realized_ts),
        "referenceStartObservedAtMs": ref_ts[0],
        "referenceEndObservedAtMs": ref_ts[-1],
        "realizedStartObservedAtMs": realized_ts[0],
        "realizedEndObservedAtMs": realized_ts[-1],
        "primary": primary,
        "challenger": challenger,
    }


def measure_dependence_drift(
    *,
    base_instrument_id: str,
    proxy_instrument_id: str,
    reference_base_returns: Mapping[int, float],
    reference_proxy_returns: Mapping[int, float],
    current_base_returns: Mapping[int, float],
    current_proxy_returns: Mapping[int, float],
) -> dict[str, Any]:
    """Measure parameter and return-distribution drift without classifying severity."""

    ref_ts, ref_base, ref_proxy = _aligned(reference_base_returns, reference_proxy_returns)
    cur_ts, cur_base, cur_proxy = _aligned(current_base_returns, current_proxy_returns)
    if len(ref_ts) < 8 or len(cur_ts) < 8:
        raise PortfolioRiskError("at least 8 aligned returns are required in each drift window")

    ref_fit = LinearRegression().fit(ref_proxy.reshape(-1, 1), ref_base)
    cur_fit = LinearRegression().fit(cur_proxy.reshape(-1, 1), cur_base)
    ref_pred = ref_fit.predict(ref_proxy.reshape(-1, 1))
    cur_pred = cur_fit.predict(cur_proxy.reshape(-1, 1))
    ref_residual_variance = float(np.var(ref_base - ref_pred, ddof=1))
    cur_residual_variance = float(np.var(cur_base - cur_pred, ddof=1))
    ref_corr = float(np.corrcoef(ref_base, ref_proxy)[0, 1])
    cur_corr = float(np.corrcoef(cur_base, cur_proxy)[0, 1])

    base_ks = ks_2samp(ref_base, cur_base, method="auto")
    proxy_ks = ks_2samp(ref_proxy, cur_proxy, method="auto")

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.dependence-model-drift-measurement",
        "componentId": "dependence-model-monitoring",
        "validatedComponentId": "portfolio-dependence-analysis",
        "baseInstrumentId": base_instrument_id,
        "proxyInstrumentId": proxy_instrument_id,
        "referenceObservationCount": len(ref_ts),
        "currentObservationCount": len(cur_ts),
        "parameterDrift": {
            "referenceBeta": format(float(ref_fit.coef_[0]), ".6f"),
            "currentBeta": format(float(cur_fit.coef_[0]), ".6f"),
            "betaDelta": format(float(cur_fit.coef_[0] - ref_fit.coef_[0]), ".6f"),
            "referenceCorrelation": format(ref_corr, ".6f"),
            "currentCorrelation": format(cur_corr, ".6f"),
            "correlationDelta": format(cur_corr - ref_corr, ".6f"),
            "referenceResidualVariance": format(ref_residual_variance, ".10f"),
            "currentResidualVariance": format(cur_residual_variance, ".10f"),
            "residualVarianceRatio": (
                format(cur_residual_variance / ref_residual_variance, ".6f")
                if ref_residual_variance > 0
                else None
            ),
        },
        "distributionDrift": {
            "baseReturnWassersteinDistance": format(
                float(wasserstein_distance(ref_base, cur_base)), ".8f"
            ),
            "proxyReturnWassersteinDistance": format(
                float(wasserstein_distance(ref_proxy, cur_proxy)), ".8f"
            ),
            "baseReturnKsStatistic": format(float(base_ks.statistic), ".6f"),
            "baseReturnKsPValue": format(float(base_ks.pvalue), ".6f"),
            "proxyReturnKsStatistic": format(float(proxy_ks.statistic), ".6f"),
            "proxyReturnKsPValue": format(float(proxy_ks.pvalue), ".6f"),
        },
    }


def build_tail_risk_report(
    series: Sequence[Mapping[str, Any]],
    *,
    confidence: float = 0.975,
) -> dict[str, Any]:
    """Compose empirical tail-risk calculations with explicit sample/horizon metadata."""

    from .portfolio_risk import historical_expected_shortfall

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
        rows.append({
            "seriesId": series_id,
            "returnHorizon": spec.get("returnHorizon"),
            "sampleLabel": spec.get("sampleLabel"),
            "liquidityHorizonDays": spec.get("liquidityHorizonDays"),
            "calculation": calculation,
        })

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.tail-risk-report",
        "componentId": "tail-risk-report",
        "confidence": format(confidence, ".6f"),
        "seriesCount": len(rows),
        "series": rows,
        "liquidityHorizonScalingApplied": False,
    }
