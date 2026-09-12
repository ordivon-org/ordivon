from __future__ import annotations

from typing import Any


def build_equal_weight_validation_portfolio(
    ips: dict[str, Any], reference: dict[str, Any]
) -> dict[str, Any]:
    if ips["construction_method"] != "equal_weight_validation":
        raise ValueError("Unsupported construction method")
    if ips["allow_short"]:
        raise ValueError("Wave A validation portfolio is long-only")

    by_symbol = {e["symbol"]: e for e in reference["entities"]}
    allowed = ips["allowed_instruments"]
    missing = [s for s in allowed if s not in by_symbol]
    if missing:
        raise ValueError(f"Missing authoritative reference identity for: {missing}")

    investable = min(1.0 - ips["min_cash_weight"], ips["max_gross_exposure"])
    unconstrained_weight = investable / len(allowed)
    weight = min(unconstrained_weight, ips["max_position_weight"])
    gross = weight * len(allowed)
    cash = 1.0 - gross

    if cash + 1e-12 < ips["min_cash_weight"]:
        raise ValueError("Portfolio violates minimum cash weight")
    if gross - 1e-12 > ips["max_gross_exposure"]:
        raise ValueError("Portfolio violates maximum gross exposure")

    positions = [
        {"symbol": symbol, "lei": by_symbol[symbol]["lei"], "target_weight": weight}
        for symbol in allowed
    ]
    return {
        "method": "equal_weight_validation",
        "base_currency": ips["base_currency"],
        "positions": positions,
        "cash_weight": cash,
        "gross_exposure": gross,
        "inputs": {
            "objective": ips["objective"],
            "reference_source": reference["source"],
            "reference_retrieved_at": reference["retrieved_at"],
        },
    }
