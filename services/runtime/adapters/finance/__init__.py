"""Alpaca Paper Trading — Read-Only Observation Provider (Phase 6I).

Implements ObservationProvider Protocol for Alpaca Paper Trading.
READ-ONLY ONLY. No order placement, cancellation, withdrawal, or transfer.
No broker write. No live trading. No margin. No leverage. No derivatives.

Paper endpoint: https://paper-api.alpaca.markets/v2
Data endpoint:   https://data.alpaca.markets

Keys loaded from env:
  ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, ALPACA_DATA_URL
  ALPACA_PAPER=true (required — refuses to init without)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from domains.finance import (
    AccountSnapshot,
    FillRecord,
    MarketDataSnapshot,
    ObservationSource,
    OrderSide,
    PositionSnapshot,
)
from domains.finance.read_only_adapter import (
    ReadOnlyAdapterCapability,
)

# ── Exceptions ──────────────────────────────────────────────────────


class AlpacaObservationError(Exception):
    """Base error for Alpaca observation adapter."""


class AlpacaUnavailableError(AlpacaObservationError):
    """API unreachable — no response."""


class AlpacaKeyMissingError(AlpacaObservationError):
    """Required env keys not found."""


class AlpacaWriteRejectedError(AlpacaObservationError):
    """Attempted to configure a non-paper or write-capable base URL."""


# ── Provider ────────────────────────────────────────────────────────


@dataclass
class AlpacaObservationProvider:
    """Read-only observation provider for Alpaca Paper Trading.

    This provider:
    - Uses paper-api.alpaca.markets (paper trading, no real money)
    - Only makes GET requests (read-only)
    - Never exposes API keys in repr, errors, or logs
    - Refuses to initialize without ALPACA_PAPER=true
    - Reports can_place_order=False in capability contract
    """

    base_url: str = field(default_factory=lambda: _env("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"))
    data_url: str = field(default_factory=lambda: _env("ALPACA_DATA_URL", "https://data.alpaca.markets"))
    api_key: str = field(default_factory=lambda: _env("ALPACA_API_KEY", ""))
    secret_key: str = field(default_factory=lambda: _env("ALPACA_SECRET_KEY", ""))
    _paper: str = field(default_factory=lambda: _env("ALPACA_PAPER", "false"))

    # Internal state
    _http: httpx.Client | None = field(default=None, repr=False, init=False)
    _capability: ReadOnlyAdapterCapability = field(init=False)
    _initialized: bool = field(default=False, init=False)

    # ── Safety guards ──────────────────────────────────────────

    def __post_init__(self) -> None:
        # Guard 1: Keys must be present (checked first)
        if not self.api_key or not self.secret_key:
            raise AlpacaKeyMissingError(
                "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment. "
                "These should be read-only paper trading keys."
            )

        # Guard 2: Paper only
        if self._paper.lower() not in ("true", "1", "yes"):
            raise AlpacaWriteRejectedError(
                "AlpacaObservationProvider requires ALPACA_PAPER=true. Live trading is not supported in this phase."
            )

        # Guard 3: Paper URL required
        if "paper-api" not in self.base_url:
            raise AlpacaWriteRejectedError(
                f"AlpacaObservationProvider requires paper-api base URL. "
                f"Got: {_redacted_url(self.base_url)}. "
                "Live trading URLs are blocked."
            )

        # Guard 4: Keys must look like paper keys (PK... prefix)
        if not self.api_key.startswith("PK"):
            raise AlpacaWriteRejectedError(
                "Alpaca API key does not start with 'PK'. Live trading keys are blocked in this phase."
            )

        # Immutable capability
        self._capability = ReadOnlyAdapterCapability(adapter_id="alpaca-paper")

    # ── HTTP client (lazy) ────────────────────────────────────

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(
                base_url=self.base_url,
                headers={
                    "APCA-API-KEY-ID": self.api_key,
                    "APCA-API-SECRET-KEY": self.secret_key,
                    "Accept": "application/json",
                },
                timeout=httpx.Timeout(10.0, connect=5.0),
            )
        return self._http

    # ── Protocol: ObservationProvider ─────────────────────────

    def get_capability(self) -> ReadOnlyAdapterCapability:
        return self._capability

    def get_account_snapshot(self) -> AccountSnapshot:
        data = self._get("/v2/account")
        return AccountSnapshot(
            venue="Alpaca Paper",
            account_alias=data.get("account_number", "unknown"),
            total_equity=float(data.get("equity", 0)),
            available_cash=float(data.get("cash", 0)),
            timestamp=_parse_iso(data.get("created_at")),
            source=ObservationSource.PROVIDER,
        )

    def get_market_snapshot(self, symbol: str) -> MarketDataSnapshot:
        resp = self._data_get(f"/v2/stocks/{symbol.upper()}/quotes/latest")
        quote = resp.get("quote", {})
        return MarketDataSnapshot(
            symbol=symbol.upper(),
            venue="Alpaca",
            price=float(quote.get("bp", 0) or quote.get("ap", 0) or 0),
            bid=float(quote["bp"]) if quote.get("bp") else None,
            ask=float(quote["ap"]) if quote.get("ap") else None,
            timestamp=_parse_iso(quote.get("t")),
            source=ObservationSource.PROVIDER,
        )

    def get_positions(self) -> list[PositionSnapshot]:
        data = self._get("/v2/positions")
        positions: list[PositionSnapshot] = []
        for p in data:
            positions.append(
                PositionSnapshot(
                    symbol=p.get("symbol", ""),
                    side=OrderSide.BUY if float(p.get("qty", 0)) > 0 else OrderSide.SELL,
                    quantity=abs(float(p.get("qty", 0))),
                    entry_price=float(p.get("avg_entry_price", 0)),
                    mark_price=float(p.get("current_price", 0)),
                    unrealized_pnl=float(p.get("unrealized_pl", 0)),
                    timestamp=datetime.now(timezone.utc),
                )
            )
        return positions

    def get_fills(self) -> list[FillRecord]:
        data = self._get("/v2/orders?status=closed&limit=50")
        fills: list[FillRecord] = []
        for o in data:
            side = OrderSide.BUY if o.get("side") == "buy" else OrderSide.SELL
            qty = float(o.get("filled_qty", 0) or 0)
            price = float(o.get("filled_avg_price", 0) or 0)
            fee = float(o.get("filled_qty", 0) or 0) * 0.0  # Alpaca is commission-free
            fills.append(
                FillRecord(
                    symbol=o.get("symbol", ""),
                    side=side,
                    quantity=abs(qty),
                    price=price,
                    fee=fee,
                    fee_currency="USD",
                    timestamp=_parse_iso(o.get("filled_at")),
                    source=ObservationSource.PROVIDER,
                )
            )
        return fills

    # ── HTTP helpers (read-only GET only) ─────────────────────

    def _get(self, path: str) -> Any:
        """GET from paper-api.alpaca.markets. Only method allowed."""
        return self._request("GET", self.base_url.rstrip("/") + path)

    def _data_get(self, path: str) -> Any:
        """GET from data.alpaca.markets."""
        return self._request("GET", self.data_url.rstrip("/") + path)

    def _request(self, method: str, url: str) -> Any:
        if method != "GET":
            raise AlpacaWriteRejectedError(
                f"AlpacaObservationProvider only supports GET. Attempted {method} {_redacted_url(url)}"
            )
        try:
            resp = self._client().get(url)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise AlpacaUnavailableError(
                f"Alpaca API returned {e.response.status_code} for {_redacted_url(url)}"
            ) from e
        except httpx.RequestError as e:
            raise AlpacaUnavailableError(f"Alpaca API unreachable: {e}") from e

    # ── Cleanup ───────────────────────────────────────────────

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    def __repr__(self) -> str:
        return (
            f"AlpacaObservationProvider("
            f"base_url={_redacted_url(self.base_url)}, "
            f"data_url={_redacted_url(self.data_url)}, "
            f"key_id={_mask(self.api_key)}, "
            f"paper_only=True, "
            f"can_place_order=False"
            f")"
        )

    def __del__(self) -> None:
        self.close()


# ── Internal helpers (no secrets exposed) ───────────────────────────


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _mask(s: str) -> str:
    if len(s) <= 8:
        return "***"
    return s[:4] + "..." + s[-4:]


def _redacted_url(url: str) -> str:
    """Remove query params from URL display to prevent token leakage."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def _parse_iso(ts: str | None) -> datetime:
    if not ts:
        return datetime.now(timezone.utc) - _ONE_YEAR
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return datetime.now(timezone.utc) - _ONE_YEAR


_ONE_YEAR = __import__("datetime").timedelta(days=365)
