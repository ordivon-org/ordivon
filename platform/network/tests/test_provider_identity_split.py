import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel):
    return json.loads((ROOT / rel).read_text())


def test_provider_profile_contains_only_provider_side_projection():
    value = load("providers/surfshark/config/provider-profile.json")
    assert value["kind"] == "ordivon.network-v2.provider-profile"
    assert value["providerId"] == "surfshark"
    assert value["site"] == "th-bkk"
    raw = json.dumps(value).lower()
    assert "privatekey" not in raw
    assert "private_key" not in raw
    assert "assignedaddress" not in raw
    assert set(value["projectedMaterial"]) == {"endpoint", "server-public-key", "provider-site"}


def test_client_identity_is_opaque_and_single_session():
    value = load("providers/surfshark/config/client-identity-linux-shared.json")
    assert value["kind"] == "ordivon.network-v2.client-identity"
    assert value["secretOwner"] == "network-provider-materials"
    assert value["concurrencyPolicy"] == "single-physical-session"
    assert value["secretProjection"] == {"privateKey": False, "assignedAddress": False}
    assert value["currentMaterialization"]["kind"] == "protected-combined-wireguard-profile-set"


def test_materialization_binding_keeps_profile_identity_and_platform_distinct():
    value = load("providers/surfshark/config/wireguard-materialization-linux.json")
    assert value["kind"] == "ordivon.network-v2.wireguard-materialization-binding"
    assert value["platform"] == "linux"
    assert value["providerProfileRef"] != value["clientIdentityRef"]
    assert value["outputKind"] == "standard-wireguard-config"
    assert value["compatibilityMode"] == "legacy-combined-profile"


def test_schema_contracts_forbid_secret_projection_fields():
    provider_schema = load("providers/schemas/provider-profile-v1.schema.json")
    identity_schema = load("providers/schemas/client-identity-v1.schema.json")
    assert provider_schema["additionalProperties"] is False
    assert "privateKey" not in provider_schema["properties"]
    assert identity_schema["properties"]["secretProjection"]["properties"]["privateKey"]["const"] is False
