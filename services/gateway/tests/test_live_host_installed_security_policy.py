"""One-way Gate: Gateway's installed Security PDP Rego must cover its read consumers.

The policy in these source tests is synthetic. Production reads the exact
Security service's declared policy and OPA paths; no fake principals or
operator grants are written. Exposes only bounded Boolean contract results.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRECHECK = ROOT / "packaging" / "check_live_host_admission.py"
INVENTORY = ROOT / "enforcement-surface.json"


@pytest.fixture
def gate() -> Any:
    spec = importlib.util.spec_from_file_location("release_installed_opa_gate", PRECHECK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_inventory() -> dict[str, list[str]]:
    document = json.loads(INVENTORY.read_text(encoding="utf-8"))
    return {
        row["name"]: (["messageRef"] if row["name"] == "message.get" else [])
        for row in document["tools"]
        if row["routeOwner"] == "host" and row["operation"] == "read"
    }


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("intact", True),
        ("old_rego_missing_message_get", False),
        ("unknown_extra_tool", False),
        ("mandatory_selector_missing", False),
        ("opa_undefined", False),
        ("opa_non_dictionary", False),
        ("opa_error", False),
    ],
)
def test_installed_security_source_contract_requires_real_effective_rego(
    gate: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutation: str,
    expected: bool,
) -> None:
    opa = tmp_path / "opa"
    opa.write_text("stub executable; calls are mocked", encoding="utf-8")
    opa.chmod(0o700)
    policy = tmp_path / "gateway_artifact.rego"
    policy.write_text("test fixture; not source or operator policy", encoding="utf-8")
    selectors = read_inventory()
    required = {"message.get": ["messageRef"]}
    if mutation == "old_rego_missing_message_get":
        selectors.pop("message.get")
        required.pop("message.get")
    elif mutation == "unknown_extra_tool":
        selectors["out.of.owner"] = []
    elif mutation == "mandatory_selector_missing":
        required["message.get"] = []

    commands: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[0] == "/usr/bin/systemctl":
            assert command[2] == gate.SECURITY_UNIT
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    f"ORDIVON_SECURITY_AUTHZEN_POLICY_FILE={policy} "
                    f"ORDIVON_SECURITY_AUTHZEN_OPA={opa}"
                ),
            )
        assert command[0] == str(opa)
        assert command[3] == str(policy)
        name = command[-1].rsplit(".", 1)[-1]
        assert name in ("host_read_selector_fields", "host_read_required_fields")
        if mutation == "opa_error":
            raise subprocess.CalledProcessError(2, command)
        table = selectors if name == "host_read_selector_fields" else required
        if mutation == "opa_undefined":
            response = {"result": []}
        elif mutation == "opa_non_dictionary":
            response = {"result": [{"expressions": [{"value": [1, 2, 3]}]}]}
        else:
            response = {"result": [{"expressions": [{"value": table}]}]}
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(response))

    monkeypatch.setattr(gate.subprocess, "run", fake_run)
    assert gate._installed_security_host_read_surface_qualified() is expected
    assert commands[0][:3] == ["/usr/bin/systemctl", "show", gate.SECURITY_UNIT]


def test_installed_opa_credential_or_policy_missing_fails_closed(
    gate: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        if command[0] != "/usr/bin/systemctl":
            pytest.fail("Must not query OPA when installed policy path is unqualified")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                f"ORDIVON_SECURITY_AUTHZEN_POLICY_FILE={tmp_path}/absent.rego "
                f"ORDIVON_SECURITY_AUTHZEN_OPA={tmp_path}/absent-opa"
            ),
        )

    monkeypatch.setattr(gate.subprocess, "run", fake_run)
    assert gate._installed_security_host_read_surface_qualified() is False


def test_read_surface_is_seventh_independent_production_release_requirement(
    gate: Any,
) -> None:
    qualified_six = {
        "status": "NECESSARY_PRECONDITIONS_PRESENT",
        "reasons": [],
        "truthBoundary": "release precondition only",
    }
    result = gate._apply_installed_security_read_surface(dict(qualified_six), qualified=False)
    assert result["status"] == "NO_GO"
    assert result["reasons"] == ["HOST_SECURITY_INSTALLED_READ_SURFACE_MISMATCH"]
    assert result["installedSecurityHostReadSurfaceQualified"] is False
    good = gate._apply_installed_security_read_surface(
        {**qualified_six, "reasons": []}, qualified=True
    )
    assert good["status"] == "NECESSARY_PRECONDITIONS_PRESENT"
    assert good["reasons"] == []
    assert good["installedSecurityHostReadSurfaceQualified"] is True
