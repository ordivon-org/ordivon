"""Podman-native ingress isolation gate for the non-installed Gluetun candidate."""
from __future__ import annotations

import configparser
import ipaddress
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
UNIT_DIR = ROOT / "capabilities/gluetun/quadlet-candidate"


def parse(name: str, section: str):
    source = UNIT_DIR / name
    config = configparser.ConfigParser(interpolation=None)
    with source.open() as stream:
        config.read_file(stream)
    return config[section]


def test_podman_has_exclusive_one_member_private_network_not_default_bridge():
    network = parse("gluetun-serialized-candidate.network", "Network")
    container = parse("gluetun-serialized-candidate.container", "Container")
    assert network["NetworkName"] == "network-v2-gluetun-private-r1"
    assert network["Driver"] == "bridge"
    assert network["Options"] == "isolate=strict"
    assert network["DisableDNS"] == "true"
    assert container["Network"] == "gluetun-serialized-candidate.network"
    assert container["IP"] == "10.253.239.2"
    small = ipaddress.ip_network(network["Subnet"], strict=True)
    assert small == ipaddress.ip_network("10.253.239.0/30")
    assert network["Gateway"] == "10.253.239.1"
    assert list(small.hosts()) == [
        ipaddress.ip_address("10.253.239.1"),
        ipaddress.ip_address("10.253.239.2"),
    ]
    assert not small.overlaps(ipaddress.ip_network("10.252.246.0/30"))
    assert not small.overlaps(ipaddress.ip_network("10.88.0.0/16"))


def test_native_quadlet_generator_binds_isolated_network_to_gluetun_only():
    generator = Path("/usr/lib/systemd/system-generators/podman-system-generator")
    if not generator.is_file():
        import pytest
        pytest.skip("Podman Quadlet generator unavailable")
    result = subprocess.run(
        [str(generator), "--dryrun"],
        env={**os.environ, "QUADLET_UNIT_DIRS": str(UNIT_DIR)},
        text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "--network systemd-" not in result.stdout or "network-v2-gluetun-private-r1" in result.stdout
    assert "--network network-v2-gluetun-private-r1" in result.stdout
    assert "--ip 10.253.239.2" in result.stdout
    assert "--opt isolate=strict" in result.stdout
    assert "--subnet 10.253.239.0/30" in result.stdout
    assert "--publish 10.252.246.1:19682:8888/tcp" in result.stdout
    assert "--network bridge" not in result.stdout


def test_static_config_excludes_default_bridge_membership():
    # Source contract only: live Podman peer rejection requires separate runtime evidence.
    network = parse("gluetun-serialized-candidate.network", "Network")
    assert network["Options"] == "isolate=strict"
    assert network["Subnet"].endswith("/30")
    # The candidate must never request shared default bridge membership.
    c = parse("gluetun-serialized-candidate.container", "Container")
    assert c["Network"] != "bridge"
    assert "podman" not in c["Network"]
