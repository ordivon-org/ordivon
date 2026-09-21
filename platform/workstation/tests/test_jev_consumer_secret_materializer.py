from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_windows_materializer_uses_dpapi_current_user_without_secret_output():
    text = (ROOT / "workstation/windows/materialize-jev-consumer-secrets.ps1").read_text()
    assert "DataProtectionScope]::CurrentUser" in text
    assert "Cryptography.ProtectedData]::Protect" in text
    assert "[Console]::In.ReadToEnd()" in text
    assert "secretContentReturned = $false" in text
    assert "secretDigestReturned = $false" in text
    assert "api-key.dpapi" in text


def test_operator_wrapper_uses_stdin_not_secret_arguments():
    text = (ROOT / "workstation/windows/materialize_jev_consumer_secrets.py").read_text()
    assert "input=json.dumps(payload" in text
    assert "payload.clear()" in text
    assert "apiKey" in text
    assert "--typesafe" in text and "--text-model" in text
