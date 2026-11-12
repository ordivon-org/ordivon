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
    assert "SERVER_COUNTRIES=Singapore" in env
    assert "SERVER_COUNTRIES=Singapore,Japan" not in env
    assert "UPDATER_PERIOD=480h" in env
    assert "UPDATER_MIN_RATIO=0.51" in env
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
    assert f"WIREGUARD_PRIVATE_KEY_SECRETFILE={native.LOADED_WG_SECRETFILE}" in source
    assert "EnvironmentFile=/etc/network-v2/gluetun/serialized-native.env" in source
    assert "/gluetun/wireguard/wg0.conf" not in source
    assert "Volume=/var/lib/network-v2/gluetun:/gluetun" in source
    assert "ExecStartPre=/usr/bin/install -d -m 0700 /var/lib/network-v2/gluetun" in source


def test_running_gluetun_loaded_settings_match_selected_native_sourcecut():
    """File parity is insufficient if Podman has not reloaded changed env."""
    expected = native.generate_env(
        native.parse_env(
            "VPN_SERVICE_PROVIDER=custom\nVPN_TYPE=wireguard\n"
            "HTTPPROXY=on\nHTTPPROXY_LISTENING_ADDRESS=:8888\n"
        ),
        "10.64.200.9/16",
    )
    # Gluetun includes empty default filters in the running OCI environment.
    loaded = expected.splitlines() + [
        f"WIREGUARD_PRIVATE_KEY_SECRETFILE={native.LOADED_WG_SECRETFILE}",
        "SERVER_CITIES=", "SERVER_HOSTNAMES=", "SERVER_NAMES=",
        "SERVER_CATEGORIES=",
    ]
    native.verify_loaded_env(expected, loaded)
    for before, after, affected_key in [
        ("SERVER_COUNTRIES=Singapore", "SERVER_COUNTRIES=Japan", "SERVER_COUNTRIES"),
        ('SERVER_REGIONS="Asia Pacific"', 'SERVER_REGIONS="Europe"', "SERVER_REGIONS"),
        ("DNS_UPSTREAM_RESOLVER_TYPE=dot", "DNS_UPSTREAM_RESOLVER_TYPE=doh", "DNS_UPSTREAM_RESOLVER_TYPE"),
    ]:
        mutated = [line.replace(before, after) for line in loaded]
        with pytest.raises(ValueError, match=affected_key):
            native.verify_loaded_env(expected, mutated)
    with pytest.raises(ValueError, match="SERVER_HOSTNAMES"):
        native.verify_loaded_env(
            expected,
            [line for line in loaded if not line.startswith("SERVER_HOSTNAMES=")]
            + ["SERVER_HOSTNAMES=one.prod.surfshark.com"],
        )
    with pytest.raises(ValueError, match="SERVER_COUNTRIES"):
        native.verify_loaded_env(expected, loaded + ["SERVER_COUNTRIES=Singapore"])
    with pytest.raises(ValueError, match="VPN_SERVICE_PROVIDER"):
        native.verify_loaded_env(expected, [line for line in loaded if not line.startswith("VPN_SERVICE_PROVIDER=")])


    # Loaded OCI env must not override the native candidate selector, pin a
    # different WireGuard endpoint, or inline a private key outside the Secret.
    for key in (
        "WIREGUARD_ENDPOINT_IP", "WIREGUARD_ENDPOINT_PORT",
        "WIREGUARD_PUBLIC_KEY", "WIREGUARD_PRIVATE_KEY",
        "WIREGUARD_PRESHARED_KEY",
    ):
        with pytest.raises(ValueError, match=key):
            native.verify_loaded_env(expected, loaded + [f"{key}=synthetic-canary"])
    with pytest.raises(ValueError, match="WIREGUARD_PRIVATE_KEY_SECRETFILE"):
        native.verify_loaded_env(expected, [
            item for item in loaded
            if not item.startswith("WIREGUARD_PRIVATE_KEY_SECRETFILE=")
        ])
    with pytest.raises(ValueError, match="WIREGUARD_PRIVATE_KEY_SECRETFILE"):
        native.verify_loaded_env(expected, [
            item.replace(native.LOADED_WG_SECRETFILE, "/tmp/not-the-podman-secret")
            for item in loaded
        ])
    with pytest.raises(ValueError, match="WIREGUARD_PRIVATE_KEY_SECRETFILE"):
        native.verify_loaded_env(
            expected,
            loaded + [f"WIREGUARD_PRIVATE_KEY_SECRETFILE={native.LOADED_WG_SECRETFILE}"],
        )



def test_country_selector_policy_is_one_authority_for_selected_and_excluded():
    policy = native.read_selector_policy()
    assert policy == {
        "regions": ["Asia Pacific"],
        "selectedCountries": ["Singapore"],
        "excludedCountries": ["Japan", "South Korea"],
    }
    inherited = native.parse_env("VPN_SERVICE_PROVIDER=custom\nVPN_TYPE=wireguard\n")
    expanded = {
        **policy,
        "selectedCountries": ["Singapore", "Hong Kong", "Malaysia"],
    }
    rendered = native.generate_env(inherited, "10.64.200.9/16", expanded)
    assert 'SERVER_REGIONS="Asia Pacific"' in rendered
    assert "SERVER_COUNTRIES=Singapore,Hong Kong,Malaysia" in rendered
    assert "WIREGUARD_ENDPOINT_IP" not in rendered

    # JSON duplicate keys must never silently replace approved country or
    # excluded-country policy fields (json.loads would otherwise keep last).
    with pytest.raises(ValueError, match="Duplicate Gluetun selector key"):
        native.parse_selector_policy(
            '{"regions":["Asia Pacific"],'
            '"selectedCountries":["Singapore"],'
            '"selectedCountries":["Japan"],'
            '"excludedCountries":["South Korea"]}'
        )
    with pytest.raises(ValueError, match="Duplicate Gluetun selector key"):
        native.parse_selector_policy(
            '{"regions":["Asia Pacific"],"selectedCountries":["Singapore"],'
            '"excludedCountries":["Japan"],"excludedCountries":[]}'
        )

    for invalid in [
        {**expanded, "selectedCountries": []},
        {**expanded, "selectedCountries": ["Japan"]},
        {**expanded, "selectedCountries": ["Singapore", "Singapore"]},
        {**expanded, "selectedCountries": ["Singapore\nHEALTH_RESTART_VPN=off"]},
        {**expanded, "selectedCountries": ["Singapore"], "regions": []},
        {**expanded, "selectedCountries": ["Singapore"], "unknownField": True},
    ]:
        with pytest.raises(ValueError):
            native.parse_selector_policy(__import__("json").dumps(invalid))



