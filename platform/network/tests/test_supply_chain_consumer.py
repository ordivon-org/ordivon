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
    assert authority["networkAuthority"]["carrierService"] == "network-v2-browserless-provider-carrier.service"
    assert authority["networkAuthority"]["providerSite"] == "th-bkk"
    route = next(r for r in egress["route"]["rules"] if r.get("inbound") == ["supply-chain-oci"])
    assert sorted(route["domain"]) == sorted(authority["allowedHttpsDomains"])
    assert sorted(route["domain_suffix"]) == sorted(authority["allowedHttpsDomainSuffixes"])
    assert route["port"] == 443
    assert route["network"] == ["tcp"]
    assert route["outbound"] == "provider-carrier"
    assert egress["route"]["rules"][-1] == {"action": "reject"}


def test_supply_chain_reuses_one_shared_carrier_without_vpn_identity():
    egress = json.loads((CONSUMER / "config" / "egress.json").read_text())
    assert egress["outbounds"] == [{
        "type": "http", "tag": "provider-carrier", "server": "10.252.246.2", "server_port": 19680,
    }]
    assert "dns" not in egress
    assert "services" not in egress
    unit = (CONSUMER / "systemd" / "network-v2-supply-chain-egress.service").read_text()
    assert "Wants=network-v2-browserless-provider-carrier.service" in unit
    assert "Requires=network-v2-browserless-provider-carrier.service" not in unit
    assert "provider-endpoints.json" not in unit
    taskfile = (ROOT / "Taskfile.yml").read_text()
    assert "rm -f /etc/network-v2/supply-chain/provider-endpoints.json" in taskfile


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

def test_supply_chain_readiness_has_bounded_local_convergence_gate():
    ready = (CONSUMER / "ready.sh").read_text()
    assert "wait_local_ready()" in ready
    assert "seq 1 120" in ready
    assert "sleep 0.25" in ready
    assert "did not converge within 30s" in ready
    assert "return 42" in ready
