from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


class OkxReadOnlyClientError(RuntimeError):
    """Failure inside the bounded OKX authenticated GET-only client."""


@dataclass(frozen=True)
class OkxReadOnlyCredentials:
    api_key: str
    secret_key: str
    passphrase: str


class OkxReadOnlyClient:
    """Three-endpoint OKX authenticated reader.

    This class deliberately has no generic public request method and no POST/PUT/DELETE
    surface. Provider truth remains OKX; this implementation owns only HMAC signing,
    HTTPS-over-proxy, and response parsing for the admitted GET-only observation contract.
    """

    _ACCOUNT_CONFIG = "/api/v5/account/config"
    _ACCOUNT_BALANCE = "/api/v5/account/balance"
    _SPOT_OPEN_ORDERS = "/api/v5/trade/orders-pending"

    def __init__(
        self,
        *,
        base_url: str,
        proxy_url: str,
        credentials: OkxReadOnlyCredentials,
        timeout_seconds: float = 15.0,
        transport_attempts: int = 3,
        retry_backoff_seconds: float = 0.25,
    ) -> None:
        if not base_url.startswith("https://"):
            raise OkxReadOnlyClientError("base_url must be HTTPS")
        if not proxy_url.startswith(("http://", "https://")):
            raise OkxReadOnlyClientError("proxy_url must be an HTTP(S) proxy")
        for name, value in (
            ("api_key", credentials.api_key),
            ("secret_key", credentials.secret_key),
            ("passphrase", credentials.passphrase),
        ):
            if not isinstance(value, str) or not value.strip():
                raise OkxReadOnlyClientError(f"{name} must be non-empty")
        if timeout_seconds <= 0:
            raise OkxReadOnlyClientError("timeout_seconds must be positive")
        if (
            not isinstance(transport_attempts, int)
            or isinstance(transport_attempts, bool)
            or transport_attempts < 1
            or transport_attempts > 5
        ):
            raise OkxReadOnlyClientError("transport_attempts must be an integer from 1 to 5")
        if retry_backoff_seconds < 0 or retry_backoff_seconds > 5:
            raise OkxReadOnlyClientError(
                "retry_backoff_seconds must be between 0 and 5"
            )

        self._base_url = base_url.rstrip("/")
        self._credentials = credentials
        self._timeout_seconds = float(timeout_seconds)
        self._transport_attempts = transport_attempts
        self._retry_backoff_seconds = float(retry_backoff_seconds)
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({"https": proxy_url})
        )

    @staticmethod
    def sign(
        *,
        timestamp: str,
        method: str,
        request_path: str,
        body: str,
        secret_key: str,
    ) -> str:
        payload = f"{timestamp}{method.upper()}{request_path}{body}".encode()
        digest = hmac.new(secret_key.encode(), payload, hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    def get_account_config(self) -> list[dict[str, Any]]:
        return self._private_get(self._ACCOUNT_CONFIG)

    def get_account_balance(self) -> list[dict[str, Any]]:
        return self._private_get(self._ACCOUNT_BALANCE)

    def get_spot_open_orders(self) -> list[dict[str, Any]]:
        return self._private_get(self._SPOT_OPEN_ORDERS, {"instType": "SPOT"})

    def _private_get(
        self,
        path: str,
        query: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        if path not in {
            self._ACCOUNT_CONFIG,
            self._ACCOUNT_BALANCE,
            self._SPOT_OPEN_ORDERS,
        }:
            raise OkxReadOnlyClientError("endpoint is outside the admitted GET-only set")

        query_text = urllib.parse.urlencode(query or {})
        request_path = path + (f"?{query_text}" if query_text else "")

        payload: Any | None = None
        last_transport_error: Exception | None = None
        for attempt in range(1, self._transport_attempts + 1):
            timestamp = (
                datetime.now(UTC)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )
            headers = {
                "Accept": "application/json",
                "User-Agent": "ordivon-capital-okx-readonly/1",
                "OK-ACCESS-KEY": self._credentials.api_key,
                "OK-ACCESS-SIGN": self.sign(
                    timestamp=timestamp,
                    method="GET",
                    request_path=request_path,
                    body="",
                    secret_key=self._credentials.secret_key,
                ),
                "OK-ACCESS-PASSPHRASE": self._credentials.passphrase,
                "OK-ACCESS-TIMESTAMP": timestamp,
            }
            request = urllib.request.Request(
                self._base_url + request_path,
                headers=headers,
                method="GET",
            )
            try:
                with self._opener.open(
                    request, timeout=self._timeout_seconds
                ) as response:
                    payload = json.loads(response.read())
                break
            except urllib.error.HTTPError as exc:
                raise OkxReadOnlyClientError(
                    f"OKX HTTP rejection for admitted GET {path}: {exc.code}"
                ) from exc
            except (
                urllib.error.URLError,
                TimeoutError,
                ConnectionResetError,
                ConnectionAbortedError,
                BrokenPipeError,
            ) as exc:
                last_transport_error = exc
                if attempt >= self._transport_attempts:
                    break
                time.sleep(self._retry_backoff_seconds * attempt)
            except json.JSONDecodeError as exc:
                raise OkxReadOnlyClientError(
                    f"OKX admitted GET returned invalid JSON for {path}"
                ) from exc

        if payload is None:
            error_name = (
                type(last_transport_error).__name__
                if last_transport_error is not None
                else "UnknownTransportError"
            )
            raise OkxReadOnlyClientError(
                f"OKX GET transport failed after "
                f"{self._transport_attempts} attempts for admitted endpoint "
                f"{path}: {error_name}"
            ) from last_transport_error

        if not isinstance(payload, dict):
            raise OkxReadOnlyClientError("OKX response must be an object")
        code = str(payload.get("code"))
        if code != "0":
            message = str(payload.get("msg") or "").strip()
            raise OkxReadOnlyClientError(
                f"OKX rejected admitted GET code={code} msg={message!r}"
            )
        rows = payload.get("data")
        if not isinstance(rows, list):
            raise OkxReadOnlyClientError("OKX response data must be a list")
        if any(not isinstance(row, dict) for row in rows):
            raise OkxReadOnlyClientError("OKX response data rows must be objects")
        return rows
