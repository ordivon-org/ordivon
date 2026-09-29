from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "config/protocol_identity_migration_v2.json").read_text())
OLD_PREFIX = "ordivon.capital." + "market."


def _active_files():
    for root_name in ("src", "config", "contracts", "schema", "scripts", "tools", "acceptance"):
        root = ROOT / root_name
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if "legacy_protocol_v1" in rel.parts:
                continue
            yield path


def _manifest(root_name: str) -> tuple[int, str]:
    root = ROOT / root_name
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        data = path.read_bytes()
        rows.append(
            (
                path.relative_to(ROOT).as_posix(),
                hashlib.sha256(data).hexdigest(),
                len(data),
            )
        )
    digest = hashlib.sha256(
        "\n".join(f"{p}\0{h}\0{n}" for p, h, n in rows).encode()
    ).hexdigest()
    return len(rows), "sha256:" + digest


def test_v2_registry_is_complete_and_no_runtime_shim_is_admitted():
    assert REGISTRY["schemaVersion"] == 2
    assert REGISTRY["standing"] == "ACTIVE_V2_NO_RUNTIME_V1_SHIM"
    assert REGISTRY["mappingCount"] == 79
    assert len(REGISTRY["mappings"]) == 79
    assert len({r["v1"] for r in REGISTRY["mappings"]}) == 79
    assert len({r["v2"] for r in REGISTRY["mappings"]}) == 79


def test_current_protocol_roots_have_no_legacy_market_identity():
    offenders = []
    for path in _active_files():
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if path.name == "protocol_identity_migration_v2.json":
            continue
        if path.name == "capital_domain_taxonomy.json":
            continue
        if OLD_PREFIX in text:
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_current_versioned_contracts_exist_and_legacy_v1_is_isolated():
    current = {
        "contracts/nonlive-effect-admission-v2.json",
        "contracts/external-write-policy-input-v2.json",
        "contracts/external-boundary-v2.json",
        "contracts/portfolio-risk-budget-v2.schema.json",
        "schema/private-reality-snapshot-v2.schema.json",
    }
    for rel in current:
        assert (ROOT / rel).is_file()
    assert (ROOT / "contracts/legacy_protocol_v1/nonlive-effect-admission-v1.json").is_file()
    assert (ROOT / "schema/legacy_protocol_v1/private-reality-snapshot-v1.schema.json").is_file()


def test_current_v2_json_documents_use_schema_version_two():
    mapped_v2 = {r["v2"] for r in REGISTRY["mappings"]}
    offenders = []
    for path in _active_files():
        if path.suffix != ".json":
            continue
        try:
            doc = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(doc, dict) and doc.get("kind") in mapped_v2:
            if doc.get("schemaVersion") != 2:
                offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_frozen_evidence_and_fixtures_remain_byte_identical_to_migration_baseline():
    assert _manifest("evidence") == (
        54,
        "sha256:c6a4f1293de042a5df2797afc8e49b90b736d704135ea4aad20914d7cb2e82be",
    )
    assert _manifest("fixtures") == (
        4,
        "sha256:69ca14c2747c05f4adbe08f178ebc4351d381283da0ef71ea5507af4819d5159",
    )


def test_v2_schema_ids_are_domain_correct():
    private = json.loads((ROOT / "schema/private-reality-snapshot-v2.schema.json").read_text())
    risk = json.loads((ROOT / "contracts/portfolio-risk-budget-v2.schema.json").read_text())
    assert private["$id"] == "ordivon.capital.trading.private-reality-snapshot.v2"
    assert private["properties"]["schemaVersion"] == {"const": 2}
    assert risk["$id"].endswith("/portfolio-risk-budget-v2.schema.json")
    assert risk["properties"]["schemaVersion"] == {"const": 2}
