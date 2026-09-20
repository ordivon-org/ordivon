from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "workstation/windows/cloudflared-runtime.dsc.yaml"
DOC = ROOT / "docs/WINDOWS_CLOUDFLARED_RUNTIME_INGRESS.md"

def test_windows_runtime_ingress_uses_upstream_package_and_scm_resource():
    text = CONFIG.read_text()
    assert "Microsoft.WinGet/Package" in text
    assert "Cloudflare.cloudflared" in text
    assert "Microsoft.Windows/Service" in text
    assert "name: Cloudflared" in text
    assert "logonAccount: LocalSystem" in text
    assert "startType: Automatic" in text
    assert "status: Running" in text

def test_windows_runtime_ingress_uses_token_file_without_secret_bytes():
    text = CONFIG.read_text()
    assert "--token-file" in text
    assert "run --token-file" in text
    assert "C:\\ProgramData\\Ordivon\\Cloudflare\\windows-runtime-canary.token" in text
    assert "TUNNEL_TOKEN=" not in text
    assert "--token " not in text
    assert "powershell.exe" not in text.lower()

def test_windows_runtime_ingress_is_native_and_does_not_proxy_through_wsl():
    text = CONFIG.read_text()
    assert "127.0.0.1:20246" in text
    assert "wsl.exe" not in text.lower()
    assert "archlinux" not in text.lower()

def test_documented_retirement_boundary_preserves_linux_production_tunnel():
    text = DOC.read_text()
    assert "ordivon-cloudflare-canary.service" in text
    assert "production A/B" in text
    assert "does not authorize deleting or moving them" in text
    assert "MUST NOT be committed to Git" in text

MATERIALIZER = ROOT / "workstation/windows/materialize-cloudflared-runtime-token.ps1"

def test_token_materializer_is_one_shot_acl_bounded_and_never_returns_secret():
    text = MATERIALIZER.read_text()
    assert "wsl.localhost\\archlinux\\etc\\cloudflared\\canary.env" in text
    assert "windows-runtime-canary.token" in text
    assert "SetAccessRuleProtection($true, $false)" in text
    assert "NT AUTHORITY" in text and "SYSTEM" in text
    assert "BUILTIN" in text and "Administrators" in text
    assert "secretContentReturned = $false" in text
    assert "Write-Output $token" not in text
    assert "ConvertTo-SecureString" not in text

def test_dsc_and_materializer_share_exact_token_path():
    config = CONFIG.read_text()
    materializer = MATERIALIZER.read_text()
    marker = "C:\\ProgramData\\Ordivon\\Cloudflare\\windows-runtime-canary.token"
    assert marker in config
    assert marker in materializer
