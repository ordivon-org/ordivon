from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = ROOT / "workstation" / "providers" / "real_chrome_user_session" / "RealChromeUserSessionProvider.ps1"
MAT = ROOT / "workstation" / "providers" / "real_chrome_user_session" / "materialize.py"


def test_provider_uses_interactive_task_scheduler_without_credentials():
    text = PROVIDER.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "new-scheduledtaskprincipal" in lowered
    assert "-logontype interactive" in lowered
    assert "-runlevel limited" in lowered
    assert "register-scheduledtask" in lowered
    assert "start-scheduledtask" in lowered
    assert "stop-scheduledtask" in lowered
    assert "unregister-scheduledtask" in lowered
    assert "passwordstored=$false" in lowered
    for forbidden in ("-password", "convertto-securestring", "credential ="):
        assert forbidden not in lowered


def test_provider_requires_loopback_proxy_and_keeps_browser_authority_false():
    text = PROVIDER.read_text(encoding="utf-8")
    assert "Test-LoopbackHttpProxy" in text
    assert "http://127.0.0.1:19781" in text
    assert "--disable-quic" in text
    assert "--proxy-server=" in text
    assert "chrome://inspect/#remote-debugging" in text
    assert "browserControlAuthorityGranted=$false" in text
    assert "providerEffectAuthorized=$false" in text


def test_provider_refuses_ambiguous_start_and_running_task_replacement():
    text = PROVIDER.read_text(encoding="utf-8")
    assert "refusing start while Chrome is already running" in text
    assert "refusing to replace a running real-Chrome carrier task" in text
    assert "refusing to remove a running real-Chrome carrier task" in text


def test_materializer_is_content_addressed_and_does_not_activate():
    text = MAT.read_text(encoding="utf-8").lower()
    assert "sha256" in text
    assert "programdata/ordivon/workstation/providers/realchromeusersessionprovider" in text
    assert '"activationattempted": false' in text
    for forbidden in ("register-scheduledtask", "start-scheduledtask", "stop-scheduledtask", "unregister-scheduledtask"):
        assert forbidden not in text
