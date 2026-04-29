"""Tests: Alpaca health snapshot — redaction + safety (Phase 6K)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from adapters.finance import AlpacaUnavailableError
from adapters.finance.health import get_alpaca_health_snapshot
from domains.finance import DataFreshnessStatus


# ── Fixtures ─────────────────────────────────────────────────────────

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


# ══════════════════════════════════════════════════════════════════════
# Missing keys → unavailable
# ══════════════════════════════════════════════════════════════════════


class TestMissingKeys:
    def test_missing_keys_returns_unavailable(self):
        with patch.dict(os.environ, {"ALPACA_PAPER": "true"}, clear=True):
            snap = get_alpaca_health_snapshot()
            assert snap.status == "unavailable"
            assert "not configured" in snap.error_summary.lower()

    def test_missing_keys_does_not_crash(self):
        with patch.dict(os.environ, {"ALPACA_PAPER": "true"}, clear=True):
            snap = get_alpaca_health_snapshot()  # must not raise
            assert snap is not None


# ══════════════════════════════════════════════════════════════════════
# Non-paper refused
# ══════════════════════════════════════════════════════════════════════


class TestNonPaperRejected:
    def test_non_paper_flag_returns_unavailable(self, paper_env):
        with patch.dict(os.environ, {"ALPACA_PAPER": "false"}):
            snap = get_alpaca_health_snapshot()
            assert snap.status == "unavailable"
            assert "rejected" in snap.error_summary.lower()

    def test_non_paper_url_returns_unavailable(self, paper_env):
        with patch.dict(os.environ, {"ALPACA_BASE_URL": "https://api.alpaca.markets"}):
            snap = get_alpaca_health_snapshot()
            assert snap.status == "unavailable"


# ══════════════════════════════════════════════════════════════════════
# Connected paper snapshot
# ══════════════════════════════════════════════════════════════════════


class TestConnectedSnapshot:
    def test_valid_account_and_market_returns_connected(self, paper_env):
        mock_account = {
            "account_number": "PA37TEST1234",
            "equity": "100000",
            "cash": "100000",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_quote = {
            "symbol": "AAPL",
            "quote": {"bp": "255.77", "t": datetime.now(timezone.utc).isoformat() + "Z"},
        }

        with (
            patch("adapters.finance.AlpacaObservationProvider._get", return_value=mock_account),
            patch("adapters.finance.AlpacaObservationProvider._data_get", return_value=mock_quote),
        ):
            snap = get_alpaca_health_snapshot()
            assert snap.status == "connected"
            assert snap.freshness == DataFreshnessStatus.CURRENT.value

    def test_account_id_is_masked(self, paper_env):
        mock_account = {
            "account_number": "PA37TEST1234",
            "equity": "100000",
            "cash": "100000",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_quote = {
            "symbol": "AAPL",
            "quote": {"bp": "255.77", "t": datetime.now(timezone.utc).isoformat() + "Z"},
        }

        with (
            patch("adapters.finance.AlpacaObservationProvider._get", return_value=mock_account),
            patch("adapters.finance.AlpacaObservationProvider._data_get", return_value=mock_quote),
        ):
            snap = get_alpaca_health_snapshot()
            assert "****" in snap.account_alias
            assert "PA37TEST1234" not in snap.account_alias

    def test_short_account_id_also_masked(self, paper_env):
        mock_account = {
            "account_number": "AB",
            "equity": "100",
            "cash": "100",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_quote = {
            "symbol": "T",
            "quote": {"bp": "10", "t": datetime.now(timezone.utc).isoformat() + "Z"},
        }

        with (
            patch("adapters.finance.AlpacaObservationProvider._get", return_value=mock_account),
            patch("adapters.finance.AlpacaObservationProvider._data_get", return_value=mock_quote),
        ):
            snap = get_alpaca_health_snapshot()
            assert "****" in snap.account_alias

    def test_write_capabilities_always_empty(self, paper_env):
        mock_account = {
            "account_number": "PA37TEST",
            "equity": "100",
            "cash": "100",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_quote = {
            "symbol": "T",
            "quote": {"bp": "10", "t": datetime.now(timezone.utc).isoformat() + "Z"},
        }

        with (
            patch("adapters.finance.AlpacaObservationProvider._get", return_value=mock_account),
            patch("adapters.finance.AlpacaObservationProvider._data_get", return_value=mock_quote),
        ):
            snap = get_alpaca_health_snapshot()
            assert snap.write_capabilities == []

    def test_sample_symbol_and_price_present(self, paper_env):
        mock_account = {
            "account_number": "PA37TEST",
            "equity": "100",
            "cash": "100",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_quote = {
            "symbol": "AAPL",
            "quote": {"bp": "255.77", "t": datetime.now(timezone.utc).isoformat() + "Z"},
        }

        with (
            patch("adapters.finance.AlpacaObservationProvider._get", return_value=mock_account),
            patch("adapters.finance.AlpacaObservationProvider._data_get", return_value=mock_quote),
        ):
            snap = get_alpaca_health_snapshot()
            assert snap.sample_symbol == "AAPL"
            assert snap.sample_price == 255.77


# ══════════════════════════════════════════════════════════════════════
# Degraded / error handling
# ══════════════════════════════════════════════════════════════════════


class TestDegraded:
    def test_account_fails_market_ok_returns_degraded(self, paper_env):
        mock_quote = {
            "symbol": "AAPL",
            "quote": {"bp": "255.77", "t": datetime.now(timezone.utc).isoformat() + "Z"},
        }

        with (
            patch("adapters.finance.AlpacaObservationProvider._get", side_effect=AlpacaUnavailableError("timeout")),
            patch("adapters.finance.AlpacaObservationProvider._data_get", return_value=mock_quote),
        ):
            snap = get_alpaca_health_snapshot()
            assert snap.status == "degraded"

    def test_both_fail_returns_degraded(self, paper_env):
        with (
            patch("adapters.finance.AlpacaObservationProvider._get", side_effect=AlpacaUnavailableError("timeout")),
            patch(
                "adapters.finance.AlpacaObservationProvider._data_get", side_effect=AlpacaUnavailableError("timeout")
            ),
        ):
            snap = get_alpaca_health_snapshot()
            assert snap.status == "degraded"
            assert snap.freshness == DataFreshnessStatus.MISSING.value


# ══════════════════════════════════════════════════════════════════════
# Redaction: no secrets
# ══════════════════════════════════════════════════════════════════════


class TestRedaction:
    def test_no_secrets_in_snapshot(self, paper_env):
        mock_account = {
            "account_number": "PA37TEST1234",
            "equity": "100000",
            "cash": "100000",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_quote = {
            "symbol": "AAPL",
            "quote": {"bp": "255.77", "t": datetime.now(timezone.utc).isoformat() + "Z"},
        }

        with (
            patch("adapters.finance.AlpacaObservationProvider._get", return_value=mock_account),
            patch("adapters.finance.AlpacaObservationProvider._data_get", return_value=mock_quote),
        ):
            snap = get_alpaca_health_snapshot()
            d = snap.to_dict()
            result_str = str(d).lower()
            # No secret-like patterns
            assert "PKTEST" not in result_str
            assert "secret" not in result_str
            assert "token" not in result_str
            assert "api_key" not in result_str

    def test_to_dict_is_serializable(self, paper_env):
        mock_account = {
            "account_number": "PA37TEST",
            "equity": "100",
            "cash": "100",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_quote = {
            "symbol": "T",
            "quote": {"bp": "10", "t": datetime.now(timezone.utc).isoformat() + "Z"},
        }

        with (
            patch("adapters.finance.AlpacaObservationProvider._get", return_value=mock_account),
            patch("adapters.finance.AlpacaObservationProvider._data_get", return_value=mock_quote),
        ):
            snap = get_alpaca_health_snapshot()
            import json

            json.dumps(snap.to_dict())  # must not raise

    def test_environment_is_always_paper(self, paper_env):
        mock_account = {
            "account_number": "PA37TEST",
            "equity": "100",
            "cash": "100",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_quote = {
            "symbol": "T",
            "quote": {"bp": "10", "t": datetime.now(timezone.utc).isoformat() + "Z"},
        }

        with (
            patch("adapters.finance.AlpacaObservationProvider._get", return_value=mock_account),
            patch("adapters.finance.AlpacaObservationProvider._data_get", return_value=mock_quote),
        ):
            snap = get_alpaca_health_snapshot()
            assert snap.environment == "paper"
