"""Finance Observation Layer — read-only adapter capability contract (Phase 6G).

Defines the ReadOnlyAdapterCapability and a MockObservationProvider
for tests and UI preview. No broker writes, no order execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Protocol

from domains.finance import (
    AccountSnapshot,
    FeeSlippageRecord,
    FillRecord,
    MarketDataSnapshot,
    ObservationSource,
    OrderSide,
    PositionSnapshot,
)


# ── Read-Only Adapter Capability ─────────────────────────────────────


@dataclass(frozen=True)
class ReadOnlyAdapterCapability:
    """Immutable capability contract for a finance observation adapter.

    This is the ground truth for what an adapter CAN and CANNOT do.
    No adapter may claim write permissions. This is enforced at
    construction — write fields are hardcoded False with no setter.
    """

    adapter_id: str = "mock-observer"
    can_read_market_data: bool = True
    can_read_account: bool = True
    can_read_positions: bool = True
    can_read_fills: bool = True
    # Write permissions — ALWAYS False, not configurable
    can_place_order: bool = False
    can_cancel_order: bool = False
    can_withdraw: bool = False
    can_transfer: bool = False

    def __post_init__(self) -> None:
        if self.can_place_order:
            raise ValueError("ReadOnlyAdapterCapability: can_place_order must be False")
        if self.can_cancel_order:
            raise ValueError("ReadOnlyAdapterCapability: can_cancel_order must be False")
        if self.can_withdraw:
            raise ValueError("ReadOnlyAdapterCapability: can_withdraw must be False")
        if self.can_transfer:
            raise ValueError("ReadOnlyAdapterCapability: can_transfer must be False")

    @property
    def is_read_only(self) -> bool:
        return True  # always

    @property
    def write_capabilities(self) -> list[str]:
        return []  # always empty


# ── Observation Provider Protocol ────────────────────────────────────


class ObservationProvider(Protocol):
    """Protocol for any finance observation adapter (mock or real).

    All methods are read-only. No place_order, cancel_order,
    withdraw, or transfer methods exist on this protocol.
    """

    def get_capability(self) -> ReadOnlyAdapterCapability: ...

    def get_market_snapshot(self, symbol: str) -> MarketDataSnapshot: ...

    def get_account_snapshot(self) -> AccountSnapshot: ...

    def get_positions(self) -> list[PositionSnapshot]: ...

    def get_fills(self) -> list[FillRecord]: ...


# ── Mock Observation Provider ────────────────────────────────────────


@dataclass
class MockObservationProvider:
    """Mock observation provider with sample static data.

    Used for tests and UI preview. All data is clearly labeled as mock.
    No broker connection, no real-time data, no order execution.
    """

    capability: ReadOnlyAdapterCapability = field(
        default_factory=lambda: ReadOnlyAdapterCapability(adapter_id="mock-observer")
    )

    def get_capability(self) -> ReadOnlyAdapterCapability:
        return self.capability

    def get_market_snapshot(self, symbol: str) -> MarketDataSnapshot:
        # Deliberately stale to test freshness handling
        return MarketDataSnapshot(
            symbol=symbol.upper(),
            venue="MOCK",
            price=100.0,
            bid=99.95,
            ask=100.05,
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=30),
            source=ObservationSource.MOCK,
        )

    def get_account_snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(
            venue="MOCK",
            account_alias="micro-capital",
            total_equity=100.0,
            available_cash=100.0,
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=30),
            source=ObservationSource.MOCK,
        )

    def get_positions(self) -> list[PositionSnapshot]:
        return []

    def get_fills(self) -> list[FillRecord]:
        return [
            FillRecord(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=1,
                price=195.12,
                fee=0.03,
                fee_currency="USD",
                source=ObservationSource.MANUAL,
            ),
        ]

    def get_fee_slippage(self) -> FeeSlippageRecord:
        return FeeSlippageRecord(
            expected_price=195.00,
            actual_price=195.12,
            fee=0.03,
            fee_currency="USD",
        )
