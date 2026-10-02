import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_provider_egress_semantic_owner_is_not_browserless():
    value = json.loads((ROOT / "config" / "provider-egress.json").read_text())
    assert value["schemaVersion"] == 1
    assert value["kind"] == "ordivon.network-v2.provider-egress-definition"
    assert value["name"] == "provider-egress"
    assert value["semanticAuthority"] == "network-v2-provider-egress"
    assert value["physicalRealization"]["namespace"] == "nv2-browserless-prod"
    assert value["physicalRealization"]["serviceUnit"] == "network-v2-browserless-provider-carrier.service"
    assert value["migration"]["legacyPhysicalNamesAreCompatibilityIdentifiers"] is True
    assert value["migration"]["physicalRenameRequiredForSemanticCorrectness"] is False


def test_consumer_authority_metadata_uses_provider_egress_semantic_name():
    paths = [
        ROOT / "consumers" / "chat-ingress" / "config" / "egress.json",
        ROOT / "consumers" / "claude" / "config" / "authority.json",
        ROOT / "consumers" / "supply-chain" / "config" / "authority.json",
        ROOT / "consumers" / "x-reality" / "config" / "authority.json",
        *sorted((ROOT / "consumers" / "finance" / "config").glob("*-authority.json")),
    ]
    assert paths
    checked = 0
    for path in paths:
        value = json.loads(path.read_text())
        authority = value.get("networkAuthority")
        if authority is None:
            continue
        assert isinstance(authority, dict), path
        assert authority["name"] == "provider-egress", path
        checked += 1
    assert checked > 0
