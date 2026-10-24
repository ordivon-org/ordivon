from __future__ import annotations

import json

import pytest
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
    assert "Wants=network-v2-browserless-dns.service network-v2-browserless-forward.service network-v2-browserless-provider-carrier.service" in target
    assert "Requires=network-v2-browserless-dns.service" not in target


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
    assert "Wants=network-v2-browserless-provider-carrier.service" in unit
    assert "Requires=network-v2-browserless-provider-carrier.service" not in unit


def test_semantic_consumers_survive_physical_carrier_loss():
    for directory, name in ((FINANCE, "finance"), (SUPPLY, "supply-chain")):
        unit = (directory / "systemd" / f"network-v2-{name}-egress.service").read_text()
        assert "Wants=network-v2-browserless-provider-carrier.service" in unit
        assert "Requires=network-v2-browserless-provider-carrier.service" not in unit
        assert "After=network-v2-browserless-provider-carrier.service" in unit


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
    assert 'systemctl restart "$WG"' in switch
    assert 'before_inode=$(stat -Lc' in switch
    assert 'test "$before_inode" = "$after_inode"' in switch
    assert 'standing:"RECOVERED_SESSION"' in switch

def test_production_path_uses_application_consequence_not_30s_handshake_age():
    script = (BROWSERLESS / "acceptance" / "production-path.sh").read_text()
    assert 'test "$handshake_age" -le 30' not in script
    assert 'test "${hs:-0}" -gt 0' in script
    assert 'openai_http' in script and 'chatgpt_http' in script
    assert 'Current liveness is proven' in script


def test_retired_network_capability_router_stays_retired():
    """The current provider and consumer policies replace the old custom routing layer."""
    for relative in (
        "scripts/network_capability_router.py",
        "config/network-capability-routes.json",
        "tests/test_network_capability_router.py",
    ):
        assert not (ROOT / relative).exists(), f"retired Network Router returned: {relative}"
    for consumer in ("x-reality", "supply-chain"):
        assert (ROOT / "consumers" / consumer / "config" / "egress.json").is_file()


@pytest.mark.parametrize(
    ("receipt", "okx_receipt", "expected_ready"),
    [
        ("407", "200 200", False),      # Proxy denial is not a healthy tunnel.
        ("401 407", "200 200", False),  # Origin-looking status with denied CONNECT.
        ("502 200", "200 200", False),  # A broken upstream is not application readiness.
        ("401 200", "200 407", False),  # Successful probes cannot override failed OKX.
        ("401 200", "200 000", False),  # OKX direct/bypassed route is not proxy evidence.
        ("401 200", "200 200", True),   # Anonymous challenge through valid CONNECT.
    ],
)
def test_browserless_shared_provider_requires_real_tunnel_and_origin_evidence(
    tmp_path: Path, receipt: str, okx_receipt: str, expected_ready: bool
) -> None:
    """Physical Bash consumer; substitute only provider config and external tools."""
    import os
    import subprocess

    script = (BROWSERLESS / "provider-carrier-ready.sh").read_text()
    provider = tmp_path / "provider.env"
    provider.write_text("PROVIDER_SITE=th-bkk\nENDPOINT=198.51.100.1\n")
    manifest = tmp_path / "MANIFEST.tsv"
    manifest.write_text("th-bkk\t198.51.100.1\n")
    script = script.replace(
        "/etc/network-v2/browserless/provider.env", str(provider)
    ).replace(
        "/etc/network-v2/providers/catalog-profiles/MANIFEST.tsv", str(manifest)
    )
    assert str(provider) in script and str(manifest) in script
    selected = tmp_path / "ready.sh"
    selected.write_text(script)
    tools = tmp_path / "bin"
    tools.mkdir()
    for name, body in {
        "systemctl": "#!/bin/sh\nexit 0\n",
        "ip": "#!/bin/sh\necho 'LISTEN 10.252.246.2:19680'\n",
        "sleep": "#!/bin/sh\nexit 0\n",
        "curl": (
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "args = sys.argv[1:]\n"
            "with open(os.environ['PROVIDER_CURL_LOG'], 'a') as stream:\n"
            "    print(' '.join(args), file=stream)\n"
            "if any('openapi.okx.com' in arg for arg in args):\n"
            "    if '-o' in args:\n"
            "        with open(args[args.index('-o')+1], 'w') as dest:\n"
            "            dest.write('{\"code\":\"0\",\"data\":[{}]}')\n"
            "    if '-w' in args:\n"
            "        print(os.environ['PROVIDER_OKX_RECEIPT'], end='')\n"
            "    sys.exit(0)\n"
            "print(os.environ['PROVIDER_RECEIPT'], end='')\n"
        ),
    }.items():
        path = tools / name
        path.write_text(body)
        path.chmod(0o755)
    curl_log = tmp_path / "curl.log"
    process = subprocess.run(
        ["/usr/bin/bash", str(selected)],
        env={
            **os.environ,
            "PATH": f"{tools}:{os.environ.get('PATH','')}",
            "PROVIDER_RECEIPT": receipt,
            "PROVIDER_OKX_RECEIPT": okx_receipt,
            "PROVIDER_CURL_LOG": str(curl_log),
        },
        capture_output=True,
        text=True,
        timeout=9,
    )
    assert (process.returncode == 0) is expected_ready, (
        receipt, process.stdout, process.stderr
    )
    if expected_ready:
        assert json.loads(process.stdout)["standing"] == "READY"
    else:
        assert '"standing":"READY"' not in process.stdout
    calls = curl_log.read_text()
    assert "api.openai.com" in calls
    assert "--noproxy" in calls and "-q" in calls
    assert "%{http_connect}" in calls
