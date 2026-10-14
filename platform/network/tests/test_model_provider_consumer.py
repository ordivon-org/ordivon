from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "consumers" / "model-provider"
DOMAINS = [
    "api.deepseek.com",
    "generativelanguage.googleapis.com",
    "openrouter.ai",
    "api.cerebras.ai",
    "integrate.api.nvidia.com",
    "open.bigmodel.cn",
]


def test_model_provider_authority_is_transport_only_and_fail_closed() -> None:
    authority = json.loads((CONSUMER / "config" / "authority.json").read_text())
    assert authority["listen"] == {
        "host": "127.0.0.1",
        "port": 19881,
        "protocol": "http",
    }
    assert authority["allowedHttpsDomains"] == DOMAINS
    assert authority["directFallback"] is False
    assert authority["authenticationAuthority"] == {
        "separate": True,
        "transportConsumerOwnsCredential": False,
    }


def test_model_provider_reuses_shared_carrier_and_rejects_unknown() -> None:
    egress = json.loads((CONSUMER / "config" / "egress.json").read_text())
    assert egress["outbounds"] == [
        {
            "type": "http",
            "tag": "provider-carrier",
            "server": "10.252.246.2",
            "server_port": 19680,
        }
    ]
    route = egress["route"]["rules"][0]
    assert route["inbound"] == ["model-provider-api"]
    assert route["domain"] == DOMAINS
    assert route["port"] == 443
    assert route["network"] == ["tcp"]
    assert route["outbound"] == "provider-carrier"
    assert egress["route"]["rules"][-1] == {"action": "reject"}


def test_model_provider_has_no_duplicate_vpn_or_credential_authority() -> None:
    unit = (
        CONSUMER
        / "systemd"
        / "network-v2-model-provider-egress.service"
    ).read_text()
    assert "Wants=network-v2-browserless-provider-carrier.service" not in unit
    assert "After=network-v2-browserless-provider-carrier.service" not in unit
    assert "Requires=network-v2-browserless-provider-carrier.service" not in unit
    assert "NetworkNamespacePath=" not in unit
    assert "wireguard" not in unit.lower()
    readme = (CONSUMER / "README.md").read_text().lower()
    assert "does not" in readme
    assert "credentials" in readme
    assert "runtime credentialauthority" in readme


def test_model_provider_readiness_checks_allowlist_and_unknown_rejection() -> None:
    ready = (CONSUMER / "ready.sh").read_text()
    for domain in DOMAINS:
        assert domain in ready
    assert "example.com" in ready
    assert 'unknownDestination":"REJECTED' in ready
    assert 'directFallback":false' in ready
    assert 'credentialMaterialized":false' in ready
