"""Prove source credential composition without exposing or reusing real VPN keys."""
import base64
import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "providers/gluetun/native_profile.py"
spec = importlib.util.spec_from_file_location("gluetun_native_profile", SOURCE)
assert spec is not None and spec.loader is not None
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)

SYNTHETIC_KEY = base64.b64encode(bytes(range(32))).decode()


def test_wireguard_materialization_is_native_and_does_not_expose_private_key():
    private, ipv4 = native.parse_wireguard(
        "[Interface]\n"
        f"PrivateKey = {SYNTHETIC_KEY}\n"
        "Address = 10.64.200.9/16, fd00::10/128\n\n"
        "[Peer]\n"
        "PublicKey = irrelevant\n"
        "Endpoint = 203.0.113.8:51820\n"
    )
    env = native.generate_env(
        native.parse_env(
            "VPN_SERVICE_PROVIDER=custom\n"
            "VPN_TYPE=wireguard\n"
            "HTTPPROXY=on\n"
            "HTTPPROXY_LISTENING_ADDRESS=:8888\n"
            "UPDATER_PERIOD=0\n"
            "DNS_UPSTREAM_RESOLVER_TYPE=doh\n"
        ),
        ipv4,
    )
    assert private == SYNTHETIC_KEY
    assert "VPN_SERVICE_PROVIDER=surfshark" in env
    assert "WIREGUARD_ADDRESSES=10.64.200.9/16" in env
    assert 'SERVER_REGIONS="Asia Pacific"' in env
    assert "SERVER_COUNTRIES=Singapore,Japan" in env
    assert "UPDATER_PERIOD=480h" in env
    # Existing Gluetun-native LAN route retains on-LAN Tailnet directness.
    assert env.count("FIREWALL_OUTBOUND_SUBNETS=192.168.0.0/24") == 1
    assert "HEALTH_RESTART_VPN=on" in env
    assert "HEALTH_TARGET_ADDRESSES=1.1.1.1:443,8.8.8.8:443" in env
    assert env.count("DNS_UPSTREAM_RESOLVER_TYPE=dot") == 1
    assert "DNS_UPSTREAM_RESOLVERS=cloudflare,google" in env
    assert "DNS_UPSTREAM_RESOLVER_TYPE=doh" not in env
    assert "HTTPPROXY_LISTENING_ADDRESS=:8888" in env
    assert SYNTHETIC_KEY not in env
    assert "WIREGUARD_ENDPOINT_IP" not in env


def test_reject_malformed_or_wrong_identity_without_effects():
    with pytest.raises(ValueError):
        native.parse_wireguard("[Interface]\nPrivateKey = invalid\nAddress = 10.64.1.2/16\n")
    with pytest.raises(ValueError):
        native.parse_env("VPN_SERVICE_PROVIDER=surfshark\nVPN_TYPE=wireguard\n")
    with pytest.raises(ValueError):
        native.parse_env("VPN_SERVICE_PROVIDER=custom\nVPN_TYPE=wireguard\nVPN_TYPE=wireguard\n")
    with pytest.raises(ValueError):
        native.generate_env({"HTTPPROXY": 'on"\nDANGER=1'}, "10.64.1.2/16")


def test_quadlet_uses_podman_secret_and_no_pinned_endpoint():
    source = (
        Path(__file__).resolve().parents[1]
        / "providers/gluetun/quadlet/network-v2-gluetun-owned.container"
    ).read_text()
    assert "Secret=network-v2-gluetun-surfshark-wgkey,type=mount,target=surfshark-wgkey" in source
    assert "WIREGUARD_PRIVATE_KEY_SECRETFILE=/run/secrets/surfshark-wgkey" in source
    assert "EnvironmentFile=/etc/network-v2/gluetun/serialized-native.env" in source
    assert "/gluetun/wireguard/wg0.conf" not in source
