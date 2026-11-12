"""Temporary open-connectivity semantics: positive acceptance for declared transition."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = {
    "chat-ingress": "sing-box.json",
    "claude": "sing-box.json",
    "codex": "sing-box.json",
    "discord": "egress.json",
    "finance": "egress.json",
    "model-provider": "egress.json",
    "supply-chain": "egress.json",
    "windows-real-chrome": "sing-box.json",
    "x-reality": "egress.json",
}

@pytest.mark.parametrize(("consumer", "filename"), ENTRIES.items())
def test_public_origins_are_no_longer_subject_to_scoped_domain_allowlists(consumer, filename):
    path = ROOT / "consumers" / consumer / "config" / filename
    value = json.loads(path.read_text())
    assert value["route"]["final"] == "provider-carrier"
    assert any(o.get("tag") == "provider-carrier" and o.get("type") == "http"
               for o in value["outbounds"])
    rules = value["route"]["rules"]
    if consumer == "finance":
        assert len(rules) == 2
        assert {tuple(rule.get("inbound", [])) for rule in rules} == {
            ("finance-us-treasury-public",), ("finance-fred-public-csv",)
        }
        assert all(rule.get("outbound") == "public-direct" for rule in rules)
    else:
        assert rules == []


def test_unrestricted_country_selector_uses_existing_upstream_scheduling():
    spec = importlib.util.spec_from_file_location(
        "profile", ROOT / "providers" / "gluetun" / "native_profile.py"
    )
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.read_selector_policy() == {
        "regions": [], "selectedCountries": [], "excludedCountries": [],
    }
    profile = m.generate_env(
        {"VPN_SERVICE_PROVIDER": "custom", "VPN_TYPE": "wireguard"},
        "10.64.100.1/16",
    )
    assert "SERVER_COUNTRIES=" not in profile
    assert "SERVER_REGIONS=" not in profile
    assert "BLOCK_MALICIOUS=off" in profile
    assert "HEALTH_RESTART_VPN=on" in profile
    assert "VPN_TYPE=wireguard" in profile


def test_developer_login_default_is_direct_and_explicit_optin_is_preserved():
    source = (ROOT / "consumers" / "developer-egress" / "profile.sh").read_text()
    assert 'ORDIVON_DEV_VPN:-off' in source
    assert 'ORDIVON_DEV_VPN=on' in source
    assert '"--systemd-env"' in source
