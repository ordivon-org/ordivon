from __future__ import annotations

import ast
import json
from pathlib import Path

CAPITAL = Path(__file__).resolve().parents[1]
REPO = CAPITAL.parents[1]
FORBIDDEN_MARKETS = {
    "trading",
    "portfolio",
    "risk",
    "research",
    "governance",
    "accounting",
}


def test_markets_owner_has_no_upward_capital_domain_imports():
    offenders = []
    for path in (CAPITAL / "src/ordivon_capital/markets").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if not name.startswith("ordivon_capital."):
                    continue
                parts = name.split(".")
                if len(parts) > 1 and parts[1] in FORBIDDEN_MARKETS:
                    offenders.append((path.name, name))
    assert offenders == []


def test_platform_services_do_not_import_capital_domain_source():
    offenders = []
    for owner in ("gateway", "runtime", "host"):
        root = REPO / "services" / owner
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".rs", ".ts", ".js"}:
                continue
            text = path.read_text(errors="ignore")
            if "ordivon_capital" in text:
                offenders.append(path.relative_to(REPO).as_posix())
    assert offenders == []


def test_candidate_tool_paths_are_not_imported_by_canonical_capital_source():
    forbidden = (
        "tools/nautilus_rc4",
        "tools/quickfixn_",
        "tools/opa_",
        "tools/tigerbeetle_",
    )
    offenders = []
    for path in (CAPITAL / "src/ordivon_capital").rglob("*.py"):
        text = path.read_text()
        if any(token in text for token in forbidden):
            offenders.append(path.relative_to(CAPITAL).as_posix())
    assert offenders == []


def test_capital_has_no_private_skill_subsystem_or_physical_skill_source_dependency():
    assert not (CAPITAL / "skills").exists()
    contract = json.loads(
        (CAPITAL / "contracts/capital-skill-boundary-v1.json").read_text()
    )
    assert contract["canonicalSkillStandard"] == "Agent Skills"
    assert (
        contract["bindingTruthRole"]
        == "EXTERNAL_PROJECT_SCOPE_ADVISORY_BINDING_NOT_CAPITAL_SOURCE_DEPENDENCY"
    )
    assert all("path" not in row for row in contract["skills"].values())
