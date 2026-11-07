"""Bounded OKX SPOT cash Demo REST effect adapter.

Provider-reported order state is authoritative. A POST ACK is not a fill, a
cancel ACK is not a cancel, and lost POST replies are UNKNOWN, never retried.
Trading owns provider semantics; Runtime owns Jobs, Accounting owns the ledger.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ordivon_capital.trading.okx_readonly_client import (
    OkxReadOnlyClient,
    OkxReadOnlyCredentials,
)


class OkxDemoError(RuntimeError):
    """Provider rejection or unusable external observation."""


class OkxDemoEffectUnknown(OkxDemoError):
    """Effectful request may have reached provider. Never auto-resubmit."""


@dataclass(frozen=True)
class OkxDemoReceipt:
    operation: str
    standing: str
    instrument_id: str
    venue_order_id: str
    client_order_id: str
    provider: str = "OKX"
    environment: str = "DEMO"


def _positive_decimal(text: str) -> str:
    try:
        number = Decimal(text)
    except (ValueError, InvalidOperation, TypeError) as exc:
        raise ValueError("quantity/price must be a finite positive decimal") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("quantity/price must be a finite positive decimal")
    return format(number, "f")


def _identity(text: str, *, instrument: bool = False) -> str:
    pattern = r"[A-Z0-9]+-[A-Z0-9]+" if instrument else r"[A-Za-z0-9]{1,32}"
    if not isinstance(text, str) or not re.fullmatch(pattern, text):
        raise ValueError("invalid instrument/client order identity")
    return text


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, request: urllib.request.Request, fp: Any, code: int,
        msg: str, headers: Any, newurl: str,
    ) -> None:
        return None


class OkxSpotDemoClient:
    """Direct Demo SPOT cash provider adapter; not an OMS or accounting engine."""

    _ENDPOINTS = frozenset({
        ("GET", "/api/v5/account/balance"),
        ("GET", "/api/v5/account/config"),
        ("GET", "/api/v5/trade/order"),
        ("GET", "/api/v5/trade/fills"),
        ("POST", "/api/v5/trade/order"),
        ("POST", "/api/v5/trade/cancel-order"),
    })

    def __init__(
        self,
        credentials: OkxReadOnlyCredentials,
        *,
        base_url: str = "https://www.okx.com",
        proxy_url: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        parts = urllib.parse.urlsplit(base_url)
        if (
            parts.scheme != "https"
            or not parts.hostname
            or not (parts.hostname == "okx.com" or parts.hostname.endswith(".okx.com"))
            or any((parts.username, parts.password, parts.port, parts.query, parts.fragment))
            or parts.path not in ("", "/")
        ):
            raise ValueError("base_url must be HTTPS OKX origin")
        if not 0 < timeout_seconds <= 60:
            raise ValueError("invalid timeout")
        if not all((credentials.api_key, credentials.secret_key, credentials.passphrase)):
            raise ValueError("separate Demo API credentials required")
        if proxy_url is not None and not proxy_url.startswith(("http://", "https://")):
            raise ValueError("proxy must be HTTP(S)")
        self._base_url = base_url.rstrip("/")
        self._credentials = credentials
        self._timeout_seconds = timeout_seconds
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler(
                {"https": proxy_url} if proxy_url is not None else {}
            ),
            _NoRedirect(),
        )

    def _request(
        self, method: str, path: str, *,
        query: dict[str, str] | None = None,
        body: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        if (method, path) not in self._ENDPOINTS:
            raise ValueError("endpoint outside bounded Demo contract")
        suffix = urllib.parse.urlencode(query or {})
        request_path = path + ("?" + suffix if suffix else "")
        body_text = json.dumps(body, separators=(",", ":")) if body is not None else ""
        timestamp = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ordivon-capital-okx-demo/1",
            "x-simulated-trading": "1",
            "OK-ACCESS-KEY": self._credentials.api_key,
            "OK-ACCESS-PASSPHRASE": self._credentials.passphrase,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-SIGN": OkxReadOnlyClient.sign(
                timestamp=timestamp, method=method,
                request_path=request_path, body=body_text,
                secret_key=self._credentials.secret_key,
            ),
        }
        request = urllib.request.Request(
            self._base_url + request_path,
            data=body_text.encode() if method == "POST" else None,
            headers=headers, method=method,
        )
        try:
            with self._opener.open(request, timeout=self._timeout_seconds) as response:
                document = json.loads(response.read())
        except (
            urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            ConnectionError, OSError, json.JSONDecodeError,
        ) as exc:
            if method == "POST":
                raise OkxDemoEffectUnknown(
                    "effect UNKNOWN after POST; reconcile by persisted client order ID"
                ) from exc
            raise OkxDemoError("provider GET observation unavailable") from exc
        if not isinstance(document, dict) or not isinstance(document.get("data"), list):
            if method == "POST":
                raise OkxDemoEffectUnknown("POST ACK malformed; effect UNKNOWN")
            raise OkxDemoError("unusable provider observation")
        if str(document.get("code")) != "0":
            if method == "GET" and path == "/api/v5/trade/order" and str(document.get("code")) == "51603":
                return []  # provider did not find it; NOT proof that no order effect exists
            raise OkxDemoError("provider rejected request; code=" + str(document.get("code")))
        rows = document["data"]
        if any(not isinstance(row, dict) for row in rows):
            if method == "POST":
                raise OkxDemoEffectUnknown("malformed POST ACK; effect UNKNOWN")
            raise OkxDemoError("malformed provider rows")
        return rows

    def account_config(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v5/account/config")

    def balance(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v5/account/balance")

    @staticmethod
    def _single_order(
        rows: list[dict[str, Any]], instrument_id: str, field: str, expected: str,
    ) -> dict[str, Any] | None:
        if len(rows) > 1:
            raise OkxDemoError("ambiguous provider order lookup")
        if not rows:
            return None
        row = rows[0]
        if str(row.get(field)) != expected or row.get("instId") != instrument_id:
            raise OkxDemoError("provider order identity mismatch")
        return row

    def order(self, *, instrument_id: str, venue_order_id: str) -> dict[str, Any] | None:
        _identity(instrument_id, instrument=True)
        if not isinstance(venue_order_id, str) or not venue_order_id.isdecimal():
            raise ValueError("venue order ID must be numeric")
        rows = self._request("GET", "/api/v5/trade/order", query={
            "instId": instrument_id, "ordId": venue_order_id,
        })
        return self._single_order(rows, instrument_id, "ordId", venue_order_id)

    def order_by_client_id(
        self, *, instrument_id: str, client_order_id: str,
    ) -> dict[str, Any] | None:
        """Query after lost POST ACK; clOrdId is NOT globally unique across history."""
        _identity(instrument_id, instrument=True)
        _identity(client_order_id)
        rows = self._request("GET", "/api/v5/trade/order", query={
            "instId": instrument_id, "clOrdId": client_order_id,
        })
        return self._single_order(rows, instrument_id, "clOrdId", client_order_id)

    def recover_unknown_place(
        self, *, instrument_id: str, client_order_id: str,
    ) -> dict[str, Any]:
        """Never reissue POST. Missing/old observations preserve UNKNOWN."""
        order = self.order_by_client_id(
            instrument_id=instrument_id, client_order_id=client_order_id,
        )
        return {"standing": "CLIENT_ID_MATCH_REQUIRES_INTENT_CORRELATION" if order else "UNKNOWN",
                "order": order}

    def fills(self, *, instrument_id: str, venue_order_id: str) -> list[dict[str, Any]]:
        _identity(instrument_id, instrument=True)
        if not isinstance(venue_order_id, str) or not venue_order_id.isdecimal():
            raise ValueError("venue order ID must be numeric")
        rows = self._request("GET", "/api/v5/trade/fills", query={
            "instType": "SPOT", "instId": instrument_id, "ordId": venue_order_id,
        })
        if any(row.get("ordId") != venue_order_id or row.get("instId") != instrument_id for row in rows):
            raise OkxDemoError("provider fill identity mismatch")
        trades = [str(row.get("tradeId")) for row in rows]
        if len(trades) != len(set(trades)) or any(t in ("", "None") for t in trades):
            raise OkxDemoError("provider trade identities incomplete or duplicated")
        return rows  # OKX recent fills are NOT full historical coverage

    def place_limit(
        self, *, instrument_id: str, side: str, size: str,
        limit_price: str, client_order_id: str,
    ) -> OkxDemoReceipt:
        _identity(instrument_id, instrument=True)
        _identity(client_order_id)
        if side not in ("buy", "sell"):
            raise ValueError("unsupported side")
        rows = self._request("POST", "/api/v5/trade/order", body={
            "instId": instrument_id, "tdMode": "cash", "side": side,
            "ordType": "limit", "sz": _positive_decimal(size),
            "px": _positive_decimal(limit_price), "clOrdId": client_order_id,
        })
        if len(rows) != 1 or rows[0].get("clOrdId") != client_order_id:
            raise OkxDemoEffectUnknown("POST order identity UNKNOWN")
        row = rows[0]
        if str(row.get("sCode")) != "0":
            raise OkxDemoError("provider explicitly rejected order; code=" + str(row.get("sCode")))
        order_id = str(row.get("ordId") or "")
        if not order_id.isdecimal():
            raise OkxDemoEffectUnknown("POST accepted without usable venue identity")
        return OkxDemoReceipt("PLACE_LIMIT", "ACCEPTED_NOT_FILLED",
                              instrument_id, order_id, client_order_id)

    def cancel(self, *, instrument_id: str, venue_order_id: str) -> OkxDemoReceipt:
        _identity(instrument_id, instrument=True)
        if not isinstance(venue_order_id, str) or not venue_order_id.isdecimal():
            raise ValueError("venue order ID must be numeric")
        rows = self._request("POST", "/api/v5/trade/cancel-order", body={
            "instId": instrument_id, "ordId": venue_order_id,
        })
        if len(rows) != 1 or str(rows[0].get("ordId")) != venue_order_id:
            raise OkxDemoEffectUnknown("cancel identity UNKNOWN")
        if str(rows[0].get("sCode")) != "0":
            raise OkxDemoError("provider explicitly rejected cancellation")
        return OkxDemoReceipt("CANCEL", "CANCEL_REQUEST_ACCEPTED_NOT_CONFIRMED",
                              instrument_id, venue_order_id,
                              str(rows[0].get("clOrdId") or ""))


def credentials_from_systemd(directory: str | None = None) -> OkxReadOnlyCredentials:
    """Use Runtime's LoadCredentialEncrypted; never put secrets in argv/env/log."""
    root = directory or os.environ.get("CREDENTIALS_DIRECTORY", "")
    if not root:
        raise ValueError("systemd CREDENTIALS_DIRECTORY is required")
    folder = Path(root)
    return OkxReadOnlyCredentials(*(
        (folder / name).read_text(encoding="utf-8").strip()
        for name in ("okx_demo_api_key", "okx_demo_secret_key", "okx_demo_passphrase")
    ))


