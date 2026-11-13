"""Active-session VPN qualification is not a standby health assertion."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "providers/gluetun/observe_active.py"
import sys
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("gluetun_active_observer", SCRIPT)
assert spec and spec.loader
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


def test_kernel_endpoint_is_unique_and_uses_ip_parser():
    assert observer.endpoint_ip("tun0 PUB 192.0.2.11:51820\n") == "192.0.2.11"
    assert observer.endpoint_ip("tun0 PUB [2001:db8::1]:51820\n") == "2001:db8::1"
    for invalid in ("", "tun0 PUB (none)", "tun0 PUB nonsense:51820",
                    "tun0 PUB 192.0.2.11:51820\ntun0 PUB 192.0.2.12:51820"):
        with pytest.raises(ValueError):
            observer.endpoint_ip(invalid)


def test_catalog_identity_must_not_be_assumed_from_public_exit():
    raw = '{"surfshark":{"servers":[{"vpn":"wireguard","ips":["192.0.2.11"],"country":"North Macedonia"}]}}'
    assert observer.catalog_country(raw, "192.0.2.11") == "North Macedonia"
    assert observer.catalog_country(raw, "192.0.2.12") is None
    assert observer.standing(
        catalog_location="North Macedonia", actual_exit="HR",
        allowed={"North Macedonia", "Croatia"},
        active_endpoint_stable=True, provider_running=True,
        business_receipts=[True, True],
    ) == "QUALIFIED_ACTIVE_SAMPLE"


def test_forbidden_or_unknown_endpoint_cannot_qualify():
    base = dict(
        catalog_location="Japan", actual_exit="JP",
        allowed={"Japan", "Croatia"},
        active_endpoint_stable=True, provider_running=True,
        business_receipts=[True, True],
    )
    for key, value, expected in [
        ("catalog_location", "Hong Kong", "REJECTED_FORBIDDEN_EXIT"),
        ("actual_exit", "HK", "REJECTED_FORBIDDEN_EXIT"),
        ("catalog_location", None, "UNKNOWN"),
        ("actual_exit", None, "UNKNOWN"),
        ("catalog_location", "Norway", "REJECTED_NOT_ALLOWED"),
        ("active_endpoint_stable", False, "UNKNOWN"),
        ("provider_running", False, "UNKNOWN"),
        ("business_receipts", [True, False], "NOT_QUALIFIED"),
        ("business_receipts", [], "NOT_QUALIFIED"),
    ]:
        assert observer.standing(**(base | {key: value})) == expected


def test_https_receipt_requires_tunnel_tls_and_origin():
    assert observer.parse_curl_receipt("200 200 0.9 1.2") == (True, 1.2)
    for receipt in ("200 0 0.9 1.2", "403 200 0.9 1.2",
                    "200 200 0 1", "200 200 2 1", "junk"):
        assert observer.parse_curl_receipt(receipt)[0] is False
