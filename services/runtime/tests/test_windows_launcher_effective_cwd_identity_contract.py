"""Source contract guard for target-principal workspace CWD admission.

This is a lexical bridge test, not a substitute for Windows native token/ACL
integration, impersonation correctness, or a Runtime deployment witness.
"""

from pathlib import Path


LAUNCHER = (
    Path(__file__).resolve().parents[1]
    / "platform"
    / "windows"
    / "Ordivon.WindowsJobLauncher.cs"
)


def test_runtime_launcher_checks_cwd_under_target_token_before_spawning():
    source = LAUNCHER.read_text(encoding="utf-8")
    run = source[source.index("private static int RunRuntime(Options options)") :]
    acquire = run.index("executionToken = AcquireExecutionToken(")
    identity = run.index("VerifyExpectedExecutionIdentity(options, tokenEvidence);")
    verify = run.index(
        "VerifyWorkingDirectoryUnderExecutionToken("
        "executionToken, options.WorkingDirectory, tokenEvidence.UserSid);"
    )
    prepare = run.index("PrepareImmutableInputs(options, tokenEvidence);")
    spawn = run.index("if (!CreateProcessAsUserW(")
    assert acquire < identity < verify < prepare < spawn


def test_target_token_cwd_probe_checks_identity_and_directory_enumeration():
    source = LAUNCHER.read_text(encoding="utf-8")
    helper = source[
        source.index("private static void VerifyWorkingDirectoryUnderExecutionToken(") :
        source.index("private static int RunRuntime(Options options)")
    ]
    assert "targetIdentity.Impersonate()" in helper
    assert "WindowsIdentity.GetCurrent()" in helper
    assert "effectiveIdentity.User.Value" in helper
    assert "EnumerateFileSystemInfos()" in helper
    assert "throw new InvalidOperationException" in helper
