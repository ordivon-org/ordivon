from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKSTATION = ROOT / "workstation"
sys.path.insert(0, str(WORKSTATION))
SPEC = importlib.util.spec_from_file_location("playwright_cli_binding", WORKSTATION / "playwright_cli_binding.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_profile_only_binds_upstream_cli_and_browser(tmp_path: Path) -> None:
    cli = tmp_path / "playwright-cli.js"; cli.write_bytes(b"cli")
    node = tmp_path / "node"; node.write_bytes(b"node"); node.chmod(0o755)
    browser = tmp_path / "chrome"; browser.write_bytes(b"chrome"); browser.chmod(0o755)
    cli_digest = MODULE.core.sha256_file(cli).removeprefix("sha256:")
    catalog = {"managed_equipment": {MODULE.CLI_EQUIPMENT_ID: {"executable": str(cli), "execution_target": "local_linux", "sha256": cli_digest}}}
    browser_binding = {
        "state": "AVAILABLE",
        "equipmentId": "browser:playwright-chromium",
        "executable": str(browser),
        "executableDigest": MODULE.core.sha256_file(browser),
        "bindingDigest": "sha256:" + "1" * 64,
        "environment": {"PLAYWRIGHT_BROWSERS_PATH": str(tmp_path)},
    }
    result = MODULE.resolve_profile(catalog, browser_binding=browser_binding, node_path=node)
    assert result["state"] == "AVAILABLE"
    assert result["commandPrefix"] == [str(node.resolve()), str(cli.resolve())]
    assert result["config"]["browser"]["launchOptions"]["executablePath"] == str(browser)
    assert result["config"]["browser"]["launchOptions"]["chromiumSandbox"] is False
    assert "browser_action_authorized" in result["nonClaims"]
    assert "domain_success" in result["nonClaims"]


def test_materialize_writes_only_upstream_config(tmp_path: Path) -> None:
    output = tmp_path / "profile.json"
    profile = {"schemaVersion": 1, "kind": "x", "config": {"browser": {"browserName": "chromium"}}}
    result = MODULE.materialize_config(profile, output.resolve())
    assert json.loads(output.read_text()) == profile["config"]
    assert oct(output.stat().st_mode & 0o777) == "0o600"
    assert result["materializedConfig"]["path"] == str(output.resolve())


def test_current_catalog_registers_exact_playwright_cli() -> None:
    catalog = MODULE.core.read_catalog(ROOT / "workstation" / "software.toml")
    row = catalog["managed_equipment"][MODULE.CLI_EQUIPMENT_ID]
    assert row["executable"].endswith("/@playwright/cli/playwright-cli.js")
    assert row["sha256"] == "66ea6722d77e57ce1bc7e850cb990d14895d17d8584405ed54a8c72fab38eb75"
