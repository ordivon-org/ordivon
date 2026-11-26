"""Real Finance payload parsing and installed route admission negative controls."""
import importlib.util
import json
from pathlib import Path

import pytest

FILE = Path(__file__).resolve().parents[1] / "acceptance/egress/finance-public-data.py"


def module():
    spec = importlib.util.spec_from_file_location("finance_public_data", FILE)
    assert spec and spec.loader
    o = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(o)
    return o


def test_okx_public_business_payload():
    m = module()
    o = m.parse_business_payload("okx-spot", json.dumps({
        "code": "0", "data": [{"instId": "BTC-USDT", "last": "76030.60",
                                "ts": "1794150767271"}]
    }))
    assert o["priceUsd"] == "76030.60"
    assert o["sourceEpochMs"] == 1794150767271


def test_binance_spot_and_usdm_payloads():
    m = module()
    spot = m.parse_business_payload("binance-spot", '{"symbol":"BTCUSDT","price":"76028.01"}')
    perps = m.parse_business_payload("binance-usdm", '{"symbol":"BTCUSDT","price":"75993.2","time":1794150766354}')
    assert spot["priceUsd"] == "76028.01"
    assert perps["priceUsd"] == "75993.2"


def test_fred_latest_valid_day_not_last_blank():
    m = module()
    csv = "DATE,DGS10\n2026-11-04,4.81\n2026-11-05,4.84\n2026-11-06,.\n"
    result = m.parse_business_payload("fred-dgs10", csv)
    assert result["sourceDate"] == "2026-11-05"
    assert result["yieldPct"] == "4.84"
    assert result["validRows"] == 2


@pytest.mark.parametrize(("name", "body"), [
    ("okx-spot", '{"code":"51000","data":[]}'),
    ("okx-spot", '{"code":"0","data":[{"instId":"ETH-USDT","last":"1","ts":"10"}]}'),
    ("okx-spot", '{"code":"0","data":[{"instId":"BTC-USDT","last":"NaN","ts":"10"}]}'),
    ("binance-spot", '{"symbol":"ETHUSDT","price":"76000"}'),
    ("binance-usdm", '{"symbol":"BTCUSDT","price":"0","time":1}'),
    ("binance-spot", '{"symbol":"BTCUSDT","price":"Infinity"}'),
    ("fred-dgs10", "DATE,DGS2\n2026-11-05,4.84"),
    ("fred-dgs10", "DATE,DGS10\n2026-11-05,."),
    ("fred-dgs10", "DATE,DGS10\n2026-11-05,-1"),
    ("unknown", "{}"),
])
def test_business_payload_failures_are_not_pass(name, body):
    with pytest.raises((ValueError, IndexError, KeyError)):
        module().parse_business_payload(name, body)


def test_source_installed_policy_exact_match_required():
    m = module()
    raw = m.SOURCE.read_bytes()
    ports = m.validate_contract(raw, raw)
    assert ports["finance-okx"] == 19283
    assert ports["finance-fred-public-csv"] == 19292


def test_policy_drift_rejected_before_requests():
    m = module()
    raw = m.SOURCE.read_bytes()
    with pytest.raises(ValueError, match="FINANCE_SOURCECUT_DRIFT"):
        m.validate_contract(raw, raw + b" ")


def test_authorized_public_direct_does_not_become_vpn_lane():
    m = module()
    raw = json.loads(m.SOURCE.read_text())
    for entry in raw["route"]["rules"]:
        if entry.get("inbound") == ["finance-fred-public-csv"]:
            entry["outbound"] = "provider-carrier"
    with pytest.raises(ValueError, match="SAMPLE_ROUTE_NOT_INSTALLED"):
        data = json.dumps(raw).encode()
        m.validate_contract(data, data)


def test_unapproved_finance_direct_lane_is_not_silently_installed():
    m = module()
    raw = json.loads(m.SOURCE.read_text())
    raw["route"]["rules"].append({
        "inbound": ["finance-okx"], "action": "route",
        "outbound": "public-direct",
    })
    with pytest.raises(ValueError, match="SAMPLE_ROUTE_NOT_INSTALLED"):
        data = json.dumps(raw).encode()
        m.validate_contract(data, data)


def test_curl_explicit_proxy_overrides_host_environment():
    m = module()
    seen = []
    class Result:
        stdout = '{"symbol":"BTCUSDT","price":"1"}\n__HTTP__:200'
        returncode = 0
    def spy(args, **kwargs):
        seen.append(args)
        return Result()
    exitcode, payload, http = m.fetch_public_data(
        "data-api.binance.vision", "/api/v3/ticker/price?symbol=BTCUSDT", 19284, runner=spy)
    assert (exitcode, http) == (0, 200)
    assert m.parse_business_payload("binance-spot", payload)["priceUsd"] == "1"
    assert seen[0][:2] == ["curl", "-q"]
    assert seen[0][seen[0].index("--noproxy") + 1] == ""
    assert seen[0][seen[0].index("--proxy") + 1] == "http://127.0.0.1:19284"
