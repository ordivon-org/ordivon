from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def by_id(value):
    return {item["realizationId"]: item for item in value["realizations"]}


def parse_lock(rel: str):
    values = {}
    for raw in (ROOT / rel).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def test_provider_realization_registry_keeps_active_and_candidate_distinct():
    value = load("providers/surfshark/config/carrier-realizations.json")
    assert value["schemaVersion"] == 1
    assert value["kind"] == "ordivon.network-v2.provider-carrier-realizations"
    assert value["providerProfileRef"] == "providers/surfshark/config/provider-profile.json"
    assert value["clientIdentityRef"] == "providers/surfshark/config/client-identity-linux-shared.json"
    assert value["activeRealizationId"] == "legacy-wireguard-r1"
    assert value["candidateRealizationIds"] == ["gluetun-v3.41.3-r1"]

    realizations = by_id(value)
    assert set(realizations) == {"legacy-wireguard-r1", "gluetun-v3.41.3-r1"}

    active = realizations["legacy-wireguard-r1"]
    assert active["standing"] == "active"
    assert active["mechanism"] == "network-v2-wg-quick"
    assert active["activationMode"] == "continuous"
    assert active["productionAuthority"] is True
    assert active["concurrentWithActive"] is False
    assert active["materializationRef"] == "providers/surfshark/config/wireguard-materialization-linux.json"
    assert active["artifactRef"] is None
    assert active["upstreamRef"] is None

    candidate = realizations["gluetun-v3.41.3-r1"]
    assert candidate["standing"] == "candidate"
    assert candidate["mechanism"] == "gluetun"
    assert candidate["activationMode"] == "serialized-only"
    assert candidate["productionAuthority"] is False
    assert candidate["concurrentWithActive"] is False
    assert candidate["materializationRef"] is None
    assert candidate["artifactRef"] == {
        "kind": "oci-image",
        "lockFile": "capabilities/gluetun/external/gluetun-image.lock",
    }
    assert candidate["upstreamRef"] == {
        "repo": "https://github.com/passteque/gluetun.git",
        "version": "v3.41.3",
        "revision": "3d1e20c5551e9cae1f9d938dc7b7214a6987f27e",
        "lockFile": "capabilities/gluetun/external/gluetun.lock",
    }


def test_registry_and_lock_do_not_project_provider_secrets():
    raw = (
        (ROOT / "providers/surfshark/config/carrier-realizations.json").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "capabilities/gluetun/external/gluetun.lock").read_text(encoding="utf-8")
    ).lower()
    forbidden = (
        "privatekey",
        "private_key",
        "assignedaddress",
        "assigned_address",
        "password=",
        "token=",
        "secret=",
    )
    for term in forbidden:
        assert term not in raw


def test_provider_egress_points_to_registry_without_changing_current_compatibility():
    value = load("config/provider-egress.json")
    physical = value["physicalRealization"]
    assert physical["realizationRegistryRef"] == "providers/surfshark/config/carrier-realizations.json"
    assert physical["compatibilityGeneration"] == "browserless-r1"
    assert physical["namespace"] == "nv2-browserless-prod"
    assert physical["serviceUnit"] == "network-v2-browserless-provider-carrier.service"
    assert physical["targetUnit"] == "network-v2-browserless.target"


def test_realization_schema_is_closed_and_admits_only_expected_states():
    schema = load("providers/schemas/provider-carrier-realizations-v1.schema.json")
    assert schema["additionalProperties"] is False
    realization = schema["$defs"]["realization"]
    assert realization["additionalProperties"] is False
    assert set(realization["properties"]["standing"]["enum"]) == {"active", "candidate"}
    assert set(realization["properties"]["activationMode"]["enum"]) == {"continuous", "serialized-only"}
    assert realization["properties"]["productionAuthority"]["type"] == "boolean"
    assert realization["properties"]["concurrentWithActive"]["type"] == "boolean"
    artifact = schema["$defs"]["artifactRef"]
    assert artifact["additionalProperties"] is False
    assert artifact["properties"]["kind"]["const"] == "oci-image"


def test_gluetun_lock_is_exact_official_tag():
    lock = parse_lock("capabilities/gluetun/external/gluetun.lock")
    assert lock == {
        "repo": "https://github.com/passteque/gluetun.git",
        "version": "v3.41.3",
        "revision": "3d1e20c5551e9cae1f9d938dc7b7214a6987f27e",
    }


def task_block(name: str) -> str:
    text = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")
    marker = f"  {name}:\n"
    start = text.index(marker)
    lines = text[start:].splitlines(keepends=True)
    block = [lines[0]]
    for line in lines[1:]:
        if line.startswith("  ") and not line.startswith("    ") and line.rstrip().endswith(":"):
            break
        block.append(line)
    return "".join(block)


