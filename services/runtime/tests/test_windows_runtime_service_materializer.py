import os
import subprocess
import unittest
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


def test_windows_runtime_concurrency_policy_is_host_specific():
    windows_env = ENV.read_text(encoding="utf-8")
    linux_env = (
        ROOT / "packaging" / "systemd" / "ordivon-runtime.env.example"
    ).read_text(encoding="utf-8")
    linux_main = (
        ROOT / "crates" / "ordivon-runtime-mcp" / "src" / "main.rs"
    ).read_text(encoding="utf-8")
    registry = (
        ROOT / "crates" / "ordivon-runtime-core" / "src" / "runtime" / "registry.rs"
    ).read_text(encoding="utf-8")

    assert "ORDIVON_GLOBAL_MAX_CONCURRENCY=12" in windows_env
    assert "ORDIVON_GLOBAL_MAX_CONCURRENCY=16" in linux_env
    assert ".unwrap_or(8);" in linux_main
    assert "const WORKSPACE_EXECUTION_LIMIT: u32 = 1;" in registry


def test_windows_service_materializer_binds_privileged_policy_as_one_operator_bundle():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "[string]$ElevatedPrincipalsJson = ''" in text
    assert "[string]$ElevatedProfilesJson = ''" in text
    assert "[string]$MaintenanceLeasePath = ''" in text
    assert "Privileged admission policy must configure principals, profiles, and maintenance lease together." in text
    assert "Privileged admission JSON must be single-line." in text
    assert "MaintenanceLeasePath must be absolute." in text
    assert "ConvertFrom-Json -ErrorAction Stop" in text
    assert "Privileged admission principal and profile arrays must be non-empty when configured." in text
    assert "'ORDIVON_WINDOWS_ELEVATED_PRINCIPALS_JSON=' + $ElevatedPrincipalsJson" in text
    assert "'ORDIVON_WINDOWS_ELEVATED_PROFILES_JSON=' + $ElevatedProfilesJson" in text
    assert "'ORDIVON_WINDOWS_MAINTENANCE_LEASE_PATH=' + $MaintenanceLeasePath" in text
    assert "principalCount = $elevatedPrincipalCount" in text
    assert "profileCount = $elevatedProfileCount" in text


def test_windows_service_materializer_keeps_privileged_policy_opt_in():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "$privilegedPolicyConfiguredCount -ne 0 -and $privilegedPolicyConfiguredCount -ne 3" in text
    assert "$privilegedPolicyConfigured = $privilegedPolicyConfiguredCount -eq 3" in text
    assert "if ($privilegedPolicyConfigured)" in text


def test_windows_cold_materialization_checks_stopped_service_before_any_mutation():
    text = SCRIPT.read_text(encoding="utf-8")
    apply = text.split("if (-not $Apply)", 1)[1]
    guard = apply.index("$service.Status -ne [ServiceProcess.ServiceControllerStatus]::Stopped")
    for effect in ("[IO.Directory]::CreateDirectory", "Copy-UnlessSameFile $runtimeSource $runtimeTarget", "[IO.File]::WriteAllText("):
        assert guard < apply.index(effect), effect


def test_pg_service_materializer_is_explicit_digest_bound_disabled_start_without_sqlite_registry():
    text = SCRIPT.read_text(encoding="utf-8")
    for fragment in (
        "[string]$PostgresEnvironmentFile = ''",
        "ordivon-runtime-pg.exe",
        "ordivon-runtime-pg.env",
        "ordivon-windows-pg-job-launcher.exe",
        "runtime-pg-mcp.token",
        "PG TokenSource must be pre-provisioned",
        "pg-store",
        "$ExpectedRuntimeSha256",
        "$ExpectedLauncherSha256",
        "$ExpectedPostgresEnvironmentSha256",
        "$WindowsPgReleaseManifest",
        "$ExpectedWindowsPgSourceCommit",
        "Get-OrdivonWindowsPgReleaseProvenance",
        "releaseManifestTarget",
        "releaseProvenance",
        "Assert-PgCandidateCommitments",
        "Get-FileHash",
        "ORDIVON_PG_DSN",
        "ORDIVON_PG_STORE_ROOT",
        "ORDIVON_PG_RUNNER",
        "ORDIVON_BEARER_TOKEN_FILE",
        "if (-not $postgres) { $stateDirectories += $registryRoot }",
        "start = $startMode",
        "if ($postgres) { 'disabled' } else { 'auto' }",
        "executionReady = $false",
    ):
        assert fragment in text, fragment
    assert "Start-Service" not in text
    assert "ORDIVON_REGISTRY_ROOT','ORDIVON_BIND','ORDIVON_BEARER_TOKEN'" in text
    assert "PG environment does not bind the planned service" in text


