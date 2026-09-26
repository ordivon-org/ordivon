from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "consumers" / "supply-chain"


def test_supply_chain_authority_matches_enforced_destination_policy():
    authority = json.loads((CONSUMER / "config" / "authority.json").read_text())
    egress = json.loads((CONSUMER / "config" / "egress.json").read_text())
    assert authority["listen"] == {"host": "127.0.0.1", "port": 19581, "protocol": "http"}
    assert authority["directFallback"] is False
    route = next(r for r in egress["route"]["rules"] if r.get("inbound") == ["supply-chain-oci"])
    assert sorted(route["domain"]) == sorted(authority["allowedHttpsDomains"])
    assert sorted(route["domain_suffix"]) == sorted(authority["allowedHttpsDomainSuffixes"])
    assert route["port"] == 443
    assert route["network"] == ["tcp"]
    assert route["outbound"] == "provider-auto"
    assert egress["route"]["rules"][-1] == {"action": "reject"}


def test_supply_chain_reuses_dual_provider_and_dns_race_without_direct_outbound():
    egress = json.loads((CONSUMER / "config" / "egress.json").read_text())
    assert egress["outbounds"] == [{
        "type": "urltest", "tag": "provider-auto", "outbounds": ["provider-b", "provider-a"],
        "url": "https://1.1.1.1/cdn-cgi/trace", "interval": "3s", "tolerance": 65535,
        "idle_timeout": "10m", "interrupt_exist_connections": True,
    }]
    assert [x["server"] for x in egress["dns"]["servers"]] == ["162.252.172.57", "149.154.159.92"]
    assert any(x.get("race") is True for x in egress["dns"]["rules"])
    assert not any(x.get("type") == "direct" for x in egress["outbounds"])


def test_docker_binding_retires_old_public_web_proxy_and_restart_is_guarded():
    dropin = (CONSUMER / "systemd" / "docker.service.d" / "ordivon-network-v2-supply-chain-proxy.conf").read_text()
    smoke = (CONSUMER / "acceptance" / "docker-rebind-smoke.sh").read_text()
    taskfile = (ROOT / "Taskfile.yml").read_text()
    assert "127.0.0.1:19581" in dropin
    assert "10.254.177.2:19381" not in dropin
    assert "always|unless-stopped" in smoke
    assert "systemctl restart docker.service" in smoke
    assert "docker pull" in smoke
    assert "rm -f /etc/systemd/system/docker.service.d/ordivon-preservation-vpn-proxy.conf" in taskfile


def test_supply_chain_has_standard_network_v2_lifecycle_tasks():
    taskfile = (ROOT / "Taskfile.yml").read_text()
    for task in (
        "consumer:supply-chain:validate:",
        "consumer:supply-chain:materialize:",
        "consumer:supply-chain:start:",
        "consumer:supply-chain:ready:",
        "consumer:supply-chain:converge:",
        "consumer:supply-chain:docker-rebind:",
        "consumer:supply-chain:verify:",
        "consumer:supply-chain:stop:",
    ):
        assert task in taskfile