def test_gluetun_source_qualification_is_explicit_and_source_only():
    script = ROOT / "capabilities/gluetun/acceptance/source-contract.sh"
    readme = ROOT / "capabilities/gluetun/README.md"
    assert script.is_file()
    assert readme.is_file()

    block = task_block("capability:gluetun:source:accept")
    assert "capabilities/gluetun/acceptance/source-contract.sh" in block

    source = script.read_text(encoding="utf-8")
    assert "capabilities/gluetun/external/gluetun.lock" in source
    assert "git init" in source
    assert "git fetch" in source
    assert 'refs/tags/$version' in source
    assert "git rev-parse HEAD" in source
    assert "test -f \"$tmp/Dockerfile\"" in source
    assert "test -f \"$tmp/go.mod\"" in source

    forbidden = (
        "/etc/network-v2/providers",
        "systemctl ",
        "wg-quick ",
        "openvpn ",
        "VPN_SERVICE_PROVIDER",
        "WIREGUARD_PRIVATE_KEY",
    )
    for term in forbidden:
        assert term not in source


def test_gluetun_source_qualification_is_not_a_production_dependency():
    text = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")
    for name in (
        "core:install",
        "core:converge",
        "consumer:browserless:provider-carrier:materialize",
        "consumer:browserless:provider-carrier:converge",
        "consumer:browserless:provider-carrier:select",
    ):
        assert "capability:gluetun:source:accept" not in task_block(name)

    assert text.count("capability:gluetun:source:accept:") == 1


def test_gluetun_candidate_image_and_nonsecret_runtime_are_pinned():
    image = parse_lock("capabilities/gluetun/external/gluetun-image.lock")
    assert image == {
        "image": "docker.io/qmcgaw/gluetun",
        "version": "v3.41.3",
        "indexDigest": "sha256:fa19cc76b2af13d57a8d3dc3066f2ada061b1c761b8aecf989b3877c0486e027",
        "amd64Digest": "sha256:1baa76576dea1dfbafbd62bb635daf40fd87171f63273c2fdfe630418783011e",
    }

    env = parse_lock("capabilities/gluetun/config/serialized-candidate.env")
    assert env == {
        "VPN_SERVICE_PROVIDER": "custom",
        "VPN_TYPE": "wireguard",
        "HTTPPROXY": "on",
        "HTTPPROXY_LISTENING_ADDRESS": ":8888",
        "DNS_SERVER": "on",
        "UPDATER_PERIOD": "0",
        "PUBLICIP_ENABLED": "off",
        "HTTP_CONTROL_SERVER_ADDRESS": "127.0.0.1:8000",
    }
    raw = (ROOT / "capabilities/gluetun/config/serialized-candidate.env").read_text(encoding="utf-8").lower()
    for term in ("private_key", "privatekey", "password", "token", "firewall_enabled_disabling_it_shoots_you_in_your_foot=off"):
        assert term not in raw


def test_gluetun_candidate_preserves_consumer_seam_via_host_veth_proxy():
    cfg = load("consumers/browserless/config/provider-carrier-gluetun-candidate.json")
    assert cfg["inbounds"] == [{
        "type": "http",
        "tag": "shared-provider-carrier",
        "listen": "10.252.246.2",
        "listen_port": 19680,
    }]
    assert cfg["outbounds"] == [{
        "type": "http",
        "tag": "gluetun-upstream",
        "server": "10.252.246.1",
        "server_port": 19682,
    }]
    assert "dns" not in cfg
    assert {"ip_is_private": True, "action": "reject"} in cfg["route"]["rules"]
    assert {"ip_version": 6, "action": "reject"} in cfg["route"]["rules"]
    assert cfg["route"]["final"] == "gluetun-upstream"


def test_gluetun_compatibility_hop_preflight_is_read_only_and_not_automatic():
    script = ROOT / "capabilities/gluetun/acceptance/compatibility-hop.sh"
    assert script.is_file()
    source = script.read_text(encoding="utf-8")
    assert "nv2-browserless-prod" in source
    assert "10.252.246.1" in source
    assert "provider-carrier-gluetun-candidate.json" in source
    assert "systemctl stop" not in source
    assert "systemctl restart" not in source
    assert "/etc/network-v2/providers" not in source
    assert "sing-box run" not in source
    assert "curl " not in source
    assert "python3 -m http.server" not in source
    assert "mktemp" not in source
    assert "ip netns add" not in source
    assert 'ip -4 route get "$HOST_IP"' in source
    assert '"twoHopExecutionProven":false' in source

    block = task_block("capability:gluetun:compatibility-hop:preflight")
    assert "capabilities/gluetun/acceptance/compatibility-hop.sh" in block

    for name in (
        "core:install",
        "core:converge",
        "consumer:browserless:provider-carrier:materialize",
        "consumer:browserless:provider-carrier:converge",
        "consumer:browserless:provider-carrier:select",
    ):
        assert "capability:gluetun:compatibility-hop:preflight" not in task_block(name)

    taskfile = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")
    assert "capability:gluetun:compatibility-hop:accept:" not in taskfile
