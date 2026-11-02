"""Read-only historical dependence and walk-forward estimator mechanics.

These estimates are observations, not hedge authorization or trade execution.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from statistics import median
from typing import Any

import numpy as np
from scipy.stats import linregress
from sklearn.linear_model import HuberRegressor, LinearRegression
from sklearn.model_selection import TimeSeriesSplit

from .risk_values import PortfolioRiskError, _float


def completed_log_returns(
    observations: Sequence[Mapping[str, Any]],
    *,
    instrument_id: str,
) -> dict[int, float]:
    if len(observations) < 2:
        raise PortfolioRiskError("at least two completed price observations are required")
    out: dict[int, float] = {}
    previous_ts = -1
    previous_close: float | None = None
    for i, row in enumerate(observations):
        ts = row.get("observedAtMs")
        if not isinstance(ts, int) or ts < 0:
            raise PortfolioRiskError(
                f"observations[{i}].observedAtMs must be a non-negative integer"
            )
        if ts <= previous_ts:
            raise PortfolioRiskError("price observations must be strictly increasing")
        previous_ts = ts
        close = _float(row.get("close"), f"observations[{i}].close")
        if close <= 0:
            raise PortfolioRiskError("close must be positive")
        if previous_close is not None:
            out[ts] = math.log(close / previous_close)
        previous_close = close
    return out


def _paired_stats(base: Sequence[float], proxy: Sequence[float]) -> dict[str, float] | None:
    if len(base) != len(proxy) or len(base) < 3:
        return None
    base_arr = np.asarray(base, dtype=float)
    proxy_arr = np.asarray(proxy, dtype=float)
    vx = float(np.var(base_arr, ddof=1))
    vy = float(np.var(proxy_arr, ddof=1))
    if vx <= 0 or vy <= 0:
        return None

    fit = linregress(proxy_arr, base_arr)
    beta = float(fit.slope)
    corr = float(fit.rvalue)
    residual = base_arr - (float(fit.intercept) + beta * proxy_arr)
    vr = float(np.var(residual, ddof=1))
    variance_reduction = 1 - vr / vx
    return {
        "correlation": corr,
        "beta": beta,
        "baseVariance": vx,
        "proxyVariance": vy,
        "residualVariance": vr,
        "varianceReductionAtFullSampleBeta": variance_reduction,
    }


def analyze_dependence(
    *,
    base_instrument_id: str,
    base_returns: Mapping[int, float],
    proxy_instrument_id: str,
    proxy_returns: Mapping[int, float],
    short_window: int = 20,
    medium_window: int = 60,
    rolling_window: int = 20,
) -> dict[str, Any]:
    """Estimate historical dependence across full, rolling, and downside samples."""

    for label, value in (
        ("short_window", short_window),
        ("medium_window", medium_window),
        ("rolling_window", rolling_window),
    ):
        if not isinstance(value, int) or value < 3:
            raise PortfolioRiskError(f"{label} must be an integer >= 3")

    timestamps = sorted(set(base_returns) & set(proxy_returns))
    if len(timestamps) < max(rolling_window, 8):
        raise PortfolioRiskError("insufficient overlapping returns for dependence analysis")
    base = [_float(base_returns[t], f"base_returns[{t}]") for t in timestamps]
    proxy = [_float(proxy_returns[t], f"proxy_returns[{t}]") for t in timestamps]

    full = _paired_stats(base, proxy)
    if full is None:
        raise PortfolioRiskError("degenerate return variance prevents dependence analysis")

    def trailing(window: int) -> dict[str, float] | None:
        if len(base) < window:
            return None
        return _paired_stats(base[-window:], proxy[-window:])

    short = trailing(short_window)
    medium = trailing(medium_window)

    downside_pairs = [(x, y) for x, y in zip(base, proxy) if x < 0]
    downside = (
        _paired_stats([x for x, _ in downside_pairs], [y for _, y in downside_pairs])
        if len(downside_pairs) >= 8
        else None
    )

    rolling: list[dict[str, float]] = []
    for end in range(rolling_window, len(base) + 1):
        stat = _paired_stats(base[end - rolling_window : end], proxy[end - rolling_window : end])
        if stat is not None:
            rolling.append(stat)
    rolling_betas = [row["beta"] for row in rolling]
    rolling_corrs = [row["correlation"] for row in rolling]

    beta_range = [min(rolling_betas), max(rolling_betas)] if rolling_betas else None
    structural_warnings: list[str] = []
    short_medium_gap: float | None = None
    if short is not None and medium is not None:
        short_medium_gap = abs(short["correlation"] - medium["correlation"])
        if short["correlation"] * medium["correlation"] < 0:
            structural_warnings.append("CORRELATION_SIGN_CHANGE")
    beta_range_width: float | None = None
    beta_range_to_median_abs: float | None = None
    if beta_range is not None:
        lo, hi = beta_range
        beta_range_width = hi - lo
        if lo * hi < 0:
            structural_warnings.append("ROLLING_BETA_SIGN_CHANGE")
        abs_med = abs(median(rolling_betas))
        if abs_med > 1e-12:
            beta_range_to_median_abs = beta_range_width / abs_med

    def render(stat: dict[str, float] | None) -> dict[str, str] | None:
        if stat is None:
            return None
        return {k: format(v, ".6f") for k, v in stat.items()}

    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.risk.historical-dependence-analysis",
        "componentId": "portfolio-dependence-analysis",
        "baseInstrumentId": base_instrument_id,
        "proxyInstrumentId": proxy_instrument_id,
        "overlapReturnCount": len(timestamps),
        "fullWindow": render(full),
        "shortWindow": {"returns": short_window, "stats": render(short)},
        "mediumWindow": {"returns": medium_window, "stats": render(medium)},
        "downsideWindow": {
            "baseNegativeReturnCount": len(downside_pairs),
            "stats": render(downside),
        },
        "rollingWindow": {
            "returns": rolling_window,
            "sampleCount": len(rolling),
            "betaMin": format(min(rolling_betas), ".6f") if rolling_betas else None,
            "betaMedian": format(median(rolling_betas), ".6f") if rolling_betas else None,
            "betaMax": format(max(rolling_betas), ".6f") if rolling_betas else None,
            "correlationMin": format(min(rolling_corrs), ".6f") if rolling_corrs else None,
            "correlationMedian": format(median(rolling_corrs), ".6f") if rolling_corrs else None,
            "correlationMax": format(max(rolling_corrs), ".6f") if rolling_corrs else None,
        },
        "diagnostics": {
            "shortMediumCorrelationGap": format(short_medium_gap, ".6f")
            if short_medium_gap is not None
            else None,
            "rollingBetaRangeWidth": format(beta_range_width, ".6f")
            if beta_range_width is not None
            else None,
            "rollingBetaRangeToMedianAbs": format(beta_range_to_median_abs, ".6f")
            if beta_range_to_median_abs is not None
            else None,
        },
        "structuralWarnings": structural_warnings,
    }


def validate_dependence_model(
    *,
    base_instrument_id: str,
    base_returns: Mapping[int, float],
    proxy_instrument_id: str,
    proxy_returns: Mapping[int, float],
    n_splits: int = 5,
    gap: int = 0,
) -> dict[str, Any]:
    """Walk-forward validation for the historical dependence model.

    Uses scikit-learn's TimeSeriesSplit, ordinary least squares as the primary
    estimator, and HuberRegressor as a robust challenger. The result is
    continuous validation evidence only; this function does not invent a
    pass/fail threshold or approve a hedge.
    """

    if not isinstance(n_splits, int) or n_splits < 2:
        raise PortfolioRiskError("n_splits must be an integer >= 2")
    if not isinstance(gap, int) or gap < 0:
        raise PortfolioRiskError("gap must be a non-negative integer")

    timestamps = sorted(set(base_returns) & set(proxy_returns))
    if len(timestamps) < max(30, n_splits + 8):
        raise PortfolioRiskError("insufficient overlapping returns for walk-forward validation")

    y = np.asarray(
        [_float(base_returns[t], f"base_returns[{t}]") for t in timestamps],
        dtype=float,
    )
    x = np.asarray(
        [_float(proxy_returns[t], f"proxy_returns[{t}]") for t in timestamps],
        dtype=float,
    ).reshape(-1, 1)

    splitter = TimeSeriesSplit(n_splits=n_splits, gap=gap)
    folds: list[dict[str, Any]] = []
    primary_variance_reductions: list[float] = []
    challenger_variance_reductions: list[float] = []
    primary_maes: list[float] = []
    challenger_maes: list[float] = []
    primary_betas: list[float] = []
    challenger_betas: list[float] = []

    for fold_id, (train_idx, test_idx) in enumerate(splitter.split(x), start=1):
        if len(train_idx) < 8 or len(test_idx) < 2:
            raise PortfolioRiskError("walk-forward split produced an undersized train/test fold")

        primary = LinearRegression().fit(x[train_idx], y[train_idx])
        challenger = HuberRegressor().fit(x[train_idx], y[train_idx])

        primary_pred = primary.predict(x[test_idx])
        challenger_pred = challenger.predict(x[test_idx])
        y_test = y[test_idx]

        base_variance = float(np.var(y_test, ddof=1))
        primary_residual = y_test - primary_pred
        challenger_residual = y_test - challenger_pred
        primary_residual_variance = float(np.var(primary_residual, ddof=1))
        challenger_residual_variance = float(np.var(challenger_residual, ddof=1))

        primary_vr = None if base_variance <= 0 else 1 - primary_residual_variance / base_variance
        challenger_vr = (
            None if base_variance <= 0 else 1 - challenger_residual_variance / base_variance
        )

        primary_mae = float(np.mean(np.abs(primary_residual)))
        challenger_mae = float(np.mean(np.abs(challenger_residual)))
        primary_beta = float(primary.coef_[0])
        challenger_beta = float(challenger.coef_[0])

        if primary_vr is not None:
            primary_variance_reductions.append(primary_vr)
        if challenger_vr is not None:
            challenger_variance_reductions.append(challenger_vr)
        primary_maes.append(primary_mae)
        challenger_maes.append(challenger_mae)
        primary_betas.append(primary_beta)
        challenger_betas.append(challenger_beta)

        folds.append(
            {
                "fold": fold_id,
                "trainCount": int(len(train_idx)),
                "testCount": int(len(test_idx)),
                "trainStartObservedAtMs": int(timestamps[int(train_idx[0])]),
                "trainEndObservedAtMs": int(timestamps[int(train_idx[-1])]),
                "testStartObservedAtMs": int(timestamps[int(test_idx[0])]),
                "testEndObservedAtMs": int(timestamps[int(test_idx[-1])]),
                "primary": {
                    "estimator": "sklearn.linear_model.LinearRegression",
                    "beta": format(primary_beta, ".6f"),
                    "intercept": format(float(primary.intercept_), ".6f"),
                    "oosMeanAbsoluteError": format(primary_mae, ".8f"),
                    "oosResidualVariance": format(primary_residual_variance, ".10f"),
                    "oosVarianceReductionVsUnhedged": (
                        format(primary_vr, ".6f") if primary_vr is not None else None
                    ),
                },
                "challenger": {
                    "estimator": "sklearn.linear_model.HuberRegressor",
                    "beta": format(challenger_beta, ".6f"),
                    "intercept": format(float(challenger.intercept_), ".6f"),
                    "oosMeanAbsoluteError": format(challenger_mae, ".8f"),
                    "oosResidualVariance": format(challenger_residual_variance, ".10f"),
                    "oosVarianceReductionVsUnhedged": (
                        format(challenger_vr, ".6f") if challenger_vr is not None else None
                    ),
                },
                "unhedgedTestVariance": format(base_variance, ".10f"),
            }
        )

    def _summary(values: Sequence[float]) -> dict[str, str] | None:
        if not values:
            return None
        return {
            "min": format(min(values), ".6f"),
            "median": format(median(values), ".6f"),
            "max": format(max(values), ".6f"),
        }

    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.risk.dependence-model-validation",
        "componentId": "portfolio-dependence-analysis",
        "validationMethod": "SCIKIT_LEARN_WALK_FORWARD_TIME_SERIES_SPLIT",
        "baseInstrumentId": base_instrument_id,
        "proxyInstrumentId": proxy_instrument_id,
        "overlapReturnCount": len(timestamps),
        "nSplits": n_splits,
        "gap": gap,
        "primaryEstimator": "sklearn.linear_model.LinearRegression",
        "challengerEstimator": "sklearn.linear_model.HuberRegressor",
        "folds": folds,
        "summary": {
            "primaryOosVarianceReduction": _summary(primary_variance_reductions),
            "challengerOosVarianceReduction": _summary(challenger_variance_reductions),
            "primaryOosMeanAbsoluteError": _summary(primary_maes),
            "challengerOosMeanAbsoluteError": _summary(challenger_maes),
            "primaryBeta": _summary(primary_betas),
            "challengerBeta": _summary(challenger_betas),
        },
    }
