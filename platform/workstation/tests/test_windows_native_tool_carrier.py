from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "workstation/windows/native-tool-carriers.json"
SCRIPT = ROOT / "workstation/windows/materialize-native-tool-carrier.ps1"


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_has_two_exact_real_carriers() -> None:
    value = _contract()
    assert value["schemaVersion"] == 1
    assert value["kind"] == "ordivon.workstation.windows-native-tool-carriers"
    rows = value["carriers"]

    go_ios = rows["go-ios-1-3-2"]
    assert go_ios == {
        "sourceUrl": "https://github.com/danielpaulus/go-ios/releases/download/v1.3.2/go-ios-win.zip",
        "archiveDigest": "sha256:939c6bcaafed183a92afb9f79cc11b1f935fa6389bfc94d3902e3f52c4dff3fe",
        "archiveMember": "ios.exe",
        "executableSha256": "sha256:c99b04f1d615fa716637efae457d5c554f32259f9d249375de0086e3cc1a1df5",
        "targetRelativePath": r"native-tools\go-ios\v1.3.2\ios.exe",
    }

    mobilecli = rows["mobilecli-1-0-20"]
    assert mobilecli == {
        "sourceUrl": "https://registry.npmjs.org/@mobilenext/mobilecli-windows-amd64/-/mobilecli-windows-amd64-1.0.20.tgz",
        "archiveDigest": "sha512:76cd220715c7d544ce6b83bb9d344ddce9a4dc00e47a3a0e717818dbae7448178a2842e942a90952ba6828a000e2a00ecd235e4d1216be90d95360523e9e1afe",
        "archiveMember": "package/mobilecli-windows-amd64.exe",
        "executableSha256": "sha256:018dcec38ee4f39ef24fd0987d85e04914294651b8da770c647f21ca04029aa4",
        "targetRelativePath": r"native-tools\mobilecli\v1.0.20\mobilecli.exe",
    }


def test_materializer_is_bounded_fail_closed_and_noninteractive() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "targetRelativePath must stay under native-tools" in text
    assert "existing target digest mismatch" in text
    assert "archive digest mismatch" in text
    assert "executable digest mismatch" in text
    assert "ArchivePath" in text
    assert "System.Net.Http.HttpClient" in text
    assert "tar.exe" in text
    assert "Expand-Archive" not in text
    assert "Invoke-WebRequest" not in text
    assert "[void]$response.EnsureSuccessStatusCode()" in text
    assert "materializerSha256" in text
    assert "contractSha256" in text
    assert "archiveVerified = ($Disposition -eq 'materialized')" in text
    assert "domainSuccess = $false" in text
    assert "taskAuthorized = $false" in text


def test_materializer_contract_does_not_encode_mobile_semantics() -> None:
    value = _contract()
    encoded = json.dumps(value, sort_keys=True).lower()
    for forbidden in ("tap", "swipe", "devicekit", "wda", "iphone", "ipad", "task success"):
        assert forbidden not in encoded



def test_carrier_contract_matches_managed_equipment_bindings() -> None:
    contract = _contract()["carriers"]
    catalog = tomllib.loads((ROOT / "workstation/software.toml").read_text(encoding="utf-8"))
    managed = catalog["managed_equipment"]
    runtime_root = "C:\\ProgramData\\Ordivon\\RuntimeCandidateR6\\"
    for carrier_id, carrier in contract.items():
        row = managed[carrier_id]
        assert row["execution_target"] == "windows_native"
        assert row["executable"] == runtime_root + carrier["targetRelativePath"]
        assert "sha256:" + row["sha256"] == carrier["executableSha256"]
