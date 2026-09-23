from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel: str):
    return json.loads((ROOT / rel).read_text())

def test_registry_schema_identity_is_digest_bound():
    registry = load("config/capital_lego_registry.json")
    contract = load("contracts/capital-lego-registry-v1.json")
    schema = ROOT / "schema/capital-lego-registry-v1.schema.json"
    digest = "sha256:" + hashlib.sha256(schema.read_bytes()).hexdigest()
    assert registry["schemaIdentity"]["sha256"] == digest
    assert contract["schemaIdentity"]["sha256"] == digest

def test_registry_covers_every_current_source_module():
    registry = load("config/capital_lego_registry.json")
    canonical = {
        row["implementation"]["path"]
        for row in registry["entries"]
        if row["sourceClass"] == "CANONICAL"
    }
    modules = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "src/ordivon_capital").glob("*/*.py")
        if p.name != "__init__.py"
    }
    assert modules <= canonical

def test_candidate_tools_are_not_canonical_owners():
    rows = load("config/capital_lego_registry.json")["entries"]
    tool_rows = [r for r in rows if r["implementation"]["path"].startswith("tools/")]
    assert tool_rows
    assert all(r["sourceClass"] == "CANDIDATE" for r in tool_rows)
    assert all(r["status"] == "CHALLENGER" for r in tool_rows)

def test_current_registry_contains_no_production_financial_write():
    rows = load("config/capital_lego_registry.json")["entries"]
    production = load("contracts/production-authorization.json")
    assert production["state"] == "BLOCK_NOT_GRANTED"
    assert all(r["effectClass"] != "PRODUCTION_FINANCIAL_WRITE" for r in rows)
    assert all(r["authorityRequirement"] != "PRODUCTION_WRITE" for r in rows)

def test_private_observers_remain_authority_blocked():
    by_id = {r["legoId"]:r for r in load("config/capital_lego_registry.json")["entries"]}
    for lego_id in ("capital.trading.binance-usdm-private-capture","capital.trading.okx-readonly-client"):
        row = by_id[lego_id]
        assert row["status"] == "BLOCKED_BY_AUTHORITY"
        assert row["authorityRequirement"] == "PRIVATE_READ"

def test_registry_verifier_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check-capital-lego-registry")],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert "CAPITAL_LEGO_REGISTRY=PASS" in result.stdout
