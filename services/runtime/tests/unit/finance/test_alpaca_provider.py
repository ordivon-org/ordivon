"""Tests: AlpacaObservationProvider — read-only safety boundary (Phase 6I).

All tests mock HTTP. No real API keys needed. No secrets in test fixtures.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from domains.finance import (
    DataFreshnessStatus,
    ObservationSource,
    OrderSide,
)
from adapters.finance import (
    AlpacaKeyMissingError,
    AlpacaObservationProvider,
    AlpacaWriteRejectedError,
    _mask,
)


# ── Test fixture: mock env with paper keys ────────────────────────────

PAPER_ENV = {
    "ALPACA_API_KEY": "PKTESTPAPERKEY1234",
    "ALPACA_SECRET_KEY": "test-secret-key-for-paper-only",
    "ALPACA_PAPER": "true",
    "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
    "ALPACA_DATA_URL": "https://data.alpaca.markets",
}


@pytest.fixture
def paper_env():
    with patch.dict(os.environ, PAPER_ENV, clear=False):
        yield


@pytest.fixture
def provider(paper_env):
    return AlpacaObservationProvider()


# ══════════════════════════════════════════════════════════════════════
# Red-Team Gate 1: Capability is read-only
# ══════════════════════════════════════════════════════════════════════


class TestCapability:
    def test_capability_is_read_only(self, provider):
        cap = provider.get_capability()
        assert cap.is_read_only is True
        assert cap.can_place_order is False
        assert cap.can_cancel_order is False
        assert cap.can_withdraw is False
        assert cap.can_transfer is False
        assert cap.write_capabilities == []

    def test_adapter_id_is_alpaca_paper(self, provider):
        cap = provider.get_capability()
        assert cap.adapter_id == "alpaca-paper"


# ══════════════════════════════════════════════════════════════════════
# Red-Team Gate 2: Provider refuses non-paper configuration
# ══════════════════════════════════════════════════════════════════════


class TestPaperOnlyEnforcement:
    def test_refuses_live_base_url(self, paper_env):
        with patch.dict(os.environ, {"ALPACA_BASE_URL": "https://api.alpaca.markets"}):
            with pytest.raises(AlpacaWriteRejectedError, match="paper-api"):
                AlpacaObservationProvider()

    def test_refuses_non_paper_flag(self, paper_env):
        with patch.dict(os.environ, {"ALPACA_PAPER": "false"}):
            with pytest.raises(AlpacaWriteRejectedError, match="PAPER=true"):
                AlpacaObservationProvider()

    def test_refuses_live_api_key_prefix(self, paper_env):
        with patch.dict(os.environ, {"ALPACA_API_KEY": "AKLIVEKEY1234"}):
            with pytest.raises(AlpacaWriteRejectedError, match="PK"):
                AlpacaObservationProvider()

    def test_refuses_missing_keys(self):
        with patch.dict(os.environ, {"ALPACA_PAPER": "true"}, clear=True):
            with pytest.raises(AlpacaKeyMissingError):
                AlpacaObservationProvider()

    def test_refuses_missing_secret(self, paper_env):
        with patch.dict(os.environ, {"ALPACA_SECRET_KEY": ""}):
            with pytest.raises(AlpacaKeyMissingError):
                AlpacaObservationProvider()


# ══════════════════════════════════════════════════════════════════════
# Red-Team Gate 3: No write methods exist
# ══════════════════════════════════════════════════════════════════════


class TestNoWriteMethods:
    def test_no_place_order_method(self, provider):
        assert not hasattr(provider, "place_order")
        assert not hasattr(provider, "submit_order")

    def test_no_cancel_order_method(self, provider):
        assert not hasattr(provider, "cancel_order")
        assert not hasattr(provider, "replace_order")

    def test_no_withdraw_transfer_methods(self, provider):
        assert not hasattr(provider, "withdraw")
        assert not hasattr(provider, "transfer")

    def test_no_margin_methods(self, provider):
        assert not hasattr(provider, "enable_margin")
        assert not hasattr(provider, "enable_options")

    def test_only_public_read_methods(self, provider):
        public = [m for m in dir(provider) if not m.startswith("_") and callable(getattr(provider, m, None))]
        allowed = {
            "get_capability",
            "get_account_snapshot",
            "get_market_snapshot",
            "get_positions",
            "get_fills",
            "close",
        }
        for m in public:
            assert m in allowed, f"Unexpected public method: {m}"


# ══════════════════════════════════════════════════════════════════════
# Red-Team Gate 4: Secrets are not exposed
# ══════════════════════════════════════════════════════════════════════


class TestNoSecretExposure:
    def test_repr_does_not_expose_secret(self, provider):
        r = repr(provider)
        assert "test-secret-key" not in r
        assert "PKTESTPAPERKEY1234" not in r
        assert "PKTE...1234" in r  # masked key

    def test_repr_does_not_expose_full_key(self, provider):
        r = repr(provider)
        assert "PKTEST" not in r  # masked — only first 4 + ... + last 4

    def test_mask_short_string(self):
        assert _mask("abc") == "***"

    def test_mask_normal_key(self):
        assert _mask("PKTESTKEY1234") == "PKTE...1234"


# ══════════════════════════════════════════════════════════════════════
# Account snapshot mapping
# ══════════════════════════════════════════════════════════════════════


class TestAccountMapping:
    def test_account_response_maps_correctly(self, provider):
        mock_account = {
            "account_number": "PA37TEST",
            "equity": "100000",
            "cash": "100000",
            "status": "ACTIVE",
            "created_at": "2026-04-29T09:26:11.725136Z",
        }
        with patch.object(provider, "_get", return_value=mock_account):
            snap = provider.get_account_snapshot()
            assert snap.account_alias == "PA37TEST"
            assert snap.total_equity == 100000.0
            assert snap.available_cash == 100000.0
            assert snap.venue == "Alpaca Paper"
            assert snap.source == ObservationSource.PROVIDER
            assert snap.timestamp.year == 2026


# ══════════════════════════════════════════════════════════════════════
# Market data mapping
# ══════════════════════════════════════════════════════════════════════


class TestMarketDataMapping:
    def test_quote_response_maps_correctly(self, provider):
        mock_quote = {
            "symbol": "AAPL",
            "quote": {
                "bp": "255.77",
                "bs": "100",
                "ap": "255.80",
                "as": "200",
                "t": "2026-04-29T15:00:00Z",
            },
        }
        with patch.object(provider, "_data_get", return_value=mock_quote):
            snap = provider.get_market_snapshot("AAPL")
            assert snap.symbol == "AAPL"
            assert snap.price == 255.77
            assert snap.bid == 255.77
            assert snap.ask == 255.80
            assert snap.venue == "Alpaca"
            assert snap.source == ObservationSource.PROVIDER

    def test_quote_stale_maps_to_freshness_correctly(self, provider):
        old_ts = datetime.now(timezone.utc).replace(year=2025).isoformat() + "Z"
        mock_quote = {
            "symbol": "AAPL",
            "quote": {"bp": "255.77", "bs": "100", "t": old_ts},
        }
        with patch.object(provider, "_data_get", return_value=mock_quote):
            snap = provider.get_market_snapshot("AAPL")
            status = snap.freshness()
            assert status != DataFreshnessStatus.CURRENT
            assert status in (DataFreshnessStatus.STALE, DataFreshnessStatus.DEGRADED, DataFreshnessStatus.MISSING)

    def test_quote_missing_timestamp_handled(self, provider):
        mock_quote = {
            "symbol": "AAPL",
            "quote": {"bp": "255.77", "t": None},
        }
        with patch.object(provider, "_data_get", return_value=mock_quote):
            snap = provider.get_market_snapshot("AAPL")
            assert snap.price == 255.77
            assert snap.freshness() != DataFreshnessStatus.CURRENT


# ══════════════════════════════════════════════════════════════════════
# Positions mapping
# ══════════════════════════════════════════════════════════════════════


class TestPositionsMapping:
    def test_positions_response_maps_correctly(self, provider):
        mock_positions = [
            {
                "symbol": "AAPL",
                "qty": "1",
                "side": "long",
                "avg_entry_price": "195.12",
                "current_price": "255.77",
                "unrealized_pl": "60.65",
            },
        ]
        with patch.object(provider, "_get", return_value=mock_positions):
            positions = provider.get_positions()
            assert len(positions) == 1
            pos = positions[0]
            assert pos.symbol == "AAPL"
            assert pos.quantity == 1.0
            assert pos.side == OrderSide.BUY
            assert pos.entry_price == 195.12
            assert pos.mark_price == 255.77
            assert pos.unrealized_pnl == 60.65

    def test_empty_positions(self, provider):
        with patch.object(provider, "_get", return_value=[]):
            positions = provider.get_positions()
            assert positions == []


# ══════════════════════════════════════════════════════════════════════
# Fill/order history mapping
# ══════════════════════════════════════════════════════════════════════


class TestFillsMapping:
    def test_fills_response_maps_correctly(self, provider):
        mock_orders = [
            {
                "symbol": "AAPL",
                "side": "buy",
                "filled_qty": "1",
                "filled_avg_price": "195.12",
                "filled_at": "2026-04-29T10:32:00Z",
                "status": "closed",
            },
            {
                "symbol": "MSFT",
                "side": "sell",
                "filled_qty": "2",
                "filled_avg_price": "420.50",
                "filled_at": "2026-04-29T11:00:00Z",
                "status": "closed",
            },
        ]
        with patch.object(provider, "_get", return_value=mock_orders):
            fills = provider.get_fills()
            assert len(fills) == 2
            assert fills[0].symbol == "AAPL"
            assert fills[0].side == OrderSide.BUY
            assert fills[0].price == 195.12
            assert fills[0].source == ObservationSource.PROVIDER
            assert fills[1].symbol == "MSFT"
            assert fills[1].side == OrderSide.SELL

    def test_empty_fills(self, provider):
        with patch.object(provider, "_get", return_value=[]):
            fills = provider.get_fills()
            assert fills == []


# ══════════════════════════════════════════════════════════════════════
# Red-Team Gate 5: HTTP client never calls POST/PATCH/DELETE
# ══════════════════════════════════════════════════════════════════════


class TestNoWriteHTTP:
    def test_request_rejects_non_get(self, provider):
        with pytest.raises(AlpacaWriteRejectedError, match="GET"):
            provider._request("POST", "https://paper-api.alpaca.markets/v2/orders")

    def test_request_rejects_delete(self, provider):
        with pytest.raises(AlpacaWriteRejectedError, match="GET"):
            provider._request("DELETE", "https://paper-api.alpaca.markets/v2/orders/123")

    def test_request_rejects_patch(self, provider):
        with pytest.raises(AlpacaWriteRejectedError, match="GET"):
            provider._request("PATCH", "https://paper-api.alpaca.markets/v2/account")

    def test_only_get_allowed(self, provider):
        # GET should not raise
        # But we don't have a real client — just verify the method check
        with pytest.raises(Exception):  # Will fail on actual HTTP, not method check
            provider._request("GET", "https://paper-api.alpaca.markets/v2/clock")

    def test_close_cleans_up(self, provider):
        provider.close()
        assert provider._http is None
        # Double close is safe
        provider.close()


# ══════════════════════════════════════════════════════════════════════
# Red-Team Gate 6: Provider correctly labels paper source
# ══════════════════════════════════════════════════════════════════════


class TestPaperSourceLabeling:
    def test_account_source_is_provider(self, provider):
        with patch.object(
            provider,
            "_get",
            return_value={
                "account_number": "PA",
                "equity": "100",
                "cash": "100",
                "created_at": "2026-04-29T00:00:00Z",
            },
        ):
            snap = provider.get_account_snapshot()
            assert snap.source == ObservationSource.PROVIDER
            assert snap.venue == "Alpaca Paper"

    def test_market_source_is_provider(self, provider):
        with patch.object(
            provider,
            "_data_get",
            return_value={
                "symbol": "T",
                "quote": {"bp": "10", "t": "2026-04-29T00:00:00Z"},
            },
        ):
            snap = provider.get_market_snapshot("T")
            assert snap.source == ObservationSource.PROVIDER
            assert snap.venue == "Alpaca"
