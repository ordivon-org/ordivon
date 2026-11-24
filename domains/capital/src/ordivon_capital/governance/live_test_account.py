"""Real account qualification is an effect-side concern, not a portfolio risk calculation.

A qualified TEST account is not approval for production trading.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from .decision_inputs import (
    DECISION_IMPLEMENTATION,
    PolicyDecisionError,
    _decimal,
    _load_json,
    _require_local_implementation,
)


def _live_test_account_decision(facts: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if facts.get("venue") not in {"OKX", "BINANCE"}:
        reasons.append("unsupported-venue")
    if facts.get("permissionStanding") != "READ_ONLY_VERIFIED":
        reasons.append("readonly-reality-not-verified")
    if facts.get("externalFinancialWriteAttempted") is not False:
        reasons.append("reality-not-readonly")
    if facts.get("clockPassed") is not True:
        reasons.append("clock-gate-not-passed")
    if facts.get("reconciliationHealthy") is not True:
        reasons.append("reconciliation-not-healthy")
    if facts.get("tradePermission") is not True:
        reasons.append("trade-permission-missing")
    if facts.get("withdrawPermission") is not False:
        reasons.append("withdraw-permission-not-proven-absent")
    if facts.get("transferPermission") not in {False, None}:
        reasons.append("transfer-permission-not-proven-absent")
    if facts.get("hasNonzeroPosition") is True:
        reasons.append("nonzero-position-present")
    if facts.get("hasOpenOrders") is True:
        reasons.append("open-order-present")
    nonquote = facts.get("nonquoteNonzeroAssets") or []
    if nonquote:
        reasons.append("nonquote-balance-present:" + ",".join(nonquote))
    if facts.get("quoteBalanceExceedsThreshold") is True:
        reasons.append("quote-balance-exceeds-test-threshold")
    blocking = sorted(set(reasons))
    return {"admitted": not blocking, "blockingReasons": blocking}


def evaluate_live_test_account(
    *,
    repo: Path,
    config_path: Path,
    reality: dict[str, Any],
    quote_asset: str,
    permission: dict[str, Any],
    clock_passed: bool,
    reconciliation_healthy: bool,
    max_quote_balance: str = "1",
) -> dict[str, Any]:
    del repo
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.capital.governance.execution-policy":
        raise PolicyDecisionError("unexpected execution-policy kind")
    _require_local_implementation(cfg)

    venue = str(reality.get("venue") or "").upper()
    positions = [
        row for row in (reality.get("positions") or []) if _decimal(row.get("quantity", "0")) != 0
    ]
    max_quote = _decimal(max_quote_balance)
    quote_total = Decimal("0")
    nonquote_nonzero: list[str] = []
    for balance in reality.get("balances") or []:
        asset = str(balance.get("asset") or "")
        total = _decimal(balance.get("total", "0"))
        if total == 0:
            continue
        if asset == quote_asset:
            quote_total += total
        else:
            nonquote_nonzero.append(asset)
    nonquote_nonzero.sort()

    decision = _live_test_account_decision(
        {
            "venue": venue,
            "permissionStanding": reality.get("permissionStanding"),
            "externalFinancialWriteAttempted": reality.get("externalFinancialWriteAttempted"),
            "clockPassed": clock_passed,
            "reconciliationHealthy": reconciliation_healthy,
            "tradePermission": permission.get("trade"),
            "withdrawPermission": permission.get("withdraw"),
            "transferPermission": permission.get("transfer"),
            "hasNonzeroPosition": bool(positions),
            "hasOpenOrders": bool(reality.get("openOrders")),
            "nonquoteNonzeroAssets": nonquote_nonzero,
            "quoteBalanceExceedsThreshold": quote_total > max_quote,
        }
    )
    admitted = decision["admitted"]
    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.governance.live-test-account-admission",
        "decisionImplementation": DECISION_IMPLEMENTATION,
        "venue": venue,
        "standing": "ADMITTED_EMPTY_LIVE_TEST_ACCOUNT" if admitted else "BLOCKED",
        "orderSubmissionAllowed": admitted,
        "productionTradingAuthorized": False,
        "withdrawalAuthorized": False,
        "transferAuthorized": False,
        "quoteAsset": quote_asset,
        "observedQuoteBalance": format(quote_total, "f"),
        "maxQuoteBalance": format(max_quote, "f"),
        "nonquoteNonzeroAssets": nonquote_nonzero,
        "blockingReasons": decision["blockingReasons"],
    }