def test_pg_materializer_preserves_build_manifest_provenance_for_activation():
    text = SCRIPT.read_text(encoding="utf-8")
    helper = (ROOT / "packaging" / "windows" / "windows-pg-release-provenance.ps1").read_text(encoding="utf-8")
    assert "ordivon.windows-pg-release" in helper
    assert "builder-manifest-claim-bound-to-exact-bytes-not-reproducible-build-proof" in helper
    assert "sourceCommitClaim" in helper
    assert "ExpectedSourceCommit" in helper
    assert "runtimeSourceArchiveSha256" in helper
    assert "cargoLockSha256" in helper
    assert "ordivon-runtime-pg.exe" in helper
    assert "ordivon-windows-pg-job-launcher.exe" in helper
    assert "ordivon-runtime-pg-release.json" in text
    assert "Staged Windows PG release manifest digest mismatch." in text
    assert "Set-ExactPrivateAcl $releaseManifestTarget $serviceSid $readOnly" in text


@unittest.skipUnless(os.name == "nt", "native Windows PowerShell 5.1 acceptance")
def test_native_pg_service_materializer_preview():
    script = ROOT / "tests" / "windows_service_materializer_pg_preview.ps1"
    subprocess.run(
        [
            "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
            "Bypass", "-File", str(script),
        ],
        check=True,
        timeout=60,
    )


def test_pg_materializer_requires_disabled_stopped_native_scm_until_all_acl_effects():
    text = SCRIPT.read_text(encoding="utf-8")
    apply = text.split("Assert-Administrator\n\nfunction Assert-PgServiceStagingFence", 1)[1]
    assert "[ServiceProcess.ServiceStartMode]::Disabled" in apply
    assert "[ServiceProcess.ServiceControllerStatus]::Stopped" in apply
    assert apply.index("Assert-PgServiceStagingFence $ServiceName $false") < apply.index("[IO.Directory]::CreateDirectory")
    assert apply.index("Assert-PgServiceStagingFence $ServiceName ($null -ne $service)") < apply.index("'create', $ServiceName")
    assert apply.rindex("Assert-PgServiceStagingFence $ServiceName $true") > apply.index("Set-ExactPrivateAcl $file $serviceSid $readOnly")


def test_windows_pg_workspace_root_is_disjoint_and_operator_scoped():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "ORDIVON_PG_WORKSPACE_ROOT = $workspaceRoot" in text
    assert "must be disjoint from the entire private ProgramData root" in text
    assert "must not traverse files or reparse points" in text
    assert "must be empty for cold materialization" in text
    assert "[IO.Directory]::CreateDirectory($workspaceRoot, $workspaceAcl)" in text
    assert "[Security.AccessControl.FileSystemRights]::ReadAttributes -bor" in text
    assert "[Security.AccessControl.FileSystemRights]::Traverse -bor" in text
    assert "[Security.AccessControl.InheritanceFlags]::None" in text


def test_windows_pg_source_export_is_independent_of_git_checkout_eol(tmp_path):
    import runpy
    import tarfile

    builder = runpy.run_path(str(ROOT / "scripts" / "prepare_windows_pg_release.py"))
    repo = tmp_path / "source"
    repo.mkdir()

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo)

    git("init", "-q")
    git("config", "core.autocrlf", "false")
    runtime = repo / "services" / "runtime"
    runtime.mkdir(parents=True)
    (runtime / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
    inputs = {"Cargo.lock": b"version = 4\n", "lib.rs": b"fn main() {}\n"}
    for name, content in inputs.items():
        (runtime / name).write_bytes(content)
    git("add", "services/runtime")
    git("-c", "user.name=Release Test", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "release source")
    commit = git("rev-parse", "HEAD").decode().strip()
    exports = []
    for autocrlf, eol in (("false", "lf"), ("true", "crlf"), ("input", "native")):
        git("config", "core.autocrlf", autocrlf)
        git("config", "core.eol", eol)
        archive = tmp_path / f"{autocrlf}.tar"
        builder["export_runtime_source"](repo, commit, archive)
        exports.append(archive.read_bytes())
        with tarfile.open(archive) as source:
            for name, content in inputs.items():
                member = source.extractfile(f"services/runtime/{name}")
                assert member is not None and member.read() == content
    assert exports[0] == exports[1] == exports[2]
