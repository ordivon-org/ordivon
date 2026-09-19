from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence


class PortfolioCounterfactualError(ValueError):
    """Fail-closed validation for read-only portfolio scenario analysis."""


_ACTIONS = {"DE_RISK", "HEDGE", "DIVERSIFY", "HOLD", "RECONCILE"}


def _d(value: Any, label: str) -> Decimal:
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise PortfolioCounterfactualError(f"invalid decimal for {label}") from exc
    if not out.is_finite():
        raise PortfolioCounterfactualError(f"non-finite decimal for {label}")
    return out


def _fmt(value: Decimal | None, places: str = "0.000001") -> str | None:
    if value is None:
        return None
    return format(value.quantize(Decimal(places)), "f")


def _ledger_state(exposure_ledger: Mapping[str, Any]) -> tuple[Decimal, Decimal, dict[str, dict[str, Any]]]:
    equity = _d(exposure_ledger.get("equityUsd"), "ledger.equityUsd")
    if equity <= 0:
        raise PortfolioCounterfactualError("ledger equity must be positive")
    available = _d(exposure_ledger.get("availableEquityUsd"), "ledger.availableEquityUsd")
    if available < 0:
        raise PortfolioCounterfactualError("ledger available equity cannot be negative")
    positions = exposure_ledger.get("positions")
    if not isinstance(positions, Sequence):
        raise PortfolioCounterfactualError("ledger.positions must be a sequence")

    by_inst: dict[str, dict[str, Any]] = {}
    for i, row in enumerate(positions):
        if not isinstance(row, Mapping):
            raise PortfolioCounterfactualError(f"ledger.positions[{i}] must be an object")
        inst = str(row.get("instrumentId") or "").strip()
        if not inst:
            raise PortfolioCounterfactualError(f"ledger.positions[{i}].instrumentId is required")
        if inst in by_inst:
            raise PortfolioCounterfactualError(f"duplicate ledger instrument: {inst}")
        signed = _d(row.get("signedNotionalUsd"), f"ledger.positions[{i}].signedNotionalUsd")
        factor_loadings = row.get("factorLoadings") or {}
        if not isinstance(factor_loadings, Mapping):
            raise PortfolioCounterfactualError("ledger factorLoadings must be an object")
        by_inst[inst] = {
            "signedNotionalUsd": signed,
            "factorLoadings": {
                str(k): _d(v, f"{inst}.factorLoadings.{k}")
                for k, v in factor_loadings.items()
            },
        }
    return equity, available, by_inst


