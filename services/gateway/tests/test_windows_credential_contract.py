from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATERIALIZER = ROOT / "packaging" / "windows" / "materialize_credentials.ps1"


def test_windows_credential_materializer_is_file_reference_only() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert "LinuxRuntimeBearerSource" in text
    assert "WindowsRuntimeBearerSource" in text
    assert "HostBearerSource" in text
    assert "ReadAllBytes" in text
    assert "WriteAllBytes" in text
    assert "Get-Content" not in text


def test_windows_credential_materializer_requires_stopped_candidate() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert "Gateway candidate must be stopped while credentials are materialized" in text
    assert "$service.Status -ne 'Stopped'" in text


def test_windows_credential_materializer_protects_exact_principals() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert "'/inheritance:r'" in text
    assert "'*S-1-5-18:(F)'" in text
    assert "'*S-1-5-32-544:(F)'" in text
    assert '"*$($ServiceSid):(R)"' in text
    assert "credential ACL principal set mismatch" in text
    assert "IsInherited" in text


def test_windows_credential_materializer_emits_digest_only_receipt() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    assert "ordivon.gateway-windows-credential-materialization" in text
    assert "sha256 = $finalDigest" in text
    assert "bytes = $finalItem.Length" in text
    assert "source = $spec.source" not in text
