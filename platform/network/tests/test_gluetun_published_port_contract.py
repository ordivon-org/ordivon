"""Source-only provider proxy publication checks, without provider credentials or containers."""
from __future__ import annotations

import configparser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUADLET = ROOT / "capabilities/gluetun/quadlet-candidate/gluetun-serialized-candidate.container"
ENV = ROOT / "capabilities/gluetun/config/serialized-candidate.env"


def env_values():
    return dict(line.split("=", 1) for line in ENV.read_text().splitlines() if line and not line.startswith("#"))


def quadlet_config():
    conf = configparser.ConfigParser(interpolation=None, strict=True)
    conf.read(QUADLET)
    return conf


def test_exact_container_port_publication_matches_consumer_adapter():
    adapter = json.loads((ROOT / "consumers/browserless/config/provider-carrier-gluetun-candidate.json").read_text())
    inbound = adapter["inbounds"][0]
    outbound = adapter["outbounds"][0]
    env = env_values()
    container = quadlet_config()["Container"]
    assert inbound["listen"] == "10.252.246.2" and inbound["listen_port"] == 19680
    assert outbound == {
        "type": "http",
        "tag": "gluetun-upstream",
        "server": "10.252.246.1",
        "server_port": 19682,
    }
    assert env["HTTPPROXY"] == "on"
    assert env["HTTPPROXY_LISTENING_ADDRESS"] == ":8888"
    assert container["PublishPort"] == "10.252.246.1:19682:8888/tcp"
    assert container["Network"] == "gluetun-serialized-candidate.network"
    assert container["IP"] == "10.253.239.2"
    assert container["Pull"] == "never"


def test_exact_container_ingress_firewall_and_locked_image():
    env = env_values()
    container = quadlet_config()["Container"]
    digest = (ROOT / "capabilities/gluetun/external/gluetun-image.lock").read_text()
    pinned = next(x.split("=", 1)[1] for x in digest.splitlines() if x.startswith("amd64Digest="))
    assert container["Image"] == "docker.io/qmcgaw/gluetun@" + pinned
    assert "8888" in env["FIREWALL_INPUT_PORTS"].split(",")
    assert "19682" not in env["FIREWALL_INPUT_PORTS"].split(",")
    assert env["HTTP_CONTROL_SERVER_ADDRESS"] == "127.0.0.1:8000"
    assert "FIREWALL_ENABLED_DISABLING_IT_SHOOTS_YOU_IN_YOUR_FOOT" not in env
    assert container["AddCapability"] == "NET_ADMIN"
    assert container["AddDevice"] == "/dev/net/tun"


def test_source_candidate_is_not_active_install_dependency():
    taskfile = (ROOT / "Taskfile.yml").read_text()
    assert "gluetun-serialized-candidate.container" not in taskfile
    # Runtime candidate has no automatic production systemd installation.
    container = quadlet_config()["Container"]
    assert container["EnvironmentFile"] == "/etc/network-v2/gluetun/serialized-candidate.env"
    assert container["Volume"] == (
        "/etc/network-v2/browserless/nv2blwg.conf:/gluetun/wireguard/wg0.conf:ro"
    )


def test_native_podman_quadlet_generator_produces_exact_port_mapping():
    import os
    import subprocess

    binary = Path("/usr/lib/systemd/system-generators/podman-system-generator")
    if not binary.exists():
        import pytest
        pytest.skip("native Podman systemd Quadlet generator unavailable")
    env = dict(os.environ)
    env["QUADLET_UNIT_DIRS"] = str(QUADLET.parent)
    result = subprocess.run(
        [str(binary), "--dryrun"],
        env=env, text=True, capture_output=True, check=False, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "--publish 10.252.246.1:19682:8888/tcp" in result.stdout
    assert "--network network-v2-gluetun-private-r1" in result.stdout
    assert "--pull never" in result.stdout
    assert "--cap-add net_admin" in result.stdout
    assert "--device /dev/net/tun" in result.stdout
    assert "--subnet 10.252.246.0/30" not in result.stdout
