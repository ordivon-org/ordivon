from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROKER = ROOT / "platform" / "windows" / "Ordivon.WindowsPrivilegedBroker.cs"
WINDOWS_RS = ROOT / "crates" / "ordivon-runtime-core" / "src" / "runtime" / "windows.rs"
BROKER_RS = ROOT / "crates" / "ordivon-runtime-core" / "src" / "runtime" / "windows_broker.rs"
TYPES_RS = ROOT / "crates" / "ordivon-runtime-core" / "src" / "runtime" / "types.rs"
EXECUTION_RS = ROOT / "crates" / "ordivon-runtime-core" / "src" / "runtime" / "engine" / "execution.rs"
MCP_MAIN = ROOT / "crates" / "ordivon-runtime-mcp" / "src" / "main.rs"


def test_broker_uses_explicit_named_pipe_acl_and_local_system_service_identity():
    text = BROKER.read_text(encoding="utf-8")
    assert "new PipeSecurity()" in text
    assert "SetAccessRuleProtection(true, false)" in text
    assert "WellKnownSidType.LocalSystemSid" in text
    assert "WellKnownSidType.BuiltinAdministratorsSid" in text
    assert "new SecurityIdentifier(allowedClientSid)" in text
    assert "PipeAccessRights.ReadWrite" in text
    assert "EnsureLocalSystem()" in text
    assert "ServiceBase.Run" in text
    assert "BuildPipeSecurity(options.AllowedClientSid)" in text


def test_broker_pins_launcher_digest_and_revalidates_every_request():
    text = BROKER.read_text(encoding="utf-8")
    assert "--launcher-sha256" in text
    assert "Sha256File(options.LauncherPath)" in text
    assert "VerifyPinnedLauncher(options);" in text
    assert "pinned launcher digest changed" in text


def test_broker_surface_is_capture_plus_elevated_runtime_spawn_not_generic_admin_shell():
    text = BROKER.read_text(encoding="utf-8")
    assert 'operation == "capture"' in text
    assert 'operation == "spawn"' in text
    assert "unsupported broker operation" in text
    assert 'operation == "jobObjectPresent"' not in text
    assert 'ContainsPair(args, "--authority", "elevated")' in text
    assert 'ValueAfter(args, "--runtime-bundle")' in text
    assert 'Contains(args, "--runtime-request-digest")' in text
    assert "IsUnderRoot(fullBundle, options.AllowedBundleRoot)" in text
    assert "broker spawn omitted required Runtime launcher identity" in text
    assert 'Contains(args, "--emit-launcher-start")' in text
    assert "broker spawn requires parent-owned launcher-start evidence" in text
    assert "options.LauncherPath" in text
    assert "ProcessStartInfo" in text


def test_broker_spawn_preserves_current_main_launcher_stderr_carrier():
    text = BROKER.read_text(encoding="utf-8")
    rust = BROKER_RS.read_text(encoding="utf-8")
    windows = WINDOWS_RS.read_text(encoding="utf-8")
    assert 'GetString(request, "launcherStderrPath")' in text
    assert 'Path.Combine(fullBundle, "launcher-stderr.log")' in text
    assert "launcher stderr carrier must be the canonical Runtime bundle launcher-stderr.log" in text
    assert "BeginLauncherStderrPump(child, launcherStderrPath)" in text
    assert "process.StandardError.BaseStream.CopyTo(carrier)" in text
    assert "FileOptions.WriteThrough" in text
    assert "launcher_stderr_path: Option<&'a str>" in rust
    assert "launcher_stderr_path: &Path" in rust
    assert 'spec.bundle_path.join("launcher-stderr.log")' in windows
    assert "&launcher_stderr_path" in windows


def test_broker_spawn_returns_parent_observed_process_creation_identity():
    text = BROKER.read_text(encoding="utf-8")
    assert "GetProcessTimes" in text
    assert "ProcessCreationTimeFileTime(child)" in text
    assert "int processId = child.Id" in text
    assert 'result["processId"] = processId' in text
    assert 'result["processCreationTimeFileTime"] = creation' in text
    assert "launcher process creation FILETIME is zero" in text

    rust = BROKER_RS.read_text(encoding="utf-8")
    assert "struct BrokerSpawnObservation" in rust
    assert "launcher_process_id: u32" in rust
    assert "launcher_process_creation_time_file_time: u64" in rust
    assert "process_creation_time_file_time" in rust


