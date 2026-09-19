from __future__ import annotations

from decimal import Decimal, InvalidOperation
import math
from statistics import median

import numpy as np
from scipy.stats import linregress
from sklearn.linear_model import HuberRegressor, LinearRegression
from sklearn.model_selection import TimeSeriesSplit
from typing import Any, Mapping, Sequence


class PortfolioRiskError(ValueError):
    """Fail-closed validation error for the read-only portfolio risk observatory."""


def _d(value: Any, label: str) -> Decimal:
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise PortfolioRiskError(f"invalid decimal for {label}") from exc
    if not out.is_finite():
        raise PortfolioRiskError(f"non-finite decimal for {label}")
    return out


def _fmt(value: Decimal | None, places: str = "0.000001") -> str | None:
    if value is None:
        return None
    return format(value.quantize(Decimal(places)), "f")


def _float(value: Any, label: str) -> float:
    out = float(_d(value, label))
    if not math.isfinite(out):
        raise PortfolioRiskError(f"non-finite float for {label}")
    return out


def build_exposure_ledger(
    *,
    equity_usd: Any,
    available_equity_usd: Any,
    positions: Sequence[Mapping[str, Any]],
    initial_margin_usd: Any | None = None,
    maintenance_margin_usd: Any | None = None,
) -> dict[str, Any]:
    """Normalize observed portfolio exposures without persisting or fetching private reality."""

    equity = _d(equity_usd, "equity_usd")
    available = _d(available_equity_usd, "available_equity_usd")
    if equity <= 0:
        raise PortfolioRiskError("equity_usd must be positive")
    if available < 0:
        raise PortfolioRiskError("available_equity_usd cannot be negative")

    imr = _d(initial_margin_usd, "initial_margin_usd") if initial_margin_usd is not None else None
    mmr = _d(maintenance_margin_usd, "maintenance_margin_usd") if maintenance_margin_usd is not None else None
    if imr is not None and imr < 0:
        raise PortfolioRiskError("initial_margin_usd cannot be negative")
    if mmr is not None and mmr < 0:
        raise PortfolioRiskError("maintenance_margin_usd cannot be negative")

    normalized: list[dict[str, Any]] = []
    gross = Decimal("0")
    net = Decimal("0")
    factor_exposure: dict[str, Decimal] = {}

    seen: set[str] = set()
    for i, row in enumerate(positions):
        inst = str(row.get("instrumentId") or "").strip()
        if not inst:
            raise PortfolioRiskError(f"positions[{i}].instrumentId is required")
        if inst in seen:
            raise PortfolioRiskError(f"duplicate position instrument: {inst}")
        seen.add(inst)

        signed = _d(row.get("signedNotionalUsd"), f"positions[{i}].signedNotionalUsd")
        gross += abs(signed)
        net += signed

        factor_loadings_raw = row.get("factorLoadings") or {}
        if not isinstance(factor_loadings_raw, Mapping):
            raise PortfolioRiskError(f"positions[{i}].factorLoadings must be an object")
        factor_loadings: dict[str, str] = {}
        for factor, loading_raw in factor_loadings_raw.items():
            factor_name = str(factor).strip()
            if not factor_name:
                raise PortfolioRiskError("factor name cannot be blank")
            loading = _d(loading_raw, f"positions[{i}].factorLoadings.{factor_name}")
            factor_loadings[factor_name] = _fmt(loading) or "0.000000"
            factor_exposure[factor_name] = factor_exposure.get(factor_name, Decimal("0")) + signed * loading

        normalized.append({
            "instrumentId": inst,
            "signedNotionalUsd": _fmt(signed),
            "absoluteNotionalUsd": _fmt(abs(signed)),
            "direction": "LONG" if signed > 0 else "SHORT" if signed < 0 else "FLAT",
            "grossShare": None,
            "equityMultiple": _fmt(abs(signed) / equity),
            "factorLoadings": factor_loadings,
        })

    if gross > 0:
        for row in normalized:
            row["grossShare"] = _fmt(_d(row["absoluteNotionalUsd"], "absoluteNotionalUsd") / gross)
    else:
        for row in normalized:
            row["grossShare"] = "0.000000"

    largest = max((_d(row["absoluteNotionalUsd"], "absoluteNotionalUsd") for row in normalized), default=Decimal("0"))
    gross_to_equity = gross / equity
    net_to_equity = net / equity
    available_ratio = available / equity

    factor_rows = [
        {
            "factor": factor,
            "signedExposureUsd": _fmt(exposure),
            "absoluteExposureToGross": _fmt(abs(exposure) / gross) if gross > 0 else "0.000000",
            "note": "factor exposures may overlap and are not additive risk contributions",
        }
        for factor, exposure in sorted(factor_exposure.items())
    ]

    return {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.exposure-ledger",
        "componentId": "exposure-ledger",
        "equityUsd": _fmt(equity),
        "availableEquityUsd": _fmt(available),
        "availableEquityRatio": _fmt(available_ratio),
        "initialMarginUsd": _fmt(imr),
        "initialMarginToEquity": _fmt(imr / equity) if imr is not None else None,
        "maintenanceMarginUsd": _fmt(mmr),
        "maintenanceMarginToEquity": _fmt(mmr / equity) if mmr is not None else None,
        "grossNotionalUsd": _fmt(gross),
        "netNotionalUsd": _fmt(net),
        "grossToEquity": _fmt(gross_to_equity),
        "netToEquity": _fmt(net_to_equity),
        "largestPositionGrossShare": _fmt(largest / gross) if gross > 0 else "0.000000",
        "positionCount": len(normalized),
        "positions": normalized,
        "factorExposure": factor_rows,
    }


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
            raise PortfolioRiskError(f"observations[{i}].observedAtMs must be a non-negative integer")
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
        stat = _paired_stats(base[end - rolling_window:end], proxy[end - rolling_window:end])
        if stat is not None:
            rolling.append(stat)
    rolling_betas = [row["beta"] for row in rolling]
    rolling_corrs = [row["correlation"] for row in rolling]

    beta_range = [min(rolling_betas), max(rolling_betas)] if rolling_betas else None
    corr_range = [min(rolling_corrs), max(rolling_corrs)] if rolling_corrs else None

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
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.historical-dependence-analysis",
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
            "shortMediumCorrelationGap": format(short_medium_gap, ".6f") if short_medium_gap is not None else None,
            "rollingBetaRangeWidth": format(beta_range_width, ".6f") if beta_range_width is not None else None,
            "rollingBetaRangeToMedianAbs": format(beta_range_to_median_abs, ".6f") if beta_range_to_median_abs is not None else None,
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
        challenger_vr = None if base_variance <= 0 else 1 - challenger_residual_variance / base_variance

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

        folds.append({
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
        })

    def _summary(values: Sequence[float]) -> dict[str, str] | None:
        if not values:
            return None
        return {
            "min": format(min(values), ".6f"),
            "median": format(median(values), ".6f"),
            "max": format(max(values), ".6f"),
        }

    return {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.dependence-model-validation",
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
        raise PortfolioRiskError("at least 20 returns are required for historical expected shortfall")

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
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.historical-expected-shortfall",
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

def build_factor_observatory(
    *,
    base_instrument_id: str,
    base_returns: Mapping[int, float],
    factor_proxies: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind named research factors to explicit market proxies and dependence estimates."""

    seen_pairs: set[tuple[str, str]] = set()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for i, proxy in enumerate(factor_proxies):
        factor = str(proxy.get("factor") or "").strip()
        inst = str(proxy.get("instrumentId") or "").strip()
        returns = proxy.get("returns")
        if not factor or not inst or not isinstance(returns, Mapping):
            raise PortfolioRiskError(f"factor_proxies[{i}] requires factor, instrumentId and returns")
        pair = (factor, inst)
        if pair in seen_pairs:
            raise PortfolioRiskError(f"duplicate factor proxy: {factor}/{inst}")
        seen_pairs.add(pair)
        dep = analyze_dependence(
            base_instrument_id=base_instrument_id,
            base_returns=base_returns,
            proxy_instrument_id=inst,
            proxy_returns=returns,
            short_window=int(proxy.get("shortWindow", 20)),
            medium_window=int(proxy.get("mediumWindow", 60)),
            rolling_window=int(proxy.get("rollingWindow", 20)),
        )
        grouped.setdefault(factor, []).append({
            "proxyInstrumentId": inst,
            "dependence": dep,
        })

    factors = [
        {
            "factor": factor,
            "proxyCount": len(proxies),
            "proxies": proxies,
        }
        for factor, proxies in sorted(grouped.items())
    ]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.factor-proxy-analysis",
        "componentId": "factor-proxy-aggregation",
        "baseInstrumentId": base_instrument_id,
        "factors": factors,
        "factorCount": len(factors),
        "factorProxyCount": len(seen_pairs),
    }


def evaluate_risk_budget(
    *,
    exposure_ledger: Mapping[str, Any],
    budget: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare observed portfolio state with explicit user or policy risk limits."""

    required = (
        "maxGrossToEquity",
        "maxLargestPositionGrossShare",
        "minAvailableEquityRatio",
        "shockMagnitudePct",
        "maxEquityLossPctAtShock",
    )
    missing = [key for key in required if budget.get(key) is None]
    if missing:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.market-capital.risk-limit-evaluation",
            "componentId": "risk-limit-evaluator",
            "standing": "INCOMPLETE",
            "missingBudgetInputs": missing,
        }

    max_gross = _d(budget["maxGrossToEquity"], "budget.maxGrossToEquity")
    max_concentration = _d(
        budget["maxLargestPositionGrossShare"],
        "budget.maxLargestPositionGrossShare",
    )
    min_available = _d(budget["minAvailableEquityRatio"], "budget.minAvailableEquityRatio")
    shock_pct = _d(budget["shockMagnitudePct"], "budget.shockMagnitudePct")
    max_loss_pct = _d(budget["maxEquityLossPctAtShock"], "budget.maxEquityLossPctAtShock")

    if max_gross <= 0:
        raise PortfolioRiskError("budget.maxGrossToEquity must be positive")
    if max_concentration <= 0 or max_concentration > 1:
        raise PortfolioRiskError("budget.maxLargestPositionGrossShare must be in (0, 1]")
    if min_available < 0 or min_available > 1:
        raise PortfolioRiskError("budget.minAvailableEquityRatio must be in [0, 1]")
    if shock_pct <= 0 or shock_pct > 100:
        raise PortfolioRiskError("budget.shockMagnitudePct must be in (0, 100]")
    if max_loss_pct <= 0 or max_loss_pct > 100:
        raise PortfolioRiskError("budget.maxEquityLossPctAtShock must be in (0, 100]")

    gross_to_equity = _d(exposure_ledger.get("grossToEquity"), "ledger.grossToEquity")
    concentration = _d(
        exposure_ledger.get("largestPositionGrossShare"),
        "ledger.largestPositionGrossShare",
    )
    available_ratio = _d(
        exposure_ledger.get("availableEquityRatio"),
        "ledger.availableEquityRatio",
    )

    positions = exposure_ledger.get("positions")
    if not isinstance(positions, Sequence):
        raise PortfolioRiskError("ledger.positions must be a sequence")

    largest_equity_multiple = max(
        (_d(row.get("equityMultiple"), "position.equityMultiple") for row in positions),
        default=Decimal("0"),
    )
    shock_loss_pct = largest_equity_multiple * shock_pct

    checks = [
        {
            "id": "MAX_GROSS_TO_EQUITY",
            "observed": _fmt(gross_to_equity),
            "limit": _fmt(max_gross),
            "passed": gross_to_equity <= max_gross,
        },
        {
            "id": "MAX_LARGEST_POSITION_GROSS_SHARE",
            "observed": _fmt(concentration),
            "limit": _fmt(max_concentration),
            "passed": concentration <= max_concentration,
        },
        {
            "id": "MIN_AVAILABLE_EQUITY_RATIO",
            "observed": _fmt(available_ratio),
            "limit": _fmt(min_available),
            "passed": available_ratio >= min_available,
        },
        {
            "id": "MAX_EQUITY_LOSS_AT_NAMED_SHOCK",
            "observed": _fmt(shock_loss_pct),
            "limit": _fmt(max_loss_pct),
            "shockMagnitudePct": _fmt(shock_pct),
            "passed": shock_loss_pct <= max_loss_pct,
        },
    ]
    breached = [row["id"] for row in checks if not row["passed"]]

    return {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.risk-limit-evaluation",
        "componentId": "risk-limit-evaluator",
        "standing": "SATISFIED" if not breached else "BREACHED",
        "checks": checks,
        "breachedChecks": breached,
    }


def build_portfolio_risk_report(
    *,
    exposure_ledger: Mapping[str, Any],
    factor_observatory: Mapping[str, Any] | None = None,
    risk_budget: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose exposure, dependence, and risk-limit results into a read-only risk report."""

    budget_eval = (
        evaluate_risk_budget(exposure_ledger=exposure_ledger, budget=risk_budget)
        if risk_budget is not None
        else {
            "schemaVersion": 1,
            "kind": "ordivon.market-capital.risk-limit-evaluation",
        "componentId": "risk-limit-evaluator",
            "standing": "INCOMPLETE",
            "missingBudgetInputs": ["riskBudget"],
        }
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.portfolio-risk-report",
        "nodes": {
            "exposureLedger": exposure_ledger,
            "factorDependenceAnalysis": factor_observatory,
            "riskLimitEvaluation": budget_eval,
        },
    }
