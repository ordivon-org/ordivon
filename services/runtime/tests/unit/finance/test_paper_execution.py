"""Tests: AlpacaPaperExecutionAdapter — paper-only safety (Phase 7P-2).

All tests mock HTTP. No real API calls. No secrets in fixtures.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from adapters.finance.paper_execution import (
    AlpacaPaperExecutionAdapter,
    PaperExecutionCapability,
    PaperLiveRejectedError,
    PaperOrderRequest,
    PaperOrderValidationError,
    _mask,
    _redacted,
)


# ── Fixtures ─────────────────────────────────────────────────────────

PAPER_ENV = {
    "ALPACA_API_KEY": "PKTESTPAPERKEY1234",
    "ALPACA_SECRET_KEY": "test-secret-key",
    "ALPACA_PAPER": "true",
    "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
}


@pytest.fixture
def paper_env():
    with patch.dict(os.environ, PAPER_ENV, clear=False):
        yield


@pytest.fixture
def adapter(paper_env):
    return AlpacaPaperExecutionAdapter()


def valid_request(**overrides) -> PaperOrderRequest:
    kwargs = {
        "symbol": "AAPL",
        "side": "buy",
        "order_type": "market",
        "quantity": 1.0,
        "plan_receipt_id": "receipt-001",
        "no_live_disclaimer": True,
    }
    kwargs.update(overrides)
    return PaperOrderRequest(**kwargs)


# ══════════════════════════════════════════════════════════════════════
# Capability tests
# ══════════════════════════════════════════════════════════════════════


class TestPaperExecutionCapability:
    def test_paper_only_by_default(self):
        cap = PaperExecutionCapability()
        assert cap.environment == "paper"
        assert cap.can_place_paper_order is True
        assert cap.can_place_live_order is False
        assert cap.can_cancel_live_order is False
        assert cap.can_withdraw is False
        assert cap.can_transfer is False
        assert cap.can_auto_trade is False
        assert cap.is_paper_only is True
        assert cap.live_write_capabilities == []

    def test_live_order_rejected(self):
        # Use __new__ + manual init to bypass frozen constructor
        cap = PaperExecutionCapability()
        with pytest.raises(ValueError, match="live orders FORBIDDEN"):
            object.__setattr__(cap, "can_place_live_order", True)
            cap.__post_init__()

    def test_live_cancel_rejected(self):
        cap = PaperExecutionCapability()
        with pytest.raises(ValueError, match="live cancel FORBIDDEN"):
            object.__setattr__(cap, "can_cancel_live_order", True)
            cap.__post_init__()

    def test_withdraw_rejected(self):
        cap = PaperExecutionCapability()
        with pytest.raises(ValueError, match="withdraw FORBIDDEN"):
            object.__setattr__(cap, "can_withdraw", True)
            cap.__post_init__()

    def test_transfer_rejected(self):
        cap = PaperExecutionCapability()
        with pytest.raises(ValueError, match="transfer FORBIDDEN"):
            object.__setattr__(cap, "can_transfer", True)
            cap.__post_init__()

    def test_auto_trade_rejected(self):
        cap = PaperExecutionCapability()
        with pytest.raises(ValueError, match="auto trade FORBIDDEN"):
            object.__setattr__(cap, "can_auto_trade", True)
            cap.__post_init__()

    def test_environment_must_be_paper(self):
        cap = PaperExecutionCapability()
        with pytest.raises(ValueError, match="'paper'"):
            object.__setattr__(cap, "environment", "live")
            cap.__post_init__()

    def test_all_write_fields_false_by_default(self):
        cap = PaperExecutionCapability()
        assert cap.can_place_live_order is False
        assert cap.can_cancel_live_order is False
        assert cap.can_withdraw is False
        assert cap.can_transfer is False
        assert cap.can_auto_trade is False
        assert cap.live_write_capabilities == []


# ══════════════════════════════════════════════════════════════════════
# Adapter initialization guards
# ══════════════════════════════════════════════════════════════════════


class TestAdapterInitGuards:
    def test_normal_init(self, adapter):
        assert adapter is not None
        cap = adapter.get_capability()
        assert cap.can_place_paper_order is True
        assert cap.can_place_live_order is False

    def test_refuses_live_url(self, paper_env):
        with patch.dict(os.environ, {"ALPACA_BASE_URL": "https://api.alpaca.markets"}):
            with pytest.raises(PaperLiveRejectedError, match="Paper-only"):
                AlpacaPaperExecutionAdapter()

    def test_refuses_paper_false(self, paper_env):
        with patch.dict(os.environ, {"ALPACA_PAPER": "false"}):
            with pytest.raises(PaperLiveRejectedError, match="PAPER"):
                AlpacaPaperExecutionAdapter()

    def test_refuses_live_key_prefix(self, paper_env):
        with patch.dict(os.environ, {"ALPACA_API_KEY": "AKLIVEKEY1234"}):
            with pytest.raises(PaperLiveRejectedError, match="PK"):
                AlpacaPaperExecutionAdapter()

    def test_refuses_missing_keys(self):
        with patch.dict(os.environ, {"ALPACA_PAPER": "true"}, clear=True):
            with pytest.raises(PaperLiveRejectedError):
                AlpacaPaperExecutionAdapter()

    def test_adapter_id_is_paper_execution(self, adapter):
        cap = adapter.get_capability()
        assert cap.adapter_id == "alpaca-paper-execution"


# ══════════════════════════════════════════════════════════════════════
# Order request validation
# ══════════════════════════════════════════════════════════════════════


class TestOrderRequestValidation:
    def test_valid_request(self):
        req = valid_request()
        assert req.symbol == "AAPL"
        assert req.side == "buy"

    def test_rejects_missing_plan_receipt_id(self):
        with pytest.raises(PaperOrderValidationError, match="plan_receipt_id"):
            valid_request(plan_receipt_id="")

    def test_rejects_missing_disclaimer(self):
        with pytest.raises(PaperOrderValidationError, match="no_live_disclaimer"):
            valid_request(no_live_disclaimer=False)

    def test_rejects_invalid_side(self):
        with pytest.raises(PaperOrderValidationError, match="side"):
            valid_request(side="short")

    def test_rejects_invalid_order_type(self):
        with pytest.raises(PaperOrderValidationError, match="order_type"):
            valid_request(order_type="stop_loss")

    def test_rejects_empty_symbol(self):
        with pytest.raises(PaperOrderValidationError, match="symbol"):
            valid_request(symbol="")

    def test_rejects_zero_quantity_and_notional(self):
        with pytest.raises(PaperOrderValidationError, match="positive"):
            valid_request(quantity=0.0, notional=0.0)

    def test_limit_order_requires_price(self):
        with pytest.raises(PaperOrderValidationError, match="limit_price"):
            valid_request(order_type="limit", limit_price=None)

    def test_limit_order_with_price_ok(self):
        req = valid_request(order_type="limit", limit_price=195.0)
        assert req.limit_price == 195.0

    def test_notional_accepted(self):
        req = valid_request(quantity=0.0, notional=100.0)
        assert req.notional == 100.0


# ══════════════════════════════════════════════════════════════════════
# Submit order (mocked)
# ══════════════════════════════════════════════════════════════════════


class TestSubmitPaperOrder:
    def test_submit_returns_receipt(self, adapter):
        mock_response = {
            "id": "order-paper-123",
            "client_order_id": "receipt-001",
            "symbol": "AAPL",
            "side": "buy",
            "type": "market",
            "qty": "1",
            "submitted_at": "2026-04-29T12:00:00Z",
            "status": "accepted",
        }
        with patch.object(adapter, "_post", return_value=mock_response):
            receipt = adapter.submit_paper_order(valid_request())
            assert receipt.provider_order_id == "order-paper-123"
            assert receipt.symbol == "AAPL"
            assert receipt.side == "buy"
            assert receipt.status == "accepted"
            assert receipt.environment == "paper"
            assert receipt.live_order is False
            assert receipt.source == "alpaca-paper"

    def test_receipt_never_live(self, adapter):
        mock_response = {
            "id": "x",
            "client_order_id": "r",
            "symbol": "T",
            "side": "sell",
            "type": "market",
            "qty": "1",
            "status": "accepted",
            "submitted_at": "2026-04-29T12:00:00Z",
        }
        with patch.object(adapter, "_post", return_value=mock_response):
            receipt = adapter.submit_paper_order(valid_request(side="sell"))
            assert receipt.live_order is False
            assert receipt.environment == "paper"

    def test_order_status_get(self, adapter):
        mock_response = {
            "id": "order-paper-456",
            "client_order_id": "r",
            "symbol": "MSFT",
            "side": "buy",
            "type": "limit",
            "qty": "2",
            "limit_price": "420.0",
            "status": "filled",
            "submitted_at": "2026-04-29T13:00:00Z",
        }
        with patch.object(adapter, "_get", return_value=mock_response):
            receipt = adapter.get_order_status("order-paper-456")
            assert receipt.provider_order_id == "order-paper-456"
            assert receipt.status == "filled"


# ══════════════════════════════════════════════════════════════════════
# No live methods
# ══════════════════════════════════════════════════════════════════════


class TestNoLiveMethods:
    def test_no_live_order_method(self, adapter):
        assert not hasattr(adapter, "submit_live_order")
        assert not hasattr(adapter, "place_live_order")
        assert not hasattr(adapter, "cancel_order")
        assert not hasattr(adapter, "withdraw")
        assert not hasattr(adapter, "transfer")

    def test_only_allowed_public_methods(self, adapter):
        public = [m for m in dir(adapter) if not m.startswith("_") and callable(getattr(adapter, m, None))]
        allowed = {"get_capability", "submit_paper_order", "get_order_status", "cancel_paper_order", "close"}
        for m in public:
            assert m in allowed, f"Unexpected public method: {m}"


# ══════════════════════════════════════════════════════════════════════
# No secret exposure
# ══════════════════════════════════════════════════════════════════════


class TestNoSecretExposure:
    def test_repr_does_not_expose_secret(self, adapter):
        r = repr(adapter)
        assert "test-secret-key" not in r
        assert "PKTESTPAPERKEY1234" not in r

    def test_repr_shows_masked_key(self, adapter):
        r = repr(adapter)
        assert "PKTE...1234" in r

    def test_repr_shows_paper_and_no_live(self, adapter):
        r = repr(adapter)
        assert "paper_only=True" in r
        assert "can_place_live_order=False" in r

    def test_redacted_url_strips_query(self):
        url = "https://paper-api.alpaca.markets/v2/orders?secret=xxx"
        result = _redacted(url)
        assert "secret" not in result
        assert "xxx" not in result

    def test_mask_short(self):
        assert _mask("abc") == "***"

    def test_mask_normal(self):
        assert _mask("PKTESTKEY1234") == "PKTE...1234"


# ══════════════════════════════════════════════════════════════════════
# Build order payload
# ══════════════════════════════════════════════════════════════════════


class TestBuildOrderPayload:
    def test_market_order_payload(self, adapter):
        req = valid_request()
        payload = adapter._build_order_payload(req)
        assert payload["symbol"] == "AAPL"
        assert payload["side"] == "buy"
        assert payload["type"] == "market"
        assert payload["qty"] == "1.0"
        assert "limit_price" not in payload

    def test_limit_order_payload(self, adapter):
        req = valid_request(order_type="limit", limit_price=195.0)
        payload = adapter._build_order_payload(req)
        assert payload["limit_price"] == "195.0"

    def test_notional_payload(self, adapter):
        req = valid_request(quantity=0.0, notional=100.0)
        payload = adapter._build_order_payload(req)
        assert payload["notional"] == "100.0"
        assert "qty" not in payload

    def test_client_order_id_from_receipt(self, adapter):
        req = valid_request(client_order_id="")
        payload = adapter._build_order_payload(req)
        assert payload["client_order_id"] == "receipt-001"


# ══════════════════════════════════════════════════════════════════════
# Close / cleanup
# ══════════════════════════════════════════════════════════════════════


class TestClose:
    def test_close_cleans_up(self, adapter):
        adapter.close()
        assert adapter._http is None
        adapter.close()  # double close safe