def test_upstream_ordered_country_preview_preserves_native_provider_and_fail_closed_admission():
    policy = native.read_selector_policy()
    preview = {
        **policy,
        "regions": [],
        "selectedCountries": ["Singapore", "Malaysia", "Hong Kong", "Thailand", "Taiwan"],
        "selectionMode": "ordered",
    }
    inherited = native.parse_env("VPN_SERVICE_PROVIDER=custom\nVPN_TYPE=wireguard\n")
    selected = native.generate_env(inherited, "10.64.200.9/16", preview)
    assert "SERVER_COUNTRIES=Singapore,Malaysia,Hong Kong,Thailand,Taiwan" in selected
    assert "SERVER_SELECTION_MODE=ordered" in selected
    assert "SERVER_REGIONS=" not in selected
    assert "VPN_SERVICE_PROVIDER=surfshark" in selected
    assert "WIREGUARD_ENDPOINT_IP" not in selected
    assert "WIREGUARD_PUBLIC_KEY" not in selected
    assert "WIREGUARD_PRIVATE_KEY" not in selected
    default = native.generate_env(inherited, "10.64.200.9/16")
    assert "SERVER_SELECTION_MODE" not in default
    assert 'SERVER_REGIONS="Asia Pacific"' in default
    assert "SERVER_COUNTRIES=Singapore\n" in default

    # A country-priority source must not mistakenly report the live single
    # country / legacy stable OCI as already conformant.
    live = default.splitlines() + [
        f"WIREGUARD_PRIVATE_KEY_SECRETFILE={native.LOADED_WG_SECRETFILE}"
    ]
    with pytest.raises(ValueError, match="SERVER_"):
        native.verify_loaded_env(selected, live)
    with pytest.raises(ValueError, match="SERVER_SELECTION_MODE"):
        native.verify_loaded_env(default, live + ["SERVER_SELECTION_MODE=ordered"])
    with pytest.raises(ValueError, match="SERVER_REGIONS"):
        native.verify_loaded_env(selected, selected.splitlines() + [
            "SERVER_REGIONS=Asia Pacific",
            f"WIREGUARD_PRIVATE_KEY_SECRETFILE={native.LOADED_WG_SECRETFILE}",
        ])
    # All these are invalid upstream-native priority claims, not reasons to
    # introduce a separate endpoint scheduler.
    for invalid in (
        {**preview, "regions": ["Asia Pacific"]},
        {**preview, "selectedCountries": ["Singapore"]},
        {**preview, "selectionMode": "random"},
        {**preview, "selectionMode": "highest-signal"},
        {**preview, "selectedCountries": ["Singapore", "Japan"]},
    ):
        with pytest.raises(ValueError):
            native.parse_selector_policy(__import__("json").dumps(invalid))



def test_provider_uses_native_vpn_namespace_dns_consumer_not_host_udp_probe():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    task = (root / "providers/gluetun/Taskfile.yml").read_text()
    assert "provider:gluetun:dns-consumer:" in task
    assert "podman inspect network-v2-gluetun-owned-r1" in task
    assert "/usr/bin/nsenter --target" in task
    assert "@127.0.0.1 example.com" in task
    assert "for rr in A AAAA" in task
    assert "task provider:gluetun:dns-consumer" in task
    rules = (root / "config/prometheus/consumer.rules.yml").read_text()
    assert rules.count("observation_plane: host_direct_udp53") == 3
    assert "VPN DoT state is unknown" in rules


def test_gluetun_dot_upstream_observes_actual_provider_namespace_and_certificate():
    from pathlib import Path
    t = (Path(__file__).resolve().parents[1] / 'providers/gluetun/Taskfile.yml').read_text()
    assert 'provider:gluetun:dns-dot-upstreams:' in t
    assert 'task provider:gluetun:dns-dot-upstreams' in t
    assert 'DNS_UPSTREAM_RESOLVER_TYPE=' in t and 'DNS_UPSTREAM_RESOLVERS=' in t
    assert 'nsenter --target' in t
    assert '+tls +tls-ca +tls-hostname=' in t
    native_source_lines = {line.strip() for line in t.splitlines()}
    assert 'cloudflare) address=1.1.1.1; hostname=cloudflare-dns.com ;;' in native_source_lines
    assert 'google) address=8.8.8.8; hostname=dns.google ;;' in native_source_lines
    assert 'VPN_NAMESPACE_DOT_UPSTREAM_DEGRADED' in t
    assert 'VPN_NAMESPACE_DOT_UPSTREAMS_UNAVAILABLE_OR_UNKNOWN' in t
    assert 'grep -Eq' in t and 'healthy=$((healthy + 1))' in t
