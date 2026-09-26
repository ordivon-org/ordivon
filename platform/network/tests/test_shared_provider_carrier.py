from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSERLESS = ROOT / "consumers" / "browserless"
FINANCE = ROOT / "consumers" / "finance"
SUPPLY = ROOT / "consumers" / "supply-chain"


def test_browserless_owns_one_internal_provider_carrier():
    cfg = json.loads((BROWSERLESS / "config" / "provider-carrier.json").read_text())
    assert cfg["inbounds"] == [{
        "type": "http", "tag": "shared-provider-carrier", "listen": "10.252.246.2", "listen_port": 19680,
    }]
    assert cfg["dns"]["servers"] == [{
        "type": "udp", "tag": "namespace-dns", "server": "127.0.0.1", "server_port": 53,
    }]
    assert cfg["outbounds"] == [{"type": "direct", "tag": "provider-direct"}]
    assert {"ip_is_private": True, "action": "reject"} in cfg["route"]["rules"]
    assert {"ip_version": 6, "action": "reject"} in cfg["route"]["rules"]
    unit = (BROWSERLESS / "systemd" / "network-v2-browserless-provider-carrier.service").read_text()
    assert "NetworkNamespacePath=/run/netns/nv2-browserless-prod" in unit
    assert "Requires=network-v2-browserless-dns.service network-v2-browserless-forward.service" in unit
    assert "provider-endpoints.json" not in unit
    target = (BROWSERLESS / "systemd" / "network-v2-browserless.target").read_text()
    assert "network-v2-browserless-provider-carrier.service" in target


def test_production_provider_defaults_to_cross_consumer_qualified_site():
    cutover = (BROWSERLESS / "production-cutover.sh").read_text()
    assert "PROVIDER_SITE=${PROVIDER_SITE:-th-bkk}" in cutover
    assert "consumers/browserless/config/provider-carrier.json" in cutover
    assert "network-v2-browserless-provider-carrier.service" in cutover


def test_finance_provider_lanes_share_carrier_and_macro_lanes_remain_direct():
    egress = json.loads((FINANCE / "config" / "egress.json").read_text())
    assert egress["outbounds"] == [
        {"type": "http", "tag": "provider-carrier", "server": "10.252.246.2", "server_port": 19680},
        {"type": "direct", "tag": "public-direct"},
    ]
    assert "dns" not in egress
    assert "services" not in egress
    routes = {tuple(r.get("inbound", [])): r for r in egress["route"]["rules"] if r.get("inbound")}
    for tag in (
        "finance-okx", "finance-binance-spot-public", "finance-binance-spot-public-ws",
        "finance-binance-usdm", "finance-okx-ws", "finance-binance-usdm-ws", "finance-binance-wallet",
    ):
        assert routes[(tag,)]["outbound"] == "provider-carrier"
    assert routes[("finance-us-treasury-public",)]["outbound"] == "public-direct"
    assert routes[("finance-fred-public-csv",)]["outbound"] == "public-direct"
    unit = (FINANCE / "systemd" / "network-v2-finance-egress.service").read_text()
    assert "provider-endpoints.json" not in unit
    assert "Requires=network-v2-browserless-provider-carrier.service" in unit


def test_no_current_consumer_materializes_duplicate_provider_identity():
    taskfile = (ROOT / "Taskfile.yml").read_text()
    assert "rm -f /etc/network-v2/finance/provider-endpoints.json" in taskfile
    assert "rm -f /etc/network-v2/supply-chain/provider-endpoints.json" in taskfile
    assert "provider-endpoints.json -c /etc/network-v2/finance" not in taskfile
    assert "provider-endpoints.json -c /etc/network-v2/supply-chain" not in taskfile
    for directory in (FINANCE / "config", SUPPLY / "config"):
        for path in directory.glob("*.json"):
            assert "provider-auto" not in path.read_text()

def test_provider_switch_uses_wg_quick_compatible_temp_profile_and_restores_target():
    switch = (BROWSERLESS / "provider-switch.sh").read_text()
    assert 'TARGET=network-v2-browserless.target' in switch
    assert 'mktemp --suffix=.conf "$STATE_DIR/nv2blwg.XXXXXX"' in switch
    assert switch.count('systemctl start "$TARGET"') >= 2
    assert 'wg-quick strip "$tmp_profile"' in switch
