"""Finance Observation Layer — pure domain models (Phase 6G).

No ORM, no DB, no broker connection, no side effects.
These are value objects for observing external financial data.
Does NOT: place orders, cancel orders, execute trades, connect brokers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────


class DataFreshnessStatus(str, Enum):
    """Freshness of observed financial data."""

    CURRENT = "current"  # ≤ 1 min old
    STALE = "stale"  # > 1 min, ≤ 15 min old
    DEGRADED = "degraded"  # > 15 min old, source may be unreliable
    MISSING = "missing"  # no data available


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class ObservationSource(str, Enum):
    """The origin of observation data — mock or real provider."""

    MOCK = "mock"
    MANUAL = "manual"
    PROVIDER = "provider"  # placeholder for real provider
    UNKNOWN = "unknown"


# ── Observation Models ───────────────────────────────────────────────


@dataclass(frozen=True)
class MarketDataSnapshot:
    """A single market data point for a symbol at a venue."""

    symbol: str
    venue: str = "MOCK"
    price: float = 0.0
    bid: float | None = None
    ask: float | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: ObservationSource = ObservationSource.MOCK

    def freshness(self, now: datetime | None = None) -> DataFreshnessStatus:
        now = now or datetime.now(timezone.utc)
        delta = (now - self.timestamp).total_seconds()
        if delta <= 60:
            return DataFreshnessStatus.CURRENT
        elif delta <= 900:
            return DataFreshnessStatus.STALE
        elif delta <= 3600:
            return DataFreshnessStatus.DEGRADED
        return DataFreshnessStatus.MISSING


@dataclass(frozen=True)
class AccountSnapshot:
    """Read-only snapshot of account equity and available cash."""

    venue: str = "MOCK"
    account_alias: str = "default"
    total_equity: float = 0.0
    available_cash: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: ObservationSource = ObservationSource.MOCK

    def freshness(self, now: datetime | None = None) -> DataFreshnessStatus:
        now = now or datetime.now(timezone.utc)
        delta = (now - self.timestamp).total_seconds()
        if delta <= 60:
            return DataFreshnessStatus.CURRENT
        elif delta <= 900:
            return DataFreshnessStatus.STALE
        elif delta <= 3600:
            return DataFreshnessStatus.DEGRADED
        return DataFreshnessStatus.MISSING


@dataclass(frozen=True)
class PositionSnapshot:
    """Read-only snapshot of a single position."""

    symbol: str
    side: OrderSide = OrderSide.BUY
    quantity: float = 0.0
    entry_price: float = 0.0
    mark_price: float = 0.0
    unrealized_pnl: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def realized_pnl(self) -> float:
        if self.quantity == 0:
            return 0.0
        if self.side == OrderSide.BUY:
            return (self.mark_price - self.entry_price) * self.quantity
        return (self.entry_price - self.mark_price) * self.quantity


@dataclass(frozen=True)
class FillRecord:
    """Read-only record of a completed fill (trade execution)."""

    symbol: str
    side: OrderSide
    quantity: float
    price: float
    fee: float = 0.0
    fee_currency: str = "USD"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: ObservationSource = ObservationSource.MANUAL


@dataclass(frozen=True)
class FeeSlippageRecord:
    """Comparison of expected vs actual execution cost."""

    expected_price: float
    actual_price: float
    fee: float = 0.0
    fee_currency: str = "USD"

    @property
    def slippage(self) -> float:
        return self.actual_price - self.expected_price

    @property
    def fee_as_pct_of_risk(self) -> float | None:
        """Fee as percentage of risk taken (requires external risk value)."""
        return None  # caller must compute with risk context
