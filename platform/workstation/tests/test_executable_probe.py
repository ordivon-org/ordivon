from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "inventory" / "probe_executables.py"
spec = importlib.util.spec_from_file_location("executable_probe", SCRIPT)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_path_scope_is_explicit_and_missing_is_not_installed_verdict() -> None:
    with patch.object(
        probe.shutil,
        "which",
        side_effect=lambda name, path: (
            r"C:\Tools\gh.exe" if (name == "gh" and path == "interactive") else None
        ),
    ) as which:
        service = probe.observe(["gh"], path="service")
        desktop = probe.observe(["gh"], path="interactive")
    assert which.call_count == 2
    assert service["commands"][0] == {
        "name": "gh",
        "resolution": "not_on_path",
        "executablePath": None,
    }
    assert desktop["commands"][0]["resolution"] == "on_path"
    assert service["pathSha256"] != desktop["pathSha256"]
    assert service["verificationBoundary"].startswith("PATH_resolution_only")


def test_rejects_shell_expressions_and_unbounded_queries() -> None:
    with pytest.raises(ValueError):
        probe.observe(["git; remove-all"])
    with pytest.raises(ValueError):
        probe.observe([])
    with pytest.raises(ValueError):
        probe.observe(["git"] * 129)


def test_windows_native_probe_reports_identity_and_rejects_command_expression() -> None:
    import json
    import os
    import shutil
    import subprocess

    if os.name != "nt" or shutil.which("pwsh") is None:
        pytest.skip("Windows PowerShell 7 is not installed on this test host")
    script = SCRIPT.with_suffix(".ps1")
    shell = shutil.which("pwsh")
    assert shell is not None
    invocation = f"& '{script.as_posix()}' -Names @('git','unlikely-tool-ordivon-test')"
    output = subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-Command", invocation],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        timeout=15,
    )
    report = json.loads(output.stdout)
    assert report["kind"] == "ordivon.workstation.executable-path-observation"
    assert report["executionPrincipal"]
    assert report["pathSha256"] and len(report["pathSha256"]) == 64
    assert report["commands"][0]["resolution"] in {"on_path", "not_on_path"}
    assert report["commands"][1]["resolution"] == "not_on_path"
    bad = subprocess.run(
        [
            shell,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"& '{script.as_posix()}' -Names @('git;unexpected')",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    assert bad.returncode != 0


def test_scoped_mise_recovers_path_miss_without_changing_path_observation(tmp_path) -> None:
    from subprocess import CompletedProcess

    binary = tmp_path / "pnpm"
    binary.write_text("fixture")
    binary.chmod(0o755)
    with patch.object(probe.shutil, "which", side_effect=lambda name, path: (
        "/usr/bin/mise" if name == "mise" else None
    )), patch.object(probe.subprocess, "run", return_value=CompletedProcess(
        [], 0, str(binary) + "\n", ""
    )) as run:
        result = probe.observe(["pnpm"], path="service", mise_scope=True)
    row = result["commands"][0]
    assert row["resolution"] == "not_on_path"
    assert row["executablePath"] is None
    assert row["mise"] == {"resolution": "resolved", "executablePath": str(binary)}
    assert run.call_args.args[0] == ["/usr/bin/mise", "which", "pnpm"]
    assert run.call_args.kwargs["cwd"] == Path.cwd()
    assert run.call_args.kwargs["env"]["PATH"] == "service"
    assert run.call_args.kwargs["env"]["MISE_OFFLINE"] == "1"
    assert run.call_args.kwargs["env"]["MISE_AUTO_INSTALL"] == "false"
    assert result["miseScope"]["verificationBoundary"].startswith("mise_which_resolution_only")


def test_scoped_mise_failure_is_not_a_missing_installation_verdict() -> None:
    from subprocess import CompletedProcess, TimeoutExpired

    with patch.object(probe.shutil, "which", return_value=None):
        result = probe.observe(["z3"], mise_scope=True)
    assert result["commands"][0]["mise"]["resolution"] == "resolver_unavailable"
    with patch.object(probe.shutil, "which", return_value="/usr/bin/mise"):
        with patch.object(probe.subprocess, "run", return_value=CompletedProcess([], 1, "", "untrusted")):
            assert probe.observe(["z3"], mise_scope=True)["commands"][0]["mise"]["resolution"] == "unresolved"
        with patch.object(probe.subprocess, "run", side_effect=TimeoutExpired("mise", 5)):
            assert probe.observe(["z3"], mise_scope=True)["commands"][0]["mise"]["resolution"] == "resolver_error"
    with patch.object(probe.shutil, "which", return_value=None):
        rows = probe.observe(["z3"] * 17, mise_scope=True)["commands"]
    assert rows[-1]["mise"]["resolution"] == "lookup_budget_exhausted"


def test_mise_inventory_distinguishes_off_path_installation() -> None:
    from subprocess import CompletedProcess

    with (
        patch.object(probe.shutil, "which", return_value="/usr/bin/mise"),
        patch.object(probe.subprocess, "run", side_effect=[
            CompletedProcess([], 0, '{"pnpm":[{"version":"12.16.1","installed":true}],'
                '"github:leanprover/lean4":[{"version":"4.35.0","installed":true}]}', ""),
            CompletedProcess([], 0, "github:leanprover/lean4\n", ""),
            CompletedProcess([], 1, "", "unresolved"),
        ]) as run,
    ):
        report = probe.observe_mise_installed(["pnpm", "lean", "unlikely-tool"])
    assert report == {
        "state": "observed",
        "installedVersions": {"pnpm": ["12.16.1"], "lean": ["4.35.0"]},
        "unmatchedNames": ["unlikely-tool"],
        "providerKeys": {"pnpm": "pnpm", "lean": "github:leanprover/lean4"},
    }
    assert run.call_args_list[0].args[0] == [
        "/usr/bin/mise", "ls", "--installed", "--json",
    ]
    assert run.call_args_list[1].args[0] == ["/usr/bin/mise", "which", "lean", "--plugin"]
    for call in run.call_args_list:
        assert call.kwargs["env"]["MISE_OFFLINE"] == "1"
        assert call.kwargs["env"]["MISE_AUTO_INSTALL"] == "false"


def test_mise_inventory_failure_is_unknown_not_absence() -> None:
    with patch.object(probe.shutil, "which", return_value=None):
        assert probe.observe_mise_installed(["pnpm"])["state"] == "unknown"
    with (
        patch.object(probe.shutil, "which", return_value="/usr/bin/mise"),
        patch.object(probe.subprocess, "run", side_effect=OSError("unavailable")),
    ):
        assert probe.observe_mise_installed(["pnpm"])["state"] == "unknown"


def test_mise_scope_resolves_even_when_system_tool_is_on_path(tmp_path) -> None:
    from subprocess import CompletedProcess

    binary = tmp_path / "python"
    binary.write_text("fixture")
    binary.chmod(0o755)
    with patch.object(probe.shutil, "which", side_effect=lambda name, path: "/usr/bin/" + name), patch.object(
        probe.subprocess, "run", return_value=CompletedProcess([], 0, str(binary), "")
    ):
        row = probe.observe(["python"], mise_scope=True)["commands"][0]
    assert row["executablePath"] == "/usr/bin/python"
    assert row["mise"]["executablePath"] == str(binary)
