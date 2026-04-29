"""Alpaca Paper — Server-side health snapshot (Phase 6K).

Read-only, paper-only, redacted. Never exposes secrets or account IDs.
Returns only safe fields for observation health display.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from adapters.finance import (
    AlpacaKeyMissingError,
    AlpacaObservationProvider,
    AlpacaUnavailableError,
    AlpacaWriteRejectedError,
)
from domains.finance import DataFreshnessStatus


# ── Health snapshot result ──────────────────────────────────────────


@dataclass
class AlpacaHealthSnapshot:
    """Redacted health status for Alpaca Paper observation provider.

    Safe to serialize and expose. No secrets. No raw account IDs.
    """

    provider_id: str = "alpaca-paper"
    environment: str = "paper"
    status: str = "unavailable"  # configured | connected | degraded | unavailable
    last_checked_at: str = ""
    freshness: str = DataFreshnessStatus.MISSING.value

    # Redacted account data (safe to show)
    account_alias: str = ""
    total_equity: float | None = None
    available_cash: float | None = None

    # Market data (sample, safe to show)
    sample_symbol: str = ""
    sample_price: float | None = None

    # Capability contract
    write_capabilities: list[str] = field(default_factory=list)

    # Error info (if degraded/unavailable)
    error_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "environment": self.environment,
            "status": self.status,
            "last_checked_at": self.last_checked_at,
            "freshness": self.freshness,
            "account_alias": self.account_alias,
            "total_equity": self.total_equity,
            "available_cash": self.available_cash,
            "sample_symbol": self.sample_symbol,
            "sample_price": self.sample_price,
            "write_capabilities": self.write_capabilities,
            "error_summary": self.error_summary,
        }


# ── Health check ────────────────────────────────────────────────────


def get_alpaca_health_snapshot() -> AlpacaHealthSnapshot:
    """Perform a read-only health check against Alpaca Paper.

    Returns a redacted snapshot suitable for API response or CLI display.
    Never exposes API keys, secrets, or full account IDs.
    Only performs GET requests. Never places orders.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Try to initialize provider
    try:
        provider = AlpacaObservationProvider()
    except AlpacaKeyMissingError:
        return AlpacaHealthSnapshot(
            status="unavailable",
            last_checked_at=now,
            error_summary="API keys not configured. Set ALPACA_API_KEY, ALPACA_SECRET_KEY, and ALPACA_PAPER=true.",
        )
    except AlpacaWriteRejectedError as e:
        return AlpacaHealthSnapshot(
            status="unavailable",
            last_checked_at=now,
            error_summary=f"Configuration rejected: {e}",
        )

    # Verify capability is read-only
    cap = provider.get_capability()
    if not cap.is_read_only or cap.can_place_order:
        provider.close()
        return AlpacaHealthSnapshot(
            status="unavailable",
            last_checked_at=now,
            error_summary="Provider capability is not read-only. Refusing to connect.",
        )

    # Try account read
    try:
        account = provider.get_account_snapshot()
        account_ok = True
    except (AlpacaUnavailableError, Exception) as e:
        account = None
        account_ok = False
        error_msg = str(e)

    # Try market data read
    try:
        market = provider.get_market_snapshot("AAPL")
        market_ok = True
    except (AlpacaUnavailableError, Exception):
        market = None
        market_ok = False

    provider.close()

    # Determine status
    if account_ok and market_ok:
        status = "connected"
        freshness = account.freshness().value if account else DataFreshnessStatus.MISSING.value
    elif account_ok or market_ok:
        status = "degraded"
        freshness = DataFreshnessStatus.DEGRADED.value
    else:
        status = "degraded"
        freshness = DataFreshnessStatus.MISSING.value
        error_msg = error_msg if not account_ok else "Unknown"

    # Build redacted snapshot
    snapshot = AlpacaHealthSnapshot(
        status=status,
        last_checked_at=now,
        freshness=freshness,
        write_capabilities=cap.write_capabilities,
    )

    if account:
        # Mask account number: PA37AKH0E5AT → PA37****E5AT
        raw_id = account.account_alias
        if len(raw_id) > 8:
            masked = raw_id[:4] + "****" + raw_id[-4:]
        else:
            masked = raw_id[:2] + "****" if len(raw_id) > 2 else "****"
        snapshot.account_alias = masked
        snapshot.total_equity = account.total_equity
        snapshot.available_cash = account.available_cash

    if market:
        snapshot.sample_symbol = market.symbol
        snapshot.sample_price = market.price

    if not account_ok:
        snapshot.error_summary = error_msg if not account_ok else ""

    return snapshot