def test_broker_protocol_is_bounded_and_never_impersonates_client():
    text = BROKER.read_text(encoding="utf-8")
    assert "MaxMessageBytes = 262144" in text
    assert "MaxCaptureBytes = 65536" in text
    assert "TokenImpersonationLevel.Identification" in text
    assert "ImpersonateNamedPipeClient" not in text


def test_elevated_windows_context_freezes_privileged_broker_digest_and_fails_closed_on_drift():
    types = TYPES_RS.read_text(encoding="utf-8")
    execution = EXECUTION_RS.read_text(encoding="utf-8")
    broker = BROKER_RS.read_text(encoding="utf-8")
    assert "privileged_broker_digest: Option<String>" in types
    assert "privileged_broker_digest =" in execution
    assert "windows_privileged_broker_profile_allowlist_v1" in execution
    assert "verify_digest(expected_broker_digest)" in execution
    assert "LaunchIdentityMismatch" in broker


def test_current_main_preserves_one_native_launch_identity_contract_for_direct_and_broker_paths():
    windows = WINDOWS_RS.read_text(encoding="utf-8")
    execution = EXECUTION_RS.read_text(encoding="utf-8")
    assert "windows_broker::spawn" in windows
    assert "child_process_creation_time_file_time(&child)" in windows
    assert "WindowsNativeLaunchObservation {" in windows
    assert "observation.launcher_process_id" in windows
    assert "launcher_process_creation_time_file_time:" in windows
    assert "bind_native_windows_dispatch_owner(&starting, &dispatch)" in execution
    assert "launcher_process_creation_time_file_time:" in execution


def test_elevated_observe_and_deadline_use_same_authority_router():
    windows = WINDOWS_RS.read_text(encoding="utf-8")
    assert "capture_windows_launcher" in windows
    assert '"--describe-process-owner"' in windows
    assert '"--terminate-process-owner-for-deadline"' in windows
    assert "expected_broker_digest" in windows
    assert "windows_broker::capture" in windows


def test_broker_configuration_is_native_windows_only_and_atomic():
    main = MCP_MAIN.read_text(encoding="utf-8")
    windows = WINDOWS_RS.read_text(encoding="utf-8")
    assert "ORDIVON_WINDOWS_PRIVILEGED_BROKER_PATH" in main
    assert "ORDIVON_WINDOWS_PRIVILEGED_BROKER_PIPE" in main
    assert "must be configured together" in main
    assert "supported only on native Windows Runtime" in main
    assert "Linux/WSL-hosted Windows execution cannot configure the native privileged broker" in windows

def test_broker_normalizes_runtime_verbatim_paths_before_legacy_path_api():
    text = BROKER.read_text(encoding="utf-8")
    assert "NormalizeBrokerPath" in text
    assert 'StartsWith(@"\\\\?\\UNC\\", StringComparison.OrdinalIgnoreCase)' in text
    assert 'StartsWith(@"\\\\?\\", StringComparison.OrdinalIgnoreCase)' in text
    assert "Path.GetFullPath(NormalizeBrokerPath(options.LauncherPath))" in text
    assert "Path.GetFullPath(NormalizeBrokerPath(options.AllowedBundleRoot))" in text
    assert "Path.GetFullPath(NormalizeBrokerPath(bundle))" in text
    assert "Path.GetFullPath(NormalizeBrokerPath(launcherStderrPath))" in text
    assert "Path.GetFullPath(NormalizeBrokerPath(root))" in text
    assert "Path.GetFullPath(NormalizeBrokerPath(path))" in text


def test_broker_client_writes_protocol_json_as_utf8_bytes_not_console_codepage():
    text = BROKER.read_text(encoding="utf-8")
    assert "Encoding.UTF8.GetBytes(response)" in text
    assert "Console.OpenStandardOutput()" in text
    assert "stdout.Write(responseBytes, 0, responseBytes.Length)" in text
    assert "Console.Out.Write(response)" not in text