def _demo_write_admitted(policy_path: Path) -> bool:
    """Check the canonical Governance declaration, never infer an effect grant."""
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    okx = policy.get("venues", {}).get("OKX", {})
    return (
        policy.get("standing") == "ADMITTED"
        and policy.get("demoWriteAdmission") == "ADMITTED"
        and policy.get("liveWriteAdmission") == "NOT_ADMITTED"
        and policy.get("externalFinancialWritesAllowed") is True
        and okx.get("environment") == "DEMO"
        and okx.get("networkSessionAllowed") is True
        and okx.get("orderSubmissionAllowed") is True
        and bool(okx.get("credentialBinding"))
    )


def main(argv: list[str] | None = None) -> int:
    """Runtime credential-bound CLI: request file -> provider evidence JSON."""
    import argparse
    from dataclasses import asdict, is_dataclass

    parser = argparse.ArgumentParser(description="OKX Demo SPOT external provider operator")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--policy", type=Path, default=Path(__file__).resolve().parents[3] /
                        "config/demo_execution_policy.json")
    parser.add_argument("--base-url", default="https://www.okx.com")
    parser.add_argument("--proxy-url")
    args = parser.parse_args(argv)
    request = json.loads(args.request.read_text(encoding="utf-8"))
    if not isinstance(request, dict) or request.get("schemaVersion") != 1:
        raise ValueError("request must be versioned exact object")
    operation = request.get("operation")
    parameters = request.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be object")
    routes = {
        "ACCOUNT_CONFIG": "account_config",
        "BALANCE": "balance",
        "ORDER": "order",
        "RECOVER_UNKNOWN_PLACE": "recover_unknown_place",
        "FILLS": "fills",
        "PLACE_LIMIT": "place_limit",
        "CANCEL": "cancel",
    }
    if operation not in routes:
        raise ValueError("unsupported Demo operator")
    if operation in ("PLACE_LIMIT", "CANCEL") and not _demo_write_admitted(args.policy):
        raise OkxDemoError("Demo external write is not admitted by current Governance owner")
    client = OkxSpotDemoClient(
        credentials_from_systemd(), base_url=args.base_url, proxy_url=args.proxy_url,
    )
    result = getattr(client, routes[operation])(**parameters)
    print(json.dumps(asdict(result) if is_dataclass(result) else result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
