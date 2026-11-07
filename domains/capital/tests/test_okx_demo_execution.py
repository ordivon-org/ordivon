"""Provider-wire falsification: official Demo headers, identity and unknown-effect recovery."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import urllib.error
from unittest.mock import patch

import pytest

from ordivon_capital.trading.okx_demo_execution import (
    OkxDemoEffectUnknown,
    OkxDemoError,
    OkxSpotDemoClient,
)
from ordivon_capital.trading.okx_readonly_client import OkxReadOnlyCredentials


class _Response:
    def __init__(self, payload: dict[str, object]):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def _client():
    return OkxSpotDemoClient(
        OkxReadOnlyCredentials("demo-key", "demo-secret", "demo-pass"),
        proxy_url="http://127.0.0.1:19283",
    )


def test_demo_limit_post_hmac_signatures_and_ack_only():
    c = _client()
    with patch.object(c._opener, "open", return_value=_Response({
        "code": "0", "data": [{"clOrdId": "Ordivon20261107One", "ordId": "123456", "sCode": "0"}],
    })) as opened:
        receipt = c.place_limit(
            instrument_id="BTC-USDT", side="buy", size="0.001",
            limit_price="40000", client_order_id="Ordivon20261107One",
        )
    req = opened.call_args.args[0]
    assert req.get_method() == "POST"
    assert req.get_header("X-simulated-trading") == "1"
    assert req.full_url == "https://www.okx.com/api/v5/trade/order"
    assert json.loads(req.data)["tdMode"] == "cash"
    assert receipt.standing == "ACCEPTED_NOT_FILLED"
    assert receipt.venue_order_id == "123456"
    stamp = req.get_header("Ok-access-timestamp")
    signature = base64.b64encode(
        hmac.new(b"demo-secret", f"{stamp}POST/api/v5/trade/order{req.data.decode()}".encode(),
                 hashlib.sha256).digest()
    ).decode()
    assert req.get_header("Ok-access-sign") == signature


def test_transport_uncertain_post_not_retried():
    c = _client()
    with patch.object(c._opener, "open", side_effect=urllib.error.URLError("lost ACK")) as opened:
        with pytest.raises(OkxDemoEffectUnknown, match="UNKNOWN"):
            c.place_limit(instrument_id="BTC-USDT", side="buy", size="0.001",
                          limit_price="40000", client_order_id="Ordivon20261107One")
    assert opened.call_count == 1


def test_read_only_recovery_after_lost_ack_and_negative_lookup():
    c = _client()
    with patch.object(c._opener, "open", return_value=_Response({
        "code": "0", "data": [{"clOrdId": "Ordivon20261107One", "instId": "BTC-USDT",
                               "ordId": "123456", "state": "live"}],
    })) as opened:
        result = c.recover_unknown_place(
            instrument_id="BTC-USDT", client_order_id="Ordivon20261107One",
        )
    assert result["standing"] == "CLIENT_ID_MATCH_REQUIRES_INTENT_CORRELATION"
    assert opened.call_args.args[0].get_method() == "GET"
    assert "clOrdId=Ordivon20261107One" in opened.call_args.args[0].full_url
    for payload in ({"code": "0", "data": []}, {"code": "51603", "data": [], "msg": "Order does not exist"}):
        with patch.object(c._opener, "open", return_value=_Response(payload)):
            assert c.recover_unknown_place(
                instrument_id="BTC-USDT", client_order_id="Ordivon20261107One",
            )["standing"] == "UNKNOWN"


def test_provider_identity_mismatch_and_fills_coverage():
    c = _client()
    with patch.object(c._opener, "open", return_value=_Response({
        "code": "0", "data": [{"clOrdId": "Ordivon20261107One", "instId": "ETH-USDT"}],
    })):
        with pytest.raises(OkxDemoError, match="identity"):
            c.order_by_client_id(instrument_id="BTC-USDT", client_order_id="Ordivon20261107One")
    with patch.object(c._opener, "open", return_value=_Response({
        "code": "0", "data": [{"ordId": "123456", "instId": "BTC-USDT", "tradeId": "1"},
                            {"ordId": "123456", "instId": "BTC-USDT", "tradeId": "1"}],
    })):
        with pytest.raises(OkxDemoError, match="identities"):
            c.fills(instrument_id="BTC-USDT", venue_order_id="123456")


def test_cancel_ack_requires_later_external_state():
    c = _client()
    with patch.object(c._opener, "open", return_value=_Response({
        "code": "0", "data": [{"ordId": "123456", "clOrdId": "Ordivon20261107One", "sCode": "0"}],
    })) as opened:
        receipt = c.cancel(instrument_id="BTC-USDT", venue_order_id="123456")
    assert receipt.standing == "CANCEL_REQUEST_ACCEPTED_NOT_CONFIRMED"
    assert opened.call_args.args[0].get_method() == "POST"


def test_provider_rejection_does_not_fabricate_acceptance():
    c = _client()
    with patch.object(c._opener, "open", return_value=_Response({
        "code": "0", "data": [{"ordId": "123456", "clOrdId": "Ordivon20261107One", "sCode": "51000"}],
    })):
        with pytest.raises(OkxDemoError, match="rejected"):
            c.place_limit(instrument_id="BTC-USDT", side="buy", size="0.001",
                          limit_price="40000", client_order_id="Ordivon20261107One")


@pytest.mark.parametrize("invalid", ["Infinity", "NaN", "-1", "0", "garbage"])
def test_invalid_amount_never_constructs_request(invalid):
    c = _client()
    with patch.object(c._opener, "open") as opened:
        with pytest.raises(ValueError):
            c.place_limit(instrument_id="BTC-USDT", side="buy", size=invalid,
                          limit_price="40000", client_order_id="Ordivon20261107One")
        opened.assert_not_called()


def test_non_okx_hosts_and_redirects_blocked():
    for url in ("https://fakeokx.com", "http://www.okx.com", "https://www.okx.com/a",
                "https://www.okx.com@evil.org", "https://www.okx.com:8443"):
        with pytest.raises(ValueError):
            OkxSpotDemoClient(
                OkxReadOnlyCredentials("key", "secret", "pass"), base_url=url,
            )
    c = _client()
    assert c._opener.handlers
    with patch.object(c._opener, "open", side_effect=urllib.error.HTTPError(
        "https://www.okx.com/api/v5/trade/order", 302, "redirect", None, None,
    )):
        with pytest.raises(OkxDemoEffectUnknown):
            c.place_limit(instrument_id="BTC-USDT", side="buy", size="0.001",
                          limit_price="40000", client_order_id="Ordivon20261107One")


def test_cli_does_not_admit_demo_write_from_prepared_policy(tmp_path, monkeypatch):
    from ordivon_capital.trading.okx_demo_execution import main
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({
        "standing": "PREPARED_NOT_ADMITTED", "demoWriteAdmission": "NOT_ADMITTED",
        "liveWriteAdmission": "NOT_ADMITTED", "externalFinancialWritesAllowed": False,
        "venues": {"OKX": {"environment": "DEMO", "orderSubmissionAllowed": False}},
    }))
    request = tmp_path / "request.json"
    request.write_text(json.dumps({
        "schemaVersion": 1, "operation": "PLACE_LIMIT",
        "parameters": {"instrument_id": "BTC-USDT", "side": "buy", "size": "0.001",
                       "limit_price": "40000", "client_order_id": "Ordivon20261107One"},
    }))
    with pytest.raises(OkxDemoError, match="not admitted"):
        main(["--request", str(request), "--policy", str(policy)])


def test_cli_usage_exists_without_credentials(capsys):
    from ordivon_capital.trading.okx_demo_execution import main
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "--request" in capsys.readouterr().out
