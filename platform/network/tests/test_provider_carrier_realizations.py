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
    assert active["upstreamRef"] is None

    candidate = realizations["gluetun-v3.41.3-r1"]
    assert candidate["standing"] == "candidate"
    assert candidate["mechanism"] == "gluetun"
    assert candidate["activationMode"] == "serialized-only"
    assert candidate["productionAuthority"] is False
    assert candidate["concurrentWithActive"] is False
    assert candidate["materializationRef"] is None
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


def test_gluetun_lock_is_exact_official_tag():
    lock = parse_lock("capabilities/gluetun/external/gluetun.lock")
    assert lock == {
        "repo": "https://github.com/passteque/gluetun.git",
        "version": "v3.41.3",
        "revision": "3d1e20c5551e9cae1f9d938dc7b7214a6987f27e",
    }
