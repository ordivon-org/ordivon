from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packaging" / "windows" / "materialize-ordivon-runtime-service.ps1"
ENV = ROOT / "packaging" / "windows" / "ordivon-runtime.env.example"


def test_windows_service_materializer_is_preview_by_default_and_never_starts_service():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "[switch]$Apply" in text
    assert "if (-not $Apply)" in text
    assert "'create', $ServiceName" in text
    assert "'config', $ServiceName" in text
    assert "'sidtype', $ServiceName, 'unrestricted'" in text
    assert "'failureflag', $ServiceName, '1'" in text
    assert "Start-Service" not in text
    assert "@('start', $ServiceName)" not in text
    assert "sc.exe start" not in text.lower()


def test_windows_service_materializer_uses_virtual_account_known_folder_and_separate_secret_file():
    text = SCRIPT.read_text(encoding="utf-8")
    env = ENV.read_text(encoding="utf-8")
    assert 'NT SERVICE\\$ServiceName' in text
    assert "CommonApplicationData" in text
    assert '--windows-service --env-file' in text
    assert "ORDIVON_BEARER_TOKEN=" not in env
    assert "ORDIVON_BEARER_TOKEN_FILE=" in env
    assert "C:\\ProgramData\\Ordivon\\Runtime" in env
    assert "ORDIVON_RUNNER_PATH" not in env
    assert "ORDIVON_WINDOWS_WSL_DISTRIBUTION" not in env


def test_windows_service_materializer_uses_least_privilege_resource_classes():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "service:FullControl" in text
    assert "service:ReadAndExecute" in text
    assert "service:Read;" in text
    assert "Set-ExactPrivateAcl $file $serviceSid $readOnly" in text
    assert "Set-ExactPrivateAcl $file $serviceSid $readExecute" in text
    assert "Set-ExactPrivateAcl $directory $serviceSid $fullControl" in text


def test_windows_service_materializer_does_not_predeclare_broad_service_privileges():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "requiredPrivileges = 'deferred-to-native-acceptance'" in text
    assert "'privs', $ServiceName" not in text
    assert "LocalSystem" not in text


def test_windows_service_materializer_supports_isolated_candidate_identity_and_port():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "[string]$Bind = '127.0.0.1:8897'" in text
    assert "[string]$NodeId = 'windows-main'" in text
    assert "Bind must be an explicit loopback address and port." in text
    assert "Bind port must be in the range 1..65535." in text
    assert "NodeId contains unsupported characters." in text
    assert "('ORDIVON_BIND=' + $Bind)" in text
    assert "('ORDIVON_NODE_ID=' + $NodeId)" in text


def test_materializer_can_reuse_existing_launcher_and_token_without_secret_staging():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "function Copy-UnlessSameFile" in text
    assert "[StringComparison]::OrdinalIgnoreCase" in text
    assert "Copy-UnlessSameFile $launcherSource $launcherTarget" in text
    assert "Copy-UnlessSameFile $tokenSourceResolved $tokenTarget" in text


def test_windows_executable_allowlist_scopes_ordivon_to_materialized_runtime_root():
    template = ENV.read_text(encoding="utf-8")
    lines = template.splitlines()
    assert (
        r"ORDIVON_ALLOWED_EXECUTABLE_ROOTS=C:\Windows;C:\Program Files;"
        r"C:\ProgramData\Ordivon\Runtime"
    ) in lines
    assert (
        r"ORDIVON_ALLOWED_EXECUTABLE_ROOTS=C:\Windows;C:\Program Files;"
        r"C:\ProgramData\Ordivon"
    ) not in lines


def test_windows_service_materializer_has_explicit_platform_native_authority_profiles():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "[ValidateSet('limited-only', 'limited-and-elevated')]" in text
    assert "[string]$WindowsAuthorityProfile = 'limited-only'" in text
    assert "$requiresLocalAdministrators = $WindowsAuthorityProfile -eq 'limited-and-elevated'" in text
    assert "Get-LocalGroup -SID $administratorsSid" in text
    assert "Add-LocalGroupMember" in text
    assert "Remove-LocalGroupMember" in text
    assert "S-1-5-32-544" in text
    assert "LocalSystem" not in text
    assert "launcher acceptance must prove both High/Admin-enabled elevated context" in text


def test_windows_service_materializer_never_claims_elevated_profile_without_effective_acceptance():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "builtinAdministratorsMembershipRequired" in text
    assert "builtinAdministratorsMembershipObserved" in text
    assert "acceptance must prove" in text
    assert "Start-Service" not in text
