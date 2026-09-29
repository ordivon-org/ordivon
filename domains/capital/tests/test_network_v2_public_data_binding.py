from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_data_binding_pins_live_transport_and_protected_endpoints():
    cfg = json.loads((ROOT / "config/network_v2_public_data.json").read_text())
    transport = cfg["transportConfig"]
    assert transport["file"] == "/etc/network-v2/finance/egress.json"
    assert transport["digest"].startswith("sha256:")
    assert transport["requiredDnsResponseRace"] is True
    assert [server["tag"] for server in transport["requiredDnsServers"]] == [
        "provider-dns-1",
        "provider-dns-2",
    ]

    endpoints = cfg["providerEndpoints"]
    assert endpoints["file"] == "/etc/network-v2/finance/provider-endpoints.json"
    assert endpoints["digest"].startswith("sha256:")
    assert endpoints["sensitive"] is True
    assert endpoints["contentDisclosureAllowed"] is False

    treasury = cfg["authorities"]["usTreasuryRest"]
    assert treasury["file"] == "/etc/network-v2/finance/us-treasury-rest-authority.json"
    assert treasury["host"] == "home.treasury.gov"
    assert treasury["proxy"] == "http://127.0.0.1:19291"

    fred = cfg["authorities"]["fredPublicCsv"]
    assert fred["file"] == "/etc/network-v2/finance/fred-public-csv-authority.json"
    assert fred["host"] == "fred.stlouisfed.org"
    assert fred["proxy"] == "http://127.0.0.1:19292"


def test_binding_checker_fails_closed_on_transport_or_endpoint_drift():
    script = (ROOT / "scripts/check-network-v2-public-data").read_text()
    assert "transport config digest drift" in script
    assert "transport DNS response-race drift" in script
    assert "provider endpoints digest drift" in script
    assert "endpoint_tags" not in script
    assert "endpoints_path.read_text" not in script
    assert "contentDisclosed" in script
    assert "transportConfig" in script
    assert "providerEndpoints" in script
