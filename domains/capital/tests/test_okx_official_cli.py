"""Actual pinned upstream Node CLI -> signed HTTP Demo protocol qualification.

The external provider is replaced by a local loopback endpoint *only* here.
Real upstream CLI mechanics execute as a physical child process; no mock of
the CLI, HMAC, command parser or Node transport is used.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import shutil
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
from urllib.parse import urlparse

import pytest

from ordivon_capital.trading.okx_demo_execution import OkxDemoError
from ordivon_capital.trading.okx_official_cli import (
    _CLI_PROJECT,
    OkxOfficialSpotDemoClient,
)
from ordivon_capital.trading.okx_readonly_client import OkxReadOnlyCredentials

pytestmark = pytest.mark.provider_qualification


class Handler(BaseHTTPRequestHandler):
    events: list[dict[str, str]] = []

    def log_message(self, *_: object) -> None:
        return

    def do_GET(self) -> None:
        self.reply()

    def do_POST(self) -> None:
        self.reply()

    def reply(self) -> None:
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode()
        self.events.append({
            "method": self.command,
            "path": self.path,
            "body": raw,
            "stamp": self.headers.get("OK-ACCESS-TIMESTAMP", ""),
            "sign": self.headers.get("OK-ACCESS-SIGN", ""),
            "key": self.headers.get("OK-ACCESS-KEY", ""),
            "demo": self.headers.get("x-simulated-trading", ""),
        })
        path = urlparse(self.path).path
        if path == "/api/v5/trade/order" and self.command == "POST":
            rows = [{"ordId": "123456789", "clOrdId": "intentAb12", "sCode": "0"}]
        elif path == "/api/v5/trade/cancel-order":
            rows = [{"ordId": "123456789", "clOrdId": "intentAb12", "sCode": "0"}]
        elif path == "/api/v5/trade/order":
            rows = [{"ordId": "123456789", "clOrdId": "intentAb12", "instId": "BTC-USDT",
                     "state": "live", "sz": "0.001", "px": "70000", "cTime": "1794078610000"}]
        elif path == "/api/v5/account/config":
            rows = [{"acctLv": "1", "perm": "read_only"}]
        elif path == "/api/v5/account/balance":
            rows = [{"details": [{"ccy": "USDT", "availBal": "100"}]}]
        else:
            rows = []
        wire = json.dumps({"code": "0", "data": rows, "msg": ""}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(wire)))
        self.end_headers()
        self.wfile.write(wire)


def _installed() -> bool:
    pkg = _CLI_PROJECT / "node_modules/@okx_ai/okx-trade-cli/package.json"
    return bool(shutil.which("node") and pkg.is_file()
                and json.loads(pkg.read_text()).get("version") == "1.5.0")


@pytest.mark.skipif(not _installed(), reason="install the pinned official Node CLI first")
def test_upstream_real_cli_signed_demo_order_and_readback(monkeypatch: pytest.MonkeyPatch):
    for key in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY",
                "https_proxy", "http_proxy", "all_proxy"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1")
    monkeypatch.setenv("no_proxy", "localhost,127.0.0.1")
    Handler.events = []
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = OkxOfficialSpotDemoClient(
            OkxReadOnlyCredentials("demo-key", "demo-secret", "demo-pass"),
        )
        # Test-only loopback override; the public CLI permits HTTPS OKX origins.
        client._base_url = f"http://127.0.0.1:{server.server_port}"
        config = client.account_config()
        assert config[0]["acctLv"] == "1"
        assert client.balance()[0]["details"][0]["ccy"] == "USDT"
        placed = client.place_limit(
            instrument_id="BTC-USDT", side="buy", size="0.001",
            limit_price="70000", client_order_id="intentAb12",
        )
        assert placed.standing == "ACCEPTED_NOT_FILLED"
        assert placed.venue_order_id == "123456789"
        result = client.recover_unknown_place(
            instrument_id="BTC-USDT", client_order_id="intentAb12",
        )
        assert result["standing"] == "CLIENT_ID_MATCH_REQUIRES_INTENT_CORRELATION"
        assert result["order"]["ordId"] == "123456789"
        assert client.fills(instrument_id="BTC-USDT", venue_order_id="123456789") == []
        cancellation = client.cancel(instrument_id="BTC-USDT", venue_order_id="123456789")
        assert cancellation.standing == "CANCEL_REQUEST_ACCEPTED_NOT_CONFIRMED"
        assert len(Handler.events) == 6

        for event in Handler.events:
            assert event["demo"] == "1"
            assert event["key"] == "demo-key"
            expected = base64.b64encode(hmac.new(
                b"demo-secret",
                (event["stamp"] + event["method"] + event["path"] + event["body"]).encode(),
                hashlib.sha256,
            ).digest()).decode()
            assert event["sign"] == expected
        place_payload = next(json.loads(x["body"]) for x in Handler.events
                             if x["path"] == "/api/v5/trade/order" and x["method"] == "POST")
        assert place_payload["tdMode"] == "cash"
        assert place_payload["ordType"] == "limit"
        assert place_payload["clOrdId"] == "intentAb12"
        assert place_payload["sz"] == "0.001"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_unqualified_route_and_unknown_credential_profile():
    assert OkxOfficialSpotDemoClient._route(
        "GET", "/api/v5/trade/order",
        {"instId": "BTC-USDT", "clOrdId": "testOne"}, None,
    ) == ["spot", "get", "--instId", "BTC-USDT", "--clOrdId", "testOne"]
    with pytest.raises(ValueError, match="outside"):
        OkxOfficialSpotDemoClient._route("POST", "/api/v5/account/transfer", None, {})
    if _installed():
        with patch.dict(os.environ, {"ORDIVON_OKX_SITE": "unsupported"}, clear=False):
            with pytest.raises(OkxDemoError, match="site"):
                OkxOfficialSpotDemoClient(OkxReadOnlyCredentials("a", "b", "c"))
        with patch.dict(os.environ, {"ORDIVON_OKX_SITE": "eea"}, clear=False):
            regional = OkxOfficialSpotDemoClient(OkxReadOnlyCredentials("a", "b", "c"))
            assert regional._base_url == "https://eea.okx.com"
            with pytest.raises(OkxDemoError, match="region"):
                OkxOfficialSpotDemoClient(
                    OkxReadOnlyCredentials("a", "b", "c"),
                    base_url="https://us.okx.com",
                )
