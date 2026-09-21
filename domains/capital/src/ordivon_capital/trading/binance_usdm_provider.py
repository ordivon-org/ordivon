from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class BinanceUsdmProviderError(RuntimeError):
    pass


def qualify_provider_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    if config.get("kind") != "ordivon.capital.market.binance-usdm-equity-perp-provider":
        raise BinanceUsdmProviderError("unexpected provider contract kind")
    effect = config.get("effectPolicy") or {}
    if any(
        effect.get(name) is not False
        for name in (
            "externalFinancialWriteAllowed",
            "tradeEndpointsAllowed",
            "accountModeMutationAllowed",
            "leverageMutationAllowed",
            "tradFiAgreementMutationAllowed",
        )
    ):
        raise BinanceUsdmProviderError("provider contract must remain fail-closed")
    agreement = config.get("tradFiAgreement") or {}
    if agreement.get("automationMayInvoke") is not False or agreement.get("userExplicitActionRequired") is not True:
        raise BinanceUsdmProviderError("TradFi agreement cannot be automated")
    return {
        "standing": config.get("standing"),
        "officialClient": config["officialClient"]["package"],
        "officialClientVersion": config["officialClient"]["version"],
        "privateUserDataStanding": config["privateReadOnlyTruth"]["standing"],
        "externalFinancialWriteAllowed": False,
    }
