from __future__ import annotations

import base64
import hashlib
import hmac
from unittest.mock import patch

import pytest

from ordivon_capital.market.okx_readonly_client import (
    OkxReadOnlyClient,
    OkxReadOnlyClientError,
    OkxReadOnlyCredentials,
)


def test_sign_matches_independent_hmac_formula():
    timestamp = "2026-09-21T00:00:00.123Z"
    path = "/api/v5/trade/orders-pending?instType=SPOT"
    secret = "dummy-secret"
    expected = base64.b64encode(
        hmac.new(
            secret.encode(),
            f"{timestamp}GET{path}".encode(),
            hashlib.sha256,
        ).digest()
    ).decode()
    assert (
        OkxReadOnlyClient.sign(
            timestamp=timestamp,
            method="GET",
            request_path=path,
            body="",
            secret_key=secret,
        )
        == expected
    )


def _client():
    return OkxReadOnlyClient(
        base_url="https://openapi.okx.com",
        proxy_url="http://127.0.0.1:19283",
        credentials=OkxReadOnlyCredentials("key", "secret", "pass"),
    )


def test_public_surface_is_read_only_and_bounded():
    public = {name for name in dir(OkxReadOnlyClient) if not name.startswith("_")}
    assert public == {
        "get_account_balance",
        "get_account_config",
        "get_spot_open_orders",
        "sign",
    }
    for forbidden in ("post", "place", "cancel", "amend", "transfer", "withdraw"):
        assert not any(forbidden in name.lower() for name in public)


def test_invalid_endpoint_fails_closed():
    with pytest.raises(OkxReadOnlyClientError, match="outside the admitted"):
        _client()._private_get("/api/v5/trade/order")


def test_only_get_request_is_constructed():
    client = _client()

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"code":"0","msg":"","data":[]}'

    with patch.object(client._opener, "open", return_value=Response()) as opened:
        assert client.get_spot_open_orders() == []
    request = opened.call_args.args[0]
    assert request.get_method() == "GET"
    assert request.full_url.endswith(
        "/api/v5/trade/orders-pending?instType=SPOT"
    )


@pytest.mark.parametrize(
    ("base", "proxy"),
    [
        ("http://openapi.okx.com", "http://127.0.0.1:19283"),
        ("https://openapi.okx.com", "socks5://127.0.0.1:1"),
    ],
)
def test_transport_contract_fails_closed(base, proxy):
    with pytest.raises(OkxReadOnlyClientError):
        OkxReadOnlyClient(
            base_url=base,
            proxy_url=proxy,
            credentials=OkxReadOnlyCredentials("key", "secret", "pass"),
        )


def test_transient_transport_error_is_retried_for_get_only():
    import urllib.error

    client = OkxReadOnlyClient(
        base_url="https://openapi.okx.com",
        proxy_url="http://127.0.0.1:19283",
        credentials=OkxReadOnlyCredentials("key", "secret", "pass"),
        transport_attempts=3,
        retry_backoff_seconds=0,
    )

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"code":"0","msg":"","data":[]}'

    with patch.object(
        client._opener,
        "open",
        side_effect=[
            urllib.error.URLError(ConnectionResetError(104, "reset")),
            Response(),
        ],
    ) as opened:
        assert client.get_account_config() == []
    assert opened.call_count == 2
    assert all(call.args[0].get_method() == "GET" for call in opened.call_args_list)


def test_transport_retry_is_bounded_and_fails_closed():
    import urllib.error

    client = OkxReadOnlyClient(
        base_url="https://openapi.okx.com",
        proxy_url="http://127.0.0.1:19283",
        credentials=OkxReadOnlyCredentials("key", "secret", "pass"),
        transport_attempts=2,
        retry_backoff_seconds=0,
    )
    with patch.object(
        client._opener,
        "open",
        side_effect=urllib.error.URLError(TimeoutError("dns timeout")),
    ) as opened:
        with pytest.raises(OkxReadOnlyClientError, match="after 2 attempts"):
            client.get_account_balance()
    assert opened.call_count == 2


def test_http_error_is_not_retried():
    import urllib.error

    client = OkxReadOnlyClient(
        base_url="https://openapi.okx.com",
        proxy_url="http://127.0.0.1:19283",
        credentials=OkxReadOnlyCredentials("key", "secret", "pass"),
        transport_attempts=3,
        retry_backoff_seconds=0,
    )
    error = urllib.error.HTTPError(
        "https://openapi.okx.com/api/v5/account/config",
        403,
        "forbidden",
        hdrs=None,
        fp=None,
    )
    with patch.object(client._opener, "open", side_effect=error) as opened:
        with pytest.raises(OkxReadOnlyClientError, match="HTTP rejection"):
            client.get_account_config()
    assert opened.call_count == 1


@pytest.mark.parametrize(
    ("attempts", "backoff"),
    [(0, 0), (6, 0), (1, -0.1), (1, 5.1)],
)
def test_retry_policy_validation(attempts, backoff):
    with pytest.raises(OkxReadOnlyClientError):
        OkxReadOnlyClient(
            base_url="https://openapi.okx.com",
            proxy_url="http://127.0.0.1:19283",
            credentials=OkxReadOnlyCredentials("key", "secret", "pass"),
            transport_attempts=attempts,
            retry_backoff_seconds=backoff,
        )
