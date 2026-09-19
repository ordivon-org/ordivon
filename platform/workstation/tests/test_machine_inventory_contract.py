from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_machine_inventory_source_registry_is_source_native() -> None:
    data = json.loads((ROOT / "inventory" / "sources.json").read_text(encoding="utf-8"))
    assert data["kind"] == "ordivon.workstation.v2.machine-inventory-source-registry"
    by_id = {row["id"]: row for row in data["sources"]}

    assert by_id["osquery-linux-host-facts"]["provider"] == "osquery"
    assert by_id["pacman-local-package-state"]["provider"] == "pacman"
    assert by_id["windows-installed-apps"]["provider"] == "winget_and_windows_uninstall_registry"
    assert by_id["runtime-execution-affordances"]["provider"] == "ordivon_runtime"
    assert by_id["standard-sbom-projection"]["provider"] == "syft"
    assert by_id["standard-sbom-projection"]["defaultFastPath"] is False

    assert "task_authorization" in data["nonClaims"]
    assert "domain_semantic_capability" in data["nonClaims"]
    assert "global_health" in data["nonClaims"]


def test_machine_inventory_queries_are_bounded_read_only_sql() -> None:
    query_root = ROOT / "inventory" / "queries"
    for name in [
        "system_identity.sql",
        "os_version.sql",
        "uptime.sql",
        "running_executables.sql",
        "python_packages.sql",
        "npm_packages.sql",
    ]:
        text = (query_root / name).read_text(encoding="utf-8").strip().lower()
        assert text.startswith("select")
        for forbidden in ["insert ", "update ", "delete ", "drop ", "alter "]:
            assert forbidden not in text


def test_dated_machine_snapshot_is_explicitly_nonsemantic() -> None:
    path = ROOT / "inventory" / "snapshots" / "2026-09-14-machine-tools.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["kind"] == "ordivon.operations.machine-inventory-snapshot"
    assert data["semanticCompletionEvaluated"] is False
    assert data["linux"]["pacman"]["totalPackageCount"] >= data["linux"]["pacman"]["explicitPackageCount"]
    assert data["windows"]["uninstallEntryCount"] == len(data["windows"]["installedApplications"])
    assert "task authorization" in data["nonClaims"]
    assert "domain semantic capability" in data["nonClaims"]
