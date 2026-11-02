"""Contract tests for the existing external OCI/OPA carrier seam.

These tests check command/response effects, not mock claim of installed providers.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from artifact_operations.providers import oci_toolchain


def _executable(path: Path) -> Path:
    path.write_text("stub external command", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_oras_forwards_native_arguments_and_parses_provider_response(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    oras = _executable(tmp_path / "oras")
    monkeypatch.setattr(oci_toolchain, "DEFAULT_ORAS", oras)
    calls: list[tuple] = []

    def observed(argv: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        calls.append((argv, options))
        return subprocess.CompletedProcess(argv, 0, stdout='{"digest":"sha256:abc"}\n', stderr="")

    monkeypatch.setattr(oci_toolchain.subprocess, "run", observed)
    assert oci_toolchain.run_oras(["manifest", "fetch", "repo:tag"], cwd=tmp_path, timeout=12) == {
        "digest": "sha256:abc"
    }
    command, options = calls[0]
    assert command == [str(oras), "manifest", "fetch", "repo:tag"]
    assert options["cwd"] == tmp_path
    assert options["timeout"] == 12
    assert options["check"] is False


def test_oras_provider_failure_does_not_claim_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    oras = _executable(tmp_path / "oras")
    monkeypatch.setattr(oci_toolchain, "DEFAULT_ORAS", oras)

    def failed(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 4, stdout="", stderr="ORAS refused")

    monkeypatch.setattr(oci_toolchain.subprocess, "run", failed)
    with pytest.raises(RuntimeError, match="ORAS refused"):
        oci_toolchain.run_oras(["push", "repo:tag"], cwd=tmp_path)


@pytest.mark.parametrize(("stdout", "ready"), [("true\n", True), ("false\n", False)])
def test_opa_uses_installed_rego_policy_and_preserves_exact_tool_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, stdout: str, ready: bool
) -> None:
    opa = _executable(tmp_path / "opa")
    policy = tmp_path / "release.rego"
    policy.write_text("package artifact.release\nready := true\n", encoding="utf-8")
    monkeypatch.setattr(oci_toolchain, "DEFAULT_OPA", opa)
    monkeypatch.setattr(oci_toolchain, "DEFAULT_RELEASE_POLICY", policy)
    calls: list[tuple] = []

    def observed(argv: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        calls.append((argv, options))
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(oci_toolchain.subprocess, "run", observed)
    request = {"verification": {"status": "PASS"}, "local_unsigned": False}
    result = oci_toolchain.evaluate_release_policy(request)
    assert result["ready"] is ready
    assert result["status"] == "PASS"  # carrier evaluation, not policy readiness
    assert result["input"] == request
    assert result["policy"]["path"] == str(policy.resolve())
    assert result["tool"]["path"] == str(opa.resolve())
    assert result["policy"]["sha256"] == oci_toolchain.sha256_file(policy)
    assert result["tool"]["sha256"] == oci_toolchain.sha256_file(opa)
    argv, options = calls[0]
    assert argv == [
        str(opa),
        "eval",
        "--format",
        "raw",
        "--data",
        str(policy),
        "--stdin-input",
        "data.artifact.release.ready",
    ]
    assert json.loads(options["input"]) == request
    assert options["check"] is False
