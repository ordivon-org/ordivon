from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

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
    assert row["sha256"] == "a174d071b97fd0480e9ff25625d7bc2880f8a795152236360a6808e74ccaf614"


def test_default_node_uses_workstation_mise_exact_pin() -> None:
    import subprocess
    import tomllib

    selected = MODULE.select_workstation_node()
    expected = tomllib.loads((ROOT / "mise.toml").read_text())["tools"]["node"]

    assert selected.is_absolute() and selected.is_file()
    assert selected != Path("/usr/bin/node")
    assert subprocess.check_output([str(selected), "--version"], text=True).strip() == f"v{expected}"


def test_missing_workstation_mise_node_does_not_fallback(monkeypatch) -> None:
    import subprocess

    import pytest

    monkeypatch.setattr(
        MODULE.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 1, "", "not installed"),
    )
    with pytest.raises(RuntimeError, match="mise.*node"):
        MODULE.select_workstation_node()


def test_installed_binding_uses_bundled_mise_owner_not_source_checkout(monkeypatch, tmp_path: Path) -> None:
    from types import SimpleNamespace

    (tmp_path / "mise.toml").write_bytes((ROOT / "mise.toml").read_bytes())
    monkeypatch.setattr(MODULE, "__file__", str(tmp_path / "playwright_cli_binding.py"))
    node = tmp_path / "node"
    node.write_bytes(b"node")
    node.chmod(0o755)
    observed = []

    def fake_run(argv, **kwargs):
        observed.append((argv, kwargs))
        output = "v26.12.1\n" if argv[-1] == "--version" else str(node) + "\n"
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)
    selected = MODULE.select_workstation_node()

    assert selected == node.resolve()
    args, invocation = observed[0]
    assert invocation["cwd"] == tmp_path
    assert args[-2:] == ["which", "node"]
    assert invocation["env"]["MISE_AUTO_INSTALL"] == "false"
    assert invocation["env"]["MISE_OFFLINE"] == "1"
    playbook = (ROOT / "ansible" / "workstation-tool-bindings.yml").read_text()
    assert "src: ../mise.toml" in playbook
    assert "dest: /usr/local/libexec/ordivon/workstation-v2/mise.toml" in playbook


def test_mise_owner_node_version_mismatch_fails_closed(monkeypatch, tmp_path: Path) -> None:
    from types import SimpleNamespace

    import pytest

    node = tmp_path / "node"
    node.write_bytes(b"node")
    node.chmod(0o755)

    def fake_run(argv, **kwargs):
        value = "v26.7.0\n" if argv[-1] == "--version" else str(node) + "\n"
        return SimpleNamespace(returncode=0, stdout=value, stderr="")

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="mise.*node"):
        MODULE.select_workstation_node()


def test_playwright_vendor_carrier_version_is_owned_once() -> None:
    import tomllib

    project = ROOT / "workstation/playwright-cli"
    manifest = json.loads((project / "package.json").read_text())
    source = (project / "pnpm-lock.yaml").read_text()
    manager = tomllib.loads((ROOT / "mise.toml").read_text())["tools"]["pnpm"]

    assert manager == "12.16.1"
    assert "packageManager" not in manifest
    assert manifest["dependencies"] == {"@playwright/cli": "0.1.25"}
    assert "specifier: 0.1.25" in source
    assert "version: 0.1.25" in source
    assert "playwright-core@1.66.0-alpha-2026-11-18" in source
    assert "pnpm@12.16.1:" not in source


def test_ansible_qualifies_pnpm_carrier_before_publishing_catalog() -> None:
    install = (ROOT / "ansible/workstation-tool-bindings.yml").read_text()

    assert "workstation/playwright-cli/pnpm-lock.yaml" in install
    assert "--frozen-lockfile" in install
    assert "--ignore-scripts" in install
    assert "a174d071b97fd0480e9ff25625d7bc2880f8a795152236360a6808e74ccaf614" in install
    assert install.index("Install exact Microsoft Playwright CLI carrier") < install.index(
        "Install Workstation v2 binding catalog"
    )
