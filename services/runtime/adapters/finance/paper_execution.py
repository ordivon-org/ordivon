"""Alpaca Paper Execution Adapter — paper-only, strictly separated (Phase 7P-2).

Implements PaperExecutionCapability and AlpacaPaperExecutionAdapter.
READ-ONLY ADAPTER IS UNCHANGED. Live trading remains NO-GO.
Paper endpoint only. Paper keys only. No real money.

This module is COMPLETELY SEPARATE from read_only_adapter.py.
No shared capability class. No shared write methods.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


# ── Exceptions ──────────────────────────────────────────────────────


class PaperExecutionError(Exception):
    """Base error for paper execution adapter."""


class PaperLiveRejectedError(PaperExecutionError):
    """Non-paper URL, key, or configuration rejected."""


class PaperOrderValidationError(PaperExecutionError):
    """Order request validation failed."""


class PaperUnavailableError(PaperExecutionError):
    """API unreachable."""


# ── Paper Execution Capability ──────────────────────────────────────


@dataclass(frozen=True)
class PaperExecutionCapability:
    """Immutable capability contract for Alpaca Paper execution.

    SEPARATE from ReadOnlyAdapterCapability. Paper-only.
    Live order/cancel/withdraw/transfer permanently False.
    """

    adapter_id: str = "alpaca-paper-execution"
    environment: str = "paper"
    can_place_paper_order: bool = True
    can_cancel_paper_order: bool = True
    can_place_live_order: bool = False
    can_cancel_live_order: bool = False
    can_withdraw: bool = False
    can_transfer: bool = False
    can_auto_trade: bool = False
    can_replace_order: bool = False

    def __post_init__(self) -> None:
        if self.can_place_live_order:
            raise ValueError("PaperExecutionCapability: live orders FORBIDDEN")
        if self.can_cancel_live_order:
            raise ValueError("PaperExecutionCapability: live cancel FORBIDDEN")
        if self.can_withdraw:
            raise ValueError("PaperExecutionCapability: withdraw FORBIDDEN")
        if self.can_transfer:
            raise ValueError("PaperExecutionCapability: transfer FORBIDDEN")
        if self.can_auto_trade:
            raise ValueError("PaperExecutionCapability: auto trade FORBIDDEN")
        if self.environment != "paper":
            raise ValueError("PaperExecutionCapability: environment must be 'paper'")

    @property
    def is_paper_only(self) -> bool:
        return True

    @property
    def live_write_capabilities(self) -> list[str]:
        return []  # always empty


# ── Paper Order Request ─────────────────────────────────────────────


@dataclass
class PaperOrderRequest:
    """Validated paper order request. Never points to live endpoint."""

    symbol: str
    side: str  # "buy" | "sell"
    order_type: str  # "market" | "limit"
    time_in_force: str = "day"
    quantity: float = 0.0
    notional: float | None = None
    limit_price: float | None = None
    client_order_id: str = ""
    plan_receipt_id: str = ""
    no_live_disclaimer: bool = False

    def __post_init__(self) -> None:
        if not self.plan_receipt_id:
            raise PaperOrderValidationError("plan_receipt_id is required. No paper order without a plan receipt.")
        if not self.no_live_disclaimer:
            raise PaperOrderValidationError(
                "no_live_disclaimer must be True. Operator must acknowledge this is a paper order, not a live trade."
            )
        if self.side not in ("buy", "sell"):
            raise PaperOrderValidationError(f"Invalid side: {self.side}. Must be 'buy' or 'sell'.")
        if self.order_type not in ("market", "limit"):
            raise PaperOrderValidationError(f"Invalid order_type: {self.order_type}. Must be 'market' or 'limit'.")
        if not self.symbol or not self.symbol.strip():
            raise PaperOrderValidationError("symbol is required.")
        qty = self.quantity or 0.0
        notl = self.notional or 0.0
        if qty <= 0.0 and notl <= 0.0:
            raise PaperOrderValidationError("quantity or notional must be positive.")
        if self.order_type == "limit" and self.limit_price is None:
            raise PaperOrderValidationError("limit_price is required for limit orders.")


# ── Paper Order Receipt ─────────────────────────────────────────────


@dataclass
class PaperOrderReceipt:
    """Receipt returned after submitting a paper order. Never live."""

    provider_order_id: str = ""
    client_order_id: str = ""
    symbol: str = ""
    side: str = ""
    order_type: str = ""
    quantity: float = 0.0
    notional: float | None = None
    limit_price: float | None = None
    submitted_at: str = ""
    status: str = ""
    environment: str = "paper"
    live_order: bool = False
    source: str = "alpaca-paper"
    plan_receipt_id: str = ""


# ── Paper Cancel Request ────────────────────────────────────────────


@dataclass
class PaperCancelRequest:
    """Validated paper cancel request. Paper-only. No replace. No auto."""

    provider_order_id: str
    cancel_receipt_id: str
    no_live_disclaimer: bool = False
    human_go: bool = False
    reason: str = ""
    environment: str = "paper"

    def __post_init__(self) -> None:
        if not self.provider_order_id:
            raise PaperOrderValidationError("provider_order_id required for cancel.")
        if not self.cancel_receipt_id:
            raise PaperOrderValidationError("cancel_receipt_id is required. No paper cancel without a receipt.")
        if not self.no_live_disclaimer:
            raise PaperOrderValidationError("no_live_disclaimer must be True. Cancel is paper-only.")
        if not self.human_go:
            raise PaperOrderValidationError("human_go must be True. No automatic paper cancel.")
        if not self.reason.strip():
            raise PaperOrderValidationError("reason is required for paper cancel.")
        if self.environment != "paper":
            raise PaperOrderValidationError("Cancel is paper-only. environment must be 'paper'.")


# ── Paper Cancel Receipt ─────────────────────────────────────────────


@dataclass
class PaperCancelReceipt:
    """Receipt returned after canceling a paper order. Never live. Never replace."""

    provider_order_id: str = ""
    cancel_receipt_id: str = ""
    status: str = ""
    canceled_at: str = ""
    environment: str = "paper"
    live_order: bool = False
    source: str = "alpaca-paper"
    reason: str = ""
    no_replace: bool = True
    no_auto: bool = True


# ── Adapter ─────────────────────────────────────────────────────────


@dataclass
class AlpacaPaperExecutionAdapter:
    """Paper-only execution adapter for Alpaca Paper Trading.

    SEPARATE from AlpacaObservationProvider (read-only).
    Paper endpoint only. Paper keys only. No live trading.

    Safety guards at init:
    - Paper URL required (paper-api)
    - Paper flag required (ALPACA_PAPER=true)
    - Paper key prefix required (PK...)
    - Keys must be present
    """

    base_url: str = field(default_factory=lambda: _penv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"))
    api_key: str = field(default_factory=lambda: _penv("ALPACA_API_KEY", ""))
    secret_key: str = field(default_factory=lambda: _penv("ALPACA_SECRET_KEY", ""))
    _paper: str = field(default_factory=lambda: _penv("ALPACA_PAPER", "false"))

    _http: httpx.Client | None = field(default=None, repr=False, init=False)
    _capability: PaperExecutionCapability = field(init=False)

    def __post_init__(self) -> None:
        # Guard 1: Keys
        if not self.api_key or not self.secret_key:
            raise PaperLiveRejectedError("ALPACA_API_KEY and ALPACA_SECRET_KEY required.")
        # Guard 2: Paper flag
        if self._paper.lower() not in ("true", "1", "yes"):
            raise PaperLiveRejectedError("ALPACA_PAPER must be true. Live trading is not supported.")
        # Guard 3: Paper URL
        if "paper-api" not in self.base_url:
            raise PaperLiveRejectedError(f"Paper-only URL required. Got: {_redacted(self.base_url)}")
        # Guard 4: Paper key prefix
        if not self.api_key.startswith("PK"):
            raise PaperLiveRejectedError("Paper key prefix (PK) required. Live keys (AK) rejected.")
        # Capability
        self._capability = PaperExecutionCapability()

    def get_capability(self) -> PaperExecutionCapability:
        return self._capability

    def submit_paper_order(self, request: PaperOrderRequest) -> PaperOrderReceipt:
        """Submit a paper order to Alpaca Paper. POST only. Never live."""
        payload = self._build_order_payload(request)
        response = self._post("/v2/orders", payload)
        return self._map_response(response, request)

    def get_order_status(self, order_id: str) -> PaperOrderReceipt:
        """Read paper order status. GET only."""
        response = self._get(f"/v2/orders/{order_id}")
        return PaperOrderReceipt(
            provider_order_id=response.get("id", ""),
            client_order_id=response.get("client_order_id", ""),
            symbol=response.get("symbol", ""),
            side=response.get("side", ""),
            order_type=response.get("type", ""),
            quantity=float(response.get("qty", 0) or 0),
            notional=float(response.get("notional", 0) or 0) if response.get("notional") else None,
            limit_price=float(response["limit_price"]) if response.get("limit_price") else None,
            submitted_at=response.get("submitted_at", response.get("created_at", "")),
            status=response.get("status", ""),
        )

    def cancel_paper_order(self, request: PaperCancelRequest) -> PaperCancelReceipt:
        """Cancel an existing paper order. DELETE only. Never live. Paper lifecycle control only."""
        try:
            self._delete(f"/v2/orders/{request.provider_order_id}")
        except PaperUnavailableError:
            # 204 No Content from Alpaca on successful cancel — body is empty
            pass
        return PaperCancelReceipt(
            provider_order_id=request.provider_order_id,
            cancel_receipt_id=request.cancel_receipt_id,
            status="canceled",
            canceled_at="",
            reason=request.reason,
        )

    # ── HTTP ───────────────────────────────────────────────────

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

    def _post(self, path: str, payload: dict) -> Any:
        return self._request("POST", self.base_url.rstrip("/") + path, payload)

    def _get(self, path: str) -> Any:
        return self._request("GET", self.base_url.rstrip("/") + path)

    def _delete(self, path: str) -> Any:
        return self._request("DELETE", self.base_url.rstrip("/") + path)

    def _request(self, method: str, url: str, payload: dict | None = None) -> Any:
        if method == "GET":
            resp = self._client().get(url)
        elif method == "POST":
            resp = self._client().post(url, json=payload)
        elif method == "DELETE":
            resp = self._client().delete(url)
        else:
            raise PaperLiveRejectedError(
                f"Only GET, POST (paper orders), and DELETE (paper cancel) allowed. Got {method}"
            )
        try:
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except json.JSONDecodeError:
            return {}  # 204 No Content etc.
        except httpx.HTTPStatusError as e:
            raise PaperUnavailableError(f"Alpaca Paper returned {e.response.status_code} for {_redacted(url)}") from e
        except httpx.RequestError as e:
            raise PaperUnavailableError(f"Alpaca Paper unreachable: {e}") from e

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _build_order_payload(req: PaperOrderRequest) -> dict:
        payload: dict = {
            "symbol": req.symbol.upper(),
            "side": req.side,
            "type": req.order_type,
            "time_in_force": req.time_in_force,
            "client_order_id": req.client_order_id or req.plan_receipt_id,
        }
        if req.quantity > 0:
            payload["qty"] = str(req.quantity)
        if req.notional and req.notional > 0:
            payload["notional"] = str(req.notional)
        if req.limit_price is not None:
            payload["limit_price"] = str(req.limit_price)
        return payload

    @staticmethod
    def _map_response(data: dict, req: PaperOrderRequest) -> PaperOrderReceipt:
        return PaperOrderReceipt(
            provider_order_id=data.get("id", ""),
            client_order_id=data.get("client_order_id", req.client_order_id),
            symbol=data.get("symbol", req.symbol),
            side=data.get("side", req.side),
            order_type=data.get("type", req.order_type),
            quantity=float(data.get("qty", 0) or 0),
            notional=float(data.get("notional", 0) or 0) if data.get("notional") else None,
            limit_price=float(data["limit_price"]) if data.get("limit_price") else None,
            submitted_at=data.get("submitted_at", data.get("created_at", "")),
            status=data.get("status", ""),
            plan_receipt_id=req.plan_receipt_id,
        )

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    def __repr__(self) -> str:
        return (
            f"AlpacaPaperExecutionAdapter("
            f"base_url={_redacted(self.base_url)}, "
            f"key_id={_mask(self.api_key)}, "
            f"paper_only=True, "
            f"can_place_live_order=False"
            f")"
        )

    def __del__(self) -> None:
        self.close()


# ── Internal helpers ────────────────────────────────────────────────


def _penv(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _mask(s: str) -> str:
    if len(s) <= 8:
        return "***"
    return s[:4] + "..." + s[-4:]


def _redacted(s: str) -> str:
    from urllib.parse import urlparse

    parsed = urlparse(s)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