def _recompute(
    *,
    equity: Decimal,
    positions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    gross = sum((abs(_d(row["signedNotionalUsd"], "signedNotionalUsd")) for row in positions.values()), Decimal("0"))
    net = sum((_d(row["signedNotionalUsd"], "signedNotionalUsd") for row in positions.values()), Decimal("0"))
    largest = max(
        (abs(_d(row["signedNotionalUsd"], "signedNotionalUsd")) for row in positions.values()),
        default=Decimal("0"),
    )
    factor_exposure: dict[str, Decimal] = {}
    normalized = []
    for inst in sorted(positions):
        row = positions[inst]
        signed = _d(row["signedNotionalUsd"], f"{inst}.signedNotionalUsd")
        loadings = row.get("factorLoadings") or {}
        rendered_loadings = {}
        for factor, value in loadings.items():
            loading = _d(value, f"{inst}.factorLoadings.{factor}")
            rendered_loadings[str(factor)] = _fmt(loading)
            factor_exposure[str(factor)] = factor_exposure.get(str(factor), Decimal("0")) + signed * loading
        normalized.append({
            "instrumentId": inst,
            "signedNotionalUsd": _fmt(signed),
            "absoluteNotionalUsd": _fmt(abs(signed)),
            "grossShare": _fmt(abs(signed) / gross) if gross > 0 else "0.000000",
            "equityMultiple": _fmt(abs(signed) / equity),
            "factorLoadings": rendered_loadings,
        })
    return {
        "grossNotionalUsd": gross,
        "netNotionalUsd": net,
        "grossToEquity": gross / equity,
        "netToEquity": net / equity,
        "largestPositionGrossShare": largest / gross if gross > 0 else Decimal("0"),
        "positions": normalized,
        "factorExposure": factor_exposure,
    }


def _apply_delta_position(
    positions: dict[str, dict[str, Any]],
    *,
    instrument_id: str,
    signed_delta_usd: Decimal,
    factor_loadings: Mapping[str, Any] | None,
) -> None:
    if not instrument_id:
        raise PortfolioCounterfactualError("instrumentId is required")
    existing = positions.get(instrument_id)
    if existing is None:
        if factor_loadings is None:
            factor_loadings = {}
        positions[instrument_id] = {
            "signedNotionalUsd": signed_delta_usd,
            "factorLoadings": {
                str(k): _d(v, f"{instrument_id}.factorLoadings.{k}")
                for k, v in factor_loadings.items()
            },
        }
        return

    existing_loadings = existing.get("factorLoadings") or {}
    if factor_loadings is not None:
        candidate = {
            str(k): _d(v, f"{instrument_id}.factorLoadings.{k}")
            for k, v in factor_loadings.items()
        }
        if candidate != existing_loadings:
            raise PortfolioCounterfactualError(
                f"factor loadings for existing instrument {instrument_id} disagree with ledger"
            )
    existing["signedNotionalUsd"] = _d(existing["signedNotionalUsd"], "existing signed notional") + signed_delta_usd
    if existing["signedNotionalUsd"] == 0:
        del positions[instrument_id]


def build_action_counterfactual(
    *,
    exposure_ledger: Mapping[str, Any],
    scenario: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply one explicit what-if scenario and derive mechanical exposure deltas."""

    scenario_id = str(scenario.get("scenarioId") or "").strip()
    action = str(scenario.get("action") or "").strip().upper()
    if not scenario_id:
        raise PortfolioCounterfactualError("scenarioId is required")
    if action not in _ACTIONS:
        raise PortfolioCounterfactualError(f"unsupported action: {action}")

    equity, available, baseline_positions = _ledger_state(exposure_ledger)
    projected_positions = {
        inst: {
            "signedNotionalUsd": row["signedNotionalUsd"],
            "factorLoadings": dict(row.get("factorLoadings") or {}),
        }
        for inst, row in baseline_positions.items()
    }
    baseline = _recompute(equity=equity, positions=baseline_positions)

    changed_instruments: set[str] = set()
    sizing_basis = str(scenario.get("sizingBasis") or "EXPLICIT_CALLER_COUNTERFACTUAL").strip()
    if sizing_basis != "EXPLICIT_CALLER_COUNTERFACTUAL":
        raise PortfolioCounterfactualError("scenario analysis accepts only EXPLICIT_CALLER_COUNTERFACTUAL sizing")

    if action == "DE_RISK":
        inst = str(scenario.get("instrumentId") or "").strip()
        if inst not in projected_positions:
            raise PortfolioCounterfactualError("DE_RISK instrument must exist in the exposure ledger")
        reduction_fraction = _d(scenario.get("reductionFraction"), "scenario.reductionFraction")
        if reduction_fraction <= 0 or reduction_fraction > 1:
            raise PortfolioCounterfactualError("reductionFraction must be in (0, 1]")
        current = _d(projected_positions[inst]["signedNotionalUsd"], "current notional")
        _apply_delta_position(
            projected_positions,
            instrument_id=inst,
            signed_delta_usd=-current * reduction_fraction,
            factor_loadings=None,
        )
        changed_instruments.add(inst)

    elif action == "HEDGE":
        inst = str(scenario.get("instrumentId") or "").strip()
        target_factor = str(scenario.get("targetFactor") or "").strip()
        if not target_factor:
            raise PortfolioCounterfactualError("HEDGE targetFactor is required")
        signed_delta = _d(scenario.get("signedNotionalDeltaUsd"), "scenario.signedNotionalDeltaUsd")
        if signed_delta == 0:
            raise PortfolioCounterfactualError("HEDGE signedNotionalDeltaUsd cannot be zero")
        _apply_delta_position(
            projected_positions,
            instrument_id=inst,
            signed_delta_usd=signed_delta,
            factor_loadings=scenario.get("factorLoadings"),
        )
        changed_instruments.add(inst)

    elif action == "DIVERSIFY":
        source = str(scenario.get("sourceInstrumentId") or "").strip()
        destination = str(scenario.get("destinationInstrumentId") or "").strip()
        if source == destination:
            raise PortfolioCounterfactualError("DIVERSIFY source and destination must differ")
        if source not in projected_positions:
            raise PortfolioCounterfactualError("DIVERSIFY source instrument must exist in ledger")
        reallocation_fraction = _d(scenario.get("reallocationFraction"), "scenario.reallocationFraction")
        if reallocation_fraction <= 0 or reallocation_fraction > 1:
            raise PortfolioCounterfactualError("reallocationFraction must be in (0, 1]")
        source_current = _d(projected_positions[source]["signedNotionalUsd"], "source current notional")
        if source_current == 0:
            raise PortfolioCounterfactualError("DIVERSIFY source notional cannot be zero")
        source_reduction = source_current * reallocation_fraction
        _apply_delta_position(
            projected_positions,
            instrument_id=source,
            signed_delta_usd=-source_reduction,
            factor_loadings=None,
        )
        destination_signed = _d(
            scenario.get("destinationSignedNotionalUsd"),
            "scenario.destinationSignedNotionalUsd",
        )
        if destination_signed == 0:
            raise PortfolioCounterfactualError("destinationSignedNotionalUsd cannot be zero")
        _apply_delta_position(
            projected_positions,
            instrument_id=destination,
            signed_delta_usd=destination_signed,
            factor_loadings=scenario.get("destinationFactorLoadings"),
        )
        changed_instruments.update({source, destination})

    elif action in {"HOLD", "RECONCILE"}:
        if any(
            scenario.get(key) is not None
            for key in (
                "instrumentId",
                "signedNotionalDeltaUsd",
                "reductionFraction",
                "sourceInstrumentId",
                "destinationInstrumentId",
                "destinationSignedNotionalUsd",
                "reallocationFraction",
            )
        ):
            raise PortfolioCounterfactualError(f"{action} scenario cannot contain position-changing fields")

    projected = _recompute(equity=equity, positions=projected_positions)

    factor_names = sorted(set(baseline["factorExposure"]) | set(projected["factorExposure"]))
    factor_delta = [
        {
            "factor": factor,
            "beforeUsd": _fmt(baseline["factorExposure"].get(factor, Decimal("0"))),
            "afterUsd": _fmt(projected["factorExposure"].get(factor, Decimal("0"))),
            "deltaUsd": _fmt(
                projected["factorExposure"].get(factor, Decimal("0"))
                - baseline["factorExposure"].get(factor, Decimal("0"))
            ),
            "note": "factor exposures may overlap and are not additive risk contributions",
        }
        for factor in factor_names
    ]

    shock = scenario.get("shock")
    shock_projection = None
    if shock is not None:
        if not isinstance(shock, Mapping):
            raise PortfolioCounterfactualError("scenario.shock must be an object")
        shock_inst = str(shock.get("instrumentId") or "").strip()
        shock_pct = _d(shock.get("magnitudePct"), "scenario.shock.magnitudePct")
        if shock_pct <= 0 or shock_pct > 100:
            raise PortfolioCounterfactualError("shock magnitudePct must be in (0, 100]")
        before_notional = abs(
            _d(baseline_positions.get(shock_inst, {}).get("signedNotionalUsd", 0), "shock before notional")
        )
        after_notional = abs(
            _d(projected_positions.get(shock_inst, {}).get("signedNotionalUsd", 0), "shock after notional")
        )
        before_loss = before_notional / equity * shock_pct
        after_loss = after_notional / equity * shock_pct
        shock_projection = {
            "instrumentId": shock_inst,
            "magnitudePct": _fmt(shock_pct),
            "beforeEquityLossPctFirstOrder": _fmt(before_loss),
            "afterEquityLossPctFirstOrder": _fmt(after_loss),
            "deltaEquityLossPctFirstOrder": _fmt(after_loss - before_loss),
            "notVaR": True,
            "notLiquidationProbability": True,
        }

    gross_delta = projected["grossNotionalUsd"] - baseline["grossNotionalUsd"]
    net_delta = projected["netNotionalUsd"] - baseline["netNotionalUsd"]

    hedge_mechanics = None
    if action == "HEDGE":
        target_factor = str(scenario.get("targetFactor") or "").strip()
        before_factor = baseline["factorExposure"].get(target_factor)
        after_factor = projected["factorExposure"].get(target_factor)
        if before_factor is None or after_factor is None:
            hedge_standing = "UNIDENTIFIED_TARGET_FACTOR_EXPOSURE"
        elif abs(after_factor) < abs(before_factor):
            hedge_standing = "TARGET_FACTOR_ABSOLUTE_EXPOSURE_REDUCED"
        elif abs(after_factor) == abs(before_factor):
            hedge_standing = "TARGET_FACTOR_ABSOLUTE_EXPOSURE_UNCHANGED"
        else:
            hedge_standing = "TARGET_FACTOR_ABSOLUTE_EXPOSURE_INCREASED"
        hedge_mechanics = {
            "targetFactor": target_factor,
            "beforeSignedExposureUsd": _fmt(before_factor) if before_factor is not None else None,
            "afterSignedExposureUsd": _fmt(after_factor) if after_factor is not None else None,
            "standing": hedge_standing,
        }

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.portfolio-action-counterfactual",
        "componentId": "portfolio-scenario-calculation",
        "scenarioId": scenario_id,
        "action": action,
        "sizingBasis": sizing_basis,
        "scenarioPurpose": str(scenario.get("purpose") or "").strip() or None,
        "baseline": {
            "grossNotionalUsd": _fmt(baseline["grossNotionalUsd"]),
            "netNotionalUsd": _fmt(baseline["netNotionalUsd"]),
            "grossToEquity": _fmt(baseline["grossToEquity"]),
            "netToEquity": _fmt(baseline["netToEquity"]),
            "largestPositionGrossShare": _fmt(baseline["largestPositionGrossShare"]),
        },
        "projected": {
            "grossNotionalUsd": _fmt(projected["grossNotionalUsd"]),
            "netNotionalUsd": _fmt(projected["netNotionalUsd"]),
            "grossToEquity": _fmt(projected["grossToEquity"]),
            "netToEquity": _fmt(projected["netToEquity"]),
            "largestPositionGrossShare": _fmt(projected["largestPositionGrossShare"]),
            "positions": projected["positions"],
        },
        "deltas": {
            "grossNotionalUsd": _fmt(gross_delta),
            "netNotionalUsd": _fmt(net_delta),
            "grossToEquity": _fmt(projected["grossToEquity"] - baseline["grossToEquity"]),
            "netToEquity": _fmt(projected["netToEquity"] - baseline["netToEquity"]),
            "largestPositionGrossShare": _fmt(
                projected["largestPositionGrossShare"] - baseline["largestPositionGrossShare"]
            ),
            "factorExposure": factor_delta,
        },
        "shockProjection": shock_projection,
        "hedgeMechanics": hedge_mechanics,
        "changedInstruments": sorted(changed_instruments),
        "availableEquityUsdObservedBefore": _fmt(available),
        "projectedAvailableEquityUsd": None,
        "exactMarginDeltaMeasured": False,
    }


def build_counterfactual_set(
    *,
    exposure_ledger: Mapping[str, Any],
    scenarios: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    seen: set[str] = set()
    rows = []
    for scenario in scenarios:
        scenario_id = str(scenario.get("scenarioId") or "").strip()
        if scenario_id in seen:
            raise PortfolioCounterfactualError(f"duplicate scenarioId: {scenario_id}")
        seen.add(scenario_id)
        rows.append(build_action_counterfactual(exposure_ledger=exposure_ledger, scenario=scenario))
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.portfolio-counterfactual-set",
        "scenarioCount": len(rows),
        "scenarios": rows,
    }


def evaluate_constraint_gate(
    *,
    counterfactual: Mapping[str, Any],
    risk_budget_evaluation: Mapping[str, Any] | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind counterfactual/evidence facts to the OPA-owned pre-trade control policy."""
    from ordivon_capital.market.opa_policy import (
        ExecutionPolicyError,
        evaluate_counterfactual_gate_policy,
    )

    repo = Path(__file__).resolve().parents[3]
    try:
        return evaluate_counterfactual_gate_policy(
            repo=repo,
            config_path=repo / "config/execution_policy.json",
            counterfactual=dict(counterfactual),
            risk_budget_evaluation=(dict(risk_budget_evaluation) if risk_budget_evaluation is not None else None),
            evidence=(dict(evidence) if evidence is not None else None),
        )
    except ExecutionPolicyError as exc:
        raise PortfolioCounterfactualError(str(exc)) from exc


def build_counterfactual_gate_set(
    *,
    counterfactual_set: Mapping[str, Any],
    risk_budget_by_scenario: Mapping[str, Mapping[str, Any]] | None = None,
    evidence_by_scenario: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    scenarios = counterfactual_set.get("scenarios")
    if not isinstance(scenarios, Sequence):
        raise PortfolioCounterfactualError("counterfactual_set.scenarios must be a sequence")
    risk_budget_by_scenario = risk_budget_by_scenario or {}
    evidence_by_scenario = evidence_by_scenario or {}
    gates = [
        evaluate_constraint_gate(
            counterfactual=row,
            risk_budget_evaluation=risk_budget_by_scenario.get(str(row.get("scenarioId"))),
            evidence=evidence_by_scenario.get(str(row.get("scenarioId"))),
        )
        for row in scenarios
    ]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.portfolio-counterfactual-gate-set",
        "scenarioCount": len(gates),
        "gates": gates,
        "allPass": bool(gates) and all(row["standing"] == "PASS" for row in gates),
    }
