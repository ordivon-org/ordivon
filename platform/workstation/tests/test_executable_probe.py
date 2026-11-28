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


def test_mise_lookup_distinguishes_managed_tool_from_path_miss(tmp_path) -> None:
    import subprocess

    managed = tmp_path / "pnpm"
    managed.write_text("fixture", encoding="utf-8")
    managed.chmod(0o755)
    with patch.object(probe.shutil, "which", side_effect=lambda name, path: (
        "/usr/bin/mise" if name == "mise" else None
    )), patch.object(subprocess, "run", return_value=subprocess.CompletedProcess(
        ["/usr/bin/mise", "which", "pnpm"], 0, stdout=str(managed) + "\n", stderr=""
    )) as run:
        report = probe.observe(["pnpm"], path="/usr/bin", include_mise=True)
    assert report["commands"][0]["resolution"] == "not_on_path"
    assert report["commands"][0]["mise"]["resolution"] == "resolved"
    assert report["commands"][0]["mise"]["executablePath"] == str(managed)
    assert run.call_args.args[0] == ["/usr/bin/mise", "which", "pnpm"]


def test_mise_lookup_failure_remains_unknown_and_does_not_run_requested_tool() -> None:
    import subprocess

    with patch.object(probe.shutil, "which", side_effect=lambda name, path: (
        "/usr/bin/mise" if name == "mise" else None
    )), patch.object(subprocess, "run", return_value=subprocess.CompletedProcess(
        ["/usr/bin/mise", "which", "missing"], 1, stdout="", stderr="not configured"
    )):
        row = probe.observe(["missing"], path="/usr/bin", include_mise=True)["commands"][0]
    assert row["resolution"] == "not_on_path"
    assert row["mise"]["resolution"] == "unknown"
    assert row["mise"]["executablePath"] is None


def test_mise_lookup_is_bounded_and_skips_path_hits() -> None:
    import subprocess

    with patch.object(probe.shutil, "which", side_effect=lambda name, path: (
        "/usr/bin/" + name if name in {"mise", "gh"} else None
    )), patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("mise", 3)) as run:
        rows = probe.observe(["gh", *[f"missing{i}" for i in range(17)]],
                             path="/usr/bin", include_mise=True)["commands"]
    assert "mise" not in rows[0]
    assert run.call_count == 16
    assert rows[1]["mise"]["reason"] == "mise_observation_failed"
    assert rows[-1]["mise"]["reason"] == "lookup_budget_exhausted"
