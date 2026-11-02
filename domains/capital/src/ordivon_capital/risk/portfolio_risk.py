"""Capital's public read-only portfolio risk facade and risk-limit composition.

Implementation changes in statistical estimators stay in dependence_analysis
and tail_risk; caller-facing functions remain importable from this module.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

from .dependence_analysis import (
    analyze_dependence as analyze_dependence,
)
from .dependence_analysis import (
    completed_log_returns as completed_log_returns,
)
from .dependence_analysis import (
    validate_dependence_model as validate_dependence_model,
)
from .risk_budget_validation import (
    RiskBudgetValidationError,
    assert_risk_budget_schema_identity,
    validate_registered_risk_budget_document,
)
from .risk_values import (
    PortfolioRiskError as PortfolioRiskError,
)
from .risk_values import (
    _d,
    _fmt_lossless,
)
from .tail_risk import historical_expected_shortfall as historical_expected_shortfall


def load_registered_risk_budget(path: Path | None = None) -> dict[str, Any]:
    """Load the owner-principal risk budget registration through JSON Schema.

    UNSET is a valid fail-closed state: it proves the policy surface exists without
    inventing owner risk tolerance. ACTIVE requires all five explicit limit values.
    """
    repo = Path(__file__).resolve().parents[3]
    config_path = path or (repo / "config/portfolio_risk_budget.json")
    schema_path = repo / "contracts/portfolio-risk-budget-v2.schema.json"
    try:
        doc = json.loads(config_path.read_text())
        assert_risk_budget_schema_identity(schema_path)
        validate_registered_risk_budget_document(doc)
    except (OSError, json.JSONDecodeError, RiskBudgetValidationError) as exc:
        raise PortfolioRiskError(f"invalid registered portfolio risk budget: {exc}") from exc
    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.risk.registered-risk-budget",
        "standing": doc["standing"],
        "owner": doc["owner"],
        "source": str(config_path.relative_to(repo))
        if config_path.is_relative_to(repo)
        else str(config_path),
        "limits": dict(doc["limits"]),
    }


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
    mmr = (
        _d(maintenance_margin_usd, "maintenance_margin_usd")
        if maintenance_margin_usd is not None
        else None
    )
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

        factor_loadings_raw = row.get("factorLoadings")
        if factor_loadings_raw is None:
            factor_loadings_raw = {}
        if not isinstance(factor_loadings_raw, Mapping):
            raise PortfolioRiskError(f"positions[{i}].factorLoadings must be an object")
        factor_loadings: dict[str, str] = {}
        for factor, loading_raw in factor_loadings_raw.items():
            if not isinstance(factor, str):
                raise PortfolioRiskError(f"positions[{i}].factorLoadings keys must be strings")
            factor_name = factor.strip()
            if not factor_name:
                raise PortfolioRiskError("factor name cannot be blank")
            if factor_name in factor_loadings:
                raise PortfolioRiskError(
                    f"positions[{i}].factorLoadings duplicate canonical factor: {factor_name}"
                )
            loading = _d(loading_raw, f"positions[{i}].factorLoadings.{factor_name}")
            factor_loadings[factor_name] = _fmt_lossless(loading)
            factor_exposure[factor_name] = (
                factor_exposure.get(factor_name, Decimal("0")) + signed * loading
            )

        normalized.append(
            {
                "instrumentId": inst,
                "signedNotionalUsd": _fmt_lossless(signed),
                "absoluteNotionalUsd": _fmt_lossless(abs(signed)),
                "direction": "LONG" if signed > 0 else "SHORT" if signed < 0 else "FLAT",
                "grossShare": None,
                "equityMultiple": _fmt_lossless(abs(signed) / equity),
                "factorLoadings": factor_loadings,
            }
        )

    if gross > 0:
        for row in normalized:
            row["grossShare"] = _fmt_lossless(
                _d(row["absoluteNotionalUsd"], "absoluteNotionalUsd") / gross
            )
    else:
        for row in normalized:
            row["grossShare"] = "0.000000"

    largest = max(
        (_d(row["absoluteNotionalUsd"], "absoluteNotionalUsd") for row in normalized),
        default=Decimal("0"),
    )
    gross_to_equity = gross / equity
    net_to_equity = net / equity
    available_ratio = available / equity

    factor_rows = [
        {
            "factor": factor,
            "signedExposureUsd": _fmt_lossless(exposure),
            "absoluteExposureToGross": _fmt_lossless(abs(exposure) / gross)
            if gross > 0
            else "0.000000",
            "note": "factor exposures may overlap and are not additive risk contributions",
        }
        for factor, exposure in sorted(factor_exposure.items())
    ]

    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.risk.exposure-ledger",
        "componentId": "exposure-ledger",
        "equityUsd": _fmt_lossless(equity),
        "availableEquityUsd": _fmt_lossless(available),
        "availableEquityRatio": _fmt_lossless(available_ratio),
        "initialMarginUsd": _fmt_lossless(imr) if imr is not None else None,
        "initialMarginToEquity": _fmt_lossless(imr / equity) if imr is not None else None,
        "maintenanceMarginUsd": _fmt_lossless(mmr) if mmr is not None else None,
        "maintenanceMarginToEquity": _fmt_lossless(mmr / equity) if mmr is not None else None,
        "grossNotionalUsd": _fmt_lossless(gross),
        "netNotionalUsd": _fmt_lossless(net),
        "grossToEquity": _fmt_lossless(gross_to_equity),
        "netToEquity": _fmt_lossless(net_to_equity),
        "largestPositionGrossShare": _fmt_lossless(largest / gross) if gross > 0 else "0.000000",
        "positionCount": len(normalized),
        "positions": normalized,
        "factorExposure": factor_rows,
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
            raise PortfolioRiskError(
                f"factor_proxies[{i}] requires factor, instrumentId and returns"
            )
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
        grouped.setdefault(factor, []).append(
            {
                "proxyInstrumentId": inst,
                "dependence": dep,
            }
        )

    factors = [
        {
            "factor": factor,
            "proxyCount": len(proxies),
            "proxies": proxies,
        }
        for factor, proxies in sorted(grouped.items())
    ]
    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.risk.factor-proxy-analysis",
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
    """Bind normalized portfolio facts to the bounded deterministic risk-limit policy."""
    from ordivon_capital.governance.policy_decision import (
        PolicyDecisionError,
        evaluate_risk_budget_policy,
    )

    repo = Path(__file__).resolve().parents[3]
    try:
        return evaluate_risk_budget_policy(
            repo=repo,
            config_path=repo / "config/execution_policy.json",
            exposure_ledger=dict(exposure_ledger),
            budget=dict(budget),
        )
    except PolicyDecisionError as exc:
        raise PortfolioRiskError(str(exc)) from exc


def build_portfolio_risk_report(
    *,
    exposure_ledger: Mapping[str, Any],
    factor_observatory: Mapping[str, Any] | None = None,
    risk_budget: Mapping[str, Any] | None = None,
    model_monitoring: Mapping[str, Any] | None = None,
    tail_risk_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose exposure, dependence, and risk-limit results into a read-only risk report."""

    if risk_budget is None:
        registration = load_registered_risk_budget()
        effective_budget = registration["limits"]
        budget_source = {
            "standing": registration["standing"],
            "owner": registration["owner"],
            "source": registration["source"],
        }
    else:
        effective_budget = dict(risk_budget)
        budget_source = {
            "standing": "CALLER_SUPPLIED",
            "owner": "CALLER",
            "source": None,
        }
    budget_eval = evaluate_risk_budget(
        exposure_ledger=exposure_ledger,
        budget=effective_budget,
    )
    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.risk.portfolio-risk-report",
        "nodes": {
            "exposureLedger": exposure_ledger,
            "factorDependenceAnalysis": factor_observatory,
            "modelMonitoring": model_monitoring,
            "tailRisk": tail_risk_report,
            "riskBudgetRegistration": budget_source,
            "riskLimitEvaluation": budget_eval,
        },
    }
