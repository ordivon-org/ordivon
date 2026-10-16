from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = (
    ROOT
    / "workstation"
    / "providers"
    / "mobile_ios_tunnel"
    / "MobileIosTunnelProvider.ps1"
)


def test_tunnel_owner_uses_limited_runtime_service_scheduled_task() -> None:
    text = PROVIDER.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "new-scheduledtaskaction" in lowered
    assert "new-scheduledtaskprincipal" in lowered
    assert "-logontype serviceaccount" in lowered
    assert "-runlevel limited" in lowered
    assert "register-scheduledtask" in lowered
    assert "start-scheduledtask" in lowered
    assert "stop-scheduledtask" in lowered
    assert "unregister-scheduledtask" in lowered
    assert "nt service\\$servicename" in lowered
    assert "tunnel start --userspace" in lowered
    assert "--pair-record-path" in lowered
    assert "runtimecandidater6\\native-tools\\go-ios\\v1.3.2\\ios.exe" in lowered


def test_tunnel_owner_fails_closed_on_go_ios_digest_drift() -> None:
    text = PROVIDER.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "get-filehash" in lowered
    assert "c99b04f1d615fa716637efae457d5c554f32259f9d249375de0086e3cc1a1df5" in lowered
    assert "go-ios carrier digest mismatch" in lowered


MATERIALIZER = (
    ROOT
    / "workstation"
    / "providers"
    / "mobile_ios_tunnel"
    / "materialize.py"
)


def test_tunnel_owner_materializer_is_content_addressed_and_never_activates() -> None:
    text = MATERIALIZER.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "sha256" in lowered
    assert "programdata/ordivon/workstation/providers/mobileiostunnelprovider" in lowered
    assert '"activationattempted": false' in lowered
    for forbidden in (
        "register-scheduledtask",
        "start-scheduledtask",
        "stop-scheduledtask",
        "unregister-scheduledtask",
    ):
        assert forbidden not in lowered


def test_tunnel_status_is_not_failed_by_go_ios_stderr_logging() -> None:
    text = PROVIDER.read_text(encoding="utf-8")
    assert "$previousErrorActionPreference=$ErrorActionPreference" in text
    assert "$ErrorActionPreference='Continue'" in text
    assert "$ErrorActionPreference=$previousErrorActionPreference" in text


def test_tunnel_readback_is_always_array_shaped_under_strict_mode() -> None:
    text = PROVIDER.read_text(encoding="utf-8")
    assert "$rows=@(Get-MatchingTunnel)" in text
    assert "$rows=Get-MatchingTunnel" not in text
    assert "@(Get-MatchingTunnel).Count" in text


def test_tunnel_owner_receipt_separates_control_plane_from_tunnel_authority() -> None:
    text = PROVIDER.read_text(encoding="utf-8")
    assert "controlPlaneAuthority='elevated'" in text
    assert "tunnelExecutionPrivilege='limited'" in text
    assert 'tunnelExecutionIdentity="NT SERVICE\\$ServiceName"' in text
    assert "executionPrivilege='limited'" not in text
