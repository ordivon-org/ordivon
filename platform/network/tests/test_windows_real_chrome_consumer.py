import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "consumers" / "windows-real-chrome"


def test_authority_is_network_only_and_fail_closed():
    value = json.loads((C / "config" / "authority.json").read_text())
    assert value["kind"] == "ordivon.network-v2.windows-real-chrome-egress"
    assert value["listen"] == {"host":"127.0.0.1","port":19781,"protocol":"mixed"}
    assert value["networkAuthority"]["name"] == "provider-egress"
    assert value["networkAuthority"]["providerProfileId"] == "surfshark:th-bkk"
    assert value["directFallback"] is False
    assert value["browserAuthority"] == {
        "separate": True,
        "grantsBrowserControl": False,
        "grantsProviderEffect": False,
    }


def test_proxy_is_public_ipv4_only_and_has_no_direct_fallback_escape():
    value = json.loads((C / "config" / "sing-box.json").read_text())
    assert value["inbounds"] == [{"type":"mixed","tag":"windows-real-chrome","listen":"127.0.0.1","listen_port":19780}]
    assert value["outbounds"] == [{"type":"http","tag":"provider-carrier","server":"10.252.246.2","server_port":19680}]
    assert {"ip_is_private": True, "action": "reject"} in value["route"]["rules"]
    assert {"ip_version": 6, "action": "reject"} in value["route"]["rules"]
    assert value["route"]["final"] == "provider-carrier"


def test_systemd_relay_is_host_loopback_to_provider_namespace():
    relay = (C / "systemd" / "network-v2-windows-real-chrome-relay.service").read_text()
    proxy = (C / "systemd" / "network-v2-windows-real-chrome-proxy.service").read_text()
    assert "127.0.0.1:19781" in relay
    assert "nv2-browserless-prod" in relay
    assert "127.0.0.1:19780" in relay
    assert "NetworkNamespacePath=/run/netns/nv2-browserless-prod" in proxy
    assert "BrowserControl" not in relay + proxy
