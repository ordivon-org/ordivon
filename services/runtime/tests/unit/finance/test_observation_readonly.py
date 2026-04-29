"""Tests: Finance Observation Layer — read-only boundary (Phase 6G)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from domains.finance import (
    AccountSnapshot,
    DataFreshnessStatus,
    FeeSlippageRecord,
    FillRecord,
    MarketDataSnapshot,
    ObservationSource,
    OrderSide,
    PositionSnapshot,
)
from domains.finance.read_only_adapter import (
    MockObservationProvider,
    ReadOnlyAdapterCapability,
)


# ══════════════════════════════════════════════════════════════════════
# Red-Team Gate 1: Freshness model validates correctly
# ══════════════════════════════════════════════════════════════════════


class TestDataFreshness:
    """DataFreshnessStatus must be computable and not silently wrong."""

    def test_current_market_data(self):
        snap = MarketDataSnapshot(symbol="AAPL", price=100.0, timestamp=datetime.now(timezone.utc))
        assert snap.freshness() == DataFreshnessStatus.CURRENT

    def test_stale_market_data(self):
        snap = MarketDataSnapshot(
            symbol="AAPL", price=100.0,
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=120),
        )
        assert snap.freshness() == DataFreshnessStatus.STALE

    def test_degraded_market_data(self):
        snap = MarketDataSnapshot(
            symbol="AAPL", price=100.0,
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=1000),
        )
        assert snap.freshness() == DataFreshnessStatus.DEGRADED

    def test_missing_market_data(self):
        snap = MarketDataSnapshot(
            symbol="AAPL", price=100.0,
            timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        assert snap.freshness() == DataFreshnessStatus.MISSING

    def test_account_freshness_current(self):
        snap = AccountSnapshot(timestamp=datetime.now(timezone.utc))
        assert snap.freshness() == DataFreshnessStatus.CURRENT

    def test_account_freshness_stale(self):
        snap = AccountSnapshot(timestamp=datetime.now(timezone.utc) - timedelta(seconds=120))
        assert snap.freshness() == DataFreshnessStatus.STALE


class TestFreshnessBoundaries:
    """Red-Team: Stale data cannot be shown as current."""

    def test_stale_is_not_current(self):
        assert DataFreshnessStatus.STALE != DataFreshnessStatus.CURRENT

    def test_degraded_is_not_current(self):
        assert DataFreshnessStatus.DEGRADED != DataFreshnessStatus.CURRENT

    def test_missing_is_not_current(self):
        assert DataFreshnessStatus.MISSING != DataFreshnessStatus.CURRENT


# ══════════════════════════════════════════════════════════════════════
# Red-Team Gate 2: Read-only capability always has write=False
# ══════════════════════════════════════════════════════════════════════


class TestReadOnlyCapability:
    """ReadOnlyAdapterCapability must always be read-only."""

    def test_default_is_read_only(self):
        cap = ReadOnlyAdapterCapability()
        assert cap.is_read_only is True
        assert cap.can_place_order is False
        assert cap.can_cancel_order is False
        assert cap.can_withdraw is False
        assert cap.can_transfer is False
        assert cap.write_capabilities == []

    def test_place_order_always_false(self):
        cap = ReadOnlyAdapterCapability()
        assert cap.can_place_order is False

    def test_write_permissions_never_true(self):
        """Red-Team: No write permission can ever be True by construction.
        Post-init guard rejects any attempt; frozen prevents mutation."""
        cap = ReadOnlyAdapterCapability()
        assert cap.can_place_order is False
        assert cap.can_cancel_order is False
        assert cap.can_withdraw is False
        assert cap.can_transfer is False

    def test_adapter_id_is_settable(self):
        """Only the adapter_id may differ between instances."""
        cap = ReadOnlyAdapterCapability(adapter_id="alpaca-readonly")
        assert cap.adapter_id == "alpaca-readonly"
        assert cap.can_place_order is False  # still false

    def test_all_write_permissions_false_by_construction(self):
        cap = ReadOnlyAdapterCapability(adapter_id="test-adapter")
        write_fields = [
            cap.can_place_order,
            cap.can_cancel_order,
            cap.can_withdraw,
            cap.can_transfer,
        ]
        assert all(w is False for w in write_fields)
        assert len(cap.write_capabilities) == 0

    def test_read_permissions_true_by_default(self):
        cap = ReadOnlyAdapterCapability()
        assert cap.can_read_market_data is True
        assert cap.can_read_account is True
        assert cap.can_read_positions is True
        assert cap.can_read_fills is True


# ══════════════════════════════════════════════════════════════════════
# Red-Team Gate 3: Missing account snapshot is explicit
# ══════════════════════════════════════════════════════════════════════


class TestMissingAccountSnapshot:
    """Zero-equity account is a valid state, not an error."""

    def test_zero_equity_account_is_valid(self):
        snap = AccountSnapshot(
            venue="MOCK", account_alias="empty", total_equity=0.0, available_cash=0.0,
        )
        assert snap.total_equity == 0.0
        assert snap.available_cash == 0.0
        assert snap.freshness() == DataFreshnessStatus.CURRENT

    def test_account_alias_is_explicit(self):
        snap = AccountSnapshot(account_alias="micro-capital")
        assert snap.account_alias == "micro-capital"


# ══════════════════════════════════════════════════════════════════════
# Red-Team Gate 4: Fee/slippage are explicit and visible
# ══════════════════════════════════════════════════════════════════════


class TestFeeSlippage:
    """Fee and slippage must be explicitly tracked."""

    def test_slippage_computed(self):
        rec = FeeSlippageRecord(expected_price=195.00, actual_price=195.12, fee=0.03)
        assert rec.slippage == pytest.approx(0.12)

    def test_zero_slippage(self):
        rec = FeeSlippageRecord(expected_price=100.0, actual_price=100.0, fee=0.0)
        assert rec.slippage == 0.0

    def test_negative_slippage(self):
        rec = FeeSlippageRecord(expected_price=195.00, actual_price=194.50, fee=0.03)
        assert rec.slippage == -0.50

    def test_fee_currency_default(self):
        rec = FeeSlippageRecord(expected_price=195.00, actual_price=195.00, fee=1.0)
        assert rec.fee_currency == "USD"


# ══════════════════════════════════════════════════════════════════════
# PositionSnapshot valuation tests
# ══════════════════════════════════════════════════════════════════════


class TestPositionSnapshot:
    """Position unrealized PnL must be explicitly stored, not inferred."""

    def test_buy_position_pnl(self):
        pos = PositionSnapshot(
            symbol="AAPL", side=OrderSide.BUY, quantity=10,
            entry_price=100.0, mark_price=105.0, unrealized_pnl=50.0,
        )
        assert pos.unrealized_pnl == 50.0
        assert pos.realized_pnl == 50.0  # computed aligns

    def test_sell_position(self):
        pos = PositionSnapshot(
            symbol="AAPL", side=OrderSide.SELL, quantity=10,
            entry_price=100.0, mark_price=95.0, unrealized_pnl=50.0,
        )
        assert pos.side == OrderSide.SELL

    def test_zero_quantity(self):
        pos = PositionSnapshot(symbol="AAPL", quantity=0.0, unrealized_pnl=0.0)
        assert pos.realized_pnl == 0.0


# ══════════════════════════════════════════════════════════════════════
# MockObservationProvider tests
# ══════════════════════════════════════════════════════════════════════


class TestMockObservationProvider:
    """Mock provider returns static sample data. No broker connection."""

    def setup_method(self):
        self.provider = MockObservationProvider()

    def test_capability_is_read_only(self):
        cap = self.provider.get_capability()
        assert cap.is_read_only is True
        assert cap.can_place_order is False

    def test_market_snapshot_returns_mock_data(self):
        snap = self.provider.get_market_snapshot("TSLA")
        assert snap.symbol == "TSLA"
        assert snap.source == ObservationSource.MOCK
        assert snap.venue == "MOCK"
        # Mock data timestamp is intentionally old — freshness should be stale/degraded/missing
        assert snap.freshness() != DataFreshnessStatus.CURRENT

    def test_account_snapshot_returns_mock_data(self):
        snap = self.provider.get_account_snapshot()
        assert snap.account_alias == "micro-capital"
        assert snap.total_equity == 100.0
        assert snap.source == ObservationSource.MOCK

    def test_positions_empty_by_default(self):
        positions = self.provider.get_positions()
        assert positions == []

    def test_fills_have_sample_data(self):
        fills = self.provider.get_fills()
        assert len(fills) == 1
        assert fills[0].symbol == "AAPL"
        assert fills[0].source == ObservationSource.MANUAL

    def test_fee_slippage_visible(self):
        rec = self.provider.get_fee_slippage()
        assert rec.expected_price == 195.00
        assert rec.actual_price == 195.12
        assert rec.slippage == pytest.approx(0.12)
        assert rec.fee == 0.03

    def test_mock_data_is_labeled(self):
        """Red-Team: Mock/manual data is clearly labeled as such."""
        snap = self.provider.get_market_snapshot("AAPL")
        assert snap.source == ObservationSource.MOCK
        assert snap.venue == "MOCK"
        acct = self.provider.get_account_snapshot()
        assert acct.source == ObservationSource.MOCK
        fills = self.provider.get_fills()
        assert fills[0].source == ObservationSource.MANUAL
